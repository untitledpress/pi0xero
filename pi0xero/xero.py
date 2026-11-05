"""
Xero OAuth2 (Authorization Code + PKCE, no client secret) and the few API
calls pi0xero needs. Same flow as xfpa, adapted for a headless Pi: the login
URL is printed, and the callback reaches the Pi either through an SSH tunnel
or by pasting the redirected URL back into the terminal.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import select
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from . import config
from .config import Config

AUTH_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/connections"
API_URL = "https://api.xero.com/api.xro/2.0"
# Granular report scope: new Xero apps can't request accounting.reports.read.
SCOPES = "offline_access accounting.reports.profitandloss.read accounting.settings.read"
REFRESH_MARGIN = timedelta(minutes=2)
TIMEOUT = 30


class LoginRequired(Exception):
    """No usable login: run `python3 -m pi0xero login`."""


class XeroError(Exception):
    """Xero answered, but not with what we needed."""


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_tokens() -> dict:
    return config.read_json(config.TOKENS_FILE) or {}


def _save_tokens(tokens: dict) -> None:
    config.write_json(config.TOKENS_FILE, tokens, private=True)


def _post_token(cfg: Config, data: dict) -> dict:
    resp = requests.post(TOKEN_URL, data={**data, "client_id": cfg.client_id}, timeout=TIMEOUT)
    if resp.status_code in (400, 401):
        raise LoginRequired(f"Xero rejected the login ({resp.status_code}): {resp.text[:200]}")
    resp.raise_for_status()
    return resp.json()


def _store(data: dict, previous: dict) -> dict:
    tokens = dict(previous)
    tokens["access_token"] = data["access_token"]
    # Xero rotates refresh tokens, so always keep the newest one.
    tokens["refresh_token"] = data.get("refresh_token", tokens.get("refresh_token"))
    tokens["expires_at"] = (_now() + timedelta(seconds=int(data.get("expires_in", 1800)))).isoformat()
    _save_tokens(tokens)
    return tokens


def access_token(cfg: Config, force_refresh: bool = False) -> str:
    tokens = _load_tokens()
    if not tokens.get("refresh_token"):
        raise LoginRequired("Not logged in to Xero.")
    expires_at = datetime.fromisoformat(tokens["expires_at"])
    if not force_refresh and expires_at - REFRESH_MARGIN > _now():
        return tokens["access_token"]
    data = _post_token(cfg, {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]})
    return _store(data, tokens)["access_token"]


def connections(cfg: Config) -> list[dict]:
    resp = requests.get(CONNECTIONS_URL, headers={"Authorization": f"Bearer {access_token(cfg)}"},
                        timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def tenant_id(cfg: Config) -> str:
    if cfg.tenant_id:
        return cfg.tenant_id
    tokens = _load_tokens()
    if tokens.get("tenant_id"):
        return tokens["tenant_id"]
    conns = connections(cfg)
    if not conns:
        raise LoginRequired("No Xero organisation is connected.")
    return conns[0]["tenantId"]


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def api_get(cfg: Config, path: str, params: dict | None = None) -> dict:
    tenant = tenant_id(cfg)
    refreshed = force = False
    for attempt in range(4):
        token, force = access_token(cfg, force_refresh=force), False
        headers = {"Authorization": f"Bearer {token}",
                   "xero-tenant-id": tenant, "Accept": "application/json"}
        resp = requests.get(f"{API_URL}/{path}", headers=headers, params=params, timeout=TIMEOUT)
        if resp.status_code == 401 and not refreshed:
            refreshed = force = True
            continue
        if resp.status_code == 401:
            raise LoginRequired("Xero refused the access token.")
        if resp.status_code == 403:
            raise LoginRequired("Xero says this login can't read that data (403). Log in again.")
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = int(resp.headers.get("Retry-After", 0) or 0) or 5 * (attempt + 1)
            time.sleep(min(wait, 60))
            continue
        resp.raise_for_status()
        return resp.json()
    raise XeroError(f"Xero kept failing on {path} (last status {resp.status_code}).")


def organisation(cfg: Config) -> dict:
    orgs = api_get(cfg, "Organisation").get("Organisations") or []
    if not orgs:
        raise XeroError("Xero returned no organisation details.")
    return orgs[0]


def profit_and_loss(cfg: Config, start: date, end: date) -> dict:
    data = api_get(cfg, "Reports/ProfitAndLoss", {
        "fromDate": start.isoformat(), "toDate": end.isoformat(), "standardLayout": "true"})
    reports = data.get("Reports") or []
    if not reports:
        raise XeroError("Xero returned an empty Profit and Loss report.")
    return reports[0]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def login(cfg: Config) -> None:
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(32)
    url = f"{AUTH_URL}?" + urlencode({
        "response_type": "code", "client_id": cfg.client_id, "redirect_uri": cfg.redirect_uri,
        "scope": SCOPES, "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
    })
    done = threading.Event()
    outcome: dict = {}

    def handle(query: str) -> str:
        """Process the callback query string. Returns a message for the user."""
        if done.is_set():
            return "Already finished."
        qs = {k: v[0] for k, v in parse_qs(query).items()}
        if "error" in qs:
            outcome["error"] = f"Xero returned an error: {qs.get('error_description') or qs['error']}"
        elif qs.get("state") != state:
            return "That URL is from a different login attempt. Use the newest one."
        elif not qs.get("code"):
            return "No code in that URL."
        else:
            try:
                data = _post_token(cfg, {"grant_type": "authorization_code", "code": qs["code"],
                                         "redirect_uri": cfg.redirect_uri, "code_verifier": verifier})
                _store(data, {})
                outcome["ok"] = True
            except (LoginRequired, requests.RequestException) as exc:
                outcome["error"] = str(exc)
        done.set()
        return "Connected to Xero. You can close this tab." if outcome.get("ok") else outcome["error"]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self.send_error(404)
                return
            body = f"<!doctype html><meta charset=utf-8><title>pi0xero</title>" \
                   f"<p style='font:18px system-ui;margin:4rem'>{handle(parsed.query)}</p>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = None
    try:
        server = HTTPServer(("127.0.0.1", cfg.redirect_port), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    except OSError as exc:
        print(f"(Couldn't listen on port {cfg.redirect_port}: {exc.strerror}. Use the paste method.)")

    print("\nOpen this URL in a browser on your computer and approve access:\n")
    print(url)
    print("\nIf you started an SSH tunnel (see README), this finishes by itself.")
    print("Otherwise the browser ends on a 'can't connect' page: copy the whole")
    print("address from its address bar and paste it here, then press Enter.\n> ", end="", flush=True)

    deadline = time.time() + 600
    while not done.is_set() and time.time() < deadline:
        ready, _, _ = select.select([sys.stdin], [], [], 0.5)
        if ready:
            line = sys.stdin.readline().strip()
            if not line:
                continue
            msg = handle(urlparse(line).query or line)
            if not done.is_set():
                print(msg + "\n> ", end="", flush=True)
    if server:
        server.shutdown()
        server.server_close()
    if not done.is_set():
        raise LoginRequired("Timed out waiting for the Xero login.")
    if not outcome.get("ok"):
        raise LoginRequired(outcome.get("error", "Login failed."))

    print("\nLogged in.")
    choose_org(cfg)


def choose_org(cfg: Config) -> None:
    conns = connections(cfg)
    if not conns:
        raise LoginRequired("No organisations were authorised. Run login again and tick one.")
    for n, conn in enumerate(conns, 1):
        print(f"  {n}. {conn.get('tenantName')}")
    pick = 0
    if len(conns) > 1 and sys.stdin.isatty():
        answer = input(f"Which organisation should the screen show? [1-{len(conns)}, default 1] ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(conns):
            pick = int(answer) - 1
    tokens = _load_tokens()
    tokens["tenant_id"] = conns[pick]["tenantId"]
    tokens["tenant_name"] = conns[pick].get("tenantName")
    _save_tokens(tokens)
    print(f"Using {conns[pick].get('tenantName')}.")

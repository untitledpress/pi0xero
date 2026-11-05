"""
python3 -m pi0xero login                 log in to Xero (once; see README)
python3 -m pi0xero update                fetch from Xero and redraw the screen
python3 -m pi0xero update --preview x.png   same, but save a PNG instead of using the screen
python3 -m pi0xero demo [--preview x.png]   draw made-up numbers (tests the screen, no Xero)
python3 -m pi0xero orgs                  pick a different organisation
python3 -m pi0xero clear                 blank the screen
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime

import requests

from . import config, display, metrics, xero

log = logging.getLogger("pi0xero")

DEMO = {"org_name": "Demo Company (UK)", "month_label": "Oct", "symbol": "£",
        "revenue_month": 48210.5, "revenue_ttm": 512340.0, "op_month": 10120.0, "op_ttm": 92410.0}


def _output(img, cfg, preview: str | None) -> None:
    if preview:
        img.convert("L").save(preview)
        print(f"Saved {preview}")
    else:
        display.show(img, cfg)


def cmd_update(args) -> int:
    cfg = config.load()
    state = config.read_json(config.STATE_FILE)
    error = None
    try:
        state = metrics.fetch(cfg)
        config.write_json(config.STATE_FILE, state)
        log.info("Revenue %s %.2f, TTM %.2f; op profit %.2f, TTM %.2f", state["month_label"],
                 state["revenue_month"], state["revenue_ttm"], state["op_month"], state["op_ttm"])
    except xero.LoginRequired as exc:
        log.error("Login needed: %s", exc)
        error = "login needed"
    except (requests.RequestException, xero.XeroError) as exc:
        log.error("Xero update failed: %s", exc)
        error = "offline" if isinstance(exc, requests.ConnectionError) else "Xero error"
    _output(display.render(state, error, cfg), cfg, args.preview)
    return 1 if error else 0


def cmd_demo(args) -> int:
    cfg = config.load(require_client_id=False)
    _output(display.render({**DEMO, "fetched_at": datetime.now().isoformat()}, None, cfg), cfg, args.preview)
    return 0


def cmd_login(args) -> int:
    cfg = config.load()
    xero.login(cfg)
    print("Run `python3 -m pi0xero update` to draw the screen.")
    return 0


def cmd_orgs(args) -> int:
    xero.choose_org(config.load())
    return 0


def cmd_clear(args) -> int:
    cfg = config.load(require_client_id=False)
    display.show(display.Image.new("1", (display.WIDTH, display.HEIGHT), 255), cfg)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="pi0xero", description="Xero numbers on a Waveshare 2.13in e-Paper.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in (("update", cmd_update), ("demo", cmd_demo)):
        p = sub.add_parser(name)
        p.add_argument("--preview", metavar="PNG", help="save a PNG instead of drawing on the screen")
        p.set_defaults(func=func)
    for name, func in (("login", cmd_login), ("orgs", cmd_orgs), ("clear", cmd_clear)):
        sub.add_parser(name).set_defaults(func=func)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (config.ConfigError, xero.LoginRequired, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())

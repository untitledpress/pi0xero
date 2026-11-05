"""Settings from config.ini and the paths of the files the app writes."""

from __future__ import annotations

import configparser
import json
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = Path(os.environ.get("PI0XERO_CONFIG", PROJECT_ROOT / "config.ini"))
DATA_DIR = Path(os.environ.get("PI0XERO_DATA", PROJECT_ROOT / "data"))
TOKENS_FILE = DATA_DIR / "tokens.json"
STATE_FILE = DATA_DIR / "state.json"


class ConfigError(Exception):
    pass


@dataclass
class Config:
    client_id: str
    redirect_port: int
    tenant_id: str
    model: str
    waveshare_lib: str
    rotate: int
    title: str
    currency_symbol: str

    @property
    def redirect_uri(self) -> str:
        return f"http://localhost:{self.redirect_port}/callback"


def load(require_client_id: bool = True) -> Config:
    parser = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    if CONFIG_FILE.exists():
        parser.read(CONFIG_FILE)
    elif require_client_id:
        raise ConfigError(f"{CONFIG_FILE} not found. Copy config.example.ini to config.ini first.")

    def get(section: str, key: str, default: str = "") -> str:
        return parser.get(section, key, fallback=default).strip()

    cfg = Config(
        client_id=get("xero", "client_id"),
        redirect_port=int(get("xero", "redirect_port", "5055") or 5055),
        tenant_id=get("xero", "tenant_id"),
        model=get("display", "model", "epd2in13_V4") or "epd2in13_V4",
        waveshare_lib=os.path.expanduser(get("display", "waveshare_lib",
                                             "~/e-Paper/RaspberryPi_JetsonNano/python/lib")),
        rotate=int(get("display", "rotate", "0") or 0),
        title=get("display", "title"),
        currency_symbol=get("display", "currency_symbol"),
    )
    if require_client_id and not cfg.client_id:
        raise ConfigError(f"Set client_id in {CONFIG_FILE}.")
    if cfg.rotate not in (0, 180):
        raise ConfigError("rotate must be 0 or 180.")
    return cfg


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return None


def write_json(path: Path, data: dict, private: bool = False) -> None:
    """Write atomically, so a power cut never leaves half a tokens file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    if private:
        os.chmod(tmp, 0o600)
    os.replace(tmp, path)

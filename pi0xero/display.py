"""
Draw the 250x122 picture and push it to the Waveshare 2.13" e-Paper HAT.

Layout (landscape):

    +---------------------------------------------+
    | Org name                     upd 5 Nov 14:30 |  black bar
    +----------------------+----------------------+
    | Revenue Oct          | Revenue TTM          |
    | £48.2k               | £512k                |
    +----------------------+----------------------+
    | Op profit Oct    21% | Op profit TTM    18% |
    | £10.1k               | £92.4k               |
    +----------------------+----------------------+
"""

from __future__ import annotations

import importlib
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import Config

WIDTH, HEIGHT = 250, 122
HEADER = 18

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/System/Library/Fonts/Supplemental", "C:/Windows/Fonts"]
REGULAR = ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf"]
BOLD = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"]


def _font(names: list[str], size: int):
    for folder in FONT_DIRS:
        for name in names:
            path = Path(folder) / name
            if path.exists():
                return ImageFont.truetype(str(path), size)
    try:
        return ImageFont.load_default(size)   # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def money(value: float | None, symbol: str = "£") -> str:
    """Short money: £950, £48.2k, £512k, £1.24m."""
    if value is None:
        return "-"
    sign = "-" if value < 0 else ""
    v = abs(value)
    if v < 1_000:
        body = f"{v:,.0f}"
    elif v < 100_000:
        body = f"{v / 1_000:.1f}k"
    elif v < 1_000_000:
        body = f"{v / 1_000:.0f}k"
    elif v < 100_000_000:
        body = f"{v / 1_000_000:.2f}m"
    else:
        body = f"{v / 1_000_000:.0f}m"
    return f"{sign}{symbol}{body}"


def _percent(part: float, whole: float) -> str:
    return f"{part / whole * 100:.0f}%" if whole > 0 else ""


def _truncate(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    return text.rstrip() + "…"


def _fit(draw: ImageDraw.ImageDraw, text: str, names: list[str], size: int, max_width: int):
    """Largest font (from size down) that fits text inside max_width."""
    while size > 8:
        font = _font(names, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 1
    return _font(names, 8)


def _when(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%-d %b %H:%M")
    except ValueError:
        return iso


def render(state: dict | None, error: str | None = None, cfg: Config | None = None) -> Image.Image:
    img = Image.new("1", (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(img)
    small = _font(REGULAR, 11)

    # Header bar
    draw.rectangle((0, 0, WIDTH - 1, HEADER - 1), fill=0)
    title = (cfg.title if cfg and cfg.title else "") or (state or {}).get("org_name") or "pi0xero"
    right = f"! {error}" if error else f"upd {_when((state or {}).get('fetched_at'))}"
    if error and state:
        right += f" ({_when(state.get('fetched_at'))})"
    right_font = _fit(draw, right, REGULAR, 11, WIDTH - 60)
    right_w = draw.textlength(right, font=right_font)
    draw.text((WIDTH - 4 - right_w, HEADER // 2), right, font=right_font, fill=255, anchor="lm")
    title_width = max(40, int(WIDTH - right_w - 14))
    title_font = _fit(draw, title, BOLD, 12, title_width) if len(title) < 30 else _font(BOLD, 11)
    title = _truncate(draw, title, title_font, title_width)
    draw.text((4, HEADER // 2), title, font=title_font, fill=255, anchor="lm")

    if not state:
        message = "Waiting for the first Xero update." if not error else "No data yet. See README."
        draw.text((WIDTH // 2, (HEIGHT + HEADER) // 2), message, font=small, fill=0, anchor="mm")
        return _rotate(img, cfg)

    sym = (cfg.currency_symbol if cfg and cfg.currency_symbol else None) or state.get("symbol", "")
    month = state.get("month_label", "")
    cells = [
        (f"Revenue {month}", money(state["revenue_month"], sym), ""),
        ("Revenue TTM", money(state["revenue_ttm"], sym), ""),
        (f"Op profit {month}", money(state["op_month"], sym), _percent(state["op_month"], state["revenue_month"])),
        ("Op profit TTM", money(state["op_ttm"], sym), _percent(state["op_ttm"], state["revenue_ttm"])),
    ]

    col_w = WIDTH // 2
    row_h = (HEIGHT - HEADER) // 2
    draw.line((col_w, HEADER, col_w, HEIGHT), fill=0)
    draw.line((0, HEADER + row_h, WIDTH, HEADER + row_h), fill=0)
    for i, (label, value, note) in enumerate(cells):
        x = (i % 2) * col_w + 5
        y = HEADER + (i // 2) * row_h + 4
        inner = col_w - 10
        draw.text((x, y), label, font=small, fill=0)
        if note:
            draw.text((x + inner, y), note, font=small, fill=0, anchor="ra")
        value_font = _fit(draw, value, BOLD, 26, inner)
        draw.text((x, y + row_h - 8), value, font=value_font, fill=0, anchor="ls")
    return _rotate(img, cfg)


def _rotate(img: Image.Image, cfg: Config | None) -> Image.Image:
    return img.rotate(180) if cfg and cfg.rotate == 180 else img


def show(img: Image.Image, cfg: Config) -> None:
    """Full refresh of the e-Paper, then put it to sleep (it keeps the picture with no power)."""
    if cfg.waveshare_lib not in sys.path:
        sys.path.insert(0, cfg.waveshare_lib)
    try:
        module = importlib.import_module(f"waveshare_epd.{cfg.model}")
    except ImportError as exc:
        raise RuntimeError(f"Can't load the Waveshare driver waveshare_epd.{cfg.model} from "
                           f"{cfg.waveshare_lib} ({exc}). See README, step 4.") from exc

    epd = module.EPD()
    try:
        epd.init()
    except TypeError:                       # V2 driver wants the update mode
        epd.init(epd.FULL_UPDATE)
    buffer = epd.getbuffer(img)
    try:
        epd.display(buffer)
    except TypeError:                       # black/red "B" panels take a second (red) layer
        epd.display(buffer, epd.getbuffer(Image.new("1", img.size, 255)))
    epd.sleep()

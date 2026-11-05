"""
Turn Xero Profit and Loss reports into the four numbers on the screen.

Revenue           = Xero's total income line (trading income / turnover).
Operating profit  = gross profit - operating expenses. Other income and
                    anything below operating expenses are left out.
Last month        = the last complete calendar month.
TTM               = the 12 complete months ending with last month.

One P&L call per month (12 calls), the same way xfpa does it: a single
12-month call can trip Xero's 365-day limit in a leap year.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime

from . import xero
from .config import Config

INCOME = ("total income", "total trading income", "total revenue", "total turnover", "total sales")
COST_OF_SALES = ("total cost of sales", "total direct costs")
GROSS = ("gross profit",)
OPEX = ("total operating expenses", "total administrative", "total overheads", "total expenses")

CURRENCY_SYMBOLS = {"GBP": "£", "USD": "$", "AUD": "$", "NZD": "$", "CAD": "$", "SGD": "$", "HKD": "$",
                    "EUR": "€", "ZAR": "R", "JPY": "¥", "INR": "₹", "CHF": "CHF "}


def last_twelve_months(today: date) -> list[tuple[date, date]]:
    """(first day, last day) of each of the 12 complete months before today, oldest first."""
    year, month = today.year, today.month
    months = []
    for _ in range(12):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        months.append((date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])))
    return list(reversed(months))


def _rows(rows: list[dict]):
    """Yield (label, first value cell) for every row, walking into sections."""
    for row in rows or []:
        if row.get("Rows"):
            yield from _rows(row["Rows"])
        cells = row.get("Cells") or []
        if row.get("RowType") in ("Row", "SummaryRow") and len(cells) >= 2:
            yield str(cells[0].get("Value") or "").strip().lower(), cells[1].get("Value")


def _num(value) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def pnl_lines(report: dict) -> dict[str, float]:
    found: dict[str, float] = {}
    for label, value in _rows(report.get("Rows", [])):
        for key, names in (("income", INCOME), ("cos", COST_OF_SALES), ("gross", GROSS), ("opex", OPEX)):
            if key not in found and any(label.startswith(n) for n in names):
                found[key] = _num(value)
    income, cos, opex = found.get("income", 0.0), found.get("cos", 0.0), found.get("opex", 0.0)
    gross = found.get("gross", income - cos)
    return {"income": income, "cos": cos, "gross": gross, "opex": opex, "operating": gross - opex}


def summarise(months: list[tuple[date, dict[str, float]]]) -> dict:
    """months: [(month end, pnl_lines)], oldest first, last one = last month."""
    last_end, last = months[-1]
    return {
        "month_label": last_end.strftime("%b"),
        "month_end": last_end.isoformat(),
        "revenue_month": round(last["income"], 2),
        "revenue_ttm": round(sum(m["income"] for _, m in months), 2),
        "op_month": round(last["operating"], 2),
        "op_ttm": round(sum(m["operating"] for _, m in months), 2),
    }


def fetch(cfg: Config, today: date | None = None) -> dict:
    org = xero.organisation(cfg)
    months = []
    for start, end in last_twelve_months(today or date.today()):
        months.append((end, pnl_lines(xero.profit_and_loss(cfg, start, end))))
    result = summarise(months)
    currency = org.get("BaseCurrency", "")
    result.update({
        "org_name": org.get("Name", ""),
        "currency": currency,
        "symbol": CURRENCY_SYMBOLS.get(currency, f"{currency} " if currency else ""),
        "fetched_at": datetime.now().isoformat(timespec="minutes"),
    })
    return result

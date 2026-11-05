from datetime import date

from pi0xero import display, metrics


def _report(income, cos, opex, gross_row=True):
    rows = [
        {"RowType": "Header", "Cells": [{"Value": ""}, {"Value": "31 Oct 2026"}]},
        {"RowType": "Section", "Title": "Trading Income", "Rows": [
            {"RowType": "Row", "Cells": [{"Value": "Sales"}, {"Value": str(income)}]},
            {"RowType": "SummaryRow", "Cells": [{"Value": "Total Trading Income"}, {"Value": str(income)}]}]},
        {"RowType": "Section", "Title": "Cost of Sales", "Rows": [
            {"RowType": "SummaryRow", "Cells": [{"Value": "Total Cost of Sales"}, {"Value": str(cos)}]}]},
    ]
    if gross_row:
        rows.append({"RowType": "Section", "Title": "", "Rows": [
            {"RowType": "Row", "Cells": [{"Value": "Gross Profit"}, {"Value": str(income - cos)}]}]})
    rows += [
        {"RowType": "Section", "Title": "Operating Expenses", "Rows": [
            {"RowType": "Row", "Cells": [{"Value": "Rent"}, {"Value": str(opex)}]},
            {"RowType": "SummaryRow", "Cells": [{"Value": "Total Operating Expenses"}, {"Value": str(opex)}]}]},
        {"RowType": "Section", "Title": "", "Rows": [
            {"RowType": "Row", "Cells": [{"Value": "Net Profit"}, {"Value": str(income - cos - opex)}]}]},
    ]
    return {"Rows": rows}


def test_pnl_lines():
    lines = metrics.pnl_lines(_report(1000, 300, 200))
    assert lines == {"income": 1000, "cos": 300, "gross": 700, "opex": 200, "operating": 500}


def test_pnl_lines_without_gross_row():
    assert metrics.pnl_lines(_report(1000, 300, 200, gross_row=False))["operating"] == 500


def test_months_cross_year():
    months = metrics.last_twelve_months(date(2026, 1, 15))
    assert months[0] == (date(2025, 1, 1), date(2025, 1, 31))
    assert months[-1] == (date(2025, 12, 1), date(2025, 12, 31))
    assert len(months) == 12


def test_summarise():
    months = [(end, {"income": 100.0, "operating": 10.0}) for _, end in metrics.last_twelve_months(date(2026, 11, 5))]
    s = metrics.summarise(months)
    assert s["month_label"] == "Oct"
    assert (s["revenue_month"], s["revenue_ttm"], s["op_month"], s["op_ttm"]) == (100, 1200, 10, 120)


def test_money():
    assert display.money(950, "£") == "£950"
    assert display.money(48210, "£") == "£48.2k"
    assert display.money(512340, "£") == "£512k"
    assert display.money(1_240_000, "$") == "$1.24m"
    assert display.money(-12_300, "£") == "-£12.3k"

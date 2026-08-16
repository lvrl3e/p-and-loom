"""Small formatting helpers shared across pages."""


def fmt_currency(value) -> str:
    if value is None:
        return "—"
    return f"${value:,.2f}"


def fmt_currency_signed(value) -> str:
    if value is None or value != value:  # None or NaN
        return "—"
    sign = "+" if value >= 0 else "-"
    return f"{sign}${abs(value):,.2f}"


def fmt_pct(value) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"



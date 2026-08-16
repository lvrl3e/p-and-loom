"""Small formatting helpers shared across pages."""


def fmt_currency(value) -> str:
    if value is None:
        return "—"
    return f"${value:,.2f}"


def fmt_pct(value) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


def fmt_ratio(value) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


def fmt_days(value) -> str:
    if value is None or value != value:  # NaN check
        return "—"
    return f"{value:.1f}"

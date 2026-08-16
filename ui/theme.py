"""
Design system for the trading journal: color tokens, global CSS injection,
and small HTML component builders (stat cards, tags, badges) used across
views for a consistent, hand-styled look on top of Streamlit's defaults.
"""

import html

import streamlit as st

BG = "#0D0D0F"
CARD_BG = "#17171A"
BORDER = "rgba(255, 255, 255, 0.08)"
TEXT_PRIMARY = "#F5F5F5"
TEXT_SECONDARY = "#A1A1AA"
ACCENT_SOFT = "#F4A6C1"
ACCENT = "#E85D9E"
ACCENT_HOVER = "#F070AC"
ACCENT_LIGHT = "#FFD6E5"
GOOD = "#22C55E"
BAD = "#EF4444"
NEUTRAL = "#A1A1AA"

GOOD_BG = "rgba(34, 197, 94, 0.12)"
BAD_BG = "rgba(239, 68, 68, 0.12)"

# Minimal stroke-style icon set (Feather-icon path data, MIT-licensed shapes)
# rendered inline so cards don't depend on an external icon font loading.
_ICON_PATHS = {
    "dollar": '<line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>',
    "target": '<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>',
    "bars": '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
    "trending-up": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline>',
    "trending-down": '<polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>',
    "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline>',
    "pulse": '<circle cx="12" cy="12" r="10"></circle><polyline points="8 12 10.5 14.5 12 9 13.5 15 16 12"></polyline>',
}


def icon_svg(name: str, size: int = 16) -> str:
    path = _ICON_PATHS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{path}</svg>'
    )


def sparkline_svg(values: list, color: str, width: int = 96, height: int = 28) -> str:
    """Tiny inline trend line for a card — not a full chart, just a shape."""
    vals = [v for v in values if v == v]  # drop NaN
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pad = 3
    n = len(vals)
    points = [
        f"{(i / (n - 1)) * (width - 2 * pad) + pad:.1f},{height - pad - ((v - lo) / span) * (height - 2 * pad):.1f}"
        for i, v in enumerate(vals)
    ]
    polyline = " ".join(points)
    last_x, last_y = points[-1].split(",")
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{color}"/>'
        f"</svg>"
    )


def esc(text) -> str:
    """HTML-escape user-entered text before embedding it in unsafe_allow_html markup."""
    if text is None:
        return ""
    return html.escape(str(text))


def pnl_color(value) -> str:
    if value is None or value != value:  # None or NaN
        return NEUTRAL
    return GOOD if value >= 0 else BAD


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, button, input, select, textarea {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        [data-testid="stAppViewContainer"], .stApp {{
            background-color: {BG};
        }}
        [data-testid="stHeader"] {{
            background-color: {BG};
            border-bottom: 1px solid {BORDER};
        }}
        [data-testid="stMainBlockContainer"] {{
            padding-top: 2.75rem;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {BG};
            border-right: 1px solid {BORDER};
        }}
        [data-testid="stSidebarNav"] {{
            padding-top: 0.25rem;
        }}
        [data-testid="stSidebarNavLink"] {{
            border-radius: 10px;
            margin: 2px 12px;
            transition: background-color 0.15s ease;
        }}
        [data-testid="stSidebarNavLink"]:hover {{
            background-color: rgba(232, 93, 158, 0.10);
        }}
        [data-testid="stSidebarNavLink"] span {{
            color: {TEXT_SECONDARY} !important;
            font-weight: 500;
        }}
        [data-testid="stSidebarNavLink"] svg {{
            fill: {TEXT_SECONDARY} !important;
        }}
        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background-color: {ACCENT};
        }}
        [data-testid="stSidebarNavLink"][aria-current="page"] span {{
            color: {BG} !important;
            font-weight: 700;
        }}
        [data-testid="stSidebarNavLink"][aria-current="page"] svg {{
            fill: {BG} !important;
        }}

        .tj-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 12px 16px 12px;
            border-bottom: 1px solid {BORDER};
        }}
        .tj-brand-mark {{
            width: 32px;
            height: 32px;
            border-radius: 9px;
            background: {ACCENT};
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: {BG};
            font-size: 0.95rem;
            flex-shrink: 0;
        }}
        .tj-brand-name {{
            color: {TEXT_PRIMARY};
            font-weight: 700;
            font-size: 0.95rem;
            line-height: 1.15;
        }}
        .tj-brand-sub {{
            display: flex;
            align-items: center;
            gap: 5px;
            color: {TEXT_SECONDARY};
            font-size: 0.7rem;
        }}
        .tj-pulse-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: {GOOD};
            box-shadow: 0 0 0 2px {GOOD_BG};
            flex-shrink: 0;
        }}

        .tj-side-panel {{
            padding: 14px 12px 6px 12px;
        }}
        .tj-side-panel-label {{
            color: {TEXT_SECONDARY};
            font-size: 0.66rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .tj-side-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 7px 0;
        }}
        .tj-side-row-label {{
            color: {TEXT_SECONDARY};
            font-size: 0.78rem;
        }}
        .tj-side-row-value {{
            font-weight: 700;
            font-size: 0.82rem;
            font-variant-numeric: tabular-nums;
        }}

        /* Buttons */
        .stButton > button, .stFormSubmitButton > button {{
            background-color: {ACCENT};
            color: {BG};
            border: none;
            border-radius: 10px;
            font-weight: 600;
            padding: 0.5rem 1.25rem;
            white-space: nowrap;
            transition: background-color 0.15s ease;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover,
        .stButton > button:focus:not(:active), .stFormSubmitButton > button:focus:not(:active) {{
            background-color: {ACCENT_HOVER};
            color: {BG};
        }}
        .stButton > button[kind="secondary"] {{
            background-color: transparent;
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
        }}
        .stButton > button[kind="secondary"]:hover {{
            border-color: {ACCENT};
            color: {ACCENT};
            background-color: transparent;
        }}
        [data-testid="stPageLink"] {{
            border-radius: 10px;
        }}

        /* Cards (via st.container(key=...)) */
        {" ".join(f'.st-key-{key} {{ background-color: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 16px; padding: 22px 24px; margin-bottom: 4px; transition: border-color 0.15s ease; }}' for key in CARD_KEYS)}
        {" ".join(f'.st-key-{key}:hover {{ border-color: rgba(232, 93, 158, 0.35); }}' for key in CARD_KEYS)}

        .tj-page-header {{
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 1.75rem;
        }}
        .tj-page-header-icon {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: rgba(232, 93, 158, 0.12);
            color: {ACCENT};
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .tj-page-header-title {{
            font-size: 1.5rem;
            font-weight: 800;
            color: {TEXT_PRIMARY};
            line-height: 1.2;
        }}
        .tj-page-header-sub {{
            color: {TEXT_SECONDARY};
            font-size: 0.88rem;
            margin-top: 2px;
        }}

        .tj-card-header {{
            margin-bottom: 16px;
        }}
        .tj-card-header-top {{
            display: flex;
            align-items: center;
            gap: 9px;
        }}
        .tj-card-header-icon {{
            width: 26px;
            height: 26px;
            border-radius: 8px;
            background: rgba(232, 93, 158, 0.12);
            color: {ACCENT};
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .tj-card-header-title {{
            font-size: 1.02rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
        }}
        .tj-card-header-sub {{
            font-size: 0.78rem;
            color: {TEXT_SECONDARY};
            margin-top: 3px;
            margin-left: 35px;
        }}

        /* DataFrame */
        [data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 12px;
            overflow: hidden;
        }}

        /* Forms */
        [data-testid="stForm"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 1.75rem 1.75rem 1.25rem 1.75rem;
        }}

        /* Expander */
        [data-testid="stExpander"] {{
            border: 1px solid {BORDER};
            border-radius: 12px;
            background-color: {CARD_BG};
        }}
        [data-testid="stExpander"] summary {{
            color: {TEXT_PRIMARY};
        }}

        /* Tabs */
        [data-baseweb="tab-list"] {{
            gap: 4px;
            border-bottom: 1px solid {BORDER};
        }}
        [data-baseweb="tab"] {{
            color: {TEXT_SECONDARY};
        }}
        [data-baseweb="tab"] p {{
            color: inherit;
            font-weight: 600;
        }}
        [aria-selected="true"][data-baseweb="tab"] {{
            color: {ACCENT} !important;
        }}
        [data-baseweb="tab-highlight"] {{
            background-color: {ACCENT} !important;
        }}

        /* Alerts */
        [data-testid="stAlert"] {{
            border-radius: 12px;
        }}

        /* Inputs */
        [data-baseweb="select"] > div, [data-baseweb="input"] {{
            border-radius: 8px !important;
            background-color: {CARD_BG};
        }}
        [data-testid="stTextArea"] textarea {{
            border-radius: 8px;
        }}

        hr {{
            border-color: {BORDER};
        }}

        /* Hand-rolled components */
        .tj-stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 14px;
        }}
        .tj-stat {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-left: 3px solid {TEXT_SECONDARY};
            border-radius: 12px;
            padding: 16px 18px;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }}
        .tj-stat:hover {{
            transform: translateY(-2px);
        }}
        .tj-stat-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 14px;
        }}
        .tj-stat-label {{
            color: {TEXT_SECONDARY};
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
            padding-top: 4px;
        }}
        .tj-stat-icon {{
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .tj-stat-value {{
            font-size: 1.55rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            line-height: 1.2;
            color: {TEXT_PRIMARY};
        }}
        .tj-stat-sub {{
            font-size: 0.76rem;
            color: {TEXT_SECONDARY};
            margin-top: 6px;
            font-variant-numeric: tabular-nums;
        }}
        .tj-stat-spark {{
            margin-top: 10px;
            line-height: 0;
            opacity: 0.9;
        }}

        .tj-tag {{
            display: inline-block;
            background: {ACCENT_LIGHT};
            color: #17171A;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 11px;
            border-radius: 999px;
            margin: 2px 5px 2px 0;
        }}
        .tj-tag-outline {{
            display: inline-block;
            background: transparent;
            color: {ACCENT_SOFT};
            border: 1px solid rgba(244, 166, 193, 0.35);
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 10px;
            border-radius: 999px;
            margin: 2px 5px 2px 0;
        }}
        .tj-badge {{
            display: inline-block;
            border-radius: 6px;
            padding: 2px 9px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        .tj-badge-long {{ color: {GOOD}; background: {GOOD_BG}; }}
        .tj-badge-short {{ color: {BAD}; background: {BAD_BG}; }}
        .tj-badge-open {{ color: {ACCENT}; background: rgba(232, 93, 158, 0.12); }}

        .tj-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.86rem;
        }}
        .tj-table th {{
            text-align: left;
            color: {TEXT_SECONDARY};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.66rem;
            letter-spacing: 0.05em;
            padding: 6px 12px 10px 0;
            border-bottom: 1px solid {BORDER};
        }}
        .tj-table td {{
            padding: 11px 12px 11px 0;
            border-bottom: 1px solid {BORDER};
            color: {TEXT_PRIMARY};
            font-variant-numeric: tabular-nums;
        }}
        .tj-table tr:last-child td {{
            border-bottom: none;
        }}
        .tj-table td.tj-muted {{
            color: {TEXT_SECONDARY};
        }}

        .tj-empty {{
            text-align: center;
            padding: 48px 20px;
            color: {TEXT_SECONDARY};
        }}
        .tj-empty-title {{
            color: {TEXT_PRIMARY};
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 6px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Container keys that should render as cards — CSS rules are generated for
# each of these from a single source of truth so views only need to pass a
# matching `key=` to st.container().
CARD_KEYS = [
    "stat-row",
    "card-equity",
    "card-distribution",
    "card-strategy",
    "card-recent-trades",
    "card-breakdown",
]


def stat_card(
    label: str,
    value: str,
    icon: str,
    accent: str = TEXT_PRIMARY,
    sub: str | None = None,
    value_color: str | None = None,
    spark: list | None = None,
) -> str:
    # NOTE: this must stay a single line with no embedded blank/whitespace-only
    # lines. Streamlit's markdown renderer treats a blank line inside a raw
    # HTML block as the end of that block, so any indented multi-line template
    # here would spill the remaining tags out as visible literal text.
    value_color = value_color or accent
    sub_html = f'<div class="tj-stat-sub">{sub}</div>' if sub else ""
    spark_html = (
        f'<div class="tj-stat-spark">{sparkline_svg(spark, accent)}</div>'
        if spark and len([v for v in spark if v == v]) >= 2
        else ""
    )
    icon_html = (
        f'<div class="tj-stat-icon" style="color:{accent}; background:{accent}1F;">{icon_svg(icon)}</div>'
    )
    return (
        f'<div class="tj-stat" style="border-left-color:{accent};">'
        f'<div class="tj-stat-top"><div class="tj-stat-label">{label}</div>{icon_html}</div>'
        f'<div class="tj-stat-value" style="color:{value_color};">{value}</div>'
        f"{sub_html}{spark_html}</div>"
    )


def stat_grid(cards_html: list[str]) -> str:
    return f'<div class="tj-stat-grid">{"".join(cards_html)}</div>'


def page_header(title: str, subtitle: str, icon: str) -> str:
    return (
        '<div class="tj-page-header">'
        f'<div class="tj-page-header-icon">{icon_svg(icon, 20)}</div>'
        f'<div><div class="tj-page-header-title">{esc(title)}</div>'
        f'<div class="tj-page-header-sub">{esc(subtitle)}</div></div>'
        "</div>"
    )


def card_header(title: str, subtitle: str | None = None, icon: str | None = None) -> str:
    icon_html = f'<div class="tj-card-header-icon">{icon_svg(icon, 15)}</div>' if icon else ""
    sub_html = f'<div class="tj-card-header-sub">{esc(subtitle)}</div>' if subtitle else ""
    return (
        '<div class="tj-card-header">'
        f'<div class="tj-card-header-top">{icon_html}<div class="tj-card-header-title">{esc(title)}</div></div>'
        f"{sub_html}</div>"
    )


def sidebar_panel(label: str, rows: list) -> str:
    """rows: list of (row_label, row_value, value_color) tuples."""
    rows_html = "".join(
        f'<div class="tj-side-row"><div class="tj-side-row-label">{esc(rl)}</div>'
        f'<div class="tj-side-row-value" style="color:{vc};">{rv}</div></div>'
        for rl, rv, vc in rows
    )
    return f'<div class="tj-side-panel"><div class="tj-side-panel-label">{esc(label)}</div>{rows_html}</div>'


def tag(text: str, outline: bool = False) -> str:
    cls = "tj-tag-outline" if outline else "tj-tag"
    return f'<span class="{cls}">{esc(text)}</span>'


def direction_badge(direction: str) -> str:
    cls = "tj-badge-long" if direction == "Long" else "tj-badge-short"
    return f'<span class="tj-badge {cls}">{direction}</span>'


def status_badge(status: str) -> str:
    if status == "Open":
        return '<span class="tj-badge tj-badge-open">Open</span>'
    return ""

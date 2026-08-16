"""
Design system for the trading journal: color tokens, global CSS injection,
and small HTML component builders (stat cards, tags, badges, progress bars,
account cards, calendar cells) used across views for a consistent,
hand-styled look on top of Streamlit's defaults.
"""

import base64
import html
import os

import streamlit as st

_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
_LOGO_ICON_PATH = os.path.join(_PROJECT_ROOT, "docs", "logo-icon.png")


@st.cache_data
def logo_icon_data_uri() -> str:
    """Base64 data URI for the P&Loom icon mark — raw <img> tags in
    st.markdown(unsafe_allow_html=True) can't reference local file paths
    (Streamlit doesn't serve arbitrary project files over HTTP), so the
    image bytes are inlined instead. Cached so the file is only read once
    per server process, not on every rerun."""
    with open(_LOGO_ICON_PATH, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

# Two full palettes, swapped per-request by apply_theme() based on the
# viewer's actual active theme (st.context.theme.type — reflects OS/browser
# "prefers-color-scheme" when the user hasn't overridden it, and Streamlit's
# own theme picker when they have). Module-level names below default to the
# dark set; apply_theme() overwrites them in place before anything else in
# a run reads them, and every function in this file reads the bare names
# (not a frozen import), so a single call at the top of app.py keeps
# everything — CSS, HTML components, chart colors — in sync.
_DARK = dict(
    BG="#0D0D0F",
    CARD_BG="#17171A",
    BORDER="rgba(255, 255, 255, 0.08)",
    TEXT_PRIMARY="#F5F5F5",
    TEXT_SECONDARY="#A1A1AA",
    ACCENT_SOFT="#F4A6C1",
    ACCENT="#E85D9E",
    ACCENT_HOVER="#F070AC",
    ACCENT_LIGHT="#FFD6E5",
    ON_ACCENT="#0D0D0F",
    GOOD="#22C55E",
    BAD="#EF4444",
    NEUTRAL="#A1A1AA",
    GOOD_BG="rgba(34, 197, 94, 0.12)",
    BAD_BG="rgba(239, 68, 68, 0.12)",
    NEUTRAL_BG="rgba(161, 161, 170, 0.12)",
)

_LIGHT = dict(
    BG="#FAFAFA",
    CARD_BG="#FFFFFF",
    BORDER="rgba(0, 0, 0, 0.08)",
    TEXT_PRIMARY="#111114",
    TEXT_SECONDARY="#6B6B76",
    ACCENT_SOFT="#D6478C",
    ACCENT="#D6478C",
    ACCENT_HOVER="#B93C74",
    ACCENT_LIGHT="#FFE3ED",
    ON_ACCENT="#0D0D0F",
    GOOD="#16A34A",
    BAD="#DC2626",
    NEUTRAL="#71717A",
    GOOD_BG="rgba(22, 163, 74, 0.10)",
    BAD_BG="rgba(220, 38, 38, 0.10)",
    NEUTRAL_BG="rgba(113, 113, 122, 0.10)",
)

# Safe defaults (dark) until apply_theme() runs.
BG = _DARK["BG"]
CARD_BG = _DARK["CARD_BG"]
BORDER = _DARK["BORDER"]
TEXT_PRIMARY = _DARK["TEXT_PRIMARY"]
TEXT_SECONDARY = _DARK["TEXT_SECONDARY"]
ACCENT_SOFT = _DARK["ACCENT_SOFT"]
ACCENT = _DARK["ACCENT"]
ACCENT_HOVER = _DARK["ACCENT_HOVER"]
ACCENT_LIGHT = _DARK["ACCENT_LIGHT"]
ON_ACCENT = _DARK["ON_ACCENT"]
GOOD = _DARK["GOOD"]
BAD = _DARK["BAD"]
NEUTRAL = _DARK["NEUTRAL"]
GOOD_BG = _DARK["GOOD_BG"]
BAD_BG = _DARK["BAD_BG"]
NEUTRAL_BG = _DARK["NEUTRAL_BG"]

CURRENT_MODE = "dark"


_SESSION_KEY = "_theme_mode"


def apply_theme() -> str:
    """Detects the viewer's active theme and updates every color name in
    this module to match. Call once, at the very top of app.py, before
    inject_css() or anything else that reads a color. Returns "dark" or
    "light" (also stored as CURRENT_MODE) in case a caller needs to branch
    on it directly (e.g. Plotly template choice).

    st.context.theme.type only reflects the browser's real
    prefers-color-scheme on a session's very first script run — confirmed
    empirically, not a guess: on every later rerun (which includes every
    st.navigation page switch, since those go over the same WebSocket
    rather than reloading the page) it silently reports a different,
    wrong value. So the first good reading is cached in session_state and
    reused for the rest of the session instead of re-trusting it each run.
    """
    global CURRENT_MODE
    cached = st.session_state.get(_SESSION_KEY)
    if cached in ("light", "dark"):
        mode = cached
    else:
        try:
            theme_type = st.context.theme.type
        except Exception:
            theme_type = None
        mode = theme_type if theme_type in ("light", "dark") else "dark"
        st.session_state[_SESSION_KEY] = mode
    globals().update(_LIGHT if mode == "light" else _DARK)
    CURRENT_MODE = mode
    return mode

# Curated palette for account color-coding — small, harmonious, colorblind-
# distinct set (borrowed from the categorical hues used elsewhere), pink
# reserved as the app's own default so a fresh account matches the brand.
ACCOUNT_COLORS = ["#E85D9E", "#2A78D6", "#1BAF7A", "#EDA100", "#4A3AA7", "#A1A1AA"]

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
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line>',
    "trash": '<polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>',
    "edit": '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>',
    "chevron-down": '<polyline points="6 9 12 15 18 9"></polyline>',
    "wallet": '<path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"></path><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"></path><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"></path>',
    "flame": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>',
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

        html, body, button, input, select, textarea {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .tj-display {{
            font-family: 'Space Grotesk', 'Inter', sans-serif;
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
            color: {ON_ACCENT} !important;
            font-weight: 700;
        }}
        [data-testid="stSidebarNavLink"][aria-current="page"] svg {{
            fill: {ON_ACCENT} !important;
        }}

        .tj-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 12px 16px 12px;
            border-bottom: 1px solid {BORDER};
        }}
        .tj-brand-mark-img {{
            width: 34px;
            height: 34px;
            border-radius: 9px;
            object-fit: cover;
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
        .tj-side-account {{
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 10px 12px;
            margin: 4px 8px;
            border-radius: 10px;
            background: {CARD_BG};
            border: 1px solid {BORDER};
        }}
        .tj-side-account-dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .tj-side-account-name {{
            color: {TEXT_PRIMARY};
            font-weight: 700;
            font-size: 0.8rem;
            line-height: 1.2;
        }}
        .tj-side-account-size {{
            color: {TEXT_SECONDARY};
            font-size: 0.7rem;
        }}

        /* Buttons */
        .stButton > button, .stFormSubmitButton > button {{
            background-color: {ACCENT};
            color: {ON_ACCENT};
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
            color: {ON_ACCENT};
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

        /* Cards (via st.container(key=...)) — fixed, known-in-advance keys */
        {" ".join(f'.st-key-{key} {{ background-color: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 16px; padding: 22px 24px; margin-bottom: 4px; transition: border-color 0.15s ease; }}' for key in CARD_KEYS)}
        {" ".join(f'.st-key-{key}:hover {{ border-color: rgba(232, 93, 158, 0.35); }}' for key in CARD_KEYS)}

        /* Cards with dynamic, data-driven keys (account id, screenshot id, ...) —
           matched by prefix since the exact key set isn't known up front. */
        [class*="st-key-acct-"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 20px 22px;
            min-height: 230px;
            box-sizing: border-box;
            transition: border-color 0.15s ease, transform 0.15s ease;
        }}
        [class*="st-key-acct-"]:hover {{
            border-color: rgba(232, 93, 158, 0.35);
            transform: translateY(-2px);
        }}
        [class*="st-key-shot-"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 10px;
            transition: border-color 0.15s ease;
        }}
        [class*="st-key-shot-"]:hover {{
            border-color: rgba(232, 93, 158, 0.35);
        }}
        [class*="st-key-calday-"] {{
            border-radius: 10px;
            padding: 3px;
            box-sizing: border-box;
        }}
        [class*="st-key-calday-"] button {{
            width: 100%;
            border-radius: 8px !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 7px 0 !important;
            white-space: pre-line !important;
            line-height: 1.6 !important;
        }}
        [class*="st-key-calday-"] button p {{
            font-size: 0.72rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }}

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
            font-family: 'Space Grotesk', 'Inter', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
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

        /* Forms & dialogs */
        [data-testid="stForm"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 1.75rem 1.75rem 1.25rem 1.75rem;
        }}
        [data-testid="stDialog"] [role="dialog"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 18px;
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
        [data-testid="stFileUploader"] section {{
            background-color: {CARD_BG};
            border: 1px dashed {BORDER};
            border-radius: 12px;
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
            min-height: 118px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
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
            font-family: 'Space Grotesk', 'Inter', sans-serif;
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
        .tj-badge-good {{ color: {GOOD}; background: {GOOD_BG}; }}
        .tj-badge-bad {{ color: {BAD}; background: {BAD_BG}; }}
        .tj-badge-neutral {{ color: {TEXT_SECONDARY}; background: {NEUTRAL_BG}; }}
        .tj-badge-accent {{ color: {ACCENT}; background: rgba(232, 93, 158, 0.12); }}

        .tj-progress-track {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 999px;
            overflow: hidden;
        }}
        .tj-progress-fill {{
            height: 100%;
            border-radius: 999px;
        }}

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

        /* Account card */
        .tj-acct-top {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 14px;
        }}
        .tj-acct-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .tj-acct-name {{
            font-family: 'Space Grotesk', 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.02rem;
            color: {TEXT_PRIMARY};
        }}
        .tj-acct-firm {{
            font-size: 0.76rem;
            color: {TEXT_SECONDARY};
        }}
        .tj-acct-balance {{
            font-family: 'Space Grotesk', 'Inter', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            font-variant-numeric: tabular-nums;
            margin-bottom: 2px;
        }}
        .tj-acct-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            padding: 5px 0;
            border-top: 1px solid {BORDER};
        }}
        .tj-acct-row-label {{ color: {TEXT_SECONDARY}; }}
        .tj-acct-row-value {{ font-weight: 600; font-variant-numeric: tabular-nums; }}

        /* Calendar */
        .tj-cal-nav {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
        }}
        .tj-cal-month {{
            font-family: 'Space Grotesk', 'Inter', sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
        }}
        .tj-cal-weekday {{
            text-align: center;
            color: {TEXT_SECONDARY};
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 700;
            padding-bottom: 8px;
        }}
        .tj-cal-legend {{
            display: flex;
            align-items: center;
            gap: 14px;
            margin-top: 14px;
            font-size: 0.75rem;
            color: {TEXT_SECONDARY};
        }}
        .tj-cal-legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .tj-cal-legend-dot {{
            width: 8px;
            height: 8px;
            border-radius: 3px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def calendar_cell_css(cells: list) -> str:
    """One small CSS rule per calendar day (~28-42 per month) so each button
    can be colored by that day's outcome without per-instance inline style,
    which Streamlit's rendered wrapper divs don't accept. Injected once per
    calendar render, right before the grid — same technique CARD_KEYS uses
    for the fixed containers, just data-driven instead of static."""
    rules = []
    for cell in cells:
        key = cell["date"].isoformat()
        if not cell["in_month"]:
            bg, border, color = "transparent", "transparent", "rgba(161,161,170,0.35)"
        elif cell["outcome"] == "Win":
            bg, border, color = GOOD_BG, "rgba(34,197,94,0.35)", GOOD
        elif cell["outcome"] == "Loss":
            bg, border, color = BAD_BG, "rgba(239,68,68,0.35)", BAD
        elif cell["outcome"] == "Breakeven":
            bg, border, color = NEUTRAL_BG, "rgba(161,161,170,0.35)", TEXT_SECONDARY
        else:
            bg, border, color = CARD_BG, BORDER, TEXT_SECONDARY
        ring = f"box-shadow: inset 0 0 0 2px {ACCENT};" if cell["is_today"] else ""
        # Background/border go on the container (the whole cell "box"), not
        # the button, so the box's painted area always exactly matches what
        # Streamlit itself sizes the container to — the day number and P&L
        # amount are both inside the SAME button label (see calendar_widget),
        # so there's only one Streamlit-measured element per cell, not two.
        rules.append(
            f'.st-key-calday-{key} {{ background-color: {bg} !important; '
            f'border: 1px solid {border} !important; {ring} }} '
            f'.st-key-calday-{key} button {{ color: {color} !important; }}'
        )
    return f"<style>{' '.join(rules)}</style>"


# Fixed, known-in-advance container keys — see the dynamic (prefix-matched)
# rules in inject_css for account cards, screenshot cards, and calendar cells.
CARD_KEYS = [
    "stat-row",
    "card-balance",
    "card-progress",
    "card-calendar-preview",
    "card-calendar-full",
    "card-distribution",
    "card-breakdown",
    "card-drawdown",
    "card-heatmap",
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


def sidebar_account_chip(name: str, size_label: str, color: str) -> str:
    return (
        '<div class="tj-side-account">'
        f'<div class="tj-side-account-dot" style="background:{color};"></div>'
        f'<div><div class="tj-side-account-name">{esc(name)}</div>'
        f'<div class="tj-side-account-size">{esc(size_label)}</div></div></div>'
    )


def tag(text: str, outline: bool = False) -> str:
    cls = "tj-tag-outline" if outline else "tj-tag"
    return f'<span class="{cls}">{esc(text)}</span>'


def outcome_badge(outcome: str | None) -> str:
    if outcome == "Win":
        return '<span class="tj-badge tj-badge-good">Win</span>'
    if outcome == "Loss":
        return '<span class="tj-badge tj-badge-bad">Loss</span>'
    if outcome == "Breakeven":
        return '<span class="tj-badge tj-badge-neutral">Breakeven</span>'
    return ""


def streak_badge(count: int, streak_type: str | None) -> str:
    if not count or not streak_type:
        return '<span class="tj-badge tj-badge-neutral">No streak</span>'
    cls = "tj-badge-good" if streak_type == "Win" else "tj-badge-bad"
    return f'<span class="tj-badge {cls}">{count} {esc(streak_type)} streak</span>'


def status_badge(status: str) -> str:
    mapping = {
        "Active": "tj-badge-good",
        "Passed": "tj-badge-accent",
        "Failed": "tj-badge-bad",
        "Archived": "tj-badge-neutral",
    }
    cls = mapping.get(status, "tj-badge-neutral")
    return f'<span class="tj-badge {cls}">{esc(status)}</span>'


def progress_bar(pct: float | None, color: str = ACCENT) -> str:
    pct = 0 if pct is None else max(0.0, min(100.0, pct))
    return (
        '<div class="tj-progress-track">'
        f'<div class="tj-progress-fill" style="width:{pct:.1f}%; background:{color};"></div></div>'
    )

import streamlit as st

from data.db import init_db, get_all_trades
from logic.calculations import add_calculated_columns
from logic import analytics
from ui import theme
from ui.format import fmt_currency_signed, fmt_pct

st.set_page_config(page_title="Trading Journal", page_icon="📈", layout="wide")
theme.inject_css()
init_db()

with st.sidebar:
    st.markdown(
        """
        <div class="tj-brand">
            <div class="tj-brand-mark">TJ</div>
            <div>
                <div class="tj-brand-name">Trading Journal</div>
                <div class="tj-brand-sub"><span class="tj-pulse-dot"></span>Live · local session</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

overview = st.Page("views/overview.py", title="Dashboard", icon=":material/space_dashboard:", default=True)
add_trade = st.Page("views/add_trade.py", title="Add Trade", icon=":material/add_circle:")
journal = st.Page("views/journal.py", title="Trade Journal", icon=":material/receipt_long:")
analytics_page = st.Page("views/analytics.py", title="Analytics", icon=":material/insights:")

pg = st.navigation([overview, add_trade, journal, analytics_page])

trades = get_all_trades()
with st.sidebar:
    if trades.empty:
        st.markdown(
            theme.sidebar_panel("Snapshot", [("Trades logged", "0", theme.TEXT_PRIMARY)]),
            unsafe_allow_html=True,
        )
    else:
        stats = analytics.summary_stats(add_calculated_columns(trades))
        st.markdown(
            theme.sidebar_panel(
                "Snapshot",
                [
                    ("Total P&L", fmt_currency_signed(stats["total_pnl"]), theme.pnl_color(stats["total_pnl"])),
                    ("Win rate", fmt_pct(stats["win_rate"]), theme.ACCENT),
                    ("Trades logged", str(len(trades)), theme.TEXT_PRIMARY),
                ],
            ),
            unsafe_allow_html=True,
        )

pg.run()

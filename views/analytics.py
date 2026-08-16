import streamlit as st

from data.db import init_db, get_all_trades
from logic.calculations import add_calculated_columns
from logic import analytics
from ui import charts, theme

init_db()


def _pnl_color(v) -> str:
    if v is None or v != v:
        return ""
    return f"color: {theme.GOOD if v >= 0 else theme.BAD}; font-weight: 600;"


def _render_breakdown(df, category_col: str, category_label: str) -> None:
    styled = df.style.map(_pnl_color, subset=["total_pnl", "avg_pnl"])
    st.dataframe(
        styled,
        width="stretch",
        hide_index=True,
        column_config={
            category_col: st.column_config.TextColumn(category_label),
            "trades": st.column_config.NumberColumn("Trades"),
            "total_pnl": st.column_config.NumberColumn("Total P&L", format="$%.2f"),
            "avg_pnl": st.column_config.NumberColumn("Avg P&L", format="$%.2f"),
            "win_rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%"),
        },
    )

st.markdown(
    theme.page_header("Analytics", "Where your edge is coming from — by ticker, month, and day of week", icon="activity"),
    unsafe_allow_html=True,
)

trades = get_all_trades()

if trades.empty:
    st.info("No trades logged yet. Use **Add Trade** in the sidebar to log your first one.")
    st.stop()

enriched = add_calculated_columns(trades)
closed = analytics.closed_trades(enriched)

if closed.empty:
    st.info("No closed trades yet — analytics need at least one closed trade.")
    st.stop()

with st.container(key="card-breakdown"):
    st.markdown(
        theme.card_header("Performance Breakdown", "Slice results by ticker, month, or day of week", icon="layers"),
        unsafe_allow_html=True,
    )
    tab_ticker, tab_month, tab_dow = st.tabs(["By Ticker", "By Month", "By Day of Week"])

    with tab_ticker:
        perf_ticker = analytics.performance_by(enriched, "ticker")
        st.plotly_chart(charts.performance_bar_chart(perf_ticker, "ticker"), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)
        _render_breakdown(perf_ticker, "ticker", "Ticker")

    with tab_month:
        perf_month = analytics.performance_by_month(enriched)
        st.plotly_chart(charts.performance_bar_chart(perf_month, "month"), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)
        _render_breakdown(perf_month, "month", "Month")

    with tab_dow:
        perf_dow = analytics.performance_by_day_of_week(enriched)
        st.plotly_chart(charts.performance_bar_chart(perf_dow, "day_of_week"), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)
        _render_breakdown(perf_dow, "day_of_week", "Day of Week")

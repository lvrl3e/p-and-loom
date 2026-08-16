import streamlit as st

from data.db import init_db, get_all_trades
from logic.calculations import add_calculated_columns
from logic import analytics
from ui import charts
from ui.format import fmt_currency, fmt_pct, fmt_ratio, fmt_days

st.set_page_config(page_title="Dashboard | Trading Journal", page_icon="📊", layout="wide")
init_db()

st.title("📊 Analytics Dashboard")

trades = get_all_trades()

if trades.empty:
    st.info("No trades logged yet. Head to **Add Trade** in the sidebar to log your first one.")
    st.stop()

enriched = add_calculated_columns(trades)
closed = analytics.closed_trades(enriched)

if closed.empty:
    st.info("No closed trades yet — performance analytics need at least one closed trade.")
    st.stop()

stats = analytics.summary_stats(enriched)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Closed Trades", stats["num_trades"])
col2.metric("Win Rate", fmt_pct(stats["win_rate"]))
col3.metric("Avg Win", fmt_currency(stats["avg_win"]))
col4.metric("Avg Loss", fmt_currency(stats["avg_loss"]))
col5.metric("Risk-Reward", fmt_ratio(stats["risk_reward_ratio"]))
col6.metric("Avg R-Multiple", (f"{stats['avg_r_multiple']:.2f}R" if stats["avg_r_multiple"] is not None else "—"))

col7, col8 = st.columns(2)
col7.metric("Total P&L", fmt_currency(stats["total_pnl"]))
col8.metric("Max Drawdown", fmt_currency(stats["max_drawdown"]))

st.divider()

st.subheader("Equity Curve")
st.plotly_chart(charts.equity_curve_chart(analytics.equity_curve(enriched)), width="stretch", theme="streamlit")

col_dist, col_strat = st.columns(2)
with col_dist:
    st.subheader("Win / Loss Distribution")
    st.plotly_chart(charts.pnl_distribution_chart(closed), width="stretch", theme="streamlit")
with col_strat:
    st.subheader("Performance by Strategy")
    perf_strategy = analytics.performance_by(enriched, "strategy")
    st.plotly_chart(charts.performance_bar_chart(perf_strategy, "strategy"), width="stretch", theme="streamlit")

st.divider()
st.subheader("Deeper Breakdowns")

tab_ticker, tab_month, tab_dow = st.tabs(["By Ticker", "By Month", "By Day of Week"])

with tab_ticker:
    perf_ticker = analytics.performance_by(enriched, "ticker")
    st.plotly_chart(charts.performance_bar_chart(perf_ticker, "ticker"), width="stretch", theme="streamlit")
    st.dataframe(perf_ticker, width="stretch", hide_index=True)

with tab_month:
    perf_month = analytics.performance_by_month(enriched)
    st.plotly_chart(charts.performance_bar_chart(perf_month, "month"), width="stretch", theme="streamlit")
    st.dataframe(perf_month, width="stretch", hide_index=True)

with tab_dow:
    perf_dow = analytics.performance_by_day_of_week(enriched)
    st.plotly_chart(charts.performance_bar_chart(perf_dow, "day_of_week"), width="stretch", theme="streamlit")
    st.dataframe(perf_dow, width="stretch", hide_index=True)

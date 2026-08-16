import streamlit as st

from data.db import init_db, get_all_trades
from logic.calculations import add_calculated_columns
from logic.analytics import summary_stats
from ui.format import fmt_currency, fmt_pct, fmt_ratio

st.set_page_config(page_title="Trading Journal", page_icon="📈", layout="wide")

init_db()

st.title("📈 Trading Journal")
st.caption("Log trades, auto-calculate performance metrics, and see what's actually working.")

trades = get_all_trades()

if trades.empty:
    st.info("No trades logged yet. Head to **Add Trade** in the sidebar to log your first one.")
else:
    enriched = add_calculated_columns(trades)
    stats = summary_stats(enriched)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trades", stats["num_trades"])
    col2.metric("Total P&L", fmt_currency(stats["total_pnl"]))
    col3.metric("Win Rate", fmt_pct(stats["win_rate"]))
    col4.metric("Risk-Reward Ratio", fmt_ratio(stats["risk_reward_ratio"]))

    open_count = int((enriched["status"] == "Open").sum())
    if open_count:
        st.caption(f"{open_count} open position(s) not yet included in performance metrics.")

    st.divider()
    st.markdown(
        "Use the sidebar to **Add Trade**, browse the full **Journal**, "
        "or dig into the **Dashboard** for equity curve, win/loss distribution, "
        "and performance by strategy."
    )

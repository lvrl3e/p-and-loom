import streamlit as st

from data.db import init_db, get_all_trades, delete_trade
from logic.calculations import add_calculated_columns

st.set_page_config(page_title="Journal | Trading Journal", page_icon="📒", layout="wide")
init_db()

st.title("📒 Trade Journal")

trades = get_all_trades()

if trades.empty:
    st.info("No trades logged yet. Head to **Add Trade** in the sidebar to log your first one.")
    st.stop()

enriched = add_calculated_columns(trades)

with st.expander("Filters", expanded=False):
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        tickers = fcol1.multiselect("Ticker", sorted(enriched["ticker"].unique()))
    with fcol2:
        strategies = fcol2.multiselect(
            "Strategy", sorted(s for s in enriched["strategy"].dropna().unique())
        )
    with fcol3:
        directions = fcol3.multiselect("Direction", ["Long", "Short"])
    with fcol4:
        statuses = fcol4.multiselect("Status", ["Open", "Closed"])

filtered = enriched.copy()
if tickers:
    filtered = filtered[filtered["ticker"].isin(tickers)]
if strategies:
    filtered = filtered[filtered["strategy"].isin(strategies)]
if directions:
    filtered = filtered[filtered["direction"].isin(directions)]
if statuses:
    filtered = filtered[filtered["status"].isin(statuses)]

st.caption(f"Showing {len(filtered)} of {len(enriched)} trades")

display_cols = [
    "id", "ticker", "direction", "status", "entry_date", "exit_date",
    "entry_price", "exit_price", "position_size", "stop_loss",
    "pnl_dollar", "pnl_pct", "holding_period_days", "r_multiple",
    "strategy", "notes",
]

st.dataframe(
    filtered[display_cols],
    width="stretch",
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "entry_date": st.column_config.DateColumn("Entry Date"),
        "exit_date": st.column_config.DateColumn("Exit Date"),
        "entry_price": st.column_config.NumberColumn("Entry $", format="$%.2f"),
        "exit_price": st.column_config.NumberColumn("Exit $", format="$%.2f"),
        "position_size": st.column_config.NumberColumn("Size"),
        "stop_loss": st.column_config.NumberColumn("Stop $", format="$%.2f"),
        "pnl_dollar": st.column_config.NumberColumn("P&L $", format="$%.2f"),
        "pnl_pct": st.column_config.NumberColumn("P&L %", format="%.2f%%"),
        "holding_period_days": st.column_config.NumberColumn("Hold (days)", format="%.1f"),
        "r_multiple": st.column_config.NumberColumn("R-Multiple", format="%.2fR"),
        "strategy": st.column_config.TextColumn("Strategy"),
        "notes": st.column_config.TextColumn("Notes", width="large"),
    },
)

st.divider()
st.subheader("Delete a trade")

trade_options = {
    f"#{row.id} — {row.ticker} ({row.direction}, {row.entry_date.date()})": row.id
    for row in filtered.itertuples()
}

if trade_options:
    col_a, col_b = st.columns([3, 1])
    with col_a:
        selected_label = st.selectbox("Select trade", list(trade_options.keys()))
    selected_id = trade_options[selected_label]

    if st.session_state.get("confirm_delete_id") != selected_id:
        with col_b:
            st.write("")
            if st.button("Delete", type="secondary"):
                st.session_state["confirm_delete_id"] = selected_id
                st.rerun()
    else:
        st.warning(f"Delete trade {selected_label}? This cannot be undone.")
        c1, c2 = st.columns(2)
        if c1.button("Confirm delete", type="primary"):
            delete_trade(selected_id)
            del st.session_state["confirm_delete_id"]
            st.rerun()
        if c2.button("Cancel"):
            del st.session_state["confirm_delete_id"]
            st.rerun()

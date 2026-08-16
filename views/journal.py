import streamlit as st

from data.db import init_db, get_all_accounts, get_daily_entries, get_all_screenshots
from logic import analytics
from ui import theme
from ui.account_selector import render_selector, selected_account_and_entries, get_selected_id, ALL_ACCOUNTS
from ui.dialogs import daily_entry_dialog
from ui.format import fmt_currency_signed

init_db()

st.markdown(
    theme.page_header("Daily Journal", "Every day you've logged, in one table", icon="book"),
    unsafe_allow_html=True,
)

accounts_df = get_all_accounts()
if accounts_df.empty:
    st.info("No accounts yet. Head to **Accounts** in the sidebar to add one.")
    st.stop()

render_selector(accounts_df)
account, starting_balance, entries = selected_account_and_entries(accounts_df, get_daily_entries)

if entries.empty:
    st.info("No daily entries yet for this selection. Log one from the Dashboard or Calendar.")
    st.stop()

tagged = analytics.with_outcome(entries).sort_values("entry_date", ascending=False).copy()

account_id = get_selected_id()
shots_df = get_all_screenshots(None if account_id == ALL_ACCOUNTS else account_id)
shot_counts = shots_df.groupby("daily_entry_id").size().to_dict() if not shots_df.empty else {}
tagged["screenshots"] = tagged["id"].map(lambda i: shot_counts.get(i, 0))
tagged["notes_preview"] = tagged["notes"].fillna("")

st.caption(f"Showing {len(tagged)} day(s)")


def _pnl_color(v) -> str:
    if v is None or v != v:
        return ""
    return f"color: {theme.pnl_color(v)}; font-weight: 600;"


styled = tagged.style.map(_pnl_color, subset=["pnl"])

st.dataframe(
    styled,
    width="stretch",
    hide_index=True,
    column_order=["entry_date", "outcome", "pnl", "trade_count", "screenshots", "notes_preview"],
    column_config={
        "entry_date": st.column_config.DateColumn("Date", format="MMM DD, YYYY"),
        "outcome": st.column_config.TextColumn("Outcome"),
        "pnl": st.column_config.NumberColumn("P&L", format="$%.2f"),
        "trade_count": st.column_config.NumberColumn("Trades", width="small"),
        "screenshots": st.column_config.NumberColumn("Files", width="small"),
        "notes_preview": st.column_config.TextColumn("Notes", width="large"),
    },
)

st.divider()
st.markdown("##### Edit a day")

if account is None:
    st.caption("Select a single account (not All Accounts) above to edit individual days.")
else:
    options = {
        f"{row.entry_date.strftime('%b %d, %Y')} — {fmt_currency_signed(row.pnl)}": row.entry_date.date()
        for row in tagged.itertuples()
    }
    col_a, col_b = st.columns([3, 1])
    with col_a:
        label = st.selectbox("Select day", list(options.keys()))
    with col_b:
        st.write("")
        if st.button("Edit", type="secondary", width="stretch"):
            daily_entry_dialog(account, options[label])

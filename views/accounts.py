import streamlit as st

from data.db import init_db, get_all_accounts, get_daily_entries, coalesce
from logic import analytics
from ui import theme
from ui.account_selector import set_selected_id
from ui.dialogs import account_dialog
from ui.format import fmt_currency_signed

init_db()

header_col, btn_col = st.columns([5, 1])
with header_col:
    st.markdown(theme.page_header("Accounts", "Manage your trading accounts", icon="users"), unsafe_allow_html=True)
with btn_col:
    if st.button("＋ Add Account", type="primary", width="stretch"):
        account_dialog()

accounts_df = get_all_accounts()

if accounts_df.empty:
    st.markdown(
        """
        <div class="tj-empty">
            <div class="tj-empty-title">No accounts yet</div>
            <div>Add your first trading account to start tracking daily P&L.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

COLS_PER_ROW = 3
rows = [accounts_df.iloc[i:i + COLS_PER_ROW] for i in range(0, len(accounts_df), COLS_PER_ROW)]

for row_df in rows:
    cols = st.columns(COLS_PER_ROW)
    for col, (_, acct) in zip(cols, row_df.iterrows()):
        with col:
            with st.container(key=f"acct-{acct['id']}"):
                entries = get_daily_entries(int(acct["id"]))
                stats = analytics.summary_stats(entries, acct["starting_balance"])
                color = theme.pnl_color(stats["total_pnl"])

                subtitle = coalesce(acct["firm"]) or coalesce(acct["account_type"]) or ""
                card_html = (
                    '<div class="tj-acct-top">'
                    f'<div class="tj-acct-dot" style="background:{acct["color"]};"></div>'
                    f'<div><div class="tj-acct-name">{theme.esc(acct["name"])}</div>'
                    f'<div class="tj-acct-firm">{theme.esc(subtitle)}</div></div></div>'
                    f'<div class="tj-acct-balance">${stats["current_balance"]:,.2f}</div>'
                    f'{theme.status_badge(acct["status"])}'
                    '<div class="tj-acct-row"><div class="tj-acct-row-label">Account Size</div>'
                    f'<div class="tj-acct-row-value">${acct["account_size"]:,.0f}</div></div>'
                    '<div class="tj-acct-row"><div class="tj-acct-row-label">Total P&L</div>'
                    f'<div class="tj-acct-row-value" style="color:{color};">{fmt_currency_signed(stats["total_pnl"])}</div></div>'
                    '<div class="tj-acct-row"><div class="tj-acct-row-label">Return</div>'
                    f'<div class="tj-acct-row-value" style="color:{color};">{stats["pnl_pct"]:+.2f}%</div></div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                st.write("")
                b1, b2 = st.columns(2)
                if b1.button("Open Dashboard", key=f"open-{acct['id']}", type="secondary", width="stretch"):
                    set_selected_id(int(acct["id"]))
                    st.switch_page("views/overview.py")
                if b2.button("Edit", key=f"edit-{acct['id']}", type="secondary", width="stretch"):
                    account_dialog(acct.to_dict())

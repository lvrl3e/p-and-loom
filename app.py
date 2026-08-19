import streamlit as st

from data.db import init_db, get_all_accounts
from ui import theme
from ui.account_selector import ensure_selection, get_selected_id, ALL_ACCOUNTS

st.set_page_config(page_title="P&Loom", page_icon="docs/logo-icon.png", layout="wide")
init_db()
theme.apply_theme()
theme.inject_css()

with st.sidebar:
    st.markdown(
        f"""
        <div class="tj-brand">
            <img src="{theme.logo_icon_data_uri()}" class="tj-brand-mark-img" alt="P&Loom" />
            <div>
                <div class="tj-brand-name">P&amp;Loom</div>
                <div class="tj-brand-sub"><span class="tj-pulse-dot"></span>Live · local session</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

overview = st.Page("views/overview.py", title="Dashboard", icon=":material/space_dashboard:", default=True)
accounts_page = st.Page("views/accounts.py", title="Accounts", icon=":material/account_balance_wallet:")
journal = st.Page("views/journal.py", title="Daily Journal", icon=":material/receipt_long:")
calendar_page = st.Page("views/calendar.py", title="Calendar", icon=":material/calendar_month:")
analytics_page = st.Page("views/analytics.py", title="Analytics", icon=":material/insights:")
screenshots_page = st.Page("views/screenshots.py", title="Screenshots", icon=":material/image:")
news_page = st.Page("views/news.py", title="Economic Calendar", icon=":material/newspaper:")
settings_page = st.Page("views/settings.py", title="Settings", icon=":material/settings:")

pg = st.navigation([overview, accounts_page, journal, calendar_page, analytics_page, screenshots_page, news_page, settings_page])

accounts_df = get_all_accounts()
ensure_selection(accounts_df)

with st.sidebar:
    selected_id = get_selected_id()
    if accounts_df.empty:
        st.markdown(
            theme.sidebar_panel("Snapshot", [("Accounts", "0", theme.TEXT_PRIMARY)]),
            unsafe_allow_html=True,
        )
    elif selected_id == ALL_ACCOUNTS:
        st.markdown(
            theme.sidebar_account_chip("All Accounts", f"{len(accounts_df)} accounts", theme.ACCENT),
            unsafe_allow_html=True,
        )
    else:
        row = accounts_df[accounts_df["id"] == selected_id]
        if not row.empty:
            acct = row.iloc[0]
            st.markdown(
                theme.sidebar_account_chip(acct["name"], f"${acct['account_size']:,.0f} account", acct["color"]),
                unsafe_allow_html=True,
            )

pg.run()

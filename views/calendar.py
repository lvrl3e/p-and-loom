import calendar as _cal
import datetime as dt

import streamlit as st

from data.db import init_db, get_all_accounts, get_daily_entries
from logic import analytics
from ui import theme
from ui.account_selector import render_selector, selected_account_and_entries
from ui.calendar_widget import render_month

init_db()

st.markdown(
    theme.page_header("Calendar", "Click any day to log or review its P&L", icon="calendar"),
    unsafe_allow_html=True,
)

accounts_df = get_all_accounts()
if accounts_df.empty:
    st.info("No accounts yet. Head to **Accounts** in the sidebar to add one.")
    st.stop()

render_selector(accounts_df)
account, starting_balance, entries = selected_account_and_entries(accounts_df, get_daily_entries)

today = dt.date.today()
if "cal_year" not in st.session_state:
    st.session_state["cal_year"] = today.year
    st.session_state["cal_month"] = today.month

with st.container(key="card-calendar-full"):
    nav_prev, nav_title, nav_next = st.columns([1, 4, 1])
    with nav_prev:
        if st.button("←", key="cal-prev", type="secondary", width="stretch"):
            m, y = st.session_state["cal_month"] - 1, st.session_state["cal_year"]
            if m < 1:
                m, y = 12, y - 1
            st.session_state["cal_month"], st.session_state["cal_year"] = m, y
    with nav_title:
        month_name = _cal.month_name[st.session_state["cal_month"]]
        st.markdown(
            f'<div class="tj-cal-month" style="text-align:center;">{month_name} {st.session_state["cal_year"]}</div>',
            unsafe_allow_html=True,
        )
    with nav_next:
        if st.button("→", key="cal-next", type="secondary", width="stretch"):
            m, y = st.session_state["cal_month"] + 1, st.session_state["cal_year"]
            if m > 12:
                m, y = 1, y + 1
            st.session_state["cal_month"], st.session_state["cal_year"] = m, y

    weeks = analytics.calendar_matrix(entries, st.session_state["cal_year"], st.session_state["cal_month"], today)
    render_month(weeks, account)

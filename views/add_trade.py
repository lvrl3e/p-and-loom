import datetime

import streamlit as st

from data.db import init_db, add_trade, distinct_strategies
from ui import theme

init_db()

st.markdown(
    theme.page_header("Add Trade", "Log a new position to the journal", icon="dollar"),
    unsafe_allow_html=True,
)

existing_strategies = distinct_strategies()
NEW_TAG_OPTION = "+ Add new tag..."

with st.form("add_trade_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("Ticker *", placeholder="AAPL").strip().upper()
        direction = st.radio("Direction *", ["Long", "Short"], horizontal=True)
    with col2:
        entry_price = st.number_input("Entry Price *", min_value=0.0, step=0.01, format="%.4f")
        position_size = st.number_input("Position Size (shares/contracts) *", min_value=0.0, step=1.0)
    with col3:
        stop_loss_enabled = st.checkbox("Log a stop-loss (enables R-multiple)")
        stop_loss = (
            st.number_input("Stop-Loss Price", min_value=0.0, step=0.01, format="%.4f")
            if stop_loss_enabled
            else None
        )

    st.divider()

    col4, col5 = st.columns(2)
    with col4:
        entry_date = st.date_input("Entry Date *", value=datetime.date.today())
    with col5:
        is_closed = st.checkbox("Trade is closed", value=True)

    if is_closed:
        col6, col7 = st.columns(2)
        with col6:
            exit_price = st.number_input("Exit Price *", min_value=0.0, step=0.01, format="%.4f")
        with col7:
            exit_date = st.date_input("Exit Date *", value=datetime.date.today())
    else:
        exit_price = None
        exit_date = None

    st.divider()

    strategy_choice = st.selectbox(
        "Strategy / Setup Tag", ["(none)"] + existing_strategies + [NEW_TAG_OPTION]
    )
    new_strategy = ""
    if strategy_choice == NEW_TAG_OPTION:
        new_strategy = st.text_input("New tag name").strip()
    elif existing_strategies:
        st.markdown(
            "".join(theme.tag(s, outline=True) for s in existing_strategies),
            unsafe_allow_html=True,
        )

    notes = st.text_area("Notes", placeholder="Optional context: catalyst, mistakes, execution quality...")

    submitted = st.form_submit_button("Save Trade", type="primary")

if submitted:
    errors = []
    if not ticker:
        errors.append("Ticker is required.")
    if entry_price <= 0:
        errors.append("Entry price must be greater than 0.")
    if position_size <= 0:
        errors.append("Position size must be greater than 0.")
    if is_closed and exit_price <= 0:
        errors.append("Exit price must be greater than 0 for a closed trade.")
    if is_closed and exit_date < entry_date:
        errors.append("Exit date cannot be before entry date.")
    if strategy_choice == NEW_TAG_OPTION and not new_strategy:
        errors.append("Enter a name for the new strategy tag, or pick an existing one.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        if strategy_choice == NEW_TAG_OPTION:
            strategy = new_strategy
        elif strategy_choice == "(none)":
            strategy = None
        else:
            strategy = strategy_choice

        trade = {
            "ticker": ticker,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price if is_closed else None,
            "position_size": position_size,
            "stop_loss": stop_loss,
            "entry_date": entry_date.isoformat(),
            "exit_date": exit_date.isoformat() if is_closed else None,
            "strategy": strategy,
            "notes": notes or None,
        }
        add_trade(trade)
        st.success(f"Saved {direction.lower()} trade on {ticker}.")

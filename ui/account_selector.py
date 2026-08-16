"""
Shared account-selection state and widget. Every page reads/writes the same
st.session_state key so switching accounts on one page carries over to the
rest of the app, and each page's stats stay scoped to that selection (or to
every account at once via the ALL_ACCOUNTS sentinel).
"""

import pandas as pd
import streamlit as st

ALL_ACCOUNTS = "__all__"
SESSION_KEY = "selected_account_id"


def ensure_selection(accounts_df: pd.DataFrame) -> None:
    """Called once per page render to guarantee session_state holds a valid
    selection — falls back to the first account if none is set yet or the
    previously selected account was deleted."""
    if accounts_df.empty:
        st.session_state[SESSION_KEY] = None
        return
    valid_ids = set(accounts_df["id"].tolist()) | {ALL_ACCOUNTS}
    if st.session_state.get(SESSION_KEY) not in valid_ids:
        st.session_state[SESSION_KEY] = int(accounts_df.iloc[0]["id"])


def get_selected_id():
    return st.session_state.get(SESSION_KEY)


def set_selected_id(account_id) -> None:
    st.session_state[SESSION_KEY] = account_id


def render_selector(accounts_df: pd.DataFrame, key: str = "account_selector_widget") -> None:
    """Renders the dropdown and writes the choice back to session_state."""
    ensure_selection(accounts_df)
    if accounts_df.empty:
        return

    options = [ALL_ACCOUNTS] + [int(i) for i in accounts_df["id"]]

    def format_option(acc_id):
        if acc_id == ALL_ACCOUNTS:
            return "🗂  All Accounts"
        row = accounts_df[accounts_df["id"] == acc_id].iloc[0]
        return f"{row['name']} — ${row['account_size']:,.0f}"

    current = st.session_state[SESSION_KEY]
    st.selectbox(
        "Account",
        options,
        format_func=format_option,
        index=options.index(current),
        key=key,
        label_visibility="collapsed",
        on_change=lambda: set_selected_id(st.session_state[key]),
    )
    # Keep the canonical session key in sync even on first render (on_change
    # only fires on user interaction, not on the initial value).
    st.session_state[SESSION_KEY] = st.session_state[key]


def selected_account_and_entries(accounts_df: pd.DataFrame, get_daily_entries):
    """Resolves the current selection into (account_or_None, starting_balance,
    entries_df). account is None for the All Accounts view. get_daily_entries
    is data.db.get_daily_entries, passed in to avoid a data<->ui import cycle."""
    ensure_selection(accounts_df)
    selected = st.session_state[SESSION_KEY]

    if selected is None:
        return None, 0.0, pd.DataFrame(columns=["id", "account_id", "entry_date", "pnl", "notes"])

    if selected == ALL_ACCOUNTS:
        starting_balance = float(accounts_df["starting_balance"].sum())
        entries = get_daily_entries(None)
        return None, starting_balance, entries

    account = accounts_df[accounts_df["id"] == selected].iloc[0].to_dict()
    entries = get_daily_entries(selected)
    return account, float(account["starting_balance"]), entries

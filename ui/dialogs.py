"""
Shared @st.dialog modals, invoked from multiple pages (Dashboard's quick-add
button, Calendar day clicks, Daily Journal's edit action, Accounts page's
add/edit/delete). Centralized here so the save/delete logic — including
screenshot file cleanup — only exists once.
"""

import datetime as dt

import streamlit as st

from data import db, storage
from ui import theme
from ui.account_selector import set_selected_id

ACCOUNT_TYPES = ["Prop Firm", "Funded Account", "Personal", "Demo"]
STATUSES = ["Active", "Passed", "Failed", "Archived"]
COLOR_NAMES = ["Pink", "Blue", "Green", "Amber", "Violet", "Gray"]


def _color_name(hex_value: str) -> str:
    try:
        return COLOR_NAMES[theme.ACCOUNT_COLORS.index(hex_value)]
    except ValueError:
        return COLOR_NAMES[0]


@st.dialog("Daily Entry")
def daily_entry_dialog(account: dict, entry_date: dt.date):
    existing = db.get_daily_entry(account["id"], entry_date.isoformat())

    st.markdown(
        f'<div style="font-family:\'Space Grotesk\',sans-serif; font-size:1.15rem; font-weight:700; '
        f'color:{theme.TEXT_PRIMARY};">{entry_date.strftime("%B %d, %Y")}</div>',
        unsafe_allow_html=True,
    )
    st.caption(account["name"])

    pnl = st.number_input(
        "Daily P&L ($)", value=float(existing["pnl"]) if existing else 0.0, step=10.0, format="%.2f"
    )
    outcome = "Win" if pnl > 0 else ("Loss" if pnl < 0 else "Breakeven")
    st.markdown(theme.outcome_badge(outcome), unsafe_allow_html=True)

    notes = st.text_area(
        "Notes",
        value=existing["notes"] if existing and existing["notes"] else "",
        height=120,
        placeholder="What happened today? Plan followed, mistakes, lessons...",
    )

    st.markdown("**Screenshots**")
    if existing:
        shots = db.get_screenshots(existing["id"])
        if shots:
            cols = st.columns(4)
            for i, shot in enumerate(shots):
                with cols[i % 4]:
                    st.image(storage.absolute_path(shot["file_path"]), width="stretch")
                    if st.button("Delete", key=f"delshot-{shot['id']}", type="secondary", width="stretch"):
                        path = db.delete_screenshot(shot["id"])
                        if path:
                            storage.delete_screenshot_file(path)
                        st.rerun()

    uploaded = st.file_uploader(
        "Upload screenshots", accept_multiple_files=True,
        type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    if col1.button("Save", type="primary", width="stretch"):
        entry_id = db.upsert_daily_entry(account["id"], entry_date.isoformat(), pnl, notes or None)
        for f in uploaded or []:
            path = storage.save_screenshot(f, account["id"], entry_date.isoformat())
            db.add_screenshot(entry_id, path)
        st.rerun()
    if existing and col2.button("Delete Entry", type="secondary", width="stretch"):
        for shot in db.get_screenshots(existing["id"]):
            storage.delete_screenshot_file(shot["file_path"])
        db.delete_daily_entry(existing["id"])
        st.rerun()


@st.dialog("Account")
def account_dialog(account: dict | None = None):
    is_edit = account is not None
    st.markdown(
        f'<div style="font-family:\'Space Grotesk\',sans-serif; font-size:1.15rem; font-weight:700; '
        f'color:{theme.TEXT_PRIMARY};">{"Edit Account" if is_edit else "New Account"}</div>',
        unsafe_allow_html=True,
    )

    name = st.text_input("Account Name *", value=account["name"] if is_edit else "", placeholder="FTMO Challenge")
    firm = st.text_input(
        "Prop Firm / Broker", value=(db.coalesce(account.get("firm"), "")) if is_edit else "", placeholder="FTMO"
    )

    col1, col2 = st.columns(2)
    with col1:
        account_size = st.number_input(
            "Account Size ($) *", min_value=0.0, step=1000.0,
            value=float(account["account_size"]) if is_edit else 100000.0,
        )
    with col2:
        starting_balance = st.number_input(
            "Starting Balance ($) *", min_value=0.0, step=1000.0,
            value=float(account["starting_balance"]) if is_edit else account_size,
        )

    col3, col4 = st.columns(2)
    with col3:
        account_type = st.selectbox(
            "Account Type", ACCOUNT_TYPES,
            index=ACCOUNT_TYPES.index(account["account_type"]) if is_edit and account.get("account_type") in ACCOUNT_TYPES else 0,
        )
    with col4:
        color_name = st.selectbox(
            "Color", COLOR_NAMES,
            index=COLOR_NAMES.index(_color_name(account["color"])) if is_edit else 0,
        )
    color = theme.ACCOUNT_COLORS[COLOR_NAMES.index(color_name)]

    status = STATUSES[0]
    if is_edit:
        status = st.selectbox("Status", STATUSES, index=STATUSES.index(account.get("status", "Active")))

    with st.expander("Prop-firm rules (optional)"):
        profit_target = st.number_input(
            "Profit Target ($)", min_value=0.0, step=100.0,
            value=float(db.coalesce(account.get("profit_target"), 0)) if is_edit else 0.0,
        )
        max_drawdown_limit = st.number_input(
            "Max Drawdown Limit ($)", min_value=0.0, step=100.0,
            value=float(db.coalesce(account.get("max_drawdown_limit"), 0)) if is_edit else 0.0,
        )
        daily_loss_limit = st.number_input(
            "Daily Loss Limit ($)", min_value=0.0, step=100.0,
            value=float(db.coalesce(account.get("daily_loss_limit"), 0)) if is_edit else 0.0,
        )

    col_a, col_b = st.columns(2)
    if col_a.button("Save", type="primary", width="stretch"):
        if not name.strip():
            st.error("Account name is required.")
        else:
            data = dict(
                name=name.strip(),
                firm=firm.strip() or None,
                account_size=account_size,
                starting_balance=starting_balance,
                account_type=account_type,
                color=color,
                status=status,
                profit_target=profit_target or None,
                max_drawdown_limit=max_drawdown_limit or None,
                daily_loss_limit=daily_loss_limit or None,
            )
            if is_edit:
                db.update_account(account["id"], data)
            else:
                new_id = db.add_account(data)
                set_selected_id(new_id)
            st.rerun()

    if is_edit and col_b.button("Delete Account", type="secondary", width="stretch"):
        shots = db.get_all_screenshots(account["id"])
        for _, row in shots.iterrows():
            storage.delete_screenshot_file(row["file_path"])
        db.delete_account(account["id"])
        set_selected_id(None)
        st.rerun()

import streamlit as st

from data import storage
from data.db import init_db, get_all_accounts, get_all_screenshots, delete_screenshot, coalesce
from ui import theme
from ui.account_selector import render_selector, get_selected_id, ALL_ACCOUNTS
from ui.format import fmt_currency_signed

init_db()

st.markdown(
    theme.page_header("Screenshots", "Every chart and note you've attached to a trading day", icon="image"),
    unsafe_allow_html=True,
)

accounts_df = get_all_accounts()
if accounts_df.empty:
    st.info("No accounts yet. Head to **Accounts** in the sidebar to add one.")
    st.stop()

render_selector(accounts_df)
account_id = get_selected_id()
shots_df = get_all_screenshots(None if account_id == ALL_ACCOUNTS else account_id)

if shots_df.empty:
    st.markdown(
        """
        <div class="tj-empty">
            <div class="tj-empty-title">No screenshots yet</div>
            <div>Attach a screenshot when logging a day from the Dashboard or Calendar.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

st.caption(f"{len(shots_df)} screenshot(s)")

COLS = 4
rows = [shots_df.iloc[i:i + COLS] for i in range(0, len(shots_df), COLS)]

for row_df in rows:
    cols = st.columns(COLS)
    for col, (_, shot) in zip(cols, row_df.iterrows()):
        with col:
            with st.container(key=f"shot-{shot['id']}"):
                st.image(storage.absolute_path(shot["file_path"]), width="stretch")
                pnl_color = theme.pnl_color(shot["pnl"])
                st.markdown(
                    f'<div style="font-weight:700; font-size:0.82rem; margin-top:6px;">{shot["entry_date"].strftime("%b %d, %Y")}</div>'
                    f'<div style="font-size:0.74rem; color:{theme.TEXT_SECONDARY};">{theme.esc(shot["account_name"])} · '
                    f'<span style="color:{pnl_color};">{fmt_currency_signed(shot["pnl"])}</span></div>',
                    unsafe_allow_html=True,
                )
                notes = coalesce(shot["notes"])
                if notes:
                    preview = notes[:80] + ("…" if len(notes) > 80 else "")
                    st.caption(preview)
                if st.button("Delete", key=f"delshot-{shot['id']}", type="secondary", width="stretch"):
                    path = delete_screenshot(int(shot["id"]))
                    if path:
                        storage.delete_screenshot_file(path)
                    st.rerun()

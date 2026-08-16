"""
Renders a month grid from logic.analytics.calendar_matrix. Shared between
the Dashboard's current-month preview and the full Calendar page so the
cell layout/coloring/click behavior only exists once.
"""

import streamlit as st

from ui import theme
from ui.dialogs import daily_entry_dialog

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def render_month(weeks: list, account: dict | None, clickable: bool = True) -> None:
    """account is None for the All Accounts view — cells render read-only
    there, since a click can't be attributed to one specific account."""
    all_cells = [cell for week in weeks for cell in week]
    st.markdown(theme.calendar_cell_css(all_cells), unsafe_allow_html=True)

    header_cols = st.columns(7)
    for col, label in zip(header_cols, WEEKDAY_LABELS):
        col.markdown(f'<div class="tj-cal-weekday">{label}</div>', unsafe_allow_html=True)

    interactive = clickable and account is not None
    for week in weeks:
        cols = st.columns(7)
        for col, cell in zip(cols, week):
            date_key = cell["date"].isoformat()
            with col:
                with st.container(key=f"calday-{date_key}"):
                    help_text = None
                    if cell["pnl"] is not None:
                        sign = "+" if cell["pnl"] >= 0 else "-"
                        help_text = f"{sign}${abs(cell['pnl']):,.2f}"
                    clicked = st.button(
                        str(cell["date"].day),
                        key=f"calday-btn-{date_key}",
                        help=help_text,
                        disabled=not interactive,
                        width="stretch",
                    )
                    if cell["pnl"] is not None:
                        color = theme.pnl_color(cell["pnl"]) if cell["outcome"] != "Breakeven" else theme.TEXT_SECONDARY
                        sign = "+" if cell["pnl"] >= 0 else "-"
                        st.markdown(
                            f'<div class="tj-cal-pnl" style="color:{color};">{sign}${abs(cell["pnl"]):,.0f}</div>',
                            unsafe_allow_html=True,
                        )
                    if clicked and interactive:
                        daily_entry_dialog(account, cell["date"])

    st.markdown(
        '<div class="tj-cal-legend">'
        f'<div class="tj-cal-legend-item"><div class="tj-cal-legend-dot" style="background:{theme.GOOD};"></div>Profit</div>'
        f'<div class="tj-cal-legend-item"><div class="tj-cal-legend-dot" style="background:{theme.BAD};"></div>Loss</div>'
        f'<div class="tj-cal-legend-item"><div class="tj-cal-legend-dot" style="background:{theme.NEUTRAL};"></div>Breakeven</div>'
        f'<div class="tj-cal-legend-item"><div class="tj-cal-legend-dot" style="background:{theme.CARD_BG}; border:1px solid {theme.BORDER};"></div>No entry</div>'
        "</div>",
        unsafe_allow_html=True,
    )

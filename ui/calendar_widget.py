"""
Renders a month grid from logic.analytics.calendar_matrix. Shared between
the Dashboard's current-month preview and the full Calendar page so the
cell layout/coloring/click behavior only exists once.
"""

import streamlit as st

from ui import theme
from ui.dialogs import daily_entry_dialog

WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


WEEK_TOTAL_COL = 6  # Saturday — Sun=0 .. Sat=6, repurposed as that week's P&L sum


def render_month(weeks: list, account: dict | None, clickable: bool = True) -> None:
    """account is None for the All Accounts view — cells render read-only
    there, since a click can't be attributed to one specific account."""
    all_cells = [cell for week in weeks for cell in week]
    week_total_keys = frozenset(week[WEEK_TOTAL_COL]["date"].isoformat() for week in weeks)
    st.markdown(theme.calendar_cell_css(all_cells, week_total_keys), unsafe_allow_html=True)

    header_cols = st.columns(7)
    for col, label in zip(header_cols, WEEKDAY_LABELS):
        col.markdown(f'<div class="tj-cal-weekday">{label}</div>', unsafe_allow_html=True)

    interactive = clickable and account is not None
    for week in weeks:
        week_pnls = [c["pnl"] for c in week if c["pnl"] is not None]
        week_total = sum(week_pnls) if week_pnls else None

        cols = st.columns(7)
        for col_idx, (col, cell) in enumerate(zip(cols, week)):
            date_key = cell["date"].isoformat()
            with col:
                with st.container(key=f"calday-{date_key}"):
                    if col_idx == WEEK_TOTAL_COL:
                        if week_total is not None:
                            sign = "+" if week_total >= 0 else "-"
                            amount = f"{sign}${abs(week_total):,.0f}"
                            help_text = f"Week total: {sign}${abs(week_total):,.2f}"
                        else:
                            amount, help_text = "—", "No entries logged this week"
                        st.button(
                            f"Total  \n{amount}",
                            key=f"calday-btn-{date_key}",
                            help=help_text,
                            disabled=True,
                            width="stretch",
                        )
                        continue

                    # The day number and P&L amount are baked into ONE button
                    # label (markdown hard-break) rather than a button plus a
                    # separate markdown element below it — Streamlit sizes its
                    # own container to fit exactly what the button reports, so
                    # a second sibling element it doesn't measure ends up
                    # rendered outside/below the colored box no matter what
                    # CSS height is set on the container (confirmed empirically:
                    # the gap persists unchanged across every height override).
                    label = str(cell["date"].day)
                    help_text = None
                    if cell["pnl"] is not None:
                        sign = "+" if cell["pnl"] >= 0 else "-"
                        amount = f"{sign}${abs(cell['pnl']):,.0f}"
                        help_text = f"{sign}${abs(cell['pnl']):,.2f}"
                        label = f"{label}  \n{amount}"
                    clicked = st.button(
                        label,
                        key=f"calday-btn-{date_key}",
                        help=help_text,
                        disabled=not interactive,
                        width="stretch",
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

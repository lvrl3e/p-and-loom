import datetime as dt

import streamlit as st

from data.db import init_db, get_all_accounts, get_daily_entries
from logic import analytics
from ui import charts, theme
from ui.account_selector import render_selector, selected_account_and_entries
from ui.format import fmt_currency, fmt_currency_signed

init_db()

st.markdown(
    theme.page_header("Analytics", "Deeper performance breakdowns from your daily P&L", icon="activity"),
    unsafe_allow_html=True,
)

accounts_df = get_all_accounts()
if accounts_df.empty:
    st.info("No accounts yet. Head to **Accounts** in the sidebar to add one.")
    st.stop()

render_selector(accounts_df)
account, starting_balance, entries = selected_account_and_entries(accounts_df, get_daily_entries)

if entries.empty:
    st.info("No daily entries yet for this selection.")
    st.stop()

stats = analytics.summary_stats(entries, starting_balance)
equity = analytics.equity_curve(entries, starting_balance)
drawdown_df = analytics.drawdown_series(equity)
streak = stats["streak"]
saturday_total = analytics.saturday_total(entries)

best_day, worst_day = stats["best_day"], stats["worst_day"]
streak_accent = theme.GOOD if streak["type"] == "Win" else (theme.BAD if streak["type"] == "Loss" else theme.NEUTRAL)

with st.container(key="stat-row"):
    cards = [
        theme.stat_card("Avg Winning Day", fmt_currency(stats["avg_daily_profit"]), icon="trending-up", accent=theme.GOOD),
        theme.stat_card("Avg Losing Day", fmt_currency(stats["avg_daily_loss"]), icon="trending-down", accent=theme.BAD),
        theme.stat_card(
            "Best Day", fmt_currency_signed(best_day["pnl"]) if best_day is not None else "—",
            icon="flag", accent=theme.GOOD,
            sub=best_day["entry_date"].strftime("%b %d, %Y") if best_day is not None else None,
        ),
        theme.stat_card(
            "Worst Day", fmt_currency_signed(worst_day["pnl"]) if worst_day is not None else "—",
            icon="alert-triangle", accent=theme.BAD,
            sub=worst_day["entry_date"].strftime("%b %d, %Y") if worst_day is not None else None,
        ),
        theme.stat_card(
            "Current Streak", str(streak["count"]) if streak["type"] else "0",
            icon="flame", accent=streak_accent,
            sub=f"{streak['type']} streak" if streak["type"] else "No active streak",
        ),
        theme.stat_card("Total P&L on Saturdays", fmt_currency_signed(saturday_total), icon="calendar", accent=theme.pnl_color(saturday_total)),
    ]
    st.markdown(theme.stat_grid(cards), unsafe_allow_html=True)

st.write("")

with st.container(key="card-drawdown"):
    st.markdown(theme.card_header("Drawdown", "Decline from the running peak balance", icon="alert-triangle"), unsafe_allow_html=True)
    st.plotly_chart(charts.drawdown_chart(drawdown_df), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)

st.write("")


def _render_table(df, category_col: str, category_label: str) -> None:
    def _pnl_color(v):
        if v is None or v != v:
            return ""
        return f"color: {theme.pnl_color(v)}; font-weight: 600;"

    styled = df.style.map(_pnl_color, subset=["total_pnl", "avg_pnl"])
    st.dataframe(
        styled, width="stretch", hide_index=True,
        column_config={
            category_col: st.column_config.TextColumn(category_label),
            "days": st.column_config.NumberColumn("Days"),
            "total_pnl": st.column_config.NumberColumn("Total P&L", format="$%.2f"),
            "avg_pnl": st.column_config.NumberColumn("Avg P&L", format="$%.2f"),
            "win_rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%"),
        },
    )


with st.container(key="card-breakdown"):
    st.markdown(theme.card_header("Performance Breakdown", "Monthly comparison and win/loss distribution", icon="layers"), unsafe_allow_html=True)
    tab_month, tab_dow, tab_dist = st.tabs(["By Month", "By Day of Week", "Distribution"])

    with tab_month:
        perf_month = analytics.performance_by_month(entries)
        st.plotly_chart(charts.performance_bar_chart(perf_month, "month"), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)
        _render_table(perf_month, "month", "Month")

    with tab_dow:
        perf_dow = analytics.performance_by_day_of_week(entries)
        st.plotly_chart(charts.performance_bar_chart(perf_dow, "day_of_week"), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)
        _render_table(perf_dow, "day_of_week", "Day")

    with tab_dist:
        st.plotly_chart(charts.pnl_distribution_chart(entries), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)

st.write("")


def _year_heatmap_html(entries_df, year: int) -> str:
    # CSS Grid with grid-auto-flow:column lays every day out into 7-row
    # columns automatically, in document order — no per-week wrapper divs
    # needed, and no risk of the columns collapsing the way nested flexbox
    # (row of column-flex divs) did here.
    tagged = analytics.with_outcome(entries_df)
    by_date = {row.entry_date.date(): row.pnl for row in tagged.itertuples() if row.entry_date.year == year}

    start = dt.date(year, 1, 1) - dt.timedelta(days=dt.date(year, 1, 1).weekday())
    end = dt.date(year, 12, 31)

    cells = []
    day = start
    while day <= end:
        if day.year != year:
            color, title = "transparent", ""
        else:
            pnl = by_date.get(day)
            if pnl is None:
                color, title = theme.CARD_BG, day.isoformat()
            elif pnl > 0:
                color, title = theme.GOOD, f"{day.isoformat()}: +${pnl:,.2f}"
            elif pnl < 0:
                color, title = theme.BAD, f"{day.isoformat()}: -${abs(pnl):,.2f}"
            else:
                color, title = theme.NEUTRAL, f"{day.isoformat()}: breakeven"
        cells.append(f'<div title="{title}" style="width:11px;height:11px;border-radius:3px;background:{color};"></div>')
        day += dt.timedelta(days=1)

    grid_style = (
        "display:grid;grid-template-rows:repeat(7,11px);grid-auto-flow:column;"
        "grid-auto-columns:11px;gap:3px;overflow-x:auto;padding-bottom:4px;"
    )
    return f'<div style="{grid_style}">{"".join(cells)}</div>'


with st.container(key="card-heatmap"):
    st.markdown(theme.card_header("Calendar Heatmap", "P&L intensity across the year — hover a square for details", icon="calendar"), unsafe_allow_html=True)
    years = sorted(entries["entry_date"].dt.year.unique(), reverse=True)
    year = st.selectbox("Year", years, label_visibility="collapsed")
    st.markdown(_year_heatmap_html(entries, year), unsafe_allow_html=True)

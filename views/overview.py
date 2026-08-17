import datetime as dt

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from data.db import get_all_accounts, get_daily_entries
from logic import analytics
from ui import charts, theme
from ui.account_selector import render_selector, selected_account_and_entries, ALL_ACCOUNTS, get_selected_id
from ui.calendar_widget import render_month
from ui.dialogs import daily_entry_dialog
from ui.format import fmt_currency_signed, fmt_pct

accounts_df = get_all_accounts()

hour = dt.datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
st.markdown(
    f'<div class="tj-page-header-title" style="font-size:1.6rem; display:flex; align-items:center; gap:10px;">'
    f'{greeting}, Trader <span style="color:{theme.ACCENT}; display:inline-flex;">{theme.icon_svg("heart", 22)}</span></div>'
    f'<div class="tj-page-header-sub" style="margin-bottom:1.25rem;">Here\'s your performance overview.</div>',
    unsafe_allow_html=True,
)

if accounts_df.empty:
    st.markdown(
        """
        <div class="tj-empty">
            <div class="tj-empty-title">No accounts yet</div>
            <div>Head to <b>Accounts</b> in the sidebar to add your first trading account.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

sel_col, btn_col = st.columns([3, 1])
with sel_col:
    render_selector(accounts_df)
with btn_col:
    account_id = get_selected_id()
    add_disabled = account_id == ALL_ACCOUNTS
    if st.button("＋ Add Trade", type="primary", width="stretch", disabled=add_disabled):
        row = accounts_df[accounts_df["id"] == account_id].iloc[0].to_dict()
        daily_entry_dialog(row, dt.date.today())

account, starting_balance, entries = selected_account_and_entries(accounts_df, get_daily_entries)
stats = analytics.summary_stats(entries, starting_balance)
equity = analytics.equity_curve(entries, starting_balance)

best_day = stats["best_day"]
best_day_value = fmt_currency_signed(best_day["pnl"]) if best_day is not None else "—"

with st.container(key="stat-row"):
    cards = [
        theme.stat_card(
            "Current Balance", f"${stats['current_balance']:,.2f}", icon="wallet", accent=theme.ACCENT,
            sub=f"Started at ${stats['starting_balance']:,.2f}",
        ),
        theme.stat_card(
            "Total P&L", fmt_currency_signed(stats["total_pnl"]), icon="dollar",
            accent=theme.pnl_color(stats["total_pnl"]),
            sub=f"{stats['pnl_pct']:+.2f}% return",
            spark=list(equity["balance"].tail(10)),
        ),
        theme.stat_card(
            "Win Rate", fmt_pct(stats["win_rate"]), icon="target", accent=theme.ACCENT,
            sub=f"{stats['winning_days']} wins · {stats['losing_days']} losses",
        ),
        theme.stat_card(
            "Best Day", best_day_value, icon="trending-up", accent=theme.GOOD,
            sub=best_day["entry_date"].strftime("%b %d, %Y") if best_day is not None else "No profitable days yet",
        ),
    ]
    st.markdown(theme.stat_grid(cards), unsafe_allow_html=True)

st.write("")

RANGE_OPTIONS = {"7D": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365, "All": None}

col_chart, col_progress = st.columns([2, 1])
with col_chart:
    with st.container(key="card-balance"):
        header_c, range_c = st.columns([3, 3])
        with header_c:
            st.markdown(theme.card_header("Performance", "Account balance over time", icon="trending-up"), unsafe_allow_html=True)
        with range_c:
            range_choice = st.segmented_control(
                "Range", list(RANGE_OPTIONS.keys()), default="All", key="balance_range", label_visibility="collapsed"
            )
        days = RANGE_OPTIONS.get(range_choice or "All")
        chart_equity = equity
        if days and not equity.empty:
            cutoff = pd.Timestamp(dt.date.today() - dt.timedelta(days=days))
            chart_equity = equity[equity["entry_date"] >= cutoff]
        st.plotly_chart(charts.balance_chart(chart_equity, starting_balance), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)
with col_progress:
    with st.container(key="card-progress"):
        st.markdown(theme.card_header("Prop-Firm Progress", icon="flag"), unsafe_allow_html=True)
        if account is None:
            st.caption("Select a single account to see profit-target and drawdown progress.")
        else:
            progress = analytics.prop_firm_progress(stats, account, equity)
            if progress["profit_target"]:
                st.markdown(
                    f'<div class="tj-stat-sub" style="margin-bottom:6px;">Profit Target — '
                    f'${stats["total_pnl"]:,.2f} / ${progress["profit_target"]:,.2f}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(theme.progress_bar(progress["target_progress_pct"], theme.GOOD), unsafe_allow_html=True)
                st.caption(f"{progress['target_progress_pct']:.1f}% · \\${progress['remaining_to_target']:,.2f} remaining")
            else:
                st.caption("No profit target set for this account.")

            st.write("")
            if progress["max_drawdown_limit"]:
                dd_label = "Trailing" if progress["drawdown_type"] == "trailing" else "Static"
                st.markdown(
                    f'<div class="tj-stat-sub" style="margin-bottom:6px;">Drawdown ({dd_label}) — '
                    f'${progress["current_drawdown"]:,.2f} / ${progress["max_drawdown_limit"]:,.2f}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(theme.progress_bar(progress["drawdown_used_pct"], theme.BAD), unsafe_allow_html=True)
                st.caption(f"\\${progress['distance_to_drawdown']:,.2f} of room left")
            else:
                st.caption("No drawdown limit set for this account.")

            st.write("")
            if progress["daily_loss_pct"]:
                st.markdown(
                    f'<div class="tj-stat-sub" style="margin-bottom:6px;">Daily Drawdown '
                    f'({progress["daily_loss_pct"]:.1f}% of day start) — '
                    f'${progress["daily_loss_used"]:,.2f} / ${progress["daily_loss_limit"]:,.2f}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(theme.progress_bar(progress["daily_loss_used_pct"], theme.BAD), unsafe_allow_html=True)
                st.caption(
                    f"Remaining: \\${progress['distance_to_daily_loss']:,.2f} · "
                    f"Max: \\${progress['daily_loss_limit']:,.2f}"
                )
                reset_h, reset_m = (int(x) for x in progress["daily_reset_time"].split(":"))
                now = dt.datetime.now()
                next_reset = now.replace(hour=reset_h, minute=reset_m, second=0, microsecond=0)
                if next_reset <= now:
                    next_reset += dt.timedelta(days=1)
                components.html(
                    theme.countdown_html(next_reset.strftime("%Y-%m-%dT%H:%M:%S"), "Timer Reset In"),
                    height=22,
                )
            else:
                st.caption("No daily drawdown limit set for this account.")

st.write("")

with st.container(key="card-calendar-preview"):
    today = dt.date.today()
    st.markdown(theme.card_header("This Month", today.strftime("%B %Y"), icon="calendar"), unsafe_allow_html=True)
    weeks = analytics.calendar_matrix(entries, today.year, today.month, today)
    render_month(weeks, account)

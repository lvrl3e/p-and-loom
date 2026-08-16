import streamlit as st

from data.db import get_all_trades
from logic.calculations import add_calculated_columns
from logic import analytics
from ui import charts, theme
from ui.format import fmt_currency, fmt_currency_signed, fmt_pct, fmt_ratio

header_col, btn_col = st.columns([5, 1])
with header_col:
    st.markdown(
        theme.page_header("Dashboard", "Overview of your trading performance", icon="pulse"),
        unsafe_allow_html=True,
    )
with btn_col:
    if st.button("＋ Add Trade", type="primary", width="stretch"):
        st.switch_page("views/add_trade.py")

trades = get_all_trades()

if trades.empty:
    with st.container(key="card-recent-trades"):
        st.markdown(
            """
            <div class="tj-empty">
                <div class="tj-empty-title">No trades logged yet</div>
                <div>Log your first trade to start seeing performance analytics here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.stop()

enriched = add_calculated_columns(trades)
stats = analytics.summary_stats(enriched)
equity = analytics.equity_curve(enriched)

rr = stats["risk_reward_ratio"]
rr_color = theme.TEXT_PRIMARY if rr is None else (theme.GOOD if rr >= 1 else theme.BAD)
dd_color = theme.TEXT_PRIMARY if stats["max_drawdown"] == 0 else theme.BAD
pnl_accent = theme.pnl_color(stats["total_pnl"])

open_count = int((enriched["status"] == "Open").sum())
trades_sub = f"{open_count} open position(s)" if open_count else "All positions closed"

with st.container(key="stat-row"):
    cards = [
        theme.stat_card(
            "Total P&L", fmt_currency_signed(stats["total_pnl"]), icon="dollar", accent=pnl_accent,
            sub=f"{fmt_currency(stats['avg_pnl_per_trade'])} avg / trade",
            spark=list(equity["cumulative_pnl"].tail(10)),
        ),
        theme.stat_card(
            "Win Rate", fmt_pct(stats["win_rate"]), icon="target", accent=theme.ACCENT,
            sub=f"{stats['win_count']} wins · {stats['loss_count']} losses",
        ),
        theme.stat_card(
            "Number of Trades", str(stats["num_trades"]), icon="layers", accent=theme.NEUTRAL,
            sub=trades_sub,
        ),
        theme.stat_card(
            "Avg Win", fmt_currency(stats["avg_win"]), icon="trending-up", accent=theme.GOOD,
            sub=f"Best: {fmt_currency(stats['best_trade'])}",
        ),
        theme.stat_card(
            "Avg Loss", fmt_currency(stats["avg_loss"]), icon="trending-down", accent=theme.BAD,
            sub=f"Worst: {fmt_currency(stats['worst_trade'])}",
        ),
        theme.stat_card(
            "Risk-Reward Ratio", fmt_ratio(rr), icon="activity", accent=rr_color,
            sub="Target ≥ 1.00R",
        ),
        theme.stat_card(
            "Max Drawdown", fmt_currency(stats["max_drawdown"]), icon="alert-triangle", accent=dd_color,
            sub="Peak-to-trough decline",
        ),
    ]
    st.markdown(theme.stat_grid(cards), unsafe_allow_html=True)

st.write("")

with st.container(key="card-equity"):
    st.markdown(theme.card_header("Equity Curve", "Cumulative realized P&L over time", icon="trending-up"), unsafe_allow_html=True)
    st.plotly_chart(charts.equity_curve_chart(equity), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)

col1, col2 = st.columns(2)
with col1:
    with st.container(key="card-distribution"):
        st.markdown(theme.card_header("Win / Loss Distribution", "Spread of P&L across closed trades", icon="bars"), unsafe_allow_html=True)
        closed = analytics.closed_trades(enriched)
        st.plotly_chart(charts.pnl_distribution_chart(closed), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)
with col2:
    with st.container(key="card-strategy"):
        st.markdown(theme.card_header("Performance by Strategy", "Which setups are actually working", icon="target"), unsafe_allow_html=True)
        perf_strategy = analytics.performance_by(enriched, "strategy")
        st.plotly_chart(charts.performance_bar_chart(perf_strategy, "strategy"), width="stretch", theme="streamlit", config=charts.PLOTLY_CONFIG)


def _recent_trades_html(df) -> str:
    rows = []
    for r in df.itertuples():
        has_pnl = r.pnl_dollar == r.pnl_dollar  # not NaN
        pnl_html = (
            f'<span style="color:{theme.pnl_color(r.pnl_dollar)}; font-weight:700;">{fmt_currency_signed(r.pnl_dollar)}</span>'
            if has_pnl
            else '<span class="tj-muted">—</span>'
        )
        has_exit = r.exit_price == r.exit_price
        exit_html = fmt_currency(r.exit_price) if has_exit else "—"
        status_html = theme.status_badge(r.status)
        strategy_html = theme.tag(r.strategy) if isinstance(r.strategy, str) and r.strategy else ""

        # Single line, no blank/whitespace-only lines — see note in ui.theme.stat_card.
        rows.append(
            f'<tr><td style="font-weight:700;">{theme.esc(r.ticker)}</td>'
            f"<td>{theme.direction_badge(r.direction)} {status_html}</td>"
            f'<td class="tj-muted">{fmt_currency(r.entry_price)}</td>'
            f'<td class="tj-muted">{exit_html}</td>'
            f"<td>{pnl_html}</td>"
            f"<td>{strategy_html}</td>"
            f'<td class="tj-muted">{r.entry_date.strftime("%b %d, %Y")}</td></tr>'
        )

    header = (
        "<thead><tr><th>Ticker</th><th>Direction</th><th>Entry</th><th>Exit</th>"
        "<th>P&amp;L</th><th>Strategy</th><th>Date</th></tr></thead>"
    )
    return f'<table class="tj-table">{header}<tbody>{"".join(rows)}</tbody></table>'


with st.container(key="card-recent-trades"):
    header_col, link_col = st.columns([5, 1])
    with header_col:
        st.markdown(theme.card_header("Recent Trades", icon="book"), unsafe_allow_html=True)
    with link_col:
        st.page_link("views/journal.py", label="View all →")

    recent = enriched.sort_values(["entry_date", "id"], ascending=False).head(6)
    st.markdown(_recent_trades_html(recent), unsafe_allow_html=True)

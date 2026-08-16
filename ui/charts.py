"""
Plotly figure builders for the analytics dashboard.

Colors follow the app's black/white/pink theme (see ui.theme): the accent
pink carries the equity curve, green/red stay reserved for profit/loss —
never reused for anything else — and chart chrome (gridlines, axis text)
uses the muted secondary-text gray so figures blend into the dark card
background they're rendered inside.
"""

import pandas as pd
import plotly.graph_objects as go

from ui.theme import ACCENT, GOOD, BAD, TEXT_PRIMARY, TEXT_SECONDARY

MUTED = TEXT_SECONDARY
GRIDLINE = "rgba(255, 255, 255, 0.07)"
ZERO_LINE = "rgba(255, 255, 255, 0.18)"

# Pass to every st.plotly_chart(..., config=PLOTLY_CONFIG) call — hides the
# default Plotly toolbar so charts read as part of the app, not a raw widget.
PLOTLY_CONFIG = {"displayModeBar": False}

_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_SECONDARY, family="Inter, -apple-system, Segoe UI, sans-serif"),
    hoverlabel=dict(bgcolor="#17171A", bordercolor="rgba(255,255,255,0.15)", font_color="#F5F5F5"),
)


def _empty_figure() -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="No closed trades yet", showarrow=False, font=dict(color=MUTED))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(**_BASE_LAYOUT, height=280)
    return fig


def equity_curve_chart(equity_df: pd.DataFrame) -> go.Figure:
    if equity_df.empty:
        return _empty_figure()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity_df["exit_date"],
            y=equity_df["cumulative_pnl"],
            mode="lines",
            line=dict(color=ACCENT, width=2.5, shape="spline", smoothing=0.3),
            fill="tozeroy",
            fillcolor="rgba(232, 93, 158, 0.14)",
            hovertemplate="Cumulative P&L: <b>$%{y:,.2f}</b><extra></extra>",
            name="Equity",
        )
    )

    last = equity_df.iloc[-1]
    fig.add_trace(
        go.Scatter(
            x=[last["exit_date"]],
            y=[last["cumulative_pnl"]],
            mode="markers",
            marker=dict(color=ACCENT, size=8, line=dict(color="#0D0D0F", width=2)),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_annotation(
        x=last["exit_date"],
        y=last["cumulative_pnl"],
        text=f"${last['cumulative_pnl']:,.0f}",
        showarrow=False,
        yshift=18,
        font=dict(color=ACCENT, size=12, family="Inter, sans-serif"),
        bgcolor="rgba(232, 93, 158, 0.12)",
        borderpad=4,
        bordercolor="rgba(232, 93, 158, 0.3)",
        borderwidth=1,
    )

    fig.add_hline(y=0, line_width=1, line_color=ZERO_LINE)
    fig.update_layout(
        margin=dict(l=10, r=10, t=28, b=10),
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Cumulative P&L ($)",
        hovermode="x unified",
        **_BASE_LAYOUT,
    )
    fig.update_xaxes(
        showgrid=False, color=MUTED,
        showspikes=True, spikemode="across", spikesnap="cursor",
        spikecolor="rgba(232, 93, 158, 0.4)", spikethickness=1, spikedash="dot",
    )
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False, color=MUTED)
    return fig


def pnl_distribution_chart(closed_df: pd.DataFrame) -> go.Figure:
    if closed_df.empty:
        return _empty_figure()

    fig = go.Figure()
    wins = closed_df[closed_df["pnl_dollar"] > 0]["pnl_dollar"]
    losses = closed_df[closed_df["pnl_dollar"] <= 0]["pnl_dollar"]

    fig.add_trace(go.Histogram(x=wins, name="Win", marker_color=GOOD, opacity=0.85))
    fig.add_trace(go.Histogram(x=losses, name="Loss", marker_color=BAD, opacity=0.85))

    if len(wins):
        fig.add_vline(x=wins.mean(), line_width=1.5, line_dash="dot", line_color=GOOD,
                       annotation_text="Avg win", annotation_font_color=GOOD, annotation_font_size=11)
    if len(losses):
        fig.add_vline(x=losses.mean(), line_width=1.5, line_dash="dot", line_color=BAD,
                       annotation_text="Avg loss", annotation_font_color=BAD, annotation_font_size=11)

    fig.update_layout(
        barmode="overlay",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="P&L per trade ($)",
        yaxis_title="Number of trades",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=TEXT_SECONDARY)),
        bargap=0.05,
        **_BASE_LAYOUT,
    )
    fig.update_xaxes(showgrid=False, color=MUTED)
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False, color=MUTED)
    return fig


def performance_bar_chart(perf_df: pd.DataFrame, category_col: str, value_col: str = "total_pnl") -> go.Figure:
    if perf_df.empty:
        return _empty_figure()

    fig = go.Figure()
    colors = [GOOD if v >= 0 else BAD for v in perf_df[value_col]]
    text = [f"${v:,.0f}" if v >= 0 else f"-${abs(v):,.0f}" for v in perf_df[value_col]]
    fig.add_trace(
        go.Bar(
            x=perf_df[category_col],
            y=perf_df[value_col],
            marker=dict(color=colors, cornerradius=6, line_width=0),
            text=text,
            textposition="outside",
            textfont=dict(color=TEXT_PRIMARY, size=11),
            cliponaxis=False,
            hovertemplate="%{x}<br>Total P&L: $%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_width=1, line_color=ZERO_LINE)
    fig.update_layout(
        margin=dict(l=10, r=10, t=28, b=10),
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Total P&L ($)",
        bargap=0.35,
        **_BASE_LAYOUT,
    )
    fig.update_xaxes(showgrid=False, color=MUTED)
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False, color=MUTED)
    return fig

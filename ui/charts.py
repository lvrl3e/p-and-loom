"""
Plotly figure builders for the analytics dashboard.

Colors follow the project's validated categorical/status palette (see
palette constants below) so charts read consistently. Figures are rendered
via st.plotly_chart(fig, theme="streamlit") at the call site, which lets
Streamlit adapt chrome (background, fonts, gridlines) to the active
light/dark theme while these explicit series colors carry identity.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BLUE = "#2a78d6"
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"
MUTED = "#898781"
GRIDLINE = "#e1e0d9"

CATEGORICAL = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]


def equity_curve_chart(equity_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if equity_df.empty:
        fig.add_annotation(text="No closed trades yet", showarrow=False, font=dict(color=MUTED))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    fig.add_trace(
        go.Scatter(
            x=equity_df["exit_date"],
            y=equity_df["cumulative_pnl"],
            mode="lines",
            line=dict(color=BLUE, width=2),
            fill="tozeroy",
            fillcolor="rgba(42, 120, 214, 0.12)",
            hovertemplate="%{x|%Y-%m-%d}<br>Cumulative P&L: $%{y:,.2f}<extra></extra>",
            name="Equity",
        )
    )
    fig.add_hline(y=0, line_width=1, line_color=MUTED)
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Cumulative P&L ($)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False)
    return fig


def pnl_distribution_chart(closed_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if closed_df.empty:
        fig.add_annotation(text="No closed trades yet", showarrow=False, font=dict(color=MUTED))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    wins = closed_df[closed_df["pnl_dollar"] > 0]["pnl_dollar"]
    losses = closed_df[closed_df["pnl_dollar"] <= 0]["pnl_dollar"]

    fig.add_trace(go.Histogram(x=wins, name="Win", marker_color=GOOD, opacity=0.85))
    fig.add_trace(go.Histogram(x=losses, name="Loss", marker_color=CRITICAL, opacity=0.85))
    fig.update_layout(
        barmode="overlay",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="P&L per trade ($)",
        yaxis_title="Number of trades",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False)
    return fig


def performance_bar_chart(perf_df: pd.DataFrame, category_col: str, value_col: str = "total_pnl") -> go.Figure:
    fig = go.Figure()
    if perf_df.empty:
        fig.add_annotation(text="No closed trades yet", showarrow=False, font=dict(color=MUTED))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    colors = [GOOD if v >= 0 else CRITICAL for v in perf_df[value_col]]
    fig.add_trace(
        go.Bar(
            x=perf_df[category_col],
            y=perf_df[value_col],
            marker_color=colors,
            hovertemplate="%{x}<br>Total P&L: $%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_width=1, line_color=MUTED)
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Total P&L ($)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False)
    return fig

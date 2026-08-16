"""
Aggregate analytics over a journal of trades.

Every function here expects a DataFrame that has already been passed
through calculations.add_calculated_columns. Only "Closed" trades count
toward performance metrics; open trades are excluded but still shown in
the raw journal table elsewhere.
"""

import numpy as np
import pandas as pd


def closed_trades(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "Closed"].copy()


def summary_stats(df: pd.DataFrame) -> dict:
    """Headline stats for the dashboard. Returns None-safe defaults when
    there are no closed trades yet."""
    closed = closed_trades(df)
    n = len(closed)

    if n == 0:
        return {
            "num_trades": 0,
            "win_rate": None,
            "avg_win": None,
            "avg_loss": None,
            "risk_reward_ratio": None,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "avg_r_multiple": None,
        }

    wins = closed[closed["pnl_dollar"] > 0]
    losses = closed[closed["pnl_dollar"] < 0]

    avg_win = wins["pnl_dollar"].mean() if len(wins) else 0.0
    avg_loss = losses["pnl_dollar"].mean() if len(losses) else 0.0

    risk_reward = (avg_win / abs(avg_loss)) if avg_loss else None

    r_multiples = closed["r_multiple"].dropna()

    return {
        "num_trades": n,
        "win_rate": len(wins) / n * 100,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "risk_reward_ratio": risk_reward,
        "total_pnl": closed["pnl_dollar"].sum(),
        "max_drawdown": max_drawdown(equity_curve(df)),
        "avg_r_multiple": r_multiples.mean() if len(r_multiples) else None,
    }


def equity_curve(df: pd.DataFrame) -> pd.DataFrame:
    """Cumulative realized P&L over time, ordered by exit date."""
    closed = closed_trades(df).sort_values("exit_date")
    if closed.empty:
        return pd.DataFrame(columns=["exit_date", "pnl_dollar", "cumulative_pnl"])
    closed["cumulative_pnl"] = closed["pnl_dollar"].cumsum()
    return closed[["exit_date", "pnl_dollar", "cumulative_pnl"]].reset_index(drop=True)


def max_drawdown(equity_df: pd.DataFrame) -> float:
    """Largest peak-to-trough decline in the cumulative P&L curve."""
    if equity_df.empty:
        return 0.0
    cum = equity_df["cumulative_pnl"]
    running_peak = cum.cummax()
    drawdown = cum - running_peak
    return float(drawdown.min())


def performance_by(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Win rate, total/avg P&L, and trade count grouped by an arbitrary
    column (strategy, ticker, ...)."""
    closed = closed_trades(df)
    if closed.empty or group_col not in closed.columns:
        return pd.DataFrame(columns=[group_col, "trades", "win_rate", "total_pnl", "avg_pnl"])

    grouped = closed.groupby(group_col, dropna=True)
    result = grouped.agg(
        trades=("pnl_dollar", "count"),
        total_pnl=("pnl_dollar", "sum"),
        avg_pnl=("pnl_dollar", "mean"),
        win_rate=("is_win", "mean"),
    ).reset_index()
    result["win_rate"] = result["win_rate"] * 100
    return result.sort_values("total_pnl", ascending=False)


def performance_by_month(df: pd.DataFrame) -> pd.DataFrame:
    closed = closed_trades(df)
    if closed.empty:
        return pd.DataFrame(columns=["month", "trades", "win_rate", "total_pnl", "avg_pnl"])
    closed = closed.copy()
    closed["month"] = closed["exit_date"].dt.to_period("M").astype(str)
    return _group_and_format(closed, "month")


def performance_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    closed = closed_trades(df)
    if closed.empty:
        return pd.DataFrame(columns=["day_of_week", "trades", "win_rate", "total_pnl", "avg_pnl"])
    closed = closed.copy()
    closed["day_of_week"] = closed["exit_date"].dt.day_name()
    result = _group_and_format(closed, "day_of_week")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result["day_of_week"] = pd.Categorical(result["day_of_week"], categories=order, ordered=True)
    return result.sort_values("day_of_week")


def _group_and_format(closed: pd.DataFrame, group_col: str) -> pd.DataFrame:
    grouped = closed.groupby(group_col, dropna=True)
    result = grouped.agg(
        trades=("pnl_dollar", "count"),
        total_pnl=("pnl_dollar", "sum"),
        avg_pnl=("pnl_dollar", "mean"),
        win_rate=("is_win", "mean"),
    ).reset_index()
    result["win_rate"] = result["win_rate"] * 100
    return result

"""
Aggregate analytics over an account's daily P&L entries.

Every function here expects a DataFrame of daily_entries rows (id,
account_id, entry_date, pnl, notes, created_at) as returned by
data.db.get_daily_entries. There is no per-trade math anymore — pnl is a
direct daily input, so "analytics" is entirely about aggregating and
sequencing that one number over time.
"""

import datetime as dt

import numpy as np
import pandas as pd


def with_outcome(df: pd.DataFrame) -> pd.DataFrame:
    """Adds an 'outcome' column: Win / Loss / Breakeven, from the sign of pnl."""
    out = df.copy()
    out["outcome"] = np.select(
        [out["pnl"] > 0, out["pnl"] < 0],
        ["Win", "Loss"],
        default="Breakeven",
    )
    return out


def equity_curve(df: pd.DataFrame, starting_balance: float) -> pd.DataFrame:
    """Cumulative P&L and running account balance over time, ordered by date."""
    if df.empty:
        return pd.DataFrame(columns=["entry_date", "pnl", "cumulative_pnl", "balance"])
    sorted_df = df.sort_values("entry_date").copy()
    sorted_df["cumulative_pnl"] = sorted_df["pnl"].cumsum()
    sorted_df["balance"] = starting_balance + sorted_df["cumulative_pnl"]
    return sorted_df[["entry_date", "pnl", "cumulative_pnl", "balance"]].reset_index(drop=True)


def max_drawdown(equity_df: pd.DataFrame) -> float:
    """Largest peak-to-trough decline in account balance."""
    if equity_df.empty:
        return 0.0
    running_peak = equity_df["balance"].cummax()
    drawdown = equity_df["balance"] - running_peak
    return float(drawdown.min())


def current_drawdown(equity_df: pd.DataFrame, starting_balance: float, drawdown_type: str = "trailing") -> float:
    """Live distance below the drawdown reference point right now — not the
    worst historical dip (see max_drawdown()), but where the account
    actually stands against its limit today. "Trailing" (default, and how
    most prop firms define it) measures from the running peak balance, so
    the reference ratchets up with every new high. "Static" measures from
    the fixed starting balance, which never moves regardless of any
    interim peak. Returned as a non-negative "amount used"; 0 when the
    balance is at or above the reference."""
    if equity_df.empty:
        return 0.0
    current_balance = float(equity_df["balance"].iloc[-1])
    if drawdown_type == "static":
        reference = starting_balance
    else:
        reference = float(equity_df["balance"].cummax().iloc[-1])
    return max(0.0, reference - current_balance)


def drawdown_series(equity_df: pd.DataFrame) -> pd.DataFrame:
    """Drawdown from the running peak balance, for the Analytics drawdown chart."""
    if equity_df.empty:
        return pd.DataFrame(columns=["entry_date", "drawdown"])
    out = equity_df.copy()
    out["drawdown"] = out["balance"] - out["balance"].cummax()
    return out[["entry_date", "drawdown"]]


def current_streak(df: pd.DataFrame) -> dict:
    """Consecutive Win or Loss days ending on the most recent entry.
    Breakeven days break a streak. Returns {"count": int, "type": "Win"|"Loss"|None}."""
    if df.empty:
        return {"count": 0, "type": None}

    outcomes = with_outcome(df).sort_values("entry_date")["outcome"].tolist()
    last = outcomes[-1]
    if last == "Breakeven":
        return {"count": 0, "type": None}

    count = 0
    for outcome in reversed(outcomes):
        if outcome == last:
            count += 1
        else:
            break
    return {"count": count, "type": last}


def saturday_total(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return float(df[df["entry_date"].dt.day_name() == "Saturday"]["pnl"].sum())


def summary_stats(df: pd.DataFrame, starting_balance: float) -> dict:
    """Headline stats for an account (or the combined "All Accounts" view,
    where starting_balance is the sum of every account's starting balance)."""
    n = len(df)

    if n == 0:
        return {
            "num_days": 0,
            "starting_balance": starting_balance,
            "current_balance": starting_balance,
            "total_pnl": 0.0,
            "pnl_pct": 0.0,
            "winning_days": 0,
            "losing_days": 0,
            "breakeven_days": 0,
            "win_rate": None,
            "avg_daily_profit": None,
            "avg_daily_loss": None,
            "best_day": None,
            "worst_day": None,
            "streak": {"count": 0, "type": None},
            "max_drawdown": 0.0,
        }

    tagged = with_outcome(df)
    wins = tagged[tagged["outcome"] == "Win"]
    losses = tagged[tagged["outcome"] == "Loss"]
    breakeven = tagged[tagged["outcome"] == "Breakeven"]
    total_pnl = df["pnl"].sum()
    equity = equity_curve(df, starting_balance)

    decided = len(wins) + len(losses)

    return {
        "num_days": n,
        "starting_balance": starting_balance,
        "current_balance": starting_balance + total_pnl,
        "total_pnl": total_pnl,
        "pnl_pct": (total_pnl / starting_balance * 100) if starting_balance else 0.0,
        "winning_days": len(wins),
        "losing_days": len(losses),
        "breakeven_days": len(breakeven),
        "win_rate": (len(wins) / decided * 100) if decided else None,
        "avg_daily_profit": wins["pnl"].mean() if len(wins) else 0.0,
        "avg_daily_loss": losses["pnl"].mean() if len(losses) else 0.0,
        "best_day": df.loc[wins["pnl"].idxmax()] if len(wins) else None,
        "worst_day": df.loc[df["pnl"].idxmin()] if n else None,
        "streak": current_streak(df),
        "max_drawdown": max_drawdown(equity),
    }


def prop_firm_progress(stats: dict, account: dict, equity_df: pd.DataFrame) -> dict:
    """None-safe progress toward an account's configured profit target /
    drawdown limit / daily loss limit — accounts don't have to set these.

    account is typically built via .iloc[...].to_dict() on a DataFrame row
    upstream, which re-coerces a stored NULL into float NaN (the same
    footgun data.db.coalesce() exists for) — NaN is truthy in Python, so a
    plain `if value:` would treat "not set" as "set to NaN" and silently
    produce nonsense percentages. pd.notna() guards against that below."""
    total_pnl = stats["total_pnl"]

    target = account.get("profit_target")
    target_progress_pct = None
    remaining_to_target = None
    if pd.notna(target):
        target_progress_pct = max(0.0, min(100.0, total_pnl / target * 100))
        remaining_to_target = max(0.0, target - total_pnl)
    else:
        target = None

    dd_limit = account.get("max_drawdown_limit")
    raw_drawdown_type = account.get("drawdown_type")
    drawdown_type = raw_drawdown_type if isinstance(raw_drawdown_type, str) and raw_drawdown_type else "trailing"
    drawdown_used = None
    distance_to_drawdown = None
    drawdown_used_pct = None
    if pd.notna(dd_limit):
        drawdown_used = current_drawdown(equity_df, stats["starting_balance"], drawdown_type)
        distance_to_drawdown = max(0.0, dd_limit - drawdown_used)
        drawdown_used_pct = max(0.0, min(100.0, drawdown_used / dd_limit * 100))
    else:
        dd_limit = None

    daily_loss_pct = account.get("daily_loss_pct")
    daily_loss_limit = None
    daily_loss_used = None
    distance_to_daily_loss = None
    daily_loss_used_pct = None
    if pd.notna(daily_loss_pct):
        today_pnl = 0.0
        today_rows = equity_df[equity_df["entry_date"] == pd.Timestamp(dt.date.today())] if not equity_df.empty else equity_df
        if not today_rows.empty:
            today_pnl = float(today_rows["pnl"].iloc[-1])

        if drawdown_type == "static":
            # Fixed at the account's starting balance, same as the overall
            # static drawdown above — the limit never moves day to day.
            day_start_balance = stats["starting_balance"]
        elif not today_rows.empty:
            day_start_balance = float(today_rows["balance"].iloc[-1]) - today_pnl
        elif not equity_df.empty:
            day_start_balance = float(equity_df["balance"].iloc[-1])
        else:
            day_start_balance = stats["starting_balance"]

        daily_loss_limit = day_start_balance * daily_loss_pct / 100
        daily_loss_used = max(0.0, -today_pnl)
        distance_to_daily_loss = max(0.0, daily_loss_limit - daily_loss_used)

        # A day can end early for either reason — the daily-loss % or the
        # overall drawdown limit — so however much room the account has left
        # today is really whichever cap is tighter. Without this, a nearly
        # maxed-out overall drawdown (e.g. $28 left of an $800 limit) would
        # still show a full daily allowance the trader can't actually use.
        if distance_to_drawdown is not None and distance_to_drawdown < distance_to_daily_loss:
            distance_to_daily_loss = distance_to_drawdown
            daily_loss_limit = daily_loss_used + distance_to_daily_loss

        daily_loss_used_pct = max(0.0, min(100.0, daily_loss_used / daily_loss_limit * 100)) if daily_loss_limit else 0.0
    else:
        daily_loss_pct = None

    raw_reset_time = account.get("daily_reset_time")
    daily_reset_time = raw_reset_time if isinstance(raw_reset_time, str) and raw_reset_time else "00:00"

    return {
        "profit_target": target,
        "target_progress_pct": target_progress_pct,
        "remaining_to_target": remaining_to_target,
        "max_drawdown_limit": dd_limit,
        "drawdown_type": drawdown_type,
        "current_drawdown": drawdown_used,
        "distance_to_drawdown": distance_to_drawdown,
        "drawdown_used_pct": drawdown_used_pct,
        "daily_loss_pct": daily_loss_pct,
        "daily_loss_limit": daily_loss_limit,
        "daily_loss_used": daily_loss_used,
        "distance_to_daily_loss": distance_to_daily_loss,
        "daily_loss_used_pct": daily_loss_used_pct,
        "daily_reset_time": daily_reset_time,
    }


def performance_by_month(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "days", "win_rate", "total_pnl", "avg_pnl"])
    tagged = with_outcome(df).copy()
    tagged["month"] = tagged["entry_date"].dt.to_period("M").astype(str)
    return _group_and_format(tagged, "month")


def performance_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["day_of_week", "days", "win_rate", "total_pnl", "avg_pnl"])
    tagged = with_outcome(df).copy()
    tagged["day_of_week"] = tagged["entry_date"].dt.day_name()
    result = _group_and_format(tagged, "day_of_week")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result["day_of_week"] = pd.Categorical(result["day_of_week"], categories=order, ordered=True)
    return result.sort_values("day_of_week")


def _group_and_format(tagged: pd.DataFrame, group_col: str) -> pd.DataFrame:
    grouped = tagged.groupby(group_col, dropna=True)
    result = grouped.agg(
        days=("pnl", "count"),
        total_pnl=("pnl", "sum"),
        avg_pnl=("pnl", "mean"),
        win_days=("outcome", lambda s: (s == "Win").sum()),
        loss_days=("outcome", lambda s: (s == "Loss").sum()),
    ).reset_index()
    decided = result["win_days"] + result["loss_days"]
    result["win_rate"] = np.where(decided > 0, result["win_days"] / decided * 100, np.nan)
    return result.drop(columns=["win_days", "loss_days"])


def calendar_matrix(df: pd.DataFrame, year: int, month: int, today) -> list:
    """Weeks (Sun-start) covering the given month, each a list of 7 dicts:
    {date, in_month, pnl, outcome, is_today}. pnl/outcome are None on days
    with no entry."""
    import calendar as _calendar

    by_date = {}
    if not df.empty:
        month_df = with_outcome(df)
        for _, row in month_df.iterrows():
            by_date[row["entry_date"].date()] = (row["pnl"], row["outcome"])

    weeks = []
    for week in _calendar.Calendar(firstweekday=6).monthdatescalendar(year, month):
        week_out = []
        for date in week:
            pnl, outcome = by_date.get(date, (None, None))
            week_out.append({
                "date": date,
                "in_month": date.month == month,
                "pnl": pnl,
                "outcome": outcome,
                "is_today": date == today,
            })
        weeks.append(week_out)
    return weeks

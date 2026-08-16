"""
Per-trade calculations: P&L, holding period, R-multiple.

Every function is vectorized over a pandas DataFrame so the whole journal
can be enriched in one pass. A trade is "closed" once it has both an
exit_price and an exit_date; open trades get NaN for every derived metric
except direction-aware unrealized fields, which this module doesn't
attempt (v1 only journals realized trades' analytics).
"""

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "direction",
    "entry_price",
    "exit_price",
    "position_size",
    "stop_loss",
    "entry_date",
    "exit_date",
]


def _sign(direction: pd.Series) -> pd.Series:
    """+1 for Long, -1 for Short."""
    return np.where(direction == "Long", 1.0, -1.0)


def add_calculated_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with pnl_dollar, pnl_pct, holding_period_days,
    r_multiple, is_win, and status columns added."""
    out = df.copy()

    sign = _sign(out["direction"])
    is_closed = out["exit_price"].notna() & out["exit_date"].notna()
    out["status"] = np.where(is_closed, "Closed", "Open")

    price_delta = out["exit_price"] - out["entry_price"]
    out["pnl_dollar"] = np.where(
        is_closed, sign * price_delta * out["position_size"], np.nan
    )

    cost_basis = out["entry_price"] * out["position_size"]
    out["pnl_pct"] = np.where(
        is_closed & (cost_basis != 0), out["pnl_dollar"] / cost_basis * 100, np.nan
    )

    holding = (out["exit_date"] - out["entry_date"]).dt.days
    out["holding_period_days"] = np.where(is_closed, holding, np.nan)

    has_stop = out["stop_loss"].notna()
    risk_dollar = (out["entry_price"] - out["stop_loss"]).abs() * out["position_size"]
    out["r_multiple"] = np.where(
        is_closed & has_stop & (risk_dollar != 0),
        out["pnl_dollar"] / risk_dollar,
        np.nan,
    )

    out["is_win"] = np.where(is_closed, out["pnl_dollar"] > 0, np.nan)

    return out

"""
Data access layer for the trading journal.

All persistence goes through this module. Today it's SQLite via the stdlib
sqlite3 driver; every function returns/accepts plain Python types (dicts,
pandas DataFrames) rather than leaking sqlite-specific objects, so swapping
the backend (e.g. to Postgres via SQLAlchemy) later only means rewriting
this file.
"""

import os
import sqlite3
from contextlib import contextmanager

import pandas as pd

DB_PATH = os.environ.get("TRADING_JOURNAL_DB", os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_journal.db"))

TRADE_COLUMNS = [
    "ticker",
    "direction",
    "entry_price",
    "exit_price",
    "position_size",
    "stop_loss",
    "entry_date",
    "exit_date",
    "strategy",
    "notes",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('Long', 'Short')),
    entry_price REAL NOT NULL,
    exit_price REAL,
    position_size REAL NOT NULL,
    stop_loss REAL,
    entry_date TEXT NOT NULL,
    exit_date TEXT,
    strategy TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute(SCHEMA)


def add_trade(trade: dict) -> int:
    """Insert a trade and return its new id."""
    fields = [c for c in TRADE_COLUMNS if c in trade]
    placeholders = ", ".join("?" for _ in fields)
    columns = ", ".join(fields)
    values = [trade[c] for c in fields]

    with get_connection() as conn:
        cur = conn.execute(
            f"INSERT INTO trades ({columns}) VALUES ({placeholders})", values
        )
        return cur.lastrowid


def update_trade(trade_id: int, trade: dict) -> None:
    fields = [c for c in TRADE_COLUMNS if c in trade]
    assignments = ", ".join(f"{c} = ?" for c in fields)
    values = [trade[c] for c in fields] + [trade_id]

    with get_connection() as conn:
        conn.execute(f"UPDATE trades SET {assignments} WHERE id = ?", values)


def delete_trade(trade_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM trades WHERE id = ?", (trade_id,))


def get_all_trades() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM trades ORDER BY entry_date DESC, id DESC", conn
        )
    for col in ("entry_date", "exit_date"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def get_trade(trade_id: int) -> dict | None:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
        return dict(row) if row else None


def distinct_strategies() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT strategy FROM trades WHERE strategy IS NOT NULL AND strategy != '' ORDER BY strategy"
        ).fetchall()
        return [r[0] for r in rows]

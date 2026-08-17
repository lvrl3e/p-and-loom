"""
Data access layer for the trading journal.

All persistence goes through this module. Today it's SQLite via the stdlib
sqlite3 driver; every function returns/accepts plain Python types (dicts,
pandas DataFrames) rather than leaking sqlite-specific objects, so swapping
the backend (e.g. to Postgres via SQLAlchemy) later only means rewriting
this file.

An account has many daily_entries (one per calendar date, enforced by a
UNIQUE constraint so re-logging a date edits in place). A daily_entry has
many trade_entries (individual trades logged that day — daily_entries.pnl
is a maintained sum of these, kept in sync by recompute_daily_pnl()
whenever a trade is added/removed, so every other reader of .pnl —
analytics, charts, calendar coloring — never has to know trades exist) and
many screenshots. This module is pure SQL — screenshot file I/O lives in
data/storage.py, orchestrated by the views.
"""

import os
import sqlite3
from contextlib import contextmanager

import pandas as pd

DB_PATH = os.environ.get("TRADING_JOURNAL_DB", os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_journal.db"))

ACCOUNT_COLUMNS = [
    "name",
    "firm",
    "account_size",
    "starting_balance",
    "account_type",
    "color",
    "profit_target",
    "max_drawdown_limit",
    "drawdown_type",
    "daily_loss_pct",
    "daily_reset_time",
    "status",
    "login_account_number",
    "login_password",
]

# Added after the original accounts table shipped — new installs get them via
# SCHEMA below, existing databases get them bolted on here since SQLite has
# no "ADD COLUMN IF NOT EXISTS" (see _migrate_accounts_columns()). Maps
# column name to the type/constraints clause used in its ALTER TABLE, since
# SQLite gives a TEXT-affinity column to anything added without one.
_ACCOUNT_MIGRATION_COLUMNS = {
    "login_account_number": "TEXT",
    "login_password": "TEXT",
    "drawdown_type": "TEXT NOT NULL DEFAULT 'trailing'",
    "daily_loss_pct": "REAL",
    "daily_reset_time": "TEXT NOT NULL DEFAULT '00:00'",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    firm TEXT,
    account_size REAL NOT NULL,
    starting_balance REAL NOT NULL,
    account_type TEXT,
    color TEXT NOT NULL DEFAULT '#E85D9E',
    profit_target REAL,
    max_drawdown_limit REAL,
    drawdown_type TEXT NOT NULL DEFAULT 'trailing',
    daily_loss_pct REAL,
    daily_reset_time TEXT NOT NULL DEFAULT '00:00',
    status TEXT NOT NULL DEFAULT 'Active',
    login_account_number TEXT,
    login_password TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    entry_date TEXT NOT NULL,
    pnl REAL NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(account_id, entry_date)
);

CREATE TABLE IF NOT EXISTS trade_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    daily_entry_id INTEGER NOT NULL REFERENCES daily_entries(id) ON DELETE CASCADE,
    pnl REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    daily_entry_id INTEGER NOT NULL REFERENCES daily_entries(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _nan_to_none(df: pd.DataFrame) -> pd.DataFrame:
    """pandas.read_sql_query turns SQL NULL into float NaN. Column-level
    operations (.fillna, .where, .notna on a Series) see this correctly
    either way, but it's normalized here too for anything that reads a
    whole column directly. Row-wise access is a separate problem — see
    coalesce() below."""
    return df.where(pd.notna(df), None)


def coalesce(value, default=None):
    """Returns default if value is None or NaN/NaT.

    Necessary (not just defensive) because extracting a single row from a
    DataFrame with mixed column dtypes (.iloc[i], .iterrows(), .to_dict()
    on a row) re-coerces a stored None back into float NaN — confirmed
    empirically, not just a theoretical edge case. NaN is truthy in Python,
    so plain `value or default` / `if value:` checks silently do the wrong
    thing on any nullable column (firm, profit_target, notes, ...) once
    it's been through row-wise access. Use this instead, everywhere a
    nullable field is read off a row/dict derived from one of this module's
    DataFrames."""
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    return value


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate_accounts_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()}
    for column, type_clause in _ACCOUNT_MIGRATION_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE accounts ADD COLUMN {column} {type_clause}")


def _backfill_daily_loss_pct(conn: sqlite3.Connection) -> None:
    """One-time carry-over for databases from before daily_loss_limit (a
    flat $ amount) was replaced by daily_loss_pct (recalculated daily off
    the day's starting balance). Only fills accounts that still have their
    old $ value and haven't been given a % yet, so it never clobbers a
    value the user has since set via the Account dialog."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()}
    if "daily_loss_limit" not in existing:
        return
    conn.execute(
        """
        UPDATE accounts
        SET daily_loss_pct = ROUND(daily_loss_limit * 100.0 / starting_balance, 2)
        WHERE daily_loss_pct IS NULL
          AND daily_loss_limit IS NOT NULL
          AND starting_balance > 0
        """
    )


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        _migrate_accounts_columns(conn)
        _backfill_daily_loss_pct(conn)


# ---------------------------------------------------------------- accounts

def add_account(account: dict) -> int:
    fields = [c for c in ACCOUNT_COLUMNS if c in account]
    placeholders = ", ".join("?" for _ in fields)
    columns = ", ".join(fields)
    values = [account[c] for c in fields]

    with get_connection() as conn:
        cur = conn.execute(
            f"INSERT INTO accounts ({columns}) VALUES ({placeholders})", values
        )
        return cur.lastrowid


def update_account(account_id: int, account: dict) -> None:
    fields = [c for c in ACCOUNT_COLUMNS if c in account]
    assignments = ", ".join(f"{c} = ?" for c in fields)
    values = [account[c] for c in fields] + [account_id]

    with get_connection() as conn:
        conn.execute(f"UPDATE accounts SET {assignments} WHERE id = ?", values)


def delete_account(account_id: int) -> None:
    """Deletes the account and (via ON DELETE CASCADE) its daily_entries and
    screenshots rows. Callers should fetch screenshot file paths first (see
    get_all_screenshots) and remove the files themselves before calling this."""
    with get_connection() as conn:
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))


def get_all_accounts() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM accounts ORDER BY created_at ASC, id ASC", conn)
    return _nan_to_none(df)


def get_account(account_id: int) -> dict | None:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        return dict(row) if row else None


# ----------------------------------------------------------- daily entries

def upsert_daily_entry(account_id: int, entry_date: str, pnl: float, notes: str | None) -> int:
    """Insert a daily entry, or update it in place if this account already
    has an entry for that date (one entry per account per date)."""
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO daily_entries (account_id, entry_date, pnl, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account_id, entry_date)
            DO UPDATE SET pnl = excluded.pnl, notes = excluded.notes
            """,
            (account_id, entry_date, pnl, notes),
        )
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute(
            "SELECT id FROM daily_entries WHERE account_id = ? AND entry_date = ?",
            (account_id, entry_date),
        ).fetchone()
        return row[0]


def get_daily_entries(account_id: int | None = None) -> pd.DataFrame:
    """All daily entries, optionally scoped to one account. account_id=None
    returns every account's entries (used for the "All Accounts" view).
    Includes a trade_count column (via LEFT JOIN trade_entries) so every
    page that already consumes this DataFrame gets trade counts for free,
    the same way it already gets pnl/notes."""
    query = """
        SELECT e.*, COUNT(t.id) AS trade_count
        FROM daily_entries e
        LEFT JOIN trade_entries t ON t.daily_entry_id = e.id
    """
    params = ()
    if account_id is not None:
        query += " WHERE e.account_id = ?"
        params = (account_id,)
    query += " GROUP BY e.id ORDER BY e.entry_date ASC, e.id ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce")
        df["notes"] = df["notes"].where(df["notes"].notna(), None)
    return df


def get_daily_entry(account_id: int, entry_date: str) -> dict | None:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM daily_entries WHERE account_id = ? AND entry_date = ?",
            (account_id, entry_date),
        ).fetchone()
        return dict(row) if row else None


def ensure_daily_entry(account_id: int, entry_date: str) -> int:
    """Returns the id of the daily_entries row for this account+date,
    creating an empty one (pnl=0, no notes) if it doesn't exist yet. Safe
    to call repeatedly — never touches pnl/notes on an existing row (unlike
    upsert_daily_entry, which overwrites both), so it can't clobber trades
    already recorded for the day."""
    existing = get_daily_entry(account_id, entry_date)
    if existing:
        return existing["id"]
    return upsert_daily_entry(account_id, entry_date, 0.0, None)


def set_daily_notes(daily_entry_id: int, notes: str | None) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE daily_entries SET notes = ? WHERE id = ?", (notes, daily_entry_id))


def delete_daily_entry(entry_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM daily_entries WHERE id = ?", (entry_id,))


# -------------------------------------------------------------- trade entries

def add_trade_entry(daily_entry_id: int, pnl: float) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO trade_entries (daily_entry_id, pnl) VALUES (?, ?)",
            (daily_entry_id, pnl),
        )
        return cur.lastrowid


def get_trade_entries(daily_entry_id: int) -> list[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM trade_entries WHERE daily_entry_id = ? ORDER BY created_at ASC, id ASC",
            (daily_entry_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_trade_entry(trade_entry_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM trade_entries WHERE id = ?", (trade_entry_id,))


def recompute_daily_pnl(daily_entry_id: int) -> float:
    """Re-sums this day's trade_entries and writes the total back onto
    daily_entries.pnl. Call after any add/delete of a trade entry — every
    other reader of daily_entries.pnl (analytics, charts, calendar cell
    coloring) stays correct without knowing trade_entries exists."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(pnl), 0) FROM trade_entries WHERE daily_entry_id = ?",
            (daily_entry_id,),
        ).fetchone()
        total = row[0] or 0.0
        conn.execute("UPDATE daily_entries SET pnl = ? WHERE id = ?", (total, daily_entry_id))
    return total


# ------------------------------------------------------------- screenshots

def add_screenshot(daily_entry_id: int, file_path: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO screenshots (daily_entry_id, file_path) VALUES (?, ?)",
            (daily_entry_id, file_path),
        )
        return cur.lastrowid


def get_screenshots(daily_entry_id: int) -> list[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM screenshots WHERE daily_entry_id = ? ORDER BY uploaded_at ASC",
            (daily_entry_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_screenshot(screenshot_id: int) -> str | None:
    """Deletes the DB row and returns its file_path so the caller can remove
    the file from disk (kept out of this module — see data/storage.py)."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT file_path FROM screenshots WHERE id = ?", (screenshot_id,)
        ).fetchone()
        conn.execute("DELETE FROM screenshots WHERE id = ?", (screenshot_id,))
        return row["file_path"] if row else None


def get_all_screenshots(account_id: int | None = None) -> pd.DataFrame:
    """Screenshots joined with their daily entry (date, account, notes) —
    used by the Screenshots gallery page."""
    query = """
        SELECT s.id, s.file_path, s.uploaded_at,
               e.id AS daily_entry_id, e.entry_date, e.pnl, e.notes, e.account_id,
               a.name AS account_name, a.color AS account_color
        FROM screenshots s
        JOIN daily_entries e ON e.id = s.daily_entry_id
        JOIN accounts a ON a.id = e.account_id
    """
    params = ()
    if account_id is not None:
        query += " WHERE e.account_id = ?"
        params = (account_id,)
    query += " ORDER BY e.entry_date DESC, s.uploaded_at ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce")
        df["notes"] = df["notes"].where(df["notes"].notna(), None)
    return df


# ------------------------------------------------------------------ settings

def get_setting(key: str, default: str | None = None) -> str | None:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def delete_setting(key: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM settings WHERE key = ?", (key,))

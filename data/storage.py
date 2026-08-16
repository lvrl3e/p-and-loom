"""
Local filesystem storage for uploaded screenshots. Kept separate from
data/db.py so that module stays pure-SQL — this one owns file I/O and
nothing else. Files live under <project_root>/uploads/, gitignored the
same way the SQLite database file is (local data, not shipped).
"""

import os
import re
import uuid

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
UPLOAD_ROOT = os.environ.get("TRADING_JOURNAL_UPLOADS", os.path.join(PROJECT_ROOT, "uploads"))

_SAFE_CHARS = re.compile(r"[^a-zA-Z0-9_.-]")


def _safe_filename(name: str) -> str:
    base = _SAFE_CHARS.sub("_", name)
    return f"{uuid.uuid4().hex[:8]}_{base}"


def save_screenshot(uploaded_file, account_id: int, entry_date: str) -> str:
    """Writes a Streamlit UploadedFile to disk and returns its path relative
    to the project root (what gets stored in screenshots.file_path)."""
    folder = os.path.join(UPLOAD_ROOT, str(account_id), entry_date)
    os.makedirs(folder, exist_ok=True)

    filename = _safe_filename(uploaded_file.name)
    absolute_path = os.path.join(folder, filename)
    with open(absolute_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return os.path.relpath(absolute_path, PROJECT_ROOT)


def absolute_path(relative_path: str) -> str:
    return os.path.join(PROJECT_ROOT, relative_path)


def delete_screenshot_file(relative_path: str) -> None:
    path = absolute_path(relative_path)
    if os.path.exists(path):
        os.remove(path)

"""Local audit log. Every query is recorded for accountability.

Uses parameterized SQL only — never string interpolation.
"""

import logging
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    mode      TEXT NOT NULL,
    target    TEXT NOT NULL,
    purpose   TEXT,
    steps     INTEGER,
    status    TEXT NOT NULL
);
"""


def init_db(db_path: str) -> None:
    """Create the audit table if it does not exist."""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(_SCHEMA)
        conn.commit()


def record(
    db_path: str,
    *,
    mode: str,
    target: str,
    purpose: str | None,
    steps: int,
    status: str,
) -> None:
    """Append one audit row. Failures are logged, never silently swallowed."""
    row = (
        datetime.now(timezone.utc).isoformat(),
        mode,
        target,
        purpose,
        steps,
        status,
    )
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(
                "INSERT INTO audit (ts, mode, target, purpose, steps, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                row,
            )
            conn.commit()
    except sqlite3.Error:
        logger.exception(
            "Failed to write audit record", extra={"mode": mode, "target": target}
        )

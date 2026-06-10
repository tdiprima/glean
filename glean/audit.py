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
    steps     INTEGER,
    status    TEXT NOT NULL
);
"""


class Auditor:
    """Records every query to the local audit log.

    Initializing an Auditor creates the audit table if it does not exist.
    Call record() for each query outcome — no separate init step required.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(_SCHEMA)
            conn.commit()

    def record(
        self,
        *,
        mode: str,
        target: str,
        steps: int,
        status: str,
    ) -> None:
        """Append one audit row. Failures are logged, never silently swallowed."""
        row = (
            datetime.now(timezone.utc).isoformat(),
            mode,
            target,
            steps,
            status,
        )
        try:
            with closing(sqlite3.connect(self._db_path)) as conn:
                conn.execute(
                    "INSERT INTO audit (ts, mode, target, steps, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    row,
                )
                conn.commit()
        except sqlite3.Error:
            logger.exception(
                "Failed to write audit record",
                extra={"mode": mode, "target": target},
            )

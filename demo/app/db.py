"""SQLite storage for the reporth demo.

Everything runs locally: a single SQLite file holds organizations, people,
students and debts. Organization isolation is enforced at the query level —
every read filters by ``org_id`` so one organization can never see another's
reports. Sensitive identifiers (cedula, registro civil) live only in the local
database and are never logged.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

DB_PATH = os.environ.get("REPORTH_DB", os.path.join(os.path.dirname(__file__), "..", "reporth.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS organizations (
    id       TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    api_key  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS debts (
    id              TEXT PRIMARY KEY,
    org_id          TEXT NOT NULL REFERENCES organizations(id),
    student_name    TEXT NOT NULL,
    student_rc      TEXT NOT NULL,   -- registro civil (menor)
    parent_name     TEXT NOT NULL,
    parent_cedula   TEXT NOT NULL,
    parent_email    TEXT NOT NULL,
    concept         TEXT NOT NULL,
    amount          REAL NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pendiente',  -- pendiente | pagada
    created_at      TEXT NOT NULL,
    last_charged_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_debts_org ON debts(org_id);
CREATE INDEX IF NOT EXISTS idx_debts_cedula ON debts(parent_cedula);
CREATE INDEX IF NOT EXISTS idx_debts_rc ON debts(student_rc);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(os.path.abspath(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a connection inside a transaction, committing on success."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

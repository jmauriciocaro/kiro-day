"""Data access for reporth, with organization isolation baked into every query.

The golden rule: reads scoped to an organization ALWAYS filter by ``org_id``.
The cross-organization query (:func:`query_person`) returns only an aggregate,
so one organization never sees another's debt detail.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.db import get_conn
from app.models import Debt, ReportIn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_org_by_api_key(api_key: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name FROM organizations WHERE api_key = ?", (api_key,)
        ).fetchone()
        return dict(row) if row else None


def create_debt(org_id: str, payload: ReportIn) -> Debt:
    debt_id = str(uuid.uuid4())
    created_at = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO debts (id, org_id, student_name, student_rc, parent_name,
                               parent_cedula, parent_email, concept, amount,
                               status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendiente', ?)
            """,
            (
                debt_id,
                org_id,
                payload.student_name,
                payload.student_rc,
                payload.parent_name,
                payload.parent_cedula,
                payload.parent_email,
                payload.concept,
                payload.amount,
                created_at,
            ),
        )
    return get_debt(org_id, debt_id)  # type: ignore[return-value]


def list_debts(org_id: str) -> List[Debt]:
    """List debts owned by this organization only."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM debts WHERE org_id = ? ORDER BY created_at DESC",
            (org_id,),
        ).fetchall()
    return [_row_to_debt(r) for r in rows]


def get_debt(org_id: str, debt_id: str) -> Optional[Debt]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM debts WHERE org_id = ? AND id = ?", (org_id, debt_id)
        ).fetchone()
    return _row_to_debt(row) if row else None


def delete_debt(org_id: str, debt_id: str) -> bool:
    """Remove a report. Only the owning organization can delete it."""
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM debts WHERE org_id = ? AND id = ?", (org_id, debt_id)
        )
        return cur.rowcount > 0


def query_person(cedula: Optional[str], registro_civil: Optional[str]) -> dict:
    """Cross-organization lookup. Returns ONLY an aggregate (no org detail).

    Matches pending debts by the parent's cedula or the student's registro
    civil, across all organizations, and reports a count + total so the caller
    can decide accept/deny without seeing who reported or why.
    """
    clauses = []
    params: list = []
    if cedula:
        clauses.append("parent_cedula = ?")
        params.append(cedula)
    if registro_civil:
        clauses.append("student_rc = ?")
        params.append(registro_civil)
    if not clauses:
        return {"reports_count": 0, "total_amount": 0.0}

    where = " OR ".join(clauses)
    with get_conn() as conn:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS c, COALESCE(SUM(amount), 0) AS t
            FROM debts
            WHERE status = 'pendiente' AND ({where})
            """,
            params,
        ).fetchone()
    return {"reports_count": int(row["c"]), "total_amount": float(row["t"])}


def list_pending_debts(org_id: str) -> List[Debt]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM debts WHERE org_id = ? AND status = 'pendiente'",
            (org_id,),
        ).fetchall()
    return [_row_to_debt(r) for r in rows]


def mark_charged(debt_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE debts SET last_charged_at = ? WHERE id = ?",
            (_now_iso(), debt_id),
        )


def _row_to_debt(row) -> Debt:
    return Debt(
        id=row["id"],
        student_name=row["student_name"],
        student_rc=row["student_rc"],
        parent_name=row["parent_name"],
        parent_cedula=row["parent_cedula"],
        parent_email=row["parent_email"],
        concept=row["concept"],
        amount=float(row["amount"]),
        status=row["status"],
        created_at=row["created_at"],
        last_charged_at=row["last_charged_at"],
    )

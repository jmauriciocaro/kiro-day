"""Seed the reporth demo database with two organizations and sample debts.

Idempotent-ish: it resets the demo data each run so the demo always starts from
a known state. Sample identifiers are fictional placeholders, not real PII.
"""
from __future__ import annotations

from app.db import get_conn, init_db
from app import repository as repo
from app.models import ReportIn

ORGS = [
    ("org-pitufos", "Jardin Los Pitufos", "org-pitufos-key"),
    ("org-saber", "Academia El Saber", "org-saber-key"),
]


def seed() -> None:
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM debts")
        conn.execute("DELETE FROM organizations")
        conn.executemany(
            "INSERT INTO organizations (id, name, api_key) VALUES (?, ?, ?)", ORGS
        )

    # One org reports a debtor; useful to demo a "denegar" query result.
    repo.create_debt(
        "org-pitufos",
        ReportIn(
            student_name="Pedro Gomez",
            student_rc="RC-10001",
            parent_name="Marta Gomez",
            parent_cedula="52000111",
            parent_email="marta@example.local",
            concept="Pension marzo",
            amount=350000,
        ),
    )
    repo.create_debt(
        "org-saber",
        ReportIn(
            student_name="Pedro Gomez",
            student_rc="RC-10001",
            parent_name="Marta Gomez",
            parent_cedula="52000111",
            parent_email="marta@example.local",
            concept="Curso de ingles",
            amount=120000,
        ),
    )
    print("Seed listo: 2 organizaciones y 2 deudas de ejemplo.")
    print("API keys:  org-pitufos-key  |  org-saber-key")


if __name__ == "__main__":
    seed()

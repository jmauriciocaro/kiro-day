"""FastAPI application for the reporth demo (runs locally with uvicorn).

Organizations authenticate with an ``X-API-Key`` header. Every org-scoped route
resolves the caller's ``org_id`` from that key and passes it down, so isolation
is enforced server-side. The cross-org query route returns only an aggregate
verdict. The single-page UI is served from ``static/index.html``.
"""
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import repository as repo
from app.db import init_db
from app.mailer import send_charge
from app.models import ChargeResult, Debt, QueryVerdict, ReportIn

app = FastAPI(
    title="reporth API",
    description="Central de reporte de deudas B2B entre prestadores de servicios (demo local).",
    version="0.1.0",
)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


@app.on_event("startup")
def _startup() -> None:
    init_db()


def current_org(x_api_key: Optional[str] = Header(default=None)) -> dict:
    """Resolve the calling organization from its API key, or reject (401)."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Falta el header X-API-Key.")
    org = repo.get_org_by_api_key(x_api_key)
    if org is None:
        raise HTTPException(status_code=401, detail="API key invalida.")
    return org


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/me")
def me(org=Depends(current_org)) -> dict:
    return {"org_id": org["id"], "org_name": org["name"]}


@app.post("/api/debts", response_model=Debt, status_code=201)
def report_debt(payload: ReportIn, org=Depends(current_org)) -> Debt:
    """Report a new debt owned by the authenticated organization."""
    return repo.create_debt(org["id"], payload)


@app.get("/api/debts", response_model=List[Debt])
def list_debts(org=Depends(current_org)) -> List[Debt]:
    """List ONLY the debts this organization reported."""
    return repo.list_debts(org["id"])


@app.delete("/api/debts/{debt_id}", status_code=204)
def delete_debt(debt_id: str, org=Depends(current_org)) -> Response:
    """Remove a report. Only the owning organization can do this."""
    if not repo.delete_debt(org["id"], debt_id):
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    return Response(status_code=204)


@app.get("/api/query", response_model=QueryVerdict)
def query_person(
    cedula: Optional[str] = None,
    registro_civil: Optional[str] = None,
    org=Depends(current_org),
) -> QueryVerdict:
    """Consult a person to decide accept/deny.

    Returns only an aggregate across all organizations: whether there are
    pending debts, how many and the total. No creditor, concept or other detail.
    """
    if not cedula and not registro_civil:
        raise HTTPException(status_code=400, detail="Indica cedula o registro civil.")
    agg = repo.query_person(cedula, registro_civil)
    has_debts = agg["reports_count"] > 0
    return QueryVerdict(
        has_debts=has_debts,
        verdict="denegar" if has_debts else "aceptar",
        reports_count=agg["reports_count"],
        total_amount=agg["total_amount"],
    )


@app.post("/api/charge", response_model=ChargeResult)
def charge_pending(org=Depends(current_org)) -> ChargeResult:
    """Send the automatic email charge for this org's pending debts."""
    pending = repo.list_pending_debts(org["id"])
    delivered = 0
    failed = 0
    details: List[str] = []
    for debt in pending:
        ok = send_charge(
            to_email=debt.parent_email,
            parent_name=debt.parent_name,
            org_name=org["name"],
            concept=debt.concept,
            amount=debt.amount,
        )
        repo.mark_charged(debt.id)
        if ok:
            delivered += 1
            details.append(f"Enviado a {debt.parent_email}")
        else:
            failed += 1
            details.append(f"No entregado a {debt.parent_email} (sin SMTP local)")
    return ChargeResult(
        charged=len(pending), delivered=delivered, failed=failed, details=details
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


# Serve static assets (the single-page UI) under /static.
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

"""End-to-end smoke check against the FastAPI app wired to a live DynamoDB.

Runs the full stack (routing -> auth -> services -> DynamoDB transaction ->
reporting) via TestClient. Expects a DynamoDB endpoint (moto server or real)
with a seeded `pos` table and users `ana`/`don`.

Env required:
    POS_TABLE_NAME, POS_DYNAMODB_ENDPOINT_URL, AWS_REGION, POS_JWT_SECRET,
    plus dummy AWS credentials for the endpoint.
"""
from __future__ import annotations

import os
import sys

# Allow running from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.auth import hash_password
from app.main import app
from app.repository import Repository

client = TestClient(app)
failures = []


def check(name, condition):
    status = "OK" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition:
        failures.append(name)


# Ensure a product exists (owner-created) and users exist.
repo = Repository()
repo.upsert_user("ana", hash_password("clave123"), "cajero")
repo.upsert_user("don", hash_password("jefe123"), "dueno")

# 1. Login as owner, create a product.
owner = client.post("/auth/login", json={"username": "don", "password": "jefe123"})
check("login dueño 200", owner.status_code == 200)
owner_token = owner.json()["access_token"]
oh = {"Authorization": f"Bearer {owner_token}"}

created = client.post(
    "/products",
    headers=oh,
    json={"sku": "CAFE-E2E", "name": "Café E2E", "price": "3000", "stock": 5},
)
check("crear producto 201", created.status_code == 201)

# 2. Login as cashier, list catalog, register a sale.
cashier = client.post("/auth/login", json={"username": "ana", "password": "clave123"})
check("login cajero 200", cashier.status_code == 200)
cashier_token = cashier.json()["access_token"]
ch = {"Authorization": f"Bearer {cashier_token}"}

catalog = client.get("/products", headers=ch)
check("listar catálogo 200", catalog.status_code == 200)
check("catálogo contiene producto", any(p["sku"] == "CAFE-E2E" for p in catalog.json()))

sale = client.post(
    "/sales",
    headers=ch,
    json={"items": [{"sku": "CAFE-E2E", "qty": 2}], "payment_method": "efectivo"},
)
check("registrar venta 201", sale.status_code == 201)
check("total calculado = 6000", sale.status_code == 201 and sale.json()["total"] == "6000")

# 3. Stock decremented 5 -> 3.
prod = client.get("/products/CAFE-E2E", headers=ch)
check("stock descontado a 3", prod.status_code == 200 and prod.json()["stock"] == 3)

# 4. Oversell is rejected (only 3 left, ask 10).
oversell = client.post(
    "/sales",
    headers=ch,
    json={"items": [{"sku": "CAFE-E2E", "qty": 10}], "payment_method": "tarjeta"},
)
check("sobreventa rechazada 409", oversell.status_code == 409)

# 5. Cashier cannot see report (403); owner can.
cashier_report = client.get("/reports/daily", headers=ch)
check("reporte denegado a cajero 403", cashier_report.status_code == 403)

owner_report = client.get("/reports/daily", headers=oh)
check("reporte dueño 200", owner_report.status_code == 200)
check(
    "reporte cuenta 1 venta, total 6000",
    owner_report.status_code == 200
    and owner_report.json()["count"] == 1
    and owner_report.json()["total"] == "6000",
)

print()
if failures:
    print(f"E2E FALLÓ: {len(failures)} comprobación(es): {failures}")
    sys.exit(1)
print("E2E OK: flujo completo verificado (login → venta → stock → reporte).")

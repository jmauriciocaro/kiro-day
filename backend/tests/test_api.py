"""API-level tests with TestClient (Requirements 1, 2, 3, 4, 5.4, 7)."""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app import auth, deps
from app.main import app
from app.models import Product
from app.services import ReportService, SalesService


@pytest.fixture
def client(repository, monkeypatch):
    monkeypatch.setenv("POS_JWT_SECRET", "test-secret-not-in-repo")
    auth._resolve_secret.cache_clear()
    from app.config import get_settings

    get_settings.cache_clear()

    # Seed users.
    repository.upsert_user("ana", auth.hash_password("clave123"), "cajero")
    repository.upsert_user("don", auth.hash_password("jefe123"), "dueno")
    # Seed a product.
    repository.create_product(
        Product(sku="CAFE-01", name="Café", price=Decimal("3500"), stock=10)
    )

    # Override dependency providers to use the mocked repository.
    app.dependency_overrides[deps.get_repository] = lambda: repository
    app.dependency_overrides[deps.get_sales_service] = lambda: SalesService(
        repository=repository
    )
    app.dependency_overrides[deps.get_report_service] = lambda: ReportService(
        repository=repository
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
    auth._resolve_secret.cache_clear()
    get_settings.cache_clear()


def _login(client, username, password):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_login_bad_credentials_is_401(client):
    resp = client.post("/auth/login", json={"username": "ana", "password": "mala"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "Usuario o clave incorrectos"


def test_list_products_requires_auth(client):
    assert client.get("/products").status_code == 401


def test_list_products_with_cashier(client):
    token = _login(client, "ana", "clave123")
    resp = client.get("/products", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()[0]["sku"] == "CAFE-01"


def test_create_product_requires_owner(client):
    cashier = _login(client, "ana", "clave123")
    resp = client.post(
        "/products",
        headers=_auth(cashier),
        json={"sku": "T-1", "name": "Té", "price": "2000", "stock": 5},
    )
    assert resp.status_code == 403


def test_create_product_as_owner(client):
    owner = _login(client, "don", "jefe123")
    resp = client.post(
        "/products",
        headers=_auth(owner),
        json={"sku": "T-1", "name": "Té", "price": "2000", "stock": 5},
    )
    assert resp.status_code == 201
    assert resp.json()["sku"] == "T-1"


def test_create_duplicate_sku_is_409(client):
    owner = _login(client, "don", "jefe123")
    body = {"sku": "CAFE-01", "name": "Café", "price": "3500", "stock": 1}
    resp = client.post("/products", headers=_auth(owner), json=body)
    assert resp.status_code == 409
    assert "SKU" in resp.json()["error"]


def test_get_missing_product_is_404(client):
    token = _login(client, "ana", "clave123")
    resp = client.get("/products/NOPE", headers=_auth(token))
    assert resp.status_code == 404


def test_create_sale_decrements_stock(client):
    token = _login(client, "ana", "clave123")
    resp = client.post(
        "/sales",
        headers=_auth(token),
        json={"items": [{"sku": "CAFE-01", "qty": 2}], "payment_method": "efectivo"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["total"] == "7000"
    # stock went from 10 to 8
    prod = client.get("/products/CAFE-01", headers=_auth(token)).json()
    assert prod["stock"] == 8


def test_create_sale_insufficient_stock_is_409(client):
    token = _login(client, "ana", "clave123")
    resp = client.post(
        "/sales",
        headers=_auth(token),
        json={"items": [{"sku": "CAFE-01", "qty": 99}], "payment_method": "efectivo"},
    )
    assert resp.status_code == 409
    assert "stock" in resp.json()["error"].lower()


def test_create_sale_unknown_sku_is_400(client):
    token = _login(client, "ana", "clave123")
    resp = client.post(
        "/sales",
        headers=_auth(token),
        json={"items": [{"sku": "NOPE", "qty": 1}], "payment_method": "efectivo"},
    )
    assert resp.status_code == 400
    assert "no existe" in resp.json()["error"]


def test_update_product_as_owner(client):
    owner = _login(client, "don", "jefe123")
    resp = client.patch(
        "/products/CAFE-01",
        headers=_auth(owner),
        json={"price": "4000", "stock": 25},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["price"] == "4000"
    assert body["stock"] == 25


def test_update_product_requires_owner(client):
    cashier = _login(client, "ana", "clave123")
    resp = client.patch(
        "/products/CAFE-01", headers=_auth(cashier), json={"stock": 1}
    )
    assert resp.status_code == 403


def test_update_missing_product_is_404(client):
    owner = _login(client, "don", "jefe123")
    resp = client.patch(
        "/products/NOPE", headers=_auth(owner), json={"stock": 1}
    )
    assert resp.status_code == 404


def test_report_with_explicit_date(client):
    owner = _login(client, "don", "jefe123")
    resp = client.get("/reports/daily?date=2000-01-01", headers=_auth(owner))
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == "2000-01-01"
    assert body["count"] == 0
    assert body["total"] == "0"


def test_report_requires_owner(client):
    cashier = _login(client, "ana", "clave123")
    assert client.get("/reports/daily", headers=_auth(cashier)).status_code == 403


def test_report_as_owner(client):
    cashier = _login(client, "ana", "clave123")
    client.post(
        "/sales",
        headers=_auth(cashier),
        json={"items": [{"sku": "CAFE-01", "qty": 1}], "payment_method": "efectivo"},
    )
    owner = _login(client, "don", "jefe123")
    resp = client.get("/reports/daily", headers=_auth(owner))
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["total"] == "3500"

"""FastAPI application: routes, role enforcement and error handling.

The app runs locally with uvicorn and on AWS Lambda through Mangum, so the
application code is identical in both environments. Domain errors are mapped to
HTTP responses with Spanish messages (consumed by the frontend).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import BaseModel

from app import auth, deps
from app.auth import require_role
from app.errors import (
    DomainError,
    DuplicateSkuError,
    InsufficientStockError,
    InvalidCredentialsError,
    ProductNotFoundError,
    SkuNotFoundError,
    StockConflictError,
)
from app.models import DailyReport, Product, ProductCreate, ProductUpdate, Sale, SaleIn

app = FastAPI(
    title="POS MVP API",
    description="Punto de venta para tiendas de barrio — API del MVP.",
    version="0.1.0",
)

# Map each domain error to an HTTP status code. Messages are already in Spanish.
_ERROR_STATUS = {
    DuplicateSkuError: 409,
    ProductNotFoundError: 404,
    SkuNotFoundError: 400,
    InsufficientStockError: 409,
    StockConflictError: 409,
    InvalidCredentialsError: 401,
}


@app.exception_handler(DomainError)
def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status_code = _ERROR_STATUS.get(type(exc), 400)
    return JSONResponse(status_code=status_code, content={"error": exc.message})


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, repo=Depends(deps.get_repository)) -> TokenOut:
    token = auth.authenticate(payload.username, payload.password, repo)
    claims = auth.decode_token(token)
    return TokenOut(access_token=token, role=claims["role"])


@app.get("/products", response_model=List[Product])
def list_products(
    repo=Depends(deps.get_repository),
    _user=Depends(require_role("cajero", "dueno")),
) -> List[Product]:
    return repo.list_products()


@app.get("/products/{sku}", response_model=Product)
def get_product(
    sku: str,
    repo=Depends(deps.get_repository),
    _user=Depends(require_role("cajero", "dueno")),
) -> Product:
    product = repo.get_product(sku)
    if product is None:
        raise ProductNotFoundError()
    return product


@app.post("/products", response_model=Product, status_code=201)
def create_product(
    payload: ProductCreate,
    repo=Depends(deps.get_repository),
    _user=Depends(require_role("dueno")),
) -> Product:
    product = Product(**payload.model_dump())
    return repo.create_product(product)


@app.patch("/products/{sku}", response_model=Product)
def update_product(
    sku: str,
    payload: ProductUpdate,
    repo=Depends(deps.get_repository),
    _user=Depends(require_role("dueno")),
) -> Product:
    updated = repo.update_product(sku, payload)
    if updated is None:
        raise ProductNotFoundError()
    return updated


@app.post("/sales", response_model=Sale, status_code=201)
def create_sale(
    payload: SaleIn,
    service=Depends(deps.get_sales_service),
    user=Depends(require_role("cajero", "dueno")),
) -> Sale:
    return service.register_sale(payload, cashier=user.username)


@app.get("/reports/daily", response_model=DailyReport)
def daily_report(
    date: Optional[str] = None,
    service=Depends(deps.get_report_service),
    _user=Depends(require_role("dueno")),
) -> DailyReport:
    return service.daily_report(date)


# AWS Lambda handler (API Gateway HTTP API -> FastAPI via Mangum).
handler = Mangum(app)

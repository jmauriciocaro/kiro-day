"""Domain models (Pydantic v2) for the POS MVP.

Monetary values use Decimal to allow exact arithmetic and summation in reports
(never float, never string). Server-side validation enforces the business rules
from the requirements: positive prices, non-negative stock, non-empty sales and
positive quantities, and an allow-listed payment method.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["efectivo", "tarjeta"]


class Product(BaseModel):
    """A catalog product."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)


class ProductCreate(BaseModel):
    """Payload to create a product."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)


class ProductUpdate(BaseModel):
    """Partial update for price and/or stock of an existing product."""

    model_config = ConfigDict(extra="forbid")

    price: Optional[Decimal] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)


class SaleItemIn(BaseModel):
    """A requested sale line: which product and how many units."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1)
    qty: int = Field(gt=0)


class SaleIn(BaseModel):
    """Incoming sale request from the cashier."""

    model_config = ConfigDict(extra="forbid")

    items: List[SaleItemIn] = Field(min_length=1)
    payment_method: PaymentMethod


class SaleItem(SaleItemIn):
    """A persisted sale line, denormalized with name and unit price."""

    name: str = Field(min_length=1)
    unit_price: Decimal = Field(gt=0)


class Sale(BaseModel):
    """A completed sale."""

    model_config = ConfigDict(extra="forbid")

    sale_id: str
    created_at: str  # ISO-8601 UTC
    items: List[SaleItem] = Field(min_length=1)
    total: Decimal = Field(gt=0)
    payment_method: PaymentMethod
    payment_status: str
    cashier: str


class DailyReport(BaseModel):
    """Aggregated sales for a single day."""

    model_config = ConfigDict(extra="forbid")

    date: str  # yyyy-mm-dd
    sales: List[Sale]
    total: Decimal = Field(ge=0)
    count: int = Field(ge=0)

"""Unit tests for domain model validation (Requirements 1.3, 2.5, 2.6)."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import ProductCreate, SaleIn, SaleItemIn


def test_product_create_valid():
    product = ProductCreate(sku="CAFE-01", name="Café", price=Decimal("3500"), stock=10)
    assert product.price == Decimal("3500")
    assert product.stock == 10


def test_product_create_rejects_negative_price():
    with pytest.raises(ValidationError):
        ProductCreate(sku="X", name="X", price=Decimal("-1"), stock=1)


def test_product_create_rejects_zero_price():
    with pytest.raises(ValidationError):
        ProductCreate(sku="X", name="X", price=Decimal("0"), stock=1)


def test_product_create_rejects_negative_stock():
    with pytest.raises(ValidationError):
        ProductCreate(sku="X", name="X", price=Decimal("10"), stock=-1)


def test_sale_item_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        SaleItemIn(sku="X", qty=0)


def test_sale_item_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        SaleItemIn(sku="X", qty=-3)


def test_sale_rejects_empty_items():
    with pytest.raises(ValidationError):
        SaleIn(items=[], payment_method="efectivo")


def test_sale_rejects_invalid_payment_method():
    with pytest.raises(ValidationError):
        SaleIn(items=[SaleItemIn(sku="X", qty=1)], payment_method="bitcoin")


def test_sale_accepts_allowed_payment_methods():
    for method in ("efectivo", "tarjeta"):
        sale = SaleIn(items=[SaleItemIn(sku="X", qty=1)], payment_method=method)
        assert sale.payment_method == method

"""Integration tests for product repository operations (Requirement 1)."""
from decimal import Decimal

import pytest

from app.errors import DuplicateSkuError
from app.models import Product, ProductUpdate


def _product(sku="CAFE-01", name="Café", price="3500", stock=10) -> Product:
    return Product(sku=sku, name=name, price=Decimal(price), stock=stock)


def test_create_and_get_product(repository):
    repository.create_product(_product())
    fetched = repository.get_product("CAFE-01")
    assert fetched is not None
    assert fetched.name == "Café"
    assert fetched.price == Decimal("3500")
    assert fetched.stock == 10


def test_get_missing_product_returns_none(repository):
    assert repository.get_product("NOPE") is None


def test_create_duplicate_sku_is_rejected(repository):
    repository.create_product(_product())
    with pytest.raises(DuplicateSkuError):
        repository.create_product(_product(name="Otro café"))


def test_list_products_returns_catalog_sorted_by_name(repository):
    repository.create_product(_product(sku="B", name="Zumo", price="2000", stock=5))
    repository.create_product(_product(sku="A", name="Agua", price="1500", stock=20))
    catalog = repository.list_products()
    assert [p.name for p in catalog] == ["Agua", "Zumo"]


def test_update_product_price_and_stock(repository):
    repository.create_product(_product())
    updated = repository.update_product(
        "CAFE-01", ProductUpdate(price=Decimal("4000"), stock=25)
    )
    assert updated is not None
    assert updated.price == Decimal("4000")
    assert updated.stock == 25


def test_update_only_stock_keeps_price(repository):
    repository.create_product(_product())
    updated = repository.update_product("CAFE-01", ProductUpdate(stock=3))
    assert updated.price == Decimal("3500")
    assert updated.stock == 3


def test_update_missing_product_returns_none(repository):
    assert repository.update_product("NOPE", ProductUpdate(stock=1)) is None

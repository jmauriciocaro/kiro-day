"""Integration tests for atomic sale registration (Requirement 3).

Exercises the real TransactWriteItems path against a mocked DynamoDB table.
"""
from decimal import Decimal

import pytest

from app.errors import StockConflictError
from app.models import Product, SaleIn, SaleItemIn
from app.services import SalesService


def _seed(repository, sku="A", name="Agua", price="1500", stock=10):
    repository.create_product(
        Product(sku=sku, name=name, price=Decimal(price), stock=stock)
    )


def test_successful_sale_decrements_stock(repository):
    _seed(repository, stock=10)
    service = SalesService(repository=repository)
    service.register_sale(
        SaleIn(items=[SaleItemIn(sku="A", qty=3)], payment_method="efectivo"),
        cashier="ana",
    )
    assert repository.get_product("A").stock == 7


def test_insufficient_stock_writes_nothing(repository):
    _seed(repository, stock=2)
    service = SalesService(repository=repository)
    # 2 units available, selling 2 of A succeeds; but a second line B missing
    # stock must cancel the whole transaction.
    _seed(repository, sku="B", name="Café", price="3500", stock=1)
    with pytest.raises(StockConflictError):
        # service validation would catch qty>stock first, so go through repo
        # directly with a sale that passes validation but fails the condition.
        from app.models import Sale, SaleItem

        sale = Sale(
            sale_id="deadbeef",
            created_at="2026-10-24T10:00:00.000000Z",
            items=[
                SaleItem(sku="A", qty=2, name="Agua", unit_price=Decimal("1500")),
                SaleItem(sku="B", qty=5, name="Café", unit_price=Decimal("3500")),
            ],
            total=Decimal("20500"),
            payment_method="efectivo",
            payment_status="aprobado",
            cashier="ana",
        )
        repository.register_sale(sale)
    # Nothing changed: both products keep their original stock.
    assert repository.get_product("A").stock == 2
    assert repository.get_product("B").stock == 1


def test_concurrent_sales_never_oversell(repository):
    """Two sales each try to buy the last 6 units of a product with 10 stock.

    One must succeed; the other must be rejected (stock would go negative).
    Executed sequentially against the same table to prove the condition guard.
    """
    _seed(repository, stock=10)
    service = SalesService(repository=repository)

    first = SaleIn(items=[SaleItemIn(sku="A", qty=6)], payment_method="efectivo")
    second = SaleIn(items=[SaleItemIn(sku="A", qty=6)], payment_method="efectivo")

    service.register_sale(first, cashier="ana")  # 10 -> 4

    # Second sale passes service validation only if read sees stock>=6; after
    # the first sale stock is 4, so service validation rejects it. Simulate the
    # race where validation read stale stock (10) but the condition enforces it.
    from app.models import Sale, SaleItem

    racing = Sale(
        sale_id="race0001",
        created_at="2026-10-24T10:00:01.000000Z",
        items=[SaleItem(sku="A", qty=6, name="Agua", unit_price=Decimal("1500"))],
        total=Decimal("9000"),
        payment_method="efectivo",
        payment_status="aprobado",
        cashier="luis",
    )
    with pytest.raises(StockConflictError):
        repository.register_sale(racing)

    # Final stock reflects only the first successful sale.
    assert repository.get_product("A").stock == 4

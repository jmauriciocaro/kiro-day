"""Unit tests for sales business logic (Requirement 2).

Uses a lightweight in-memory fake repository so these tests stay fast and
independent of DynamoDB. Atomic persistence is covered in the integration
tests (test_sales_atomic.py).
"""
from decimal import Decimal

import pytest

from app.errors import InsufficientStockError, SkuNotFoundError
from app.models import Product, SaleIn, SaleItemIn
from app.services import SalesService


class FakeRepo:
    def __init__(self, products):
        self._products = {p.sku: p for p in products}
        self.registered = None

    def get_product(self, sku):
        return self._products.get(sku)

    def register_sale(self, sale):
        self.registered = sale
        return sale


def _service(products):
    return SalesService(repository=FakeRepo(products))


def test_total_is_calculated_server_side():
    products = [
        Product(sku="A", name="Agua", price=Decimal("1500"), stock=10),
        Product(sku="B", name="Café", price=Decimal("3500"), stock=10),
    ]
    service = _service(products)
    sale_in = SaleIn(
        items=[SaleItemIn(sku="A", qty=2), SaleItemIn(sku="B", qty=1)],
        payment_method="efectivo",
    )
    sale = service.register_sale(sale_in, cashier="ana")
    # 2*1500 + 1*3500 = 6500
    assert sale.total == Decimal("6500")
    assert sale.payment_status == "aprobado"
    assert sale.cashier == "ana"
    assert {line.sku: line.qty for line in sale.items} == {"A": 2, "B": 1}


def test_unknown_sku_is_rejected():
    service = _service([Product(sku="A", name="Agua", price=Decimal("1500"), stock=5)])
    sale_in = SaleIn(items=[SaleItemIn(sku="NOPE", qty=1)], payment_method="efectivo")
    with pytest.raises(SkuNotFoundError):
        service.register_sale(sale_in, cashier="ana")


def test_insufficient_stock_is_rejected():
    service = _service([Product(sku="A", name="Agua", price=Decimal("1500"), stock=1)])
    sale_in = SaleIn(items=[SaleItemIn(sku="A", qty=5)], payment_method="efectivo")
    with pytest.raises(InsufficientStockError):
        service.register_sale(sale_in, cashier="ana")

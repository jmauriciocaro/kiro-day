"""Integration tests for the daily sales report (Requirement 4)."""
from decimal import Decimal

from app.models import Product, SaleIn, SaleItemIn
from app.services import ReportService, SalesService


def _seed_product(repository, sku="A", name="Agua", price="1500", stock=100):
    repository.create_product(
        Product(sku=sku, name=name, price=Decimal(price), stock=stock)
    )


def _today(repository):
    # Register sales "today" through the service so created_at is today's date.
    from app.services import _today_utc

    return _today_utc()


def test_report_aggregates_total_and_count(repository):
    _seed_product(repository)
    sales = SalesService(repository=repository)
    sales.register_sale(
        SaleIn(items=[SaleItemIn(sku="A", qty=2)], payment_method="efectivo"),
        cashier="ana",
    )
    sales.register_sale(
        SaleIn(items=[SaleItemIn(sku="A", qty=1)], payment_method="tarjeta"),
        cashier="ana",
    )

    report = ReportService(repository=repository).daily_report()
    assert report.count == 2
    assert report.total == Decimal("4500")  # (2*1500) + (1*1500)
    assert len(report.sales) == 2


def test_report_sales_are_ordered_by_time(repository):
    _seed_product(repository)
    sales = SalesService(repository=repository)
    for _ in range(3):
        sales.register_sale(
            SaleIn(items=[SaleItemIn(sku="A", qty=1)], payment_method="efectivo"),
            cashier="ana",
        )
    report = ReportService(repository=repository).daily_report()
    timestamps = [s.created_at for s in report.sales]
    assert timestamps == sorted(timestamps)


def test_report_empty_day_returns_zero(repository):
    report = ReportService(repository=repository).daily_report("2000-01-01")
    assert report.count == 0
    assert report.total == Decimal("0")
    assert report.sales == []


def test_report_defaults_to_today(repository):
    _seed_product(repository)
    SalesService(repository=repository).register_sale(
        SaleIn(items=[SaleItemIn(sku="A", qty=1)], payment_method="efectivo"),
        cashier="ana",
    )
    report = ReportService(repository=repository).daily_report()
    from app.services import _today_utc

    assert report.date == _today_utc()
    assert report.count == 1

"""Business logic for the POS: sales and daily reports.

Services orchestrate validation, server-side total calculation, the simulated
payment, and the atomic stock-decrementing write. They depend on the Repository
and PaymentProvider abstractions, not on boto3 or FastAPI.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from app.errors import InsufficientStockError, SkuNotFoundError
from app.models import DailyReport, Sale, SaleIn, SaleItem
from app.payments import PaymentProvider, SimulatedPaymentProvider
from app.repository import Repository


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class SalesService:
    """Create sales with server-side totals and atomic stock decrement."""

    def __init__(
        self,
        repository: Repository,
        payment_provider: Optional[PaymentProvider] = None,
    ) -> None:
        self._repo = repository
        self._payments = payment_provider or SimulatedPaymentProvider()

    def register_sale(self, sale_in: SaleIn, cashier: str) -> Sale:
        """Validate, price, charge (simulated) and persist a sale atomically."""
        # Resolve each line against the current catalog and validate stock.
        line_items = []
        total = Decimal("0")
        for item in sale_in.items:
            product = self._repo.get_product(item.sku)
            if product is None:
                raise SkuNotFoundError(item.sku)
            if item.qty > product.stock:
                raise InsufficientStockError(product.name)
            line_total = product.price * item.qty
            total += line_total
            line_items.append(
                SaleItem(
                    sku=product.sku,
                    qty=item.qty,
                    name=product.name,
                    unit_price=product.price,
                )
            )

        # Simulated charge (approves without collecting real money).
        payment = self._payments.charge(total, sale_in.payment_method)

        sale = Sale(
            sale_id=uuid4().hex,
            created_at=_utc_now_iso(),
            items=line_items,
            total=total,
            payment_method=sale_in.payment_method,
            payment_status=payment.status,
            cashier=cashier,
        )

        # Atomic persist: create SALE + decrement stock (condition stock >= qty).
        # Raises StockConflictError if a concurrent sale emptied the stock.
        return self._repo.register_sale(sale)


class ReportService:
    """Daily sales reporting."""

    def __init__(self, repository: Repository) -> None:
        self._repo = repository

    def daily_report(self, day: Optional[str] = None) -> DailyReport:
        """Return the sales report for `day` (yyyy-mm-dd), defaulting to today.

        Returns an empty list with total 0 when there are no sales (not an
        error).
        """
        report_day = day or _today_utc()
        sales = self._repo.list_sales_by_day(report_day)
        total = sum((s.total for s in sales), Decimal("0"))
        return DailyReport(
            date=report_day,
            sales=sales,
            total=total,
            count=len(sales),
        )

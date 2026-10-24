"""Payment abstraction for the POS.

The MVP charge is simulated: it approves without moving real money. The
`PaymentProvider` protocol is the integration point so a real gateway (e.g.
Stripe) can replace `SimulatedPaymentProvider` later without changing the sale
logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class PaymentResult:
    """Outcome of a charge attempt."""

    status: str  # "aprobado" in the MVP (simulated)
    reference: str


class PaymentProvider(Protocol):
    """Contract every payment provider must satisfy."""

    def charge(self, amount: Decimal, method: str) -> PaymentResult:
        """Charge `amount` using `method`; return the payment result."""
        ...


class SimulatedPaymentProvider:
    """MVP provider: approves every charge without collecting real money.

    Integration point for a real payment gateway in a later iteration.
    """

    def charge(self, amount: Decimal, method: str) -> PaymentResult:
        return PaymentResult(status="aprobado", reference=f"SIM-{uuid4().hex[:8]}")

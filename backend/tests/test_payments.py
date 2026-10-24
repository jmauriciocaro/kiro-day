"""Unit tests for the simulated payment provider (Requirement 2.7)."""
from decimal import Decimal

from app.payments import SimulatedPaymentProvider


def test_simulated_charge_is_approved():
    provider = SimulatedPaymentProvider()
    result = provider.charge(Decimal("10000"), "efectivo")
    assert result.status == "aprobado"
    assert result.reference.startswith("SIM-")


def test_simulated_charge_reference_is_unique():
    provider = SimulatedPaymentProvider()
    r1 = provider.charge(Decimal("1"), "tarjeta")
    r2 = provider.charge(Decimal("1"), "tarjeta")
    assert r1.reference != r2.reference

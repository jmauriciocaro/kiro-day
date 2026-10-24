"""Single-table key conventions for the `pos` DynamoDB table.

Centralizes how each entity maps to the generic PK/SK so the repository and
tests agree on one source of truth.
"""
from __future__ import annotations


def product_pk(sku: str) -> str:
    return f"PRODUCT#{sku}"


def product_sk(sku: str) -> str:
    return f"PRODUCT#{sku}"


def sale_pk(day: str) -> str:
    """day is an ISO date, yyyy-mm-dd (UTC)."""
    return f"SALE#{day}"


def sale_sk(timestamp: str, sale_id: str) -> str:
    """timestamp is ISO-8601 UTC so SK sorts chronologically."""
    return f"SALE#{timestamp}#{sale_id}"


def user_pk(username: str) -> str:
    return f"USER#{username}"


def user_sk(username: str) -> str:
    return f"USER#{username}"

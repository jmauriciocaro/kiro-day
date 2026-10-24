"""Domain errors raised by services/repository, with Spanish messages.

The API layer (Task 9) maps these to HTTP status codes. Keeping them as plain
exceptions lets the business logic stay independent of FastAPI.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for expected, user-facing domain errors."""

    message = "Error de dominio"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message


class DuplicateSkuError(DomainError):
    message = "Ya existe un producto con ese SKU"


class ProductNotFoundError(DomainError):
    message = "Producto no encontrado"


class SkuNotFoundError(DomainError):
    """A SKU referenced in a sale does not exist."""

    def __init__(self, sku: str) -> None:
        super().__init__(f"El producto {sku} no existe")


class InsufficientStockError(DomainError):
    """Not enough stock for a product at validation time."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Sin stock suficiente para {name}")


class StockConflictError(DomainError):
    """Concurrent sale emptied the stock; the transaction was cancelled."""

    message = "Stock agotado, intente de nuevo"


class InvalidCredentialsError(DomainError):
    message = "Usuario o clave incorrectos"


class ForbiddenError(DomainError):
    message = "No tienes permiso para esta acción"

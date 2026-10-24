"""Dependency providers for FastAPI routes.

Centralizes construction of the Repository and services so routes stay thin and
tests can override these providers with mocked instances.
"""
from __future__ import annotations

from app.repository import Repository
from app.services import ReportService, SalesService


def get_repository() -> Repository:
    return Repository()


def get_sales_service() -> SalesService:
    return SalesService(repository=get_repository())


def get_report_service() -> ReportService:
    return ReportService(repository=get_repository())

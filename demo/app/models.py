"""Pydantic models for the reporth demo API.

Monetary amounts are plain floats here for demo simplicity; a production system
would use Decimal. The response models are split so the public *query* endpoint
exposes only the minimum needed to accept/deny, never another organization's
full debt detail.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportIn(BaseModel):
    """Payload to report a new debt from the authenticated organization."""

    model_config = ConfigDict(extra="forbid")

    student_name: str = Field(min_length=1)
    student_rc: str = Field(min_length=1, description="Registro civil del estudiante (menor)")
    parent_name: str = Field(min_length=1)
    parent_cedula: str = Field(min_length=1)
    parent_email: str = Field(min_length=3)
    concept: str = Field(min_length=1)
    amount: float = Field(gt=0)


class Debt(BaseModel):
    """A debt as seen by its OWNING organization (full detail)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    student_name: str
    student_rc: str
    parent_name: str
    parent_cedula: str
    parent_email: str
    concept: str
    amount: float
    status: str
    created_at: str
    last_charged_at: Optional[str] = None


class QueryVerdict(BaseModel):
    """Minimal result of consulting a person before accepting them.

    Deliberately does NOT include which organizations reported, concepts or any
    personal detail beyond the aggregate needed to decide accept/deny.
    """

    model_config = ConfigDict(extra="forbid")

    has_debts: bool
    verdict: Literal["aceptar", "denegar"]
    reports_count: int
    total_amount: float


class ChargeResult(BaseModel):
    """Outcome of running the automatic email charge."""

    model_config = ConfigDict(extra="forbid")

    charged: int
    delivered: int
    failed: int
    details: List[str]

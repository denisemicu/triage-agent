from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


EvidenceStatus = Literal["FOUND", "UNKNOWN", "CONFLICT"]
Route = Literal["QUALIFIED", "REVIEW_REQUIRED", "NOT_QUALIFIED"]

EvidenceValue = (
    str
    | int
    | float
    | bool
    | list[str]
    | None
)


class EvidenceField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: EvidenceValue = None
    status: EvidenceStatus
    source: str | None = None
    evidence: str | None = None
    notes: str | None = None


class TriageExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: EvidenceField
    registered_business: EvidenceField
    employee_count: EvidenceField
    region: EvidenceField
    service_model: EvidenceField

    missing_information: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    special_handling_flags: list[str] = Field(default_factory=list)

    recommended_clarification: str | None = None


class RuleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    status: Literal[
        "PASS",
        "FAIL",
        "UNKNOWN",
        "HUMAN_REVIEW",
    ]
    explanation: str


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: Route
    rule_results: list[RuleResult]
    reason: str
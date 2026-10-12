from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator

FactStatus = Literal["stated", "inferred", "unknown"]


class FieldValue(BaseModel):
    value: Optional[str] = None
    status: FactStatus = "unknown"
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_value(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() or None
        if isinstance(v, list):
            parts = [str(x).strip() for x in v if str(x).strip()]
            return " ".join(parts) if parts else None
        if isinstance(v, (int, float, bool)):
            return str(v)
        return None

    @field_validator("evidence", mode="before")
    @classmethod
    def _coerce_evidence(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        return []

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, v: Any) -> float:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, f))


class InventoryRecord(BaseModel):
    model_name: FieldValue = FieldValue()
    model_id: FieldValue = FieldValue()
    business_function: FieldValue = FieldValue()
    business_owner: FieldValue = FieldValue()
    model_owner: FieldValue = FieldValue()
    development_team: FieldValue = FieldValue()
    business_purpose: FieldValue = FieldValue()
    intended_use: FieldValue = FieldValue()
    output_variables: FieldValue = FieldValue()
    downstream_uses: FieldValue = FieldValue()
    model_type: FieldValue = FieldValue()
    methodology: FieldValue = FieldValue()
    key_assumptions: FieldValue = FieldValue()
    limitations: FieldValue = FieldValue()
    input_data: FieldValue = FieldValue()
    data_sources: FieldValue = FieldValue()
    model_status: FieldValue = FieldValue()
    lifecycle_stage: FieldValue = FieldValue()
    validation_status: FieldValue = FieldValue()
    last_validation_date: FieldValue = FieldValue()
    monitoring_approach: FieldValue = FieldValue()
    known_weaknesses: FieldValue = FieldValue()
    remediation_actions: FieldValue = FieldValue()
    third_party_dependencies: FieldValue = FieldValue()
    proposed_risk_considerations: FieldValue = FieldValue()
    development_approach: FieldValue = FieldValue()
    implementation_environment: FieldValue = FieldValue()
    missing_information: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    human_review_status: Literal["pending", "reviewed", "corrected"] = "pending"


class ExtractionEnvelope(BaseModel):
    fields: dict[str, FieldValue] = Field(default_factory=dict)


class GapEnvelope(BaseModel):
    missing_information: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)

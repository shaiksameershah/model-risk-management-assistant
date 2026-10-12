from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

FactStatus = Literal["stated", "inferred", "unknown"]


class FieldValue(BaseModel):
    value: Optional[str] = None
    status: FactStatus = "unknown"
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0


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

from __future__ import annotations
from . import config, prompts
from .llm import generate_json
from .schema import ExtractionEnvelope, GapEnvelope, InventoryRecord, FieldValue


def _extract_group(source: str, fields: list[str]) -> dict[str, FieldValue]:
    user = prompts.EXTRACTION_USER.format(fields=", ".join(fields), source=source)
    raw = generate_json(prompts.EXTRACTION_SYSTEM, user)
    envelope = ExtractionEnvelope.model_validate(raw)
    for f in fields:
        envelope.fields.setdefault(f, FieldValue())
    return envelope.fields


def _analyze_gaps(source: str, record: InventoryRecord) -> GapEnvelope:
    record_json = record.model_dump_json(indent=2)
    user = prompts.GAP_USER.format(source=source, record_json=record_json)
    raw = generate_json(prompts.GAP_SYSTEM, user)
    return GapEnvelope.model_validate(raw)


def extract_inventory(source: str) -> InventoryRecord:
    record = InventoryRecord()
    for group_fields in config.FIELD_GROUPS.values():
        extracted = _extract_group(source, group_fields)
        for name, fv in extracted.items():
            if hasattr(record, name):
                setattr(record, name, fv)

    gaps = _analyze_gaps(source, record)
    record.missing_information = gaps.missing_information
    record.contradictions = gaps.contradictions
    record.follow_up_questions = gaps.follow_up_questions
    return record

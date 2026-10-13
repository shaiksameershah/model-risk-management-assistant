"""Two-pass extraction pipeline: per-field-group extraction + gap analysis."""
from __future__ import annotations
import logging
from . import config, prompts
from .llm import generate_json
from .schema import ExtractionEnvelope, GapEnvelope, InventoryRecord, FieldValue

log = logging.getLogger(__name__)


def _empty_group(fields: list[str], reason: str) -> dict[str, FieldValue]:
    return {
        f: FieldValue(status="unknown", evidence=[f"extract_failed:{reason}"])
        for f in fields
    }


def _extract_group(source: str, fields: list[str]) -> dict[str, FieldValue]:
    user = prompts.EXTRACTION_USER.format(fields=", ".join(fields), source=source)

    # Two attempts. First the standard prompt. If it fails, try once more; the
    # model is stochastic even at temperature 0 when it hits a bad token path.
    for attempt in range(2):
        try:
            raw = generate_json(prompts.EXTRACTION_SYSTEM, user)
            envelope = ExtractionEnvelope.model_validate(raw)
            for f in fields:
                envelope.fields.setdefault(f, FieldValue())
            return envelope.fields
        except Exception as exc:  # noqa: BLE001 — LLM output can fail in many ways
            log.warning("extract_group attempt %d failed for %s: %s",
                        attempt + 1, fields, exc)

    # Both attempts failed. Return unknown for every field in this group and
    # let the rest of the pipeline continue.
    return _empty_group(fields, "group_failed_after_retry")


def _analyze_gaps(source: str, record: InventoryRecord) -> GapEnvelope:
    record_json = record.model_dump_json(indent=2)
    user = prompts.GAP_USER.format(source=source, record_json=record_json)
    try:
        raw = generate_json(prompts.GAP_SYSTEM, user)
        return GapEnvelope.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        log.warning("gap analysis failed: %s", exc)
        return GapEnvelope(
            missing_information=["gap_analysis_failed"],
            contradictions=[],
            follow_up_questions=[],
        )


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

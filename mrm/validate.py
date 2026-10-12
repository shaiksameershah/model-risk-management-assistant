from __future__ import annotations
import re
from difflib import SequenceMatcher
from .schema import InventoryRecord, FieldValue

FUZZY_THRESHOLD = 0.85
DATE_RE = re.compile(
    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)


def _fuzzy_in(needle: str, haystack: str, threshold: float = FUZZY_THRESHOLD) -> bool:
    if not needle:
        return False
    if needle in haystack:
        return True
    n = len(needle)
    for i in range(0, max(1, len(haystack) - n + 1)):
        window = haystack[i:i + n + 20]
        if SequenceMatcher(None, needle, window).ratio() >= threshold:
            return True
    return False


def _guard_field(name: str, fv: FieldValue, source: str) -> FieldValue:
    if fv.status != "stated":
        return fv

    if name == "last_validation_date" and fv.value:
        if not DATE_RE.search(source):
            return FieldValue(status="unknown",
                              evidence=[f"guard_failed:{name}:date_not_in_source"])

    if not fv.evidence:
        return FieldValue(status="unknown",
                          evidence=[f"guard_failed:{name}:no_evidence"])

    for quote in fv.evidence:
        clean = quote.replace("INFERRED: ", "").replace("CONTRADICTION: ", "")
        if not _fuzzy_in(clean, source):
            return FieldValue(status="unknown",
                              evidence=[f"guard_failed:{name}:evidence_not_verbatim"])

    if fv.value and len(fv.value) > 3:
        if not _fuzzy_in(fv.value, source, threshold=0.75):
            return FieldValue(status="unknown",
                              evidence=[f"guard_failed:{name}:value_not_grounded"])
    return fv


def apply_guards(record: InventoryRecord, source: str) -> InventoryRecord:
    for name, value in record.model_dump().items():
        if isinstance(value, dict) and "status" in value:
            fv = FieldValue.model_validate(value)
            setattr(record, name, _guard_field(name, fv, source))

    for name, value in record.model_dump().items():
        if isinstance(value, dict) and value.get("status") == "unknown":
            for ev in value.get("evidence", []):
                if ev.startswith("guard_failed:") and ev not in record.missing_information:
                    record.missing_information.append(ev)
    return record

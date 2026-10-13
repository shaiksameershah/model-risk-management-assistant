"""High-level orchestration: source text in, guarded record out.

Both the CLI (app.py) and the Streamlit UI (streamlit_app.py) call this.
"""
from __future__ import annotations

from dataclasses import dataclass
from .extract import extract_inventory
from .validate import apply_guards
from .schema import InventoryRecord


@dataclass
class ExtractionResult:
    source: str
    record: InventoryRecord

    @property
    def stated_count(self) -> int:
        return sum(
            1 for v in self.record.model_dump().values()
            if isinstance(v, dict) and v.get("status") == "stated"
        )

    @property
    def inferred_count(self) -> int:
        return sum(
            1 for v in self.record.model_dump().values()
            if isinstance(v, dict) and v.get("status") == "inferred"
        )

    @property
    def unknown_count(self) -> int:
        return sum(
            1 for v in self.record.model_dump().values()
            if isinstance(v, dict) and v.get("status") == "unknown"
        )

    @property
    def guard_failures(self) -> list[str]:
        return [
            m for m in self.record.missing_information
            if m.startswith("guard_failed:")
        ]


def run_pipeline(source: str) -> ExtractionResult:
    """Extract a record from source text and apply guards."""
    record = extract_inventory(source)
    record = apply_guards(record, source)
    return ExtractionResult(source=source, record=record)

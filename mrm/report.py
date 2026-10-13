"""JSON, Markdown, and CSV writers for review-ready drafts."""
from __future__ import annotations
import csv
from pathlib import Path
from . import config
from .schema import InventoryRecord


def write_json(record: InventoryRecord, case_id: str) -> Path:
    path = config.OUTPUT_DIR / f"{case_id}.json"
    path.write_text(record.model_dump_json(indent=2))
    return path


def write_markdown(record: InventoryRecord, case_id: str) -> Path:
    lines = [f"# Model Inventory Draft — {case_id}", ""]
    lines.append("> Draft for human review. Not a regulatory filing. "
                 "No compliance claim is made or implied.\n")

    def section(title, names):
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Field | Value | Status | Evidence |")
        lines.append("|---|---|---|---|")
        for n in names:
            fv = getattr(record, n)
            value = (fv.value or "").replace("|", "\\|")
            ev = " / ".join(e.replace("|", "\\|") for e in fv.evidence)
            lines.append(f"| `{n}` | {value} | {fv.status} | {ev} |")
        lines.append("")

    for group, fields in config.FIELD_GROUPS.items():
        section(group.title(), fields)

    lines.append("## Missing information")
    for m in record.missing_information:
        lines.append(f"- {m}")
    lines.append("")

    lines.append("## Contradictions")
    for c in record.contradictions:
        lines.append(f"- {c}")
    lines.append("")

    lines.append("## Follow-up questions for the model owner")
    for q in record.follow_up_questions:
        lines.append(f"- {q}")
    lines.append("")

    path = config.OUTPUT_DIR / f"{case_id}.md"
    path.write_text("\n".join(lines))
    return path


def write_csv(record: InventoryRecord, case_id: str) -> Path:
    path = config.OUTPUT_DIR / f"{case_id}.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["field", "value", "status", "evidence", "confidence"])
        for name, value in record.model_dump().items():
            if isinstance(value, dict) and "status" in value:
                w.writerow([
                    name,
                    value.get("value") or "",
                    value.get("status"),
                    " | ".join(value.get("evidence") or []),
                    value.get("confidence", 0.0),
                ])
    return path

"""
Extraction-quality tests against gold-labelled synthetic cases.

These call the local Ollama model, so they are marked `llm` and only run when
explicitly opted in:

    pytest -m llm
    pytest -m llm --quality-report          # prints per-case metrics

Fast CI stays fast by running `pytest -m "not llm"` (the default given
addopts above does not include llm).
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
import pytest
from mrm.extract import extract_inventory
from mrm.validate import apply_guards

pytestmark = pytest.mark.llm

CASES_DIR = Path("data/synthetic_cases")


@dataclass
class CaseResult:
    case_id: str
    total: int
    correct: int
    unsupported: int
    missing_recall_num: int
    missing_recall_den: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 1.0


def _load_pairs() -> list[tuple[Path, Path]]:
    pairs = []
    for txt in sorted(CASES_DIR.glob("case_*.txt")):
        gold = txt.with_suffix(".gold.json")
        if gold.exists():
            pairs.append((txt, gold))
    return pairs


def _evaluate(txt_path: Path, gold_path: Path) -> CaseResult:
    source = txt_path.read_text()
    gold = json.loads(gold_path.read_text())

    record = extract_inventory(source)
    record = apply_guards(record, source)

    expected = gold.get("expected_status", {})
    must_not = gold.get("must_not_be_stated", [])

    correct = total = 0
    for field, expected_status in expected.items():
        total += 1
        got = getattr(record, field).status
        if got == expected_status:
            correct += 1

    unsupported = sum(
        1 for field in must_not
        if getattr(record, field).status == "stated"
    )

    # Recall on "missing" fields: fraction of fields that are unknown in the
    # gold AND unknown in the extractor. Treated as a directional signal.
    gold_unknowns = {f for f, s in expected.items() if s == "unknown"}
    recovered = sum(
        1 for f in gold_unknowns
        if getattr(record, f).status == "unknown"
    )

    return CaseResult(
        case_id=txt_path.stem,
        total=total,
        correct=correct,
        unsupported=unsupported,
        missing_recall_num=recovered,
        missing_recall_den=len(gold_unknowns),
    )


@pytest.mark.parametrize("txt_path,gold_path", _load_pairs(),
                         ids=lambda p: p.stem if isinstance(p, Path) else "")
def test_case_meets_quality_bar(txt_path, gold_path):
    result = _evaluate(txt_path, gold_path)

    # Hard rules — must never be violated.
    assert result.unsupported == 0, (
        f"{result.case_id}: hallucinated 'stated' on fields that must not be "
        f"stated. Violations will appear below."
    )

    # Soft quality bar — tunable. Start permissive; tighten as the system matures.
    assert result.accuracy >= 0.6, (
        f"{result.case_id}: accuracy {result.accuracy:.2f} "
        f"({result.correct}/{result.total}) below 0.60 threshold."
    )


def test_aggregate_quality_report(capsys):
    """Runs every gold-labelled case once and prints a summary."""
    results = [_evaluate(txt, gold) for txt, gold in _load_pairs()]
    if not results:
        pytest.skip("no gold-labelled cases found")

    lines = ["", "Extraction quality report", "=" * 60]
    total_correct = total_expected = total_unsupported = 0
    for r in results:
        acc = r.accuracy
        miss_recall = (r.missing_recall_num / r.missing_recall_den
                       if r.missing_recall_den else 1.0)
        lines.append(
            f"{r.case_id}: acc={acc:.2f} "
            f"({r.correct}/{r.total})  "
            f"unsupported={r.unsupported}  "
            f"missing_recall={miss_recall:.2f}"
        )
        total_correct += r.correct
        total_expected += r.total
        total_unsupported += r.unsupported

    macro_acc = total_correct / total_expected if total_expected else 0.0
    lines.append("-" * 60)
    lines.append(
        f"Macro accuracy: {macro_acc:.2f}  "
        f"Total unsupported claims: {total_unsupported}  "
        f"Cases: {len(results)}"
    )
    lines.append("")
    with capsys.disabled():
        print("\n".join(lines))

    assert total_unsupported == 0, "Hallucinations detected across cases."
    assert macro_acc >= 0.6, f"Macro accuracy {macro_acc:.2f} below 0.60"

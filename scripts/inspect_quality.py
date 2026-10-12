"""Per-field comparison between extractor output and gold labels.

Usage (from project root):
    python -m scripts.inspect_quality data/synthetic_cases/case_003.txt
    # or
    python scripts/inspect_quality.py data/synthetic_cases/case_003.txt
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Ensure the project root is importable when running the script directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mrm.extract import extract_inventory
from mrm.validate import apply_guards


def main(txt_path_str: str) -> None:
    txt_path = Path(txt_path_str)
    gold_path = txt_path.with_suffix(".gold.json")
    if not gold_path.exists():
        print(f"No gold file at {gold_path}")
        sys.exit(1)

    source = txt_path.read_text()
    gold = json.loads(gold_path.read_text())
    expected = gold.get("expected_status", {})
    must_not = set(gold.get("must_not_be_stated", []))

    print(f"Running extractor on {txt_path.name} ...")
    record = extract_inventory(source)
    record = apply_guards(record, source)

    print()
    print(f"{'field':<32} {'gold':<10} {'got':<10} {'match':<6} {'value':<50}")
    print("-" * 110)

    correct = total = 0
    for field, exp_status in expected.items():
        total += 1
        got_status = getattr(record, field).status
        value = getattr(record, field).value or ""
        value = value[:48] + "..." if len(value) > 48 else value
        match = "OK" if got_status == exp_status else "MISS"
        if got_status == exp_status:
            correct += 1
        print(f"{field:<32} {exp_status:<10} {got_status:<10} {match:<6} {value:<50}")

    print()
    for field in must_not:
        got_status = getattr(record, field).status
        flag = "VIOLATION" if got_status == "stated" else "ok"
        value = getattr(record, field).value or ""
        value = value[:48] + "..." if len(value) > 48 else value
        print(f"[must_not_be_stated] {field:<24} {got_status:<10} {flag:<10} {value}")

    print()
    if total:
        print(f"Accuracy: {correct}/{total} = {correct / total:.2f}")
    else:
        print("No expected fields in gold.")
    print("Missing information:", record.missing_information)
    print("Contradictions:", record.contradictions)
    print("Follow-up questions:")
    for q in record.follow_up_questions:
        print(f"  - {q}")


if __name__ == "__main__":
    main(sys.argv[1])

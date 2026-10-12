"""Show the extractor's raw output *before* guards for a given case.

Usage:
    python -m scripts.inspect_raw data/synthetic_cases/case_003.txt
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mrm.extract import extract_inventory


def main(txt_path_str: str) -> None:
    txt_path = Path(txt_path_str)
    source = txt_path.read_text()
    print(f"Running raw extractor on {txt_path.name} ...")
    record = extract_inventory(source)

    print()
    for name, value in record.model_dump().items():
        if isinstance(value, dict) and "status" in value:
            status = value.get("status")
            if status == "unknown":
                continue
            val = value.get("value") or ""
            if len(val) > 70:
                val = val[:67] + "..."
            print(f"\n[{name}]  status={status}  confidence={value.get('confidence', 0):.2f}")
            print(f"  value:    {val!r}")
            for ev in value.get("evidence", []):
                ev_short = ev if len(ev) <= 90 else ev[:87] + "..."
                print(f"  evidence: {ev_short!r}")


if __name__ == "__main__":
    main(sys.argv[1])

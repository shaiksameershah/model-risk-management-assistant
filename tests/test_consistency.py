import os
from pathlib import Path
import pytest
from mrm.extract import extract_inventory

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LLM_TESTS") != "1",
    reason="set RUN_LLM_TESTS=1 to run LLM tests",
)

CASE = Path("data/synthetic_cases/case_001.txt")


def test_repeated_runs_are_identical():
    source = CASE.read_text()
    runs = [extract_inventory(source).model_dump_json() for _ in range(3)]
    assert len(set(runs)) == 1

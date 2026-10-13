"""Smoke test: the Streamlit app must be importable without errors.

We do NOT actually run streamlit here — that requires a live browser. We just
check that the module parses and that its top-level imports resolve.
"""
import importlib


def test_streamlit_app_imports():
    importlib.import_module("streamlit_app")


def test_pipeline_returns_result():
    from mrm.pipeline import run_pipeline
    # Use a tiny source; this does call the LLM only if not skipped — so we
    # skip unless RUN_LLM_TESTS=1.
    import os
    import pytest
    if os.getenv("RUN_LLM_TESTS") != "1":
        pytest.skip("set RUN_LLM_TESTS=1 to exercise the pipeline")
    result = run_pipeline("The Test Model is a linear regression model.")
    assert result.record is not None

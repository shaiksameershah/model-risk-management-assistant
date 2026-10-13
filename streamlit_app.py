"""Streamlit UI for the Model Risk Documentation Assistant.

Run with:
    streamlit run streamlit_app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from mrm import config
from mrm.pipeline import run_pipeline, ExtractionResult
from mrm.report import write_json, write_markdown, write_csv
from mrm.schema import FieldValue

# ---- Page setup -----------------------------------------------------------

st.set_page_config(
    page_title="MRM Documentation Assistant",
    page_icon="📋",
    layout="wide",
)


# ---- Session state --------------------------------------------------------

def _init_state() -> None:
    if "result" not in st.session_state:
        st.session_state.result = None
    if "case_id" not in st.session_state:
        st.session_state.case_id = ""


_init_state()


# ---- Helpers --------------------------------------------------------------

STATUS_COLORS = {
    "stated": "🟢",
    "inferred": "🟡",
    "unknown": "⚪",
}


def _field_names() -> list[str]:
    """All inventory field names, in FIELD_GROUPS order."""
    names = []
    for group_fields in config.FIELD_GROUPS.values():
        names.extend(group_fields)
    return names


def _render_record(result: ExtractionResult) -> ExtractionResult:
    """Render the extracted record for review. Returns the (possibly edited) result."""
    record = result.record

    # Summary bar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stated", result.stated_count)
    c2.metric("Inferred", result.inferred_count)
    c3.metric("Unknown", result.unknown_count)
    c4.metric("Guard failures", len(result.guard_failures))

    if result.guard_failures:
        with st.expander(f"⚠️ {len(result.guard_failures)} guard failures", expanded=False):
            for g in result.guard_failures:
                st.write(f"- `{g}`")

    st.markdown("---")
    st.markdown("### Extracted fields")
    st.caption(
        "🟢 stated (evidence in source) · 🟡 inferred (marked by model) · ⚪ unknown"
    )

    # Field-by-field editor, grouped
    for group, fields in config.FIELD_GROUPS.items():
        with st.expander(f"**{group.title()}**", expanded=True):
            for name in fields:
                fv: FieldValue = getattr(record, name)
                _render_field_row(name, fv, record)

    # Follow-up questions
    st.markdown("---")
    st.markdown("### Follow-up questions for the model owner")
    if record.follow_up_questions:
        for q in record.follow_up_questions:
            st.markdown(f"- {q}")
    else:
        st.caption("No questions — source appears complete.")

    # Contradictions
    if record.contradictions:
        st.markdown("### Contradictions")
        for c in record.contradictions:
            st.warning(c)

    return result


def _render_field_row(name: str, fv: FieldValue, record) -> None:
    """One editable row per field."""
    cols = st.columns([1.2, 3, 1.2, 3])

    icon = STATUS_COLORS.get(fv.status, "?")
    cols[0].markdown(f"**{icon} `{name}`**")

    new_value = cols[1].text_input(
        label=f"value_{name}",
        value=fv.value or "",
        key=f"value_{name}",
        label_visibility="collapsed",
        placeholder="(empty)",
    )

    new_status = cols[2].selectbox(
        label=f"status_{name}",
        options=["stated", "inferred", "unknown"],
        index=["stated", "inferred", "unknown"].index(fv.status),
        key=f"status_{name}",
        label_visibility="collapsed",
    )

    # Evidence display (read-only for now)
    ev_display = " | ".join(fv.evidence) if fv.evidence else "—"
    cols[3].markdown(
        f"<small style='color:#888'>{ev_display}</small>",
        unsafe_allow_html=True,
    )

    # If the user changed anything, write back
    if new_value != (fv.value or "") or new_status != fv.status:
        setattr(record, name, FieldValue(
            value=new_value or None,
            status=new_status,
            evidence=fv.evidence or ([new_value] if new_value else []),
            confidence=fv.confidence,
        ))
        if record.human_review_status == "pending":
            record.human_review_status = "corrected"


def _downloads(result: ExtractionResult, case_id: str) -> None:
    """Three download buttons: JSON, MD, CSV."""
    record = result.record

    # Write to data/out so the same files the CLI produces are also available
    j = write_json(record, case_id)
    m = write_markdown(record, case_id)
    c = write_csv(record, case_id)

    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "⬇️ JSON",
        data=record.model_dump_json(indent=2),
        file_name=f"{case_id}.json",
        mime="application/json",
    )
    col2.download_button(
        "⬇️ Markdown",
        data=m.read_text(),
        file_name=f"{case_id}.md",
        mime="text/markdown",
    )
    col3.download_button(
        "⬇️ CSV",
        data=c.read_text(),
        file_name=f"{case_id}.csv",
        mime="text/csv",
    )


# ---- Layout ---------------------------------------------------------------

st.title("📋 Model Risk Documentation Assistant")
st.caption(
    "Local draft generator for MRM inventory records. "
    "Runs entirely on your machine via Ollama. Not a regulatory filing."
)

# Two-column top: input on the left, output on the right
left, right = st.columns([1, 1.4])

with left:
    st.markdown("### Input")

    case_id = st.text_input(
        "Case ID",
        value=st.session_state.case_id or "case_streamlit",
        help="Used as the filename when exporting.",
    )
    st.session_state.case_id = case_id

    input_mode = st.radio(
        "Source",
        ["Paste text", "Upload file", "Load example case"],
        horizontal=True,
    )

    source = ""
    if input_mode == "Paste text":
        source = st.text_area(
            "Model description",
            height=380,
            placeholder="Paste a model description here...",
        )
    elif input_mode == "Upload file":
        uploaded = st.file_uploader("Upload .txt", type=["txt"])
        if uploaded is not None:
            source = uploaded.read().decode("utf-8", errors="replace")
            st.text_area("Preview", value=source, height=300, disabled=True)
    else:
        sample = Path("data/synthetic_cases/case_001.txt")
        if sample.exists():
            source = sample.read_text()
            st.text_area("Preview", value=source, height=300, disabled=True)
        else:
            st.warning("Sample case not found. Use 'Paste text' instead.")

    run_clicked = st.button(
        "▶︎ Extract inventory draft",
        type="primary",
        disabled=not source.strip(),
        help="Runs ~9 LLM calls. On M-series Macs this takes 1-3 minutes.",
    )

with right:
    st.markdown("### Draft record")

    if run_clicked and source.strip():
        with st.spinner("Extracting... this takes 1–3 minutes with deepseek-r1:7b."):
            try:
                st.session_state.result = run_pipeline(source)
            except Exception as exc:  # noqa: BLE001 — surface any failure
                st.error(f"Extraction failed: {exc}")
                st.session_state.result = None

    if st.session_state.result is None:
        st.info("Paste a model description on the left and click **Extract**.")
    else:
        result = st.session_state.result
        result = _render_record(result)
        st.session_state.result = result

        st.markdown("---")
        st.markdown("### Export")
        _downloads(result, st.session_state.case_id)

        st.caption(
            f"human_review_status = `{result.record.human_review_status}`. "
            "Edits you make above are reflected in the exported files."
        )


## Evaluation results

Measurements were taken with `deepseek-r1:7b` at temperature 0 with a fixed
seed on macOS. Full run: `pytest -m llm -v` (~1h30m wall-clock; the pipeline
issues ~9 LLM calls per case).

### Synthetic dataset

Ten hand-labelled cases under `data/synthetic_cases/`, each paired with a
`.gold.json` file declaring the expected status (`stated` / `inferred` /
`unknown`) per field, plus a `must_not_be_stated` list that captures
hallucination traps.

Coverage:
- 002 – contradictory owner attributions
- 003 – inference trap (risk implied but not stated)
- 004 – vendor-supplied model (opaque methodology)
- 005 – minimal description (graceful degradation)
- 006 – LLM-based summariser (novel model type)
- 007 – decommissioning model (lifecycle edge case)
- 008 – date in prose form ("15 March 2024")
- 009 – one-sentence description (extreme degradation)
- 010 – conflicting validation dates
- 011 – never-validated model (negative fact)

### Headline metrics

| Metric | Value |
|---|---|
| Macro field-extraction accuracy | **0.87** |
| Unsupported claims (hallucinations) | **0** |
| JSON schema validity | 100% |
| Fast test suite (no LLM) | 15 passed |

### Per-case accuracy

| Case | Accuracy | Unsupported |
|---|---|---|
| 002 – Contradictory owner | 0.87 (13/15) | 0 |
| 003 – Inference trap | 0.92 (12/13) | 0 |
| 004 – Vendor model | 0.82 (9/11) | 0 |
| 005 – Minimal description | 1.00 (4/4) | 0 |
| 006 – LLM summariser | 0.90 (9/10) | 0 |
| 007 – Decommissioning | 0.85 (11/13) | 0 |
| 008 – Prose date | 0.83 (10/12) | 0 |
| 009 – One sentence | 1.00 (2/2) | 0 |
| 010 – Conflicting dates | 0.90 (9/10) | 0 |
| 011 – Never validated | 0.85 (11/13) | 0 |

### How hallucination control works

Three layers, in order:

1. **Prompt rules.** The extraction prompt forbids inventing owners, dates,
   ratings, and evidence; requires short verbatim quotes; forbids picking one
   of two conflicting dates; forbids copying the model name into `model_type`.
2. **Deterministic evidence guards** (`mrm/validate.py`). Every `stated` field
   must have at least one evidence quote that appears in the source after
   normalisation. Dates must match `DATE_RE` and be unique in the source.
   `model_type` must not equal `model_name`. `input_data` must be grounded in
   explicit input language, not in verbs of analysis ("assesses", "measures").
3. **Human review.** The CLI requires the reviewer to accept, edit, or reject
   each draft before export.

Every guard failure downgrades the field to `unknown` and records a
`guard_failed:<field>:<reason>` entry. Unsupported claims are checked by the
test suite (`must_not_be_stated` lists) and enforced as a hard failure.

### Reproducing these numbers

    pip install -r requirements.txt
    ollama pull deepseek-r1:7b
    pytest -m llm -v

Runtime is dominated by the LLM. To iterate quickly, temporarily switch
`MODEL_NAME` in `mrm/config.py` to `deepseek-r1:1.5b` — faster but less
accurate; remember to switch back before citing numbers.

### Known limitations

- Field-extraction accuracy is not 100%. Fourteen fields were missed across
  the ten cases, almost always because the guard downgraded a field the
  extractor marked `stated`. In each case the resulting record is *safer*
  (fewer claims, more explicit unknowns) — which is the design intent.
- The extractor sometimes infers plausible-but-unstated values. These are
  captured as `inferred`, rendered separately in the report, and never
  presented as facts.
- Runtime is ~9 minutes per case on M-series Macs. This is acceptable for a
  human-in-the-loop MRM workflow but slow for batch use. Group consolidation
  in `FIELD_GROUPS` is the obvious next optimization.
- The system does not assign risk ratings, approve models, or claim
  regulatory compliance. SR 11-7 was superseded in April 2026; the schema
  follows a familiar inventory structure and can be mapped to an
  institution-specific framework via `mrm/config.py`.

## Streamlit UI

A browser-based review UI is available:

    streamlit run streamlit_app.py

Opens at http://localhost:8501. Features:

- Paste a model description, upload a `.txt`, or load a bundled example
- Progress indicator during extraction
- Side-by-side source and draft, with grouped fields
- Inline editing of value and status per field
- Guard failures and contradictions surfaced in dedicated panels
- Download JSON, Markdown, or CSV exports

The Streamlit app shares its extraction pipeline with the CLI (`mrm/pipeline.py`),
so results are identical.

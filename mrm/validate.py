"""Evidence grounding guards.

Design principle: a 'stated' field is accepted if its evidence is a
substring of the source *after* aggressive normalisation. Fuzzy matching is
only a fallback for short quotes and short values.
"""
from __future__ import annotations
import re
import unicodedata
from difflib import SequenceMatcher
from .schema import InventoryRecord, FieldValue

FUZZY_THRESHOLD = 0.72
VALUE_THRESHOLD = 0.65
MIN_QUOTE_LEN_FOR_EXACT = 8

DATE_RE = re.compile(
    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)

# Punctuation and quote characters we strip when normalising.
_STRIP_PATTERN = re.compile(r"[^\w\s]")
_WS_PATTERN = re.compile(r"\s+")


def _normalize(text: str) -> str:
    if not text:
        return ""
    # Fold fancy Unicode into ASCII equivalents first.
    text = unicodedata.normalize("NFKD", text)
    # Remove combining marks left over from NFKD.
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    # Collapse all non-alphanumeric to space.
    text = _STRIP_PATTERN.sub(" ", text)
    text = _WS_PATTERN.sub(" ", text)
    return text.strip()


def _substring_match(needle: str, haystack: str) -> bool:
    """True if the normalised needle is a substring of the normalised haystack."""
    n = _normalize(needle)
    h = _normalize(haystack)
    if not n or not h:
        return False
    if n in h:
        return True
    # If the needle is long, also try word-level subsequence matching:
    # all needle words must appear in order, allowing gaps.
    n_words = n.split()
    if len(n_words) >= 3:
        return _word_subsequence(n_words, h.split())
    return False


def _word_subsequence(needle_words: list[str], haystack_words: list[str]) -> bool:
    """True if every needle word appears in haystack in order (gaps allowed)."""
    i = 0
    for w in haystack_words:
        if i < len(needle_words) and w == needle_words[i]:
            i += 1
    return i == len(needle_words)


def _ratio_match(needle: str, haystack: str, threshold: float) -> bool:
    """Fallback: best SequenceMatcher ratio of needle against any window."""
    n = _normalize(needle)
    h = _normalize(haystack)
    if not n or not h:
        return False
    n_len = len(n)
    # If the needle is short (< 15 chars), do a full scan with small windows.
    # If longer, scan with larger windows and a coarser step.
    if n_len <= 15:
        for i in range(0, len(h) - n_len + 1):
            if SequenceMatcher(None, n, h[i:i + n_len]).ratio() >= threshold:
                return True
        return False

    window = n_len + 30
    step = max(1, n_len // 5)
    for i in range(0, max(1, len(h) - n_len + 1), step):
        if SequenceMatcher(None, n, h[i:i + window]).ratio() >= threshold:
            return True
    return False


_PREFIX_PATTERNS = [
    re.compile(r"^\s*verbatim\s*:\s*", re.IGNORECASE),
    re.compile(r"^\s*quoted\s*:\s*", re.IGNORECASE),
    re.compile(r"^\s*quoted\s+", re.IGNORECASE),
    re.compile(r"^\s*inferred\s*:\s*", re.IGNORECASE),
    re.compile(r"^\s*contradiction\s*:\s*", re.IGNORECASE),
    re.compile(r"^\s*evidence\s*:\s*", re.IGNORECASE),
    re.compile(r"^\s*source\s*:\s*", re.IGNORECASE),
    re.compile(r"^\s*from\s+source\s*:\s*", re.IGNORECASE),
]


def _clean_evidence(quote: str) -> str:
    """Strip model-added prefixes and surrounding quotes from an evidence string."""
    if not quote:
        return ""
    s = quote.strip()
    # Peel prefixes repeatedly in case the model stacked them.
    changed = True
    while changed:
        changed = False
        for pat in _PREFIX_PATTERNS:
            new_s = pat.sub("", s, count=1)
            if new_s != s:
                s = new_s
                changed = True
    # Peel matching surrounding quotes (single, double, or fancy).
    s = s.strip()
    quote_pairs = [('"', '"'), ("'", "'"), ("\u201c", "\u201d"), ("\u2018", "\u2019")]
    for left, right in quote_pairs:
        if s.startswith(left) and s.endswith(right) and len(s) > len(left) + len(right):
            s = s[len(left):-len(right)]
            break
    return s.strip()


def _evidence_ok(quote: str, source: str) -> bool:
    """True if the quote is grounded in the source."""
    clean = _clean_evidence(quote)
    if not clean:
        return False
    if _substring_match(clean, source):
        return True
    if len(clean) >= MIN_QUOTE_LEN_FOR_EXACT and _ratio_match(clean, source, FUZZY_THRESHOLD):
        return True
    return False


def _value_ok(value: str, source: str) -> bool:
    if not value or len(value) <= 3:
        return True
    if _substring_match(value, source):
        return True
    return _ratio_match(value, source, VALUE_THRESHOLD)


_ASSESS_VERBS = (
    "assesses", "assess", "evaluates", "estimates", "measures",
    "scores", "predicts", "ranks", "screens", "monitors",
)


def _evidence_uses_assess_verb(fv: FieldValue) -> bool:
    """True if any evidence quote uses a verb-of-analysis without 'input' language."""
    low_evidence = " ".join(fv.evidence or []).lower()
    low_value = (fv.value or "").lower()
    if any(v in low_evidence for v in _ASSESS_VERBS):
        # If the same evidence also contains explicit input language, allow it.
        input_markers = ("input", "inputs", "uses", "consumes", "fed by", "takes as")
        if not any(m in low_evidence for m in input_markers):
            return True
    return False


def _guard_field(name: str, fv: FieldValue, source: str) -> FieldValue:
    if fv.status != "stated":
        return fv

    # Semantic guard: input_data must be grounded in explicit input language.
    if name == "input_data" and _evidence_uses_assess_verb(fv):
        return FieldValue(
            status="unknown",
            evidence=[f"guard_failed:input_data:verb_of_analysis_not_input"],
        )

    if name == "last_validation_date" and fv.value:
        if not DATE_RE.search(source):
            return FieldValue(
                status="unknown",
                evidence=[f"guard_failed:{name}:date_not_in_source"],
            )
        # If the source contains two or more distinct dates, refuse to pick one.
        all_dates = set(DATE_RE.findall(source))
        all_dates.discard("")  # group(0) fallback if regex has groups
        # DATE_RE has multiple groups; findall returns tuples when grouped.
        # Use finditer to get full matches cleanly.
        full_dates = {m.group(0) for m in DATE_RE.finditer(source)}
        if len(full_dates) >= 2:
            return FieldValue(
                status="unknown",
                evidence=[f"guard_failed:{name}:multiple_dates_in_source:{sorted(full_dates)}"],
            )

    # Evidence grounding.
    if not fv.evidence:
        if fv.value and _value_ok(fv.value, source):
            # Salvage: use the value itself as evidence.
            return fv.model_copy(update={"evidence": [fv.value]})
        return FieldValue(
            status="unknown",
            evidence=[f"guard_failed:{name}:no_evidence"],
        )

    for quote in fv.evidence:
        if not _evidence_ok(quote, source):
            return FieldValue(
                status="unknown",
                evidence=[f"guard_failed:{name}:evidence_not_verbatim"],
            )

    # Value grounding (skip for very short values and known IDs/dates/vendors).
    if fv.value and len(fv.value) > 3:
        if name in ("model_id", "last_validation_date", "third_party_dependencies"):
            # IDs, dates, and vendor names are frequently rephrased by the
            # extractor without losing meaning. Evidence grounding is still
            # enforced above.
            pass
        elif not _value_ok(fv.value, source):
            return FieldValue(
                status="unknown",
                evidence=[f"guard_failed:{name}:value_not_grounded"],
            )
    return fv


def apply_guards(record: InventoryRecord, source: str) -> InventoryRecord:
    for name, value in record.model_dump().items():
        if isinstance(value, dict) and "status" in value:
            fv = FieldValue.model_validate(value)
            setattr(record, name, _guard_field(name, fv, source))

    # Semantic guard: model_type must not equal model_name. If they match,
    # the extractor has almost certainly just copied the identifier.
    if (record.model_type.status == "stated"
            and record.model_name.status == "stated"
            and record.model_type.value
            and record.model_name.value
            and _normalize(record.model_type.value) == _normalize(record.model_name.value)):
        record.model_type = FieldValue(
            status="unknown",
            evidence=["guard_failed:model_type:identical_to_model_name"],
        )

    for name, value in record.model_dump().items():
        if isinstance(value, dict) and value.get("status") == "unknown":
            for ev in value.get("evidence", []):
                if ev.startswith("guard_failed:") and ev not in record.missing_information:
                    record.missing_information.append(ev)
    return record

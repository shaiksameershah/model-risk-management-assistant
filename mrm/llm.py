"""Thin Ollama client with tolerant JSON extraction from model responses."""
from __future__ import annotations
import json
import re
from typing import Any
import ollama
from . import config


_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def _extract_json_object(text: str) -> str:
    """Return the first balanced JSON object from text.

    Handles: markdown fences, leading/trailing prose, stray whitespace.
    """
    text = text.strip()
    m = _FENCE_RE.match(text)
    if m:
        text = m.group(1).strip()

    # Find the first '{' and its matching '}'.
    start = text.find("{")
    if start < 0:
        raise ValueError(f"no JSON object found in response: {text[:120]!r}")

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    raise ValueError("unbalanced JSON braces in model response")


def generate_json(system: str, user: str) -> dict[str, Any]:
    resp = ollama.Client(host=config.OLLAMA_HOST).chat(
        model=config.MODEL_NAME,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        format="json",
        options={
            "temperature": config.TEMPERATURE,
            "seed": config.SEED,
            "num_ctx": config.NUM_CTX,
        },
    )
    content = resp["message"]["content"]
    cleaned = _extract_json_object(content)
    return json.loads(cleaned)

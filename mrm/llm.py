from __future__ import annotations
import json
from typing import Any
import ollama
from . import config


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
    return json.loads(resp["message"]["content"])

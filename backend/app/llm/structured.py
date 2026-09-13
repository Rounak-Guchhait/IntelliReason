from __future__ import annotations

import json
import re

from langchain_core.messages import BaseMessage
from pydantic import BaseModel


def extract_json(text: str) -> dict:
    """Best-effort JSON extraction from a model response."""
    if isinstance(text, dict):
        return text
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract JSON from model output: {text[:300]!r}")


def invoke_structured(
    model, schema: type[BaseModel], messages: list[BaseMessage]
) -> BaseModel:
    """Call the model expecting structured output, with a JSON fallback."""
    try:
        structured = model.with_structured_output(schema)
        return structured.invoke(messages)
    except Exception:  # noqa: BLE001
        response = model.invoke(messages)
        data = extract_json(response.content)
        return schema.model_validate(data)
"""Single place that talks to the LLM. Owner: A.

Everything else calls these helpers, so swapping models or adding tracing is one edit.

Provider: OpenAI (chat completions + structured outputs).
- Models come from settings.model_main / settings.model_fast (PILLWISE_MODEL_MAIN / _FAST).
- The API key comes from settings.openai_api_key (OPENAI_API_KEY).

Text-only calls are cached under settings.cache_dir/llm/ so the stage demo works with
PILLWISE_OFFLINE=1. Calls with an image are NEVER cached (privacy: no photos or label
text from a person's bottle are stored).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel

from pillwise.config import get_settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

SYSTEM = (
    "You are a careful assistant inside a medication-safety app. "
    "Use only the information you are given. Never invent dosing or medical advice. "
    "If the information is not there, say so (or return null)."
)


class LLMError(RuntimeError):
    """The model could not produce a usable answer."""


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    key = get_settings().openai_api_key
    if not key:
        raise LLMError("OPENAI_API_KEY is not set (.env)")
    return OpenAI(api_key=key)


def _model(fast: bool) -> str:
    s = get_settings()
    model = s.model_fast if fast else s.model_main
    if model.startswith("claude"):
        raise LLMError(f"model '{model}' is not an OpenAI model; set PILLWISE_MODEL_MAIN / PILLWISE_MODEL_FAST in .env")
    return model


def _messages(prompt: str, image: bytes | None, mime_type: str) -> list[dict]:
    if image is None:
        user: str | list[dict] = prompt
    else:
        b64 = base64.b64encode(image).decode()
        user = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
        ]
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def _call(method, **kwargs):
    """Call with temperature 0; retry without it for models that reject the parameter."""
    from openai import BadRequestError

    try:
        return method(temperature=0, **kwargs)
    except BadRequestError as exc:
        if "temperature" not in str(exc):
            raise
        return method(**kwargs)


# ---------------------------------------------------------------------------
# Cache for text-only calls (public label text in, explanation out)
# ---------------------------------------------------------------------------


def _cache_path(kind: str, model: str, prompt: str, schema: str = ""):
    key = hashlib.sha1(f"{kind}|{model}|{schema}|{prompt}".encode()).hexdigest()[:16]
    return get_settings().cache_dir / "llm" / f"{key}.json"


def _cache_get(path) -> str | None:
    if path.exists():
        return json.loads(path.read_text())["output"]
    if get_settings().offline:
        raise LLMError("offline and LLM answer not cached")
    return None


def _cache_put(path, output: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"output": output}))


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def structured(
    prompt: str, output_type: type[T], *, image: bytes | None = None, mime_type: str = "image/jpeg", fast: bool = False
) -> T:
    """Ask the model for an instance of `output_type` (OpenAI structured outputs)."""
    model = _model(fast)
    path = None
    if image is None:
        schema = json.dumps(output_type.model_json_schema(), sort_keys=True)
        path = _cache_path("structured", model, prompt, schema)
        cached = _cache_get(path)
        if cached is not None:
            return output_type.model_validate_json(cached)

    resp = _call(
        _client().chat.completions.parse,
        model=model,
        messages=_messages(prompt, image, mime_type),
        response_format=output_type,
    )
    msg = resp.choices[0].message
    if getattr(msg, "refusal", None) or msg.parsed is None:
        raise LLMError(f"model returned no structured output (refusal={getattr(msg, 'refusal', None)!r})")
    out = msg.parsed
    if path is not None:
        _cache_put(path, out.model_dump_json())
    return out


def text(prompt: str, *, fast: bool = False) -> str:
    """Plain text answer."""
    model = _model(fast)
    path = _cache_path("text", model, prompt)
    cached = _cache_get(path)
    if cached is not None:
        return cached

    resp = _call(_client().chat.completions.create, model=model, messages=_messages(prompt, None, ""))
    out = (resp.choices[0].message.content or "").strip()
    if not out:
        raise LLMError("model returned empty text")
    _cache_put(path, out)
    return out

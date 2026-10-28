"""Single place that talks to the LLM. Owner: A.

Everything else calls these helpers, so swapping models or adding tracing is one edit.

TODO(A):
- [ ] structured(prompt, output_type, *, image=None, fast=False) -> output_type instance
      (Pydantic AI Agent with output_type, or Anthropic tool-use returning JSON).
- [ ] text(prompt, *, fast=False) -> str
- [ ] Read keys/models from pillwise.config.get_settings(); never hard-code them.
- [ ] Low temperature for extraction/quoting.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def structured(
    prompt: str, output_type: type[T], *, image: bytes | None = None, mime_type: str = "image/jpeg", fast: bool = False
) -> T:
    raise NotImplementedError("A: implement LLM structured call")


def text(prompt: str, *, fast: bool = False) -> str:
    raise NotImplementedError("A: implement LLM text call")

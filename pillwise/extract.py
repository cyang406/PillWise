"""Bottle photo -> list[Medication] using a vision model. Owner: A.

Contract: extract_from_image(image_bytes, mime_type) -> list[Medication]

Rules:
- Copy `directions` verbatim from the label; if unreadable, leave None. Never invent dosing.
- Return source="photo", confirmed=False. The UI asks the person to confirm.
- Do not log or store the image.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel

from pillwise import llm
from pillwise.schemas import Medication

log = logging.getLogger(__name__)


# Internal LLM output models. Every field is required (OpenAI strict mode); null = not readable.
class _Bottle(BaseModel):
    name: str
    strength: str | None
    directions: str | None
    raw_text: str


class _Bottles(BaseModel):
    bottles: list[_Bottle]


PROMPT = """Read the medicine bottle(s) or package(s) in this photo.

Return one entry per separate bottle or package you can see. For each:
- name: the medicine name as printed (brand or generic, e.g. "Advil" or "Ibuprofen").
- strength: the strength as printed (e.g. "200 mg"), or null if you cannot read it.
- directions: the directions for use COPIED WORD FOR WORD from the label, including
  every number, unit and bracket. Return null if ANY part of the directions is cut off,
  hidden, folded around the bottle, blurred or unreadable. Never join visible fragments
  into a sentence, never fill gaps, never write, summarize or fix directions. A partly
  read direction is more dangerous than none: the person will type it in.
- raw_text: the main label text you can read for that item, copied as printed.

Do not guess. If a word is unreadable, leave it out. If there is no readable medicine
label in the photo, return an empty list."""


def _clean(s: str | None) -> str | None:
    s = (s or "").strip()
    return s or None


def extract_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[Medication]:
    if not image_bytes:
        return []
    try:
        out = llm.structured(PROMPT, _Bottles, image=image_bytes, mime_type=mime_type)
    except Exception as exc:  # noqa: BLE001 - unreadable photo must not crash the UI
        log.warning("extraction failed: %s", type(exc).__name__)
        return []

    meds: list[Medication] = []
    for b in out.bottles:
        name = _clean(b.name)
        if not name:
            continue
        meds.append(
            Medication(
                raw_text=(b.raw_text or "").strip(),
                name=name,
                strength=_clean(b.strength),
                directions=_clean(b.directions),
                source="photo",
                confirmed=False,
            )
        )
    log.info("extracted %d medicine(s) from photo", len(meds))
    return meds

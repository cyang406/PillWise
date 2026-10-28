"""Bottle photo -> list[Medication] using a vision model. Owner: A.

Contract: extract_from_image(image_bytes, mime_type) -> list[Medication]

Rules:
- Copy `directions` verbatim from the label; if unreadable, leave None. Never invent dosing.
- Return source="photo", confirmed=False. The UI asks the person to confirm.
- Do not log or store the image.

TODO(A):
- [ ] Prompt the vision model (settings.model_main) for structured output (Pydantic AI or tool-use JSON).
- [ ] Handle several bottles in one photo.
- [ ] Return [] (not an exception) when nothing readable is found.
"""

from __future__ import annotations

from pillwise.schemas import Medication


def extract_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[Medication]:
    raise NotImplementedError("A: implement vision extraction")

"""Per-pill cards (MVP) and plain language / translation / quiz (stretch A). Owner: A.

Contracts:
    pill_cards(meds) -> list[PillCard]                         # MVP
    simplify(report, language) -> SimplifiedSummary            # stretch A
    make_quiz(report, n) -> list[QuizQuestion]                 # stretch A (could)

Rules:
- Explain only what the label says; `how_to_take` is copied from Medication.directions.
- simplify(): rewrite until textstat.flesch_kincaid_grade <= settings.target_reading_grade
  (max 3 tries); for es/zh, translate, back-translate, score similarity
  (sentence-transformers) and set drift_ok = drift_score >= settings.drift_threshold.
- Keep every SimplifiedSection.source_ids pointing at the Finding it came from.
"""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel

from pillwise import evidence, llm
from pillwise.schemas import Language, Medication, PillCard, QuizQuestion, Report, SimplifiedSummary

log = logging.getLogger(__name__)

NO_LABEL = "We could not find the official label for this medicine. Ask your pharmacist what it is for."

CARD_SECTIONS = (
    "boxed_warning",
    "warnings",
    "warnings_and_cautions",
    "do_not_use",
    "ask_doctor_or_pharmacist",
    "when_using",
    "geriatric_use",
    "stop_use",
)


class _CardText(BaseModel):
    what_it_is_for: str
    watch_for: list[str]


CARD_PROMPT = """You explain a medicine to an older adult, in plain words (about 6th-grade reading level).

Use ONLY the FDA label text below for "{name}". Do not add facts that are not in it.
Never give doses or tell the person how much or how often to take it.

- what_it_is_for: one or two short sentences: what this medicine is used for.
- watch_for: up to 4 short items (under 15 words each): the most important warnings
  or side effects from the label that the person should watch for.

WHAT IT IS FOR (label):
{purpose}

WARNINGS (label):
{warnings}"""


def _first_sentence(text: str, limit: int = 300) -> str | None:
    """First sentence of `text`, as an exact substring (safe to show as a label quote)."""
    text = text.strip()
    if not text:
        return None
    m = re.search(r"[.!?](\s|$)", text)
    s = text[: m.end()].strip() if m else text
    return s if len(s) <= limit else None


def _purpose_quote(label: dict) -> str | None:
    for sec in evidence.PURPOSE_SECTIONS:
        q = _first_sentence(evidence.section_text(label, sec))
        if q and len(q.split()) >= 2:
            return q
    return None


def pill_card(med: Medication) -> PillCard:
    base = {"med_key": med.key, "name": med.name, "how_to_take": med.directions}  # COPIED, never generated
    try:
        label = evidence.fetch_label(med.match_names)
    except Exception as exc:  # noqa: BLE001
        log.warning("label fetch failed for %s: %s", med.key, exc)
        label = None
    if not label:
        return PillCard(**base, what_it_is_for=NO_LABEL)

    quote = _purpose_quote(label)
    ev = [evidence.label_evidence(label, quote)] if quote else []
    purpose = "\n".join(evidence.section_text(label, s) for s in evidence.PURPOSE_SECTIONS).strip()
    warnings = "\n".join(evidence.section_text(label, s)[:3000] for s in CARD_SECTIONS).strip()
    try:
        out = llm.structured(
            CARD_PROMPT.format(
                name=med.generic_name or med.name, purpose=purpose[:3000], warnings=warnings or "(none)"
            ),
            _CardText,
            fast=True,
        )
        return PillCard(
            **base,
            what_it_is_for=out.what_it_is_for.strip() or (quote or NO_LABEL),
            watch_for=[w.strip() for w in out.watch_for if w.strip()][:4],
            evidence=ev,
        )
    except Exception as exc:  # noqa: BLE001 - fall back to the label's own words
        log.warning("card explanation failed for %s: %s", med.key, exc)
        return PillCard(**base, what_it_is_for=quote or NO_LABEL, evidence=ev)


def pill_cards(meds: list[Medication]) -> list[PillCard]:
    return [pill_card(m) for m in meds]


def simplify(report: Report, language: Language = "en") -> SimplifiedSummary:
    raise NotImplementedError("A: stretch A - plain language")


def make_quiz(report: Report, n: int = 3) -> list[QuizQuestion]:
    raise NotImplementedError("A: stretch A - teach-back quiz")

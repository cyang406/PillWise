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

from pillwise.schemas import Language, Medication, PillCard, QuizQuestion, Report, SimplifiedSummary


def pill_cards(meds: list[Medication]) -> list[PillCard]:
    raise NotImplementedError("A: implement pill cards")


def simplify(report: Report, language: Language = "en") -> SimplifiedSummary:
    raise NotImplementedError("A: stretch A - plain language")


def make_quiz(report: Report, n: int = 3) -> list[QuizQuestion]:
    raise NotImplementedError("A: stretch A - teach-back quiz")

"""Shared data contracts for PillWise.

FROZEN FILE: every branch imports these models. Change them only through a
"contract change" commit on `main` (see CLAUDE.md), never inside a role branch.

Design rules baked into these models:
- Severity is decided by data and rules (checkers), never by the LLM.
- `directions` / `how_to_take` are copied from the bottle or label, never generated.
- Every Finding carries at least one Evidence with a source and a version.
- `what_to_do` always ends with the pharmacist footer (enforced by a validator).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enums and constants
# ---------------------------------------------------------------------------

Severity = Literal["major", "moderate", "caution", "minor", "unknown"]

#: Higher number = more serious. Use this to sort findings; never compare strings.
SEVERITY_RANK: dict[str, int] = {
    "major": 4,
    "moderate": 3,
    "caution": 2,
    "minor": 1,
    "unknown": 0,
}

FindingKind = Literal[
    "interaction",  # drug-drug (DDInter, ONC)
    "older_adult_risk",  # single drug risky at 65+ (Beers)
    "older_adult_combo",  # combination risky at 65+ (Beers, e.g. 2+ anticholinergics)
    "duplicate",  # same ingredient twice / therapeutic duplication
    "food",  # drug-food or drug-alcohol (DDInter)
]

EvidenceSource = Literal["DDInter", "openFDA", "Beers 2023", "ONC", "RxNorm", "bottle"]

MedSource = Literal["photo", "manual", "synthea", "scenario"]

Language = Literal["en", "es", "zh"]

SAFETY_FOOTER = "Talk to your pharmacist or doctor before changing anything."


def _stable_id(*parts: str) -> str:
    """Deterministic short id, so the same finding gets the same id across runs."""
    raw = "|".join(p.strip().lower() for p in parts)
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


class PatientContext(BaseModel):
    """What we know about the person. Everything is optional; nothing is stored."""

    age: int | None = Field(default=None, ge=0, le=120)
    language: Language = "en"

    @property
    def is_older_adult(self) -> bool | None:
        """True if 65+, False if younger, None if unknown (show Beers as 'if 65+')."""
        return None if self.age is None else self.age >= 65


class Medication(BaseModel):
    """One medicine on the person's list."""

    raw_text: str = ""  # exactly what we read off the bottle (or typed)
    name: str  # display name, e.g. "Advil" or "ibuprofen"
    strength: str | None = None  # e.g. "200 mg"
    directions: str | None = None  # COPIED from the label; never generated
    rxcui: str | None = None  # filled by normalize(); None = could not normalize
    generic_name: str | None = None  # normalized ingredient name(s), lower case
    ingredients: list[str] = Field(default_factory=list)  # lower-case RxNorm ingredient (TTY=IN) names, no salts
    source: MedSource = "manual"
    confirmed: bool = False  # True after the person reviewed it in the UI

    @property
    def key(self) -> str:
        """Lower-case name used for matching when ingredients are empty."""
        return (self.generic_name or self.name).strip().lower()

    @property
    def match_names(self) -> list[str]:
        """All lower-case names a checker should try to match against."""
        names = [i.lower() for i in self.ingredients] or [self.key]
        return sorted(set(names))


# ---------------------------------------------------------------------------
# Outputs of checkers and evidence
# ---------------------------------------------------------------------------


class Evidence(BaseModel):
    source: EvidenceSource
    text: str  # a QUOTE for openFDA; our own summary for Beers (copyrighted)
    url: str | None = None
    version: str  # label effective date, dataset version, or "seed-2026-10-28"


class Finding(BaseModel):
    id: str = ""  # auto-filled from kind + drugs if empty
    kind: FindingKind
    severity: Severity
    drugs: list[str]  # lower-case generic names involved, sorted
    title: str  # short, e.g. "Bleeding risk: warfarin + ibuprofen"
    plain_summary: str  # 1-2 sentences, plain words
    what_to_do: str  # always ends with SAFETY_FOOTER (validator adds it)
    evidence: list[Evidence] = Field(min_length=1)
    checker: str  # name of the checker that produced it, e.g. "ddinter"

    @field_validator("drugs")
    @classmethod
    def _normalize_drugs(cls, v: list[str]) -> list[str]:
        return sorted({d.strip().lower() for d in v if d.strip()})

    @model_validator(mode="after")
    def _fill_id_and_footer(self) -> Finding:
        if not self.id:
            self.id = _stable_id(self.kind, *self.drugs)
        if not self.what_to_do.rstrip().endswith(SAFETY_FOOTER):
            self.what_to_do = f"{self.what_to_do.rstrip()} {SAFETY_FOOTER}".strip()
        return self

    @property
    def rank(self) -> int:
        return SEVERITY_RANK[self.severity]


class PillCard(BaseModel):
    """Per-medicine explanation card. Text comes from the label, explained by the LLM."""

    med_key: str  # Medication.key
    name: str
    what_it_is_for: str
    how_to_take: str | None = None  # COPIED from bottle/label directions
    watch_for: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# The report: the single object the UI renders
# ---------------------------------------------------------------------------


class Report(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    patient: PatientContext = Field(default_factory=PatientContext)
    meds: list[Medication]
    findings: list[Finding] = Field(default_factory=list)
    pill_cards: list[PillCard] = Field(default_factory=list)
    unchecked: list[str] = Field(default_factory=list)  # names we could NOT check; never "safe"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model: str = "none"
    data_versions: dict[str, str] = Field(default_factory=dict)  # {"ddinter": "2.0", ...}
    is_mock: bool = False

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: (-f.rank, f.title))

    @property
    def worst_severity(self) -> Severity | None:
        return self.sorted_findings()[0].severity if self.findings else None


# ---------------------------------------------------------------------------
# Stretch A (idea 5): plain language, translation, teach-back
# ---------------------------------------------------------------------------


class SimplifiedSection(BaseModel):
    title: str
    text: str
    source_ids: list[str] = Field(default_factory=list)  # Finding.id / PillCard.med_key it came from


class SimplifiedSummary(BaseModel):
    language: Language
    sections: list[SimplifiedSection]
    reading_grade: float | None = None  # textstat grade of the English version
    back_translation: str | None = None  # only for non-English
    drift_score: float | None = None  # 0..1 similarity of back-translation to English; higher = safer
    drift_ok: bool | None = None


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=2)
    correct_index: int
    explanation: str
    source_id: str | None = None  # Finding.id the question tests

    @model_validator(mode="after")
    def _check_index(self) -> QuizQuestion:
        if not 0 <= self.correct_index < len(self.options):
            raise ValueError("correct_index out of range")
        return self


# ---------------------------------------------------------------------------
# Stretch B (idea 6): clinic / caregiver population view
# ---------------------------------------------------------------------------


class ClinicPatientSummary(BaseModel):
    patient_id: str
    age: int | None
    n_meds: int
    n_findings: int
    worst_severity: Severity | None
    top_finding_title: str | None = None


# ---------------------------------------------------------------------------
# Audit trail (Solix data-lineage story)
# ---------------------------------------------------------------------------


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    report_id: str
    event: Literal["report_created", "finding", "pill_card", "simplified", "error"]
    finding_id: str | None = None
    source: str | None = None
    source_version: str | None = None
    model: str | None = None
    detail: str = ""

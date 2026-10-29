"""The ONLY module the UI (app/) is allowed to import from the backend.

FROZEN FILE (shared contract). Signatures here are the handshake between
A (pipeline), B (data/rules) and C (UI):

- C calls these functions and renders the returned models.
- A implements the real behaviour in orchestrator / extract / explain / agents.
- B's checkers are reached through orchestrator, never from here directly.

Every function switches on `settings.mock`: True -> pillwise.mocks (canned,
always works), False -> the real implementation. Integration flips
PILLWISE_MOCK=0 once the real path passes the scenarios.
"""

from __future__ import annotations

from pillwise.config import get_settings
from pillwise.schemas import (
    AuditEvent,
    ClinicPatientSummary,
    Language,
    Medication,
    PatientContext,
    QuizQuestion,
    Report,
    SimplifiedSummary,
)


def read_bottle(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[Medication]:
    """Photo of one or more bottles -> medicines (unconfirmed). Owner: A (extract.py)."""
    if get_settings().mock:
        from pillwise import mocks

        return mocks.mock_read_bottle(image_bytes, mime_type)
    from pillwise import extract

    return extract.extract_from_image(image_bytes, mime_type)


def check(meds: list[Medication], patient: PatientContext | None = None) -> Report:
    """Confirmed medicine list -> full Report (findings, cards, evidence). Owner: A (orchestrator.py)."""
    patient = patient or PatientContext()
    if get_settings().mock:
        from pillwise import mocks

        return mocks.mock_report(meds, patient)
    from pillwise import orchestrator

    return orchestrator.build_report(meds, patient)


def simplify(report: Report, language: Language = "en") -> SimplifiedSummary:
    """Stretch A: plain-language (and translated) summary of a Report. Owner: A (explain.py)."""
    if get_settings().mock:
        from pillwise import mocks

        return mocks.mock_simplify(report, language)
    from pillwise import explain

    return explain.simplify(report, language)


def quiz(report: Report, n: int = 3) -> list[QuizQuestion]:
    """Stretch A: teach-back questions about the most important findings. Owner: A (explain.py)."""
    if get_settings().mock:
        from pillwise import mocks

        return mocks.mock_quiz(report, n)
    from pillwise import explain

    return explain.make_quiz(report, n)


def clinic_scan(limit: int = 200) -> list[ClinicPatientSummary]:
    """Stretch B: scan the synthetic 65+ population. Owner: A + B (agents/)."""
    if get_settings().mock:
        from pillwise import mocks

        return mocks.mock_clinic_scan(limit)
    from pillwise.agents import clinic

    return clinic.scan(limit)


def clinic_patient(patient_id: str) -> Report:
    """Stretch B: full Report for one synthetic patient. Owner: A + B (agents/)."""
    if get_settings().mock:
        from pillwise import mocks

        return mocks.mock_clinic_patient(patient_id)
    from pillwise.agents import clinic

    return clinic.patient_report(patient_id)


def match_names(meds: list[Medication]) -> list[Medication]:
    """Name -> RxNorm ingredients only (no checks), so the UI can flag names it can't match before checking.

    Owner: A (normalize.py). Unmatched medicines come back unchanged (no ingredients); never a reason to say "safe".
    """
    if get_settings().mock:
        from pillwise import mocks

        return mocks.mock_match_names(meds)
    from pillwise import normalize

    return normalize.normalize_all(meds)


def recent_audit_events(limit: int = 200) -> list[AuditEvent]:
    """Newest audit events for the UI trust panel (C3). Owner: B (audit.py). [] in mock mode (nothing logged)."""
    if get_settings().mock:
        return []
    from pillwise import audit

    return audit.recent_events(limit)


def load_scenario(name: str) -> tuple[list[Medication], PatientContext]:
    """Load a scripted demo scenario from data/scenarios/<name>.json (works in both modes)."""
    import json

    path = get_settings().scenarios_dir / f"{name}.json"
    data = json.loads(path.read_text())
    meds = [Medication(**m, source="scenario", confirmed=True) for m in data["meds"]]
    return meds, PatientContext(**data.get("patient", {}))


def list_scenarios() -> list[str]:
    return sorted(p.stem for p in get_settings().scenarios_dir.glob("*.json"))

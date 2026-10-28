"""Canned responses so every branch can run before the real pipeline exists.

FROZEN FILE (shared contract). C builds the UI against these; A and B use them
as the shape their real output must match. Everything returned here is marked
`is_mock=True` / version "MOCK" so it can never be mistaken for real output.

The mock rules are a tiny hard-coded table, just enough for the three demo
scenarios in data/scenarios/ to pass. They are NOT clinical data.
"""

from __future__ import annotations

from pillwise.schemas import (
    SEVERITY_RANK,
    ClinicPatientSummary,
    Evidence,
    Finding,
    Language,
    Medication,
    PatientContext,
    PillCard,
    QuizQuestion,
    Report,
    SimplifiedSection,
    SimplifiedSummary,
)

MOCK_VERSION = "MOCK"

_INTERACTIONS: dict[frozenset[str], tuple[str, str, str]] = {
    frozenset({"warfarin", "ibuprofen"}): (
        "major",
        "Bleeding risk: warfarin + ibuprofen",
        "Taking these together can raise the chance of serious bleeding.",
    ),
}

_OLDER_ADULT: dict[str, str] = {
    "diphenhydramine": "Can cause confusion, dizziness and falls in people 65 and older.",
    "oxybutynin": "Can cause confusion, constipation and dry mouth in people 65 and older.",
    "ibuprofen": "Regular use can irritate the stomach and strain the kidneys in people 65 and older.",
}

_ANTICHOLINERGIC = {"diphenhydramine", "oxybutynin"}

# Names the mock "knows"; anything else lands in Report.unchecked, like the real pipeline.
_KNOWN = (
    {n for pair in _INTERACTIONS for n in pair}
    | set(_OLDER_ADULT)
    | {
        "acetaminophen",
        "loratadine",
        "lisinopril",
    }
)


def _ev(text: str, source: str = "DDInter") -> Evidence:
    return Evidence(source=source, text=f"[MOCK] {text}", url=None, version=MOCK_VERSION)  # type: ignore[arg-type]


def _names(meds: list[Medication]) -> set[str]:
    out: set[str] = set()
    for m in meds:
        out.update(m.match_names)
    return out


def mock_read_bottle(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[Medication]:
    return [
        Medication(
            raw_text="Ibuprofen Tablets USP 200 mg. Pain reliever/fever reducer (NSAID)",
            name="Ibuprofen",
            strength="200 mg",
            directions="Take 1 tablet every 4 to 6 hours while symptoms persist.",
            generic_name="ibuprofen",
            ingredients=["ibuprofen"],
            source="photo",
        ),
        Medication(
            raw_text="Diphenhydramine HCl 25 mg. Nighttime sleep-aid",
            name="Diphenhydramine",
            strength="25 mg",
            directions="Take 2 caplets at bedtime if needed.",
            generic_name="diphenhydramine",
            ingredients=["diphenhydramine"],
            source="photo",
        ),
    ]


def mock_report(meds: list[Medication], patient: PatientContext) -> Report:
    names = _names(meds)
    findings: list[Finding] = []

    for pair, (sev, title, summary) in _INTERACTIONS.items():
        if pair <= names:
            findings.append(
                Finding(
                    kind="interaction",
                    severity=sev,  # type: ignore[arg-type]
                    drugs=sorted(pair),
                    title=title,
                    plain_summary=summary,
                    what_to_do="Do not start or stop either medicine on your own.",
                    evidence=[_ev("Interaction listed as Major."), _ev("Label warns about bleeding.", "openFDA")],
                    checker="mock",
                )
            )

    if patient.is_older_adult is not False:  # True or unknown
        for drug, why in _OLDER_ADULT.items():
            if drug in names:
                findings.append(
                    Finding(
                        kind="older_adult_risk",
                        severity="caution",
                        drugs=[drug],
                        title=f"Extra care at 65+: {drug}",
                        plain_summary=why,
                        what_to_do="Ask whether a safer option exists.",
                        evidence=[_ev("Listed in older-adult risk criteria.", "Beers 2023")],
                        checker="mock",
                    )
                )
        anti = sorted(names & _ANTICHOLINERGIC)
        if len(anti) >= 2:
            findings.append(
                Finding(
                    kind="older_adult_combo",
                    severity="moderate",
                    drugs=anti,
                    title="Two or more anticholinergic medicines",
                    plain_summary="Together these add up and raise the risk of confusion and falls.",
                    what_to_do="Ask whether one of them can be stopped or replaced.",
                    evidence=[_ev("Combination listed in older-adult criteria.", "Beers 2023")],
                    checker="mock",
                )
            )

    cards = [
        PillCard(
            med_key=m.key,
            name=m.name,
            what_it_is_for=f"[MOCK] What {m.name} is usually used for.",
            how_to_take=m.directions,
            watch_for=["[MOCK] A side effect to watch for."],
            evidence=[_ev(f"Label section for {m.name}.", "openFDA")],
        )
        for m in meds
    ]
    findings.sort(key=lambda f: (-SEVERITY_RANK[f.severity], f.title))
    return Report(
        patient=patient,
        meds=meds,
        findings=findings,
        pill_cards=cards,
        unchecked=[m.name for m in meds if not set(m.match_names) & _KNOWN],
        model="mock",
        data_versions={"ddinter": MOCK_VERSION, "beers": MOCK_VERSION, "openfda": MOCK_VERSION},
        is_mock=True,
    )


def mock_simplify(report: Report, language: Language = "en") -> SimplifiedSummary:
    sections = [
        SimplifiedSection(title=f.title, text=f"[MOCK {language}] {f.plain_summary}", source_ids=[f.id])
        for f in report.sorted_findings()
    ] or [SimplifiedSection(title="No problems found", text=f"[MOCK {language}] Nothing to flag.")]
    return SimplifiedSummary(
        language=language,
        sections=sections,
        reading_grade=5.8,
        back_translation=None if language == "en" else "[MOCK] back-translation",
        drift_score=None if language == "en" else 0.91,
        drift_ok=None if language == "en" else True,
    )


def mock_quiz(report: Report, n: int = 3) -> list[QuizQuestion]:
    qs = [
        QuizQuestion(
            question=f"[MOCK] What should you do about: {f.title}?",
            options=["Stop both medicines today", "Ask your pharmacist first", "Ignore it"],
            correct_index=1,
            explanation="Never change medicines on your own; ask first.",
            source_id=f.id,
        )
        for f in report.sorted_findings()
    ]
    return qs[:n]


def mock_clinic_scan(limit: int = 200) -> list[ClinicPatientSummary]:
    rows = [
        ClinicPatientSummary(
            patient_id="mock-001",
            age=78,
            n_meds=7,
            n_findings=3,
            worst_severity="major",
            top_finding_title="Bleeding risk: warfarin + ibuprofen",
        ),
        ClinicPatientSummary(
            patient_id="mock-002",
            age=71,
            n_meds=4,
            n_findings=1,
            worst_severity="caution",
            top_finding_title="Extra care at 65+: diphenhydramine",
        ),
        ClinicPatientSummary(patient_id="mock-003", age=66, n_meds=2, n_findings=0, worst_severity=None),
    ]
    return rows[:limit]


def mock_clinic_patient(patient_id: str) -> Report:
    from pillwise.api import load_scenario

    meds, patient = load_scenario("warfarin_nsaid")
    return mock_report(meds, patient)

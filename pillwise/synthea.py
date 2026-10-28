"""Synthetic patients for the clinic view. Owner: B (docs/PARALLEL_AB.md, seam 3).

Contract with A (agents/clinic.py builds on these two functions only):
    list_patients(limit=200) -> list[tuple[str, int | None]]   # (patient_id, age)
    patient_meds(patient_id) -> list[Medication]                # source="synthea"

STUB: two hard-coded synthetic patients so A can start A11 now. B12 later
replaces the data with Synthea output (data/synthea.duckdb) behind the same
signatures. Never real people.
"""

from __future__ import annotations

from pillwise.schemas import Medication

# (age, [(display name, lower-case RxNorm IN names)])
_PATIENTS: dict[str, tuple[int | None, list[tuple[str, list[str]]]]] = {
    "stub-001": (78, [("Warfarin", ["warfarin"]), ("Ibuprofen", ["ibuprofen"]), ("Lisinopril", ["lisinopril"])]),
    "stub-002": (
        81,
        [
            ("Diphenhydramine", ["diphenhydramine"]),
            ("Oxybutynin", ["oxybutynin"]),
            ("Acetaminophen", ["acetaminophen"]),
        ],
    ),
}


def list_patients(limit: int = 200) -> list[tuple[str, int | None]]:
    return [(pid, age) for pid, (age, _) in sorted(_PATIENTS.items())][:limit]


def patient_meds(patient_id: str) -> list[Medication]:
    """Raises KeyError for an unknown id (never an empty, 'safe-looking' list)."""
    _, meds = _PATIENTS[patient_id]
    return [
        Medication(name=name, generic_name=", ".join(ings), ingredients=ings, source="synthea", confirmed=True)
        for name, ings in meds
    ]

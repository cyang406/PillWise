"""Clinic view over a synthetic 65+ population. Owners: A (agents) + B (data).

Contracts (called by pillwise.api):
    scan(limit) -> list[ClinicPatientSummary]
    patient_report(patient_id) -> Report

Plan:
- B: scripts/gen_synthea.sh + scripts/load_synthea.py -> data/synthea.duckdb with
  tables patients(id, birthdate) and medications(patient_id, description, code, start, stop).
- A: planner agent picks which patients to review; it runs the SAME checkers through
  orchestrator.build_report (no new rules); reviewer agent writes a one-line summary.
- Every agent tool call is logged through pillwise.audit.
"""

from __future__ import annotations

from pillwise.schemas import ClinicPatientSummary, Report


def scan(limit: int = 200) -> list[ClinicPatientSummary]:
    raise NotImplementedError("stretch B")


def patient_report(patient_id: str) -> Report:
    raise NotImplementedError("stretch B")

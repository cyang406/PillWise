"""Checker interface. FROZEN FILE (shared contract).

A checker turns a confirmed medicine list into Findings using curated data or
hard-coded rules only. It must never call an LLM and must be deterministic:
same input -> same output. That is the core safety promise of PillWise.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from pillwise.schemas import Finding, Medication, PatientContext


class CheckResult(BaseModel):
    """What `pillwise.checks.run_all()` returns to the orchestrator."""

    findings: list[Finding] = Field(default_factory=list)
    versions: dict[str, str] = Field(default_factory=dict)  # checker name -> version
    errors: dict[str, str] = Field(default_factory=dict)  # checker name -> error message
    unmatched: list[str] = Field(default_factory=list)  # med names no checker could match at all


@runtime_checkable
class Checker(Protocol):
    #: short id used in Finding.checker and in the audit log, e.g. "ddinter"
    name: str
    #: dataset/rules version shown in evidence and Report.data_versions
    version: str

    def check(self, meds: list[Medication], patient: PatientContext) -> list[Finding]:
        """Return findings for this list. Must not raise on unknown drugs; skip them."""
        ...

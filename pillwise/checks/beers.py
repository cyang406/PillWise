"""Older-adult risk checker based on a hand-built subset of the 2023 AGS Beers Criteria. Owner: B.

Data: data/beers.json. The Beers Criteria are copyrighted: the JSON holds our
OWN short summaries plus a citation, never copied table text.

Rules:
- Run when patient.is_older_adult is True, or None (age unknown -> phrase as "if you are 65 or older").
- Skip entirely when patient.is_older_adult is False.

TODO(B):
- [ ] Single-drug rules: data["drugs"] -> kind="older_adult_risk", severity="caution".
- [ ] Combination rules: data["combos"] (e.g. 2+ drugs tagged "anticholinergic",
      3+ tagged "cns_active", opioid + benzodiazepine) -> kind="older_adult_combo", severity="moderate".
- [ ] Evidence source "Beers 2023", url = the PubMed citation in the JSON.
- [ ] Unit tests in tests/test_checks_beers.py.
"""

from __future__ import annotations

from pillwise.config import get_settings
from pillwise.schemas import Finding, Medication, PatientContext


class BeersChecker:
    name = "beers"
    version = "2023-subset-seed"

    def __init__(self, path=None) -> None:
        self.path = path or get_settings().beers_path

    def check(self, meds: list[Medication], patient: PatientContext) -> list[Finding]:
        raise NotImplementedError("B: implement Beers rules")

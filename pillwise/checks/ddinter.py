"""DDInter 2.0 drug-drug (and drug-food) interaction checker. Owner: B.

Data: run `python scripts/load_ddinter.py` once to build data/ddinter.sqlite
from the CSVs downloaded into data/raw/ddinter/ (see docs/DATA_SOURCES.md).

TODO(B):
- [ ] Look up every pair of meds (by match_names) in the `interactions` table.
- [ ] Map DDInter level -> Severity: Major->major, Moderate->moderate, Minor->minor, Unknown->unknown.
- [ ] One Finding per pair, kind="interaction", evidence source "DDInter" with url to the DDInter page if known.
- [ ] plain_summary / what_to_do: short template text per severity (no LLM here).
- [ ] Stretch: drug-food records -> kind="food".
- [ ] Unit tests in tests/test_checks_ddinter.py using tests/fixtures/ddinter_sample.csv.
"""

from __future__ import annotations

from pillwise.config import get_settings
from pillwise.schemas import Finding, Medication, PatientContext

LEVEL_TO_SEVERITY = {"major": "major", "moderate": "moderate", "minor": "minor", "unknown": "unknown"}


class DDInterChecker:
    name = "ddinter"
    version = "2.0"

    def __init__(self, db_path=None) -> None:
        self.db_path = db_path or get_settings().ddinter_db

    def check(self, meds: list[Medication], patient: PatientContext) -> list[Finding]:
        raise NotImplementedError("B: implement DDInter lookup")

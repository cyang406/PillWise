"""Always-flag high-priority interaction pairs. Owner: B.

Data: data/onc_high.json (seed list; B verifies each pair against the source
paper before the demo and updates `verified`).

TODO(B):
- [ ] Load the JSON, match any member of group_a with any member of group_b.
- [ ] Emit kind="interaction", severity="major", evidence source "ONC".
- [ ] Only emit rules with "verified": true unless settings.mock is on.
"""

from __future__ import annotations

from pillwise.config import get_settings
from pillwise.schemas import Finding, Medication, PatientContext


class ONCChecker:
    name = "onc"
    version = "seed-2026-10-28"

    def __init__(self, path=None) -> None:
        self.path = path or get_settings().onc_path

    def check(self, meds: list[Medication], patient: PatientContext) -> list[Finding]:
        raise NotImplementedError("B: implement ONC hard rules")

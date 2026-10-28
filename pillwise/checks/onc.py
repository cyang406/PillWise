"""Always-flag high-priority interaction pairs. Owner: B.

Data: data/onc_high.json (seed list; B verifies each pair against the source
paper before the demo and updates `verified`).

Any member of group_a together with any member of group_b -> kind="interaction",
severity="major", evidence source "ONC". Only rules with "verified": true are
used, unless settings.mock is on.
"""

from __future__ import annotations

import json
from pathlib import Path

from pillwise.config import get_settings
from pillwise.schemas import Evidence, Finding, Medication, PatientContext

WHAT_TO_DO = "Do not start or stop either medicine on your own. Talk to whoever prescribed them soon."


class ONCChecker:
    name = "onc"
    version = "seed-2026-10-28"

    def __init__(self, path=None) -> None:
        self.path = Path(path or get_settings().onc_path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.source = self.data["source"]

    def rules(self) -> list[dict]:
        include_unverified = get_settings().mock
        return [r for r in self.data["rules"] if r.get("verified") or include_unverified]

    def known_names(self, names: set[str]) -> set[str]:
        listed = {d for r in self.rules() for d in r["group_a"] + r["group_b"]}
        return names & listed

    def check(self, meds: list[Medication], patient: PatientContext) -> list[Finding]:
        findings: dict[str, Finding] = {}
        for rule in self.rules():
            group_a, group_b = set(rule["group_a"]), set(rule["group_b"])
            for i, m1 in enumerate(meds):
                for m2 in meds[i + 1 :]:
                    for x in m1.match_names:
                        for y in m2.match_names:
                            if x in group_a and y in group_b:
                                a, b = x, y
                            elif y in group_a and x in group_b:
                                a, b = y, x
                            else:
                                continue
                            f = self._finding(rule, a, b)
                            findings.setdefault(f.id, f)
        return list(findings.values())

    def _finding(self, rule: dict, a: str, b: str) -> Finding:
        return Finding(
            kind="interaction",
            severity="major",
            drugs=[a, b],
            title=f"High-priority interaction: {a} + {b}",
            plain_summary=rule["summary"],
            what_to_do=WHAT_TO_DO,
            evidence=[
                Evidence(
                    source="ONC",
                    text=f"On the high-priority interaction list ({self.source['citation']}): {rule['summary']}",
                    url=self.source["url"],
                    version=self.source["version"] if rule.get("verified") else f"{self.version} (unverified)",
                )
            ],
            checker=self.name,
        )

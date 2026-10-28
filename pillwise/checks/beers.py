"""Older-adult risk checker based on a hand-built subset of the 2023 AGS Beers Criteria. Owner: B.

Data: data/beers.json. The Beers Criteria are copyrighted: the JSON holds our
OWN short summaries plus a citation, never copied table text.

Rules:
- Run when patient.is_older_adult is True, or None (age unknown -> phrase as "if you are 65 or older").
- Skip entirely when patient.is_older_adult is False.
- Single-drug rules (data["drugs"]) -> kind="older_adult_risk", severity="caution".
- Combination rules (data["combos"]) -> kind="older_adult_combo", severity="moderate".
  "count_tag": at least `min_count` different drugs carry `tag`.
  "pair_tags": one drug with `tag_a` and a different drug with `tag_b`.
- Entries with verified=false still run, but their evidence version says "(unverified seed)".
"""

from __future__ import annotations

import json
from pathlib import Path

from pillwise.config import get_settings
from pillwise.schemas import Evidence, Finding, Medication, PatientContext


class BeersChecker:
    name = "beers"
    version = "2023-subset-seed"

    def __init__(self, path=None) -> None:
        self.path = Path(path or get_settings().beers_path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.source = self.data["source"]
        self.tags: dict[str, set[str]] = {k: set(v) for k, v in self.data["tags"].items()}

    def known_names(self, names: set[str]) -> set[str]:
        listed = {d for e in self.data["drugs"] for d in e["drugs"]}
        for members in self.tags.values():
            listed |= members
        return names & listed

    def check(self, meds: list[Medication], patient: PatientContext) -> list[Finding]:
        older = patient.is_older_adult
        if older is False:
            return []
        names: set[str] = set()
        for m in meds:
            names.update(m.match_names)

        findings: dict[str, Finding] = {}

        def add(f: Finding) -> None:
            if f.id in findings:  # two entries matched the same drugs: keep one card, all evidence
                findings[f.id].evidence.extend(f.evidence)
            else:
                findings[f.id] = f

        for entry in self.data["drugs"]:
            for drug in sorted(names & set(entry["drugs"])):
                add(self._finding(entry, "older_adult_risk", "caution", [drug], older, f"Extra care at 65+: {drug}"))

        for combo in self.data["combos"]:
            drugs = self._combo_drugs(combo, names)
            if drugs:
                add(self._finding(combo, "older_adult_combo", "moderate", drugs, older, combo["label"]))

        return list(findings.values())

    def _combo_drugs(self, combo: dict, names: set[str]) -> list[str]:
        if combo["type"] == "count_tag":
            hits = names & self.tags.get(combo["tag"], set())
            return sorted(hits) if len(hits) >= combo["min_count"] else []
        if combo["type"] == "pair_tags":
            a = names & self.tags.get(combo["tag_a"], set())
            b = names & self.tags.get(combo["tag_b"], set())
            if a and b and (len(a | b) >= 2):
                return sorted(a | b)
            return []
        raise ValueError(f"unknown Beers combo type {combo['type']!r} in {combo['id']}")

    def _finding(
        self, entry: dict, kind: str, severity: str, drugs: list[str], older: bool | None, title: str
    ) -> Finding:
        risk = entry["risk"]
        summary = risk if older else f"If you are 65 or older: {risk[0].lower()}{risk[1:]}"
        version = self.source["version"] if entry.get("verified") else f"{self.source['version']} (unverified seed)"
        return Finding(
            kind=kind,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            drugs=drugs,
            title=title,
            plain_summary=summary,
            what_to_do=entry["advice"],
            evidence=[
                Evidence(
                    source="Beers 2023",
                    text=f"{entry['label']}. {risk} (Our summary of {self.source['citation']}.)",
                    url=self.source["url"],
                    version=version,
                )
            ],
            checker=self.name,
        )

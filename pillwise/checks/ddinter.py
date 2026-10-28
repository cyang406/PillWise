"""DDInter 2.0 drug-drug (and drug-food) interaction checker. Owner: B.

Data: run `python scripts/load_ddinter.py` once to build data/ddinter.sqlite
from the CSVs downloaded into data/raw/ddinter/ (see docs/DATA_SOURCES.md).

Every pair of meds is looked up by `match_names` (ingredients). One Finding per
ingredient pair found, severity straight from the DDInter level. Text is a fixed
template per severity: no LLM here.

A missing database raises, so run_all() records "could not check" instead of
silently returning no findings.
"""

from __future__ import annotations

import logging
import sqlite3
from itertools import combinations
from pathlib import Path

from pillwise.config import get_settings
from pillwise.schemas import Evidence, Finding, Medication, PatientContext

log = logging.getLogger(__name__)

LEVEL_TO_SEVERITY = {"major": "major", "moderate": "moderate", "minor": "minor", "unknown": "unknown"}

DDINTER_URL = "https://ddinter2.scbdd.com/"

# Template text per severity (our words). `what_to_do` gets the pharmacist footer from the schema.
TEMPLATES: dict[str, tuple[str, str]] = {
    "major": (
        "These medicines can affect each other in a serious way. Using them together may need to be avoided "
        "or closely watched.",
        "Do not start or stop either medicine on your own. Ask soon whether this combination is right for you.",
    ),
    "moderate": (
        "These medicines can affect each other. Using them together may need extra monitoring or a dose change.",
        "Keep taking your medicines as prescribed and ask whether this combination needs a check.",
    ),
    "minor": (
        "These medicines can have a small effect on each other. It usually does not need a change.",
        "Mention this combination at your next pharmacy visit.",
    ),
    "unknown": (
        "A drug-interaction database lists these medicines together, but how serious it is is not known.",
        "Ask whether this combination needs any attention.",
    ),
}


class DDInterChecker:
    name = "ddinter"
    version = "2.0"

    def __init__(self, db_path=None) -> None:
        self.db_path = Path(db_path or get_settings().ddinter_db)

    def _connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(f"{self.db_path} not built; run `make ddinter`")
        return sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)

    def known_names(self, names: set[str]) -> set[str]:
        """Which of these lower-case names appear anywhere in DDInter."""
        if not names:
            return set()
        with self._connect() as con:
            marks = ",".join("?" * len(names))
            args = sorted(names)
            rows = con.execute(
                f"SELECT drug_a FROM interactions WHERE drug_a IN ({marks}) "
                f"UNION SELECT drug_b FROM interactions WHERE drug_b IN ({marks})",
                args + args,
            ).fetchall()
        return {r[0] for r in rows}

    def check(self, meds: list[Medication], patient: PatientContext) -> list[Finding]:
        findings: dict[str, Finding] = {}
        with self._connect() as con:
            for m1, m2 in combinations(meds, 2):
                for a in m1.match_names:
                    for b in m2.match_names:
                        if a == b:  # same ingredient twice is a duplicate, not an interaction
                            continue
                        lo, hi = sorted((a, b))
                        row = con.execute(
                            "SELECT level, id_a, id_b FROM interactions WHERE drug_a=? AND drug_b=?", (lo, hi)
                        ).fetchone()
                        if row is None:
                            continue
                        f = self._finding(lo, hi, row[0], row[1], row[2])
                        findings.setdefault(f.id, f)
        return list(findings.values())

    def _finding(self, a: str, b: str, level: str, id_a: str | None, id_b: str | None) -> Finding:
        severity = LEVEL_TO_SEVERITY.get((level or "").strip().lower(), "unknown")
        summary, todo = TEMPLATES[severity]
        ids = f" ({id_a} / {id_b})" if id_a and id_b else ""
        label = "Unknown" if severity == "unknown" else severity.capitalize()
        return Finding(
            kind="interaction",
            severity=severity,  # type: ignore[arg-type]
            drugs=[a, b],
            title=f"{label} interaction: {a} + {b}",
            plain_summary=summary,
            what_to_do=todo,
            evidence=[
                Evidence(
                    source="DDInter",
                    text=f"DDInter 2.0 lists {a} + {b} with interaction level '{label}'{ids}.",
                    url=DDINTER_URL,
                    version=self.version,
                )
            ],
            checker=self.name,
        )

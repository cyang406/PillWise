"""Checker registry. Owner: B.

Contract with A (do not change the signature of run_all):
    run_all(meds, patient) -> CheckResult

A checker that raises is recorded in CheckResult.errors; it never turns into
"no findings". The UI must show errors as "could not check", never as safe.
"""

from __future__ import annotations

from pillwise.checks.base import Checker, CheckResult
from pillwise.schemas import Medication, PatientContext


def get_checkers() -> list[Checker]:
    """Instantiate every enabled checker. B: add new checkers here."""
    from pillwise.checks.beers import BeersChecker
    from pillwise.checks.ddinter import DDInterChecker
    from pillwise.checks.onc import ONCChecker

    return [DDInterChecker(), ONCChecker(), BeersChecker()]


def run_all(meds: list[Medication], patient: PatientContext) -> CheckResult:
    result = CheckResult()
    by_id: dict[str, int] = {}
    for checker in get_checkers():
        result.versions[checker.name] = checker.version
        try:
            for f in checker.check(meds, patient):
                if f.id in by_id:  # e.g. ONC and DDInter flag the same pair: merge, keep worst
                    existing = result.findings[by_id[f.id]]
                    existing.evidence.extend(f.evidence)
                    if f.rank > existing.rank:
                        existing.severity = f.severity
                    continue
                by_id[f.id] = len(result.findings)
                result.findings.append(f)
        except NotImplementedError:
            result.errors[checker.name] = "not implemented yet"
        except Exception as exc:  # noqa: BLE001 - a broken checker must not crash the report
            result.errors[checker.name] = f"{type(exc).__name__}: {exc}"
    # TODO(B): fill result.unmatched with meds that no dataset recognised.
    return result

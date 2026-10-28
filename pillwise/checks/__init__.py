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
    checkers = get_checkers()
    for checker in checkers:
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
    result.unmatched = _unmatched(meds, checkers, result)
    return result


def _unmatched(meds: list[Medication], checkers: list[Checker], result: CheckResult) -> list[str]:
    """Names of meds that no working checker's dataset recognised (shown as "could not check")."""
    names = {n for m in meds for n in m.match_names}
    known: set[str] = set()
    for checker in checkers:
        if checker.name in result.errors or not hasattr(checker, "known_names"):
            continue
        try:
            known |= checker.known_names(names)
        except Exception as exc:  # noqa: BLE001 - treat as "recognised nothing", never as safe
            result.errors.setdefault(checker.name, f"{type(exc).__name__}: {exc}")
    return [m.name for m in meds if not set(m.match_names) & known]

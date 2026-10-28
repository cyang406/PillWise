"""Run every demo scenario through pillwise.api.check and verify expectations.

SHARED script (used by every branch and by the integration agent).

    python scripts/run_scenarios.py            # uses PILLWISE_MOCK from env (default 1)
    PILLWISE_MOCK=0 python scripts/run_scenarios.py   # the real pipeline

Exit code 0 = all scenarios pass. Expectation format (data/scenarios/*.json):
    "expect": {
      "must_flag": [{"kind": "...", "drugs": [...], "min_severity": "..."}],
      "max_severity": "minor" | null      # nothing may be worse than this
    }
A must_flag item matches a finding with the same kind whose drugs include all listed drugs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pillwise import api  # noqa: E402
from pillwise.config import get_settings  # noqa: E402
from pillwise.schemas import SEVERITY_RANK, Report  # noqa: E402


def evaluate(report: Report, expect: dict) -> list[str]:
    problems: list[str] = []
    for want in expect.get("must_flag", []):
        need = set(want["drugs"])
        hits = [f for f in report.findings if f.kind == want["kind"] and need <= set(f.drugs)]
        if not hits:
            problems.append(f"missing {want['kind']} for {sorted(need)}")
        elif max(h.rank for h in hits) < SEVERITY_RANK[want.get("min_severity", "unknown")]:
            problems.append(f"{want['kind']} {sorted(need)} below {want['min_severity']}")
    cap = expect.get("max_severity")
    if cap is not None:
        worse = [f.title for f in report.findings if f.rank > SEVERITY_RANK[cap]]
        if worse:
            problems.append(f"expected nothing above {cap}, got {worse}")
    for f in report.findings:
        if not f.evidence:
            problems.append(f"finding without evidence: {f.title}")
    return problems


def main() -> int:
    settings = get_settings()
    print(f"mode: {'MOCK' if settings.mock else 'REAL'}")
    failed = 0
    for name in api.list_scenarios():
        data = json.loads((settings.scenarios_dir / f"{name}.json").read_text())
        meds, patient = api.load_scenario(name)
        try:
            report = api.check(meds, patient)
            problems = evaluate(report, data.get("expect", {}))
        except NotImplementedError as exc:
            problems = [f"not implemented: {exc}"]
        status = "PASS" if not problems else "FAIL"
        failed += bool(problems)
        print(f"[{status}] {name}: {data.get('title', '')}")
        for p in problems:
            print(f"    - {p}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""A6: build_report end to end on the 3 scenarios.

Real normalize / evidence / explain over recorded RxNorm + openFDA responses, a fake LLM,
and the mock checker (B's real checkers are swapped in at CP2; see docs/PARALLEL_AB.md).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from pillwise import api, checks, llm, mocks, orchestrator
from pillwise.checks.base import CheckResult
from pillwise.config import get_settings
from pillwise.schemas import Medication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from run_scenarios import evaluate  # noqa: E402

CACHE = Path(__file__).parent / "fixtures" / "pipeline" / "cache"


def mock_check_result(meds, patient) -> CheckResult:
    """Local stand-in for mocks.mock_check_result (pending contract change)."""
    return CheckResult(findings=mocks.mock_report(meds, patient).findings, versions={"mock": mocks.MOCK_VERSION})


def fake_llm(prompt, output_type, **kw):
    if "quote" in output_type.model_fields:
        corpus = prompt.split("LABEL TEXT:\n", 1)[1]
        first = corpus.split(". ")[0] + "."
        return output_type(quote=first)
    return output_type(what_it_is_for="Plain explanation.", watch_for=["Something to watch"])


@pytest.fixture(autouse=True)
def pipeline_env(monkeypatch, tmp_path):
    monkeypatch.setenv("PILLWISE_CACHE_DIR", str(CACHE))
    monkeypatch.setenv("PILLWISE_OFFLINE", "1")
    monkeypatch.setenv("PILLWISE_AUDIT_DB", str(tmp_path / "audit.sqlite"))
    monkeypatch.setattr(checks, "run_all", mock_check_result)
    monkeypatch.setattr(llm, "structured", fake_llm)


@pytest.mark.parametrize("name", api.list_scenarios())
def test_scenario_through_pipeline(name):
    meds, patient = api.load_scenario(name)
    report = orchestrator.build_report(meds, patient)
    expect = json.loads((get_settings().scenarios_dir / f"{name}.json").read_text())["expect"]
    assert evaluate(report, expect) == []
    assert all(m.rxcui for m in report.meds)
    assert report.unchecked == []
    by_key = {c.med_key: c for c in report.pill_cards}
    for m in report.meds:
        assert by_key[m.key].how_to_take == m.directions


def test_unknown_drug_is_unchecked_not_safe():
    report = orchestrator.build_report([Medication(name="Zzzfakedrug")], api.PatientContext(age=70))
    assert report.unchecked == ["Zzzfakedrug"]
    assert report.findings == []


def test_evidence_step_crash_keeps_findings(monkeypatch):
    from pillwise import evidence

    def boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(evidence, "attach_label_evidence", boom)
    meds, patient = api.load_scenario("warfarin_nsaid")
    report = orchestrator.build_report(meds, patient)
    assert any(f.kind == "interaction" for f in report.findings)

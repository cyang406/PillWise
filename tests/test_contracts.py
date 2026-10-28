"""Contract tests. SHARED: must pass on every branch at every commit.

If one of these fails after your change, you broke the handshake between roles.
Fix your code, not this file (changing it is a contract change on main).
"""

from __future__ import annotations

import inspect
import json

import pytest

from pillwise import api, checks, mocks
from pillwise.checks.base import Checker, CheckResult
from pillwise.config import get_settings
from pillwise.schemas import SAFETY_FOOTER, Evidence, Finding, Medication, PatientContext, Report

# --- schemas -----------------------------------------------------------------


def test_finding_gets_id_and_footer():
    f = Finding(
        kind="interaction",
        severity="major",
        drugs=["Warfarin", "ibuprofen"],
        title="t",
        plain_summary="s",
        what_to_do="Ask first.",
        checker="test",
        evidence=[Evidence(source="DDInter", text="x", version="1")],
    )
    assert f.drugs == ["ibuprofen", "warfarin"]
    assert f.what_to_do.endswith(SAFETY_FOOTER)
    assert len(f.id) == 12


def test_finding_requires_evidence():
    with pytest.raises(ValueError):
        Finding(
            kind="interaction",
            severity="major",
            drugs=["a"],
            title="t",
            plain_summary="s",
            what_to_do="w",
            checker="c",
            evidence=[],
        )


# --- api signatures (C depends on these) --------------------------------------

EXPECTED_API = {
    "read_bottle": ["image_bytes", "mime_type"],
    "check": ["meds", "patient"],
    "simplify": ["report", "language"],
    "quiz": ["report", "n"],
    "clinic_scan": ["limit"],
    "clinic_patient": ["patient_id"],
    "load_scenario": ["name"],
    "list_scenarios": [],
}


@pytest.mark.parametrize("name,params", EXPECTED_API.items())
def test_api_signatures(name, params):
    assert list(inspect.signature(getattr(api, name)).parameters) == params


def test_owned_module_entry_points_exist():
    """A and B may change bodies, never these names (api.py calls them)."""
    from pillwise import audit, evidence, explain, extract, normalize, orchestrator
    from pillwise.agents import clinic

    for mod, names in [
        (extract, ["extract_from_image"]),
        (normalize, ["normalize_all", "normalize_one"]),
        (evidence, ["attach_label_evidence", "fetch_label"]),
        (explain, ["pill_cards", "simplify", "make_quiz"]),
        (orchestrator, ["build_report"]),
        (audit, ["log_event", "log_report", "recent_events"]),
        (checks, ["run_all", "get_checkers"]),
        (clinic, ["scan", "patient_report"]),
    ]:
        for n in names:
            assert callable(getattr(mod, n)), f"{mod.__name__}.{n} missing"


def test_checkers_follow_protocol():
    for c in checks.get_checkers():
        assert isinstance(c, Checker)
        assert c.name and c.version


def test_run_all_never_raises():
    result = checks.run_all([Medication(name="warfarin", ingredients=["warfarin"])], PatientContext(age=80))
    assert isinstance(result, CheckResult)


# --- mock mode end to end (the UI's baseline) ---------------------------------


def test_mock_pipeline_end_to_end(mock_mode):
    meds = api.read_bottle(b"fake", "image/jpeg")
    assert meds and all(isinstance(m, Medication) for m in meds)
    report = api.check(meds, PatientContext(age=75))
    assert isinstance(report, Report) and report.is_mock
    assert report.findings and report.pill_cards
    assert api.simplify(report, "es").sections
    assert api.quiz(report)
    assert api.clinic_scan(5)
    assert isinstance(api.clinic_patient("mock-001"), Report)


def test_mock_unknown_drug_is_unchecked_not_safe(mock_mode):
    report = api.check([Medication(name="Totally Made Up 5 mg")], PatientContext(age=70))
    assert report.unchecked == ["Totally Made Up 5 mg"]


# --- data files are valid ------------------------------------------------------


def test_scenarios_load():
    names = api.list_scenarios()
    assert {"safe_otc", "warfarin_nsaid", "beers_sleep_aid"} <= set(names)
    for n in names:
        meds, patient = api.load_scenario(n)
        assert meds and patient.age


def test_seed_json_shapes():
    s = get_settings()
    beers = json.loads(s.beers_path.read_text())
    assert {"source", "tags", "drugs", "combos"} <= set(beers)
    onc = json.loads(s.onc_path.read_text())
    assert all({"group_a", "group_b", "summary"} <= set(r) for r in onc["rules"])


def test_mocks_are_marked():
    assert mocks.MOCK_VERSION == "MOCK"


def test_mock_check_result_matches_run_all_shape():
    meds, patient = api.load_scenario("warfarin_nsaid")
    result = mocks.mock_check_result(meds, patient)
    assert isinstance(result, CheckResult)
    assert result.findings and all(f.evidence for f in result.findings)
    assert result.versions == {"mock": mocks.MOCK_VERSION}

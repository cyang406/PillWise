"""ONC high-priority checker."""

import json

import pytest

from pillwise.checks.onc import ONCChecker
from pillwise.schemas import Medication, PatientContext


def med(name):
    return Medication(name=name, ingredients=[name.lower()])


@pytest.fixture
def onc_file(tmp_path):
    path = tmp_path / "onc.json"
    path.write_text(
        json.dumps(
            {
                "source": {"citation": "test", "url": "https://example.org", "version": "2012"},
                "rules": [
                    {"id": "ok", "verified": True, "group_a": ["a"], "group_b": ["b"], "summary": "S."},
                    {"id": "seed", "verified": False, "group_a": ["c"], "group_b": ["d"], "summary": "T."},
                ],
            }
        )
    )
    return path


def test_real_data_statin_pair(monkeypatch):
    monkeypatch.setenv("PILLWISE_MOCK", "0")
    [f] = ONCChecker().check([med("Clarithromycin"), med("Simvastatin")], PatientContext())
    assert f.severity == "major" and f.kind == "interaction"
    assert f.drugs == ["clarithromycin", "simvastatin"]
    assert f.evidence[0].source == "ONC" and f.evidence[0].version == "2012"


def test_verified_rule_runs_in_real_mode(onc_file, monkeypatch):
    monkeypatch.setenv("PILLWISE_MOCK", "0")
    [f] = ONCChecker(path=onc_file).check([med("B"), med("A"), med("C")], PatientContext())
    assert f.drugs == ["a", "b"] and f.evidence[0].version == "2012"


def test_unverified_rules_only_in_mock(onc_file, monkeypatch):
    meds = [med("C"), med("D")]
    monkeypatch.setenv("PILLWISE_MOCK", "0")
    assert ONCChecker(path=onc_file).check(meds, PatientContext()) == []
    monkeypatch.setenv("PILLWISE_MOCK", "1")
    [f] = ONCChecker(path=onc_file).check(meds, PatientContext())
    assert "unverified" in f.evidence[0].version

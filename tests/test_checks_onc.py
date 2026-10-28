"""ONC high-priority checker."""

import json

from pillwise.checks.onc import ONCChecker
from pillwise.schemas import Medication, PatientContext


def med(name):
    return Medication(name=name, ingredients=[name.lower()])


def test_unverified_rules_only_in_mock(monkeypatch):
    meds = [med("Clarithromycin"), med("Simvastatin")]
    monkeypatch.setenv("PILLWISE_MOCK", "0")
    assert ONCChecker().check(meds, PatientContext()) == []
    monkeypatch.setenv("PILLWISE_MOCK", "1")
    [f] = ONCChecker().check(meds, PatientContext())
    assert f.severity == "major" and f.kind == "interaction"
    assert f.drugs == ["clarithromycin", "simvastatin"]
    assert f.evidence[0].source == "ONC" and "unverified" in f.evidence[0].version


def test_verified_rule_runs_in_real_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("PILLWISE_MOCK", "0")
    path = tmp_path / "onc.json"
    path.write_text(
        json.dumps(
            {
                "source": {"citation": "test", "url": "https://example.org", "version": "2012"},
                "rules": [{"id": "x", "verified": True, "group_a": ["a"], "group_b": ["b"], "summary": "S."}],
            }
        )
    )
    [f] = ONCChecker(path=path).check([med("B"), med("A"), med("C")], PatientContext())
    assert f.drugs == ["a", "b"] and f.evidence[0].version == "2012"

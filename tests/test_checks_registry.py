"""run_all: errors, unmatched, merge of ONC + DDInter findings."""

import sys
from pathlib import Path

import pytest

from pillwise import checks
from pillwise.schemas import Medication, PatientContext

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from load_ddinter import load  # noqa: E402


def med(name):
    return Medication(name=name, ingredients=[name.lower()])


@pytest.fixture
def dd_db(tmp_path, monkeypatch):
    db = tmp_path / "dd.sqlite"
    load([ROOT / "tests" / "fixtures" / "ddinter_sample.csv"], db)
    monkeypatch.setenv("PILLWISE_DDINTER_DB", str(db))
    monkeypatch.setenv("PILLWISE_MOCK", "0")
    return db


def test_unmatched_lists_unknown_meds(dd_db):
    res = checks.run_all([med("Warfarin"), med("Ibuprofen"), med("Mysterium")], PatientContext(age=70))
    assert res.unmatched == ["Mysterium"]
    assert res.errors == {}
    assert set(res.versions) == {"ddinter", "onc", "beers"}
    assert any(f.kind == "interaction" and f.severity == "major" for f in res.findings)


def test_missing_ddinter_is_an_error_and_unmatched(tmp_path, monkeypatch):
    monkeypatch.setenv("PILLWISE_DDINTER_DB", str(tmp_path / "missing.sqlite"))
    res = checks.run_all([med("Lisinopril"), med("Diphenhydramine")], PatientContext(age=70))
    assert "ddinter" in res.errors
    assert res.unmatched == ["Lisinopril"]  # only DDInter would know it: could not check, never safe

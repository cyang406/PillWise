"""DDInter checker against the hand-made fixture (not clinical data)."""

import sys
from pathlib import Path

import pytest

from pillwise.checks.ddinter import DDInterChecker
from pillwise.schemas import SAFETY_FOOTER, Medication, PatientContext

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from load_ddinter import load  # noqa: E402


@pytest.fixture
def checker(tmp_path):
    db = tmp_path / "dd.sqlite"
    load([ROOT / "tests" / "fixtures" / "ddinter_sample.csv"], db)
    return DDInterChecker(db_path=db)


def med(name, *ingredients):
    return Medication(name=name, ingredients=list(ingredients))


def test_major_pair_found_in_either_order(checker):
    for meds in (
        [med("Advil", "ibuprofen"), med("Coumadin", "warfarin")],
        [med("Coumadin", "warfarin"), med("Advil", "ibuprofen")],
    ):
        [f] = checker.check(meds, PatientContext(age=70))
        assert f.kind == "interaction"
        assert f.severity == "major"
        assert f.drugs == ["ibuprofen", "warfarin"]
        assert f.checker == "ddinter"
        assert f.evidence[0].source == "DDInter" and f.evidence[0].version == "2.0"
        assert f.what_to_do.endswith(SAFETY_FOOTER)


def test_multi_ingredient_and_no_self_pairs(checker):
    meds = [med("Combo", "ibuprofen", "diphenhydramine"), med("Coumadin", "warfarin"), med("Ditropan", "oxybutynin")]
    found = {tuple(f.drugs): f.severity for f in checker.check(meds, PatientContext())}
    assert found == {("ibuprofen", "warfarin"): "major", ("diphenhydramine", "oxybutynin"): "moderate"}


def test_unknown_drugs_give_nothing_but_are_not_known(checker):
    meds = [med("Zyrtec", "cetirizine"), med("Coumadin", "warfarin")]
    assert checker.check(meds, PatientContext()) == []
    assert checker.known_names({"cetirizine", "warfarin"}) == {"warfarin"}


def test_missing_db_raises_not_empty(tmp_path):
    with pytest.raises(FileNotFoundError):
        DDInterChecker(db_path=tmp_path / "nope.sqlite").check([med("a", "a"), med("b", "b")], PatientContext())


def test_deterministic(checker):
    meds = [med("Coumadin", "warfarin"), med("Tylenol", "acetaminophen"), med("Advil", "ibuprofen")]
    assert checker.check(meds, PatientContext()) == checker.check(meds, PatientContext())

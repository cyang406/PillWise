"""A3: RxNorm normalization from recorded responses (tests/fixtures/pipeline/cache/rxnorm)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pillwise import normalize
from pillwise.schemas import Medication

CACHE = Path(__file__).parent / "fixtures" / "pipeline" / "cache"


@pytest.fixture(autouse=True)
def offline_fixtures(monkeypatch):
    monkeypatch.setenv("PILLWISE_CACHE_DIR", str(CACHE))
    monkeypatch.setenv("PILLWISE_OFFLINE", "1")


# Name contract with B (docs/PARALLEL_AB.md): lower-case RxNorm IN names.
GOLDEN = [
    ("Warfarin", "5 mg", ["warfarin"]),
    ("Ibuprofen", "200 mg", ["ibuprofen"]),
    ("Advil", None, ["ibuprofen"]),
    ("Acetaminophen", "500 mg", ["acetaminophen"]),
    ("Loratadine", "10 mg", ["loratadine"]),
    ("Diphenhydramine", "25 mg", ["diphenhydramine"]),
    ("Oxybutynin", "5 mg", ["oxybutynin"]),
    ("Lisinopril", "10 mg", ["lisinopril"]),
]


@pytest.mark.parametrize("name,strength,expected", GOLDEN)
def test_golden_names(name, strength, expected):
    med = normalize.normalize_one(Medication(name=name, strength=strength, directions="Take 1 daily."))
    assert med.rxcui
    assert med.ingredients == expected
    assert med.match_names == expected
    assert med.directions == "Take 1 daily."  # untouched


def test_unknown_drug_keeps_existing_ingredients():
    med = Medication(name="Zzzfakedrug", ingredients=["zzzfake"])
    out = normalize.normalize_one(med)
    assert out.rxcui is None
    assert out.ingredients == ["zzzfake"]


def test_cache_miss_offline_does_not_raise():
    out = normalize.normalize_one(Medication(name="Never Cached Drug"))
    assert out.rxcui is None and out.ingredients == []


def test_normalize_all_keeps_order():
    names = [m.name for m in normalize.normalize_all([Medication(name="Lisinopril"), Medication(name="Warfarin")])]
    assert names == ["Lisinopril", "Warfarin"]

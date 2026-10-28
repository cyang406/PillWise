"""Loader smoke test (B may extend)."""

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from load_ddinter import load  # noqa: E402


def test_load_fixture(tmp_path):
    db = tmp_path / "dd.sqlite"
    n = load([ROOT / "tests" / "fixtures" / "ddinter_sample.csv"], db)
    assert n == 4
    row = (
        sqlite3.connect(db)
        .execute("SELECT level FROM interactions WHERE drug_a='ibuprofen' AND drug_b='warfarin'")
        .fetchone()
    )
    assert row == ("major",)

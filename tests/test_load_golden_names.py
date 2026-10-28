"""Golden name list (docs/PARALLEL_AB.md, seam 1): every scenario ingredient must be in the DDInter DB.

A's normalize returns lower-case RxNorm IN names; this proves B's data uses the same spelling.
Skipped until `make ddinter` has built data/ddinter.sqlite.
"""

import json
import sqlite3

import pytest

from pillwise.config import get_settings

GOLDEN = ["warfarin", "ibuprofen", "acetaminophen", "loratadine", "diphenhydramine", "oxybutynin", "lisinopril"]


def test_scenarios_use_only_golden_names():
    names = set()
    for path in get_settings().scenarios_dir.glob("*.json"):
        for m in json.loads(path.read_text(encoding="utf-8"))["meds"]:
            names.update(m["ingredients"])
    assert names <= set(GOLDEN)


def test_golden_names_in_ddinter_db():
    db = get_settings().ddinter_db
    if not db.exists():
        pytest.skip("data/ddinter.sqlite not built yet (make ddinter)")
    con = sqlite3.connect(db)
    missing = [
        n
        for n in GOLDEN
        if not con.execute("SELECT 1 FROM interactions WHERE drug_a=? OR drug_b=? LIMIT 1", (n, n)).fetchone()
    ]
    assert missing == [], f"not in DDInter under the RxNorm IN name: {missing}"

"""Scenario tests. SHARED.

Mock mode must always pass. Real mode is the definition of "MVP done"
(checkpoint 2); it is skipped until DDInter is loaded and the pipeline exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from pillwise import api
from pillwise.config import get_settings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from run_scenarios import evaluate  # noqa: E402

SCENARIOS = api.list_scenarios()


def _expect(name):
    return json.loads((get_settings().scenarios_dir / f"{name}.json").read_text())["expect"]


@pytest.mark.parametrize("name", SCENARIOS)
def test_scenario_mock(name, mock_mode):
    meds, patient = api.load_scenario(name)
    assert evaluate(api.check(meds, patient), _expect(name)) == []


@pytest.mark.parametrize("name", SCENARIOS)
def test_scenario_real(name, real_mode):
    if not get_settings().ddinter_db.exists():
        pytest.skip("data/ddinter.sqlite not built yet (B: scripts/load_ddinter.py)")
    meds, patient = api.load_scenario(name)
    try:
        report = api.check(meds, patient)
    except NotImplementedError as exc:
        pytest.skip(f"pipeline not implemented yet: {exc}")
    assert evaluate(report, _expect(name)) == []

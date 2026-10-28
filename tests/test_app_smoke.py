"""UI smoke tests in mock mode (owner: C; extend freely)."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from pillwise import api  # noqa: E402

APP = Path(__file__).resolve().parent.parent / "app"


def test_home_renders(mock_mode):
    at = AppTest.from_file(str(APP / "Home.py")).run(timeout=30)
    assert not at.exception
    assert at.title[0].value.endswith("PillWise")


def test_results_render_mock_report(mock_mode):
    meds, patient = api.load_scenario("warfarin_nsaid")
    report = api.check(meds, patient)
    at = AppTest.from_file(str(APP / "pages" / "1_Results.py"))
    at.session_state["report"] = report
    at.run(timeout=30)
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "warfarin" in text.lower()

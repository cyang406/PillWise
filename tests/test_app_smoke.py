"""UI smoke tests in mock mode (owner: C; extend freely)."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from pillwise import api  # noqa: E402
from pillwise.schemas import Evidence, Finding, PillCard, Report  # noqa: E402

APP = Path(__file__).resolve().parent.parent / "app"
RESULTS = "pages/1_Results.py"


def results_page(report: Report) -> AppTest:
    """Open Results the way the app does: start at Home, then switch page (page links need Home as main)."""
    at = AppTest.from_file(str(APP / "Home.py")).run(timeout=30)
    at.session_state["report"] = report
    return at.switch_page(RESULTS).run(timeout=30)


def text_of(at: AppTest) -> str:
    return " ".join(m.value for m in [*at.markdown, *at.error, *at.caption, *at.success, *at.warning])


def button(at: AppTest, label: str):
    return next(b for b in at.button if b.label == label)


def test_home_renders(mock_mode):
    at = AppTest.from_file(str(APP / "Home.py")).run(timeout=30)
    assert not at.exception
    assert at.title[0].value.endswith("PillWise")
    assert "Check each name against the bottle" in text_of(at)


def test_scenario_confirm_goes_to_results(mock_mode):
    at = AppTest.from_file(str(APP / "Home.py")).run(timeout=30)
    at.selectbox[0].select("warfarin_nsaid").run(timeout=30)
    button(at, "Load scenario").click().run(timeout=30)
    assert len(at.session_state["meds"]) == 3
    button(at, "Confirm and check").click().run(timeout=30)
    assert not at.exception
    report = at.session_state["report"]
    assert report is not None and all(m.confirmed for m in report.meds)
    assert report.patient.age == 72


def test_results_render_mock_report(mock_mode):
    meds, patient = api.load_scenario("warfarin_nsaid")
    at = results_page(api.check(meds, patient))
    assert not at.exception
    assert "warfarin" in text_of(at).lower()


def _report(**kw) -> Report:
    ev = Evidence(source="DDInter", text="Listed pair.", version="2.0")
    base = dict(
        meds=[],
        findings=[
            Finding(
                kind="interaction",
                severity="unknown",
                drugs=["acetaminophen", "loratadine"],
                title="Acetaminophen + loratadine",
                plain_summary="Listed together.",
                what_to_do="Mention it.",
                evidence=[ev],
                checker="ddinter",
            )
        ],
    )
    base.update(kw)
    return Report(**base)


def test_unchecked_box_never_says_safe(mock_mode):
    at = results_page(_report(unchecked=["Mysterol", "(checker 'ddinter' failed: no db)"]))
    assert not at.exception
    errors = " ".join(e.value for e in at.error)
    assert "Mysterol" in errors and "does NOT mean they are safe" in errors
    assert "Some safety checks did not run" in errors


def test_unknown_severity_is_labelled_not_rated(mock_mode):
    at = results_page(_report())
    assert "Not rated" in text_of(at)


def test_pill_card_without_directions_says_so(mock_mode):
    card = PillCard(med_key="ibuprofen", name="Ibuprofen", what_it_is_for="Pain reliever.", how_to_take=None)
    at = results_page(_report(pill_cards=[card]))
    assert "We could not read directions on your label" in text_of(at)

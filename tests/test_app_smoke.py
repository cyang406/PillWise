"""UI tests for the one-page app (owner: C). Mock mode unless marked real."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP))
import components  # noqa: E402
from pillwise import api  # noqa: E402
from pillwise.schemas import Evidence, Finding, PillCard, Report  # noqa: E402

HOME = str(APP / "Home.py")


def text_of(at: AppTest) -> str:
    parts = [*at.markdown, *at.error, *at.caption, *at.success, *at.warning, *at.info, *at.header, *at.subheader]
    return " ".join(str(m.value) for m in parts) + " " + " ".join(c.label for c in at.checkbox)


def headers(at: AppTest) -> list[str]:
    return [h.value for h in at.header]


def button(at: AppTest, label: str):
    return next(b for b in at.button if b.label == label)


def load_sample(at: AppTest, scenario: str) -> AppTest:
    button(at, scenario.replace("_", " ").capitalize()).click().run(timeout=60)
    return at


def checked(scenario: str) -> AppTest:
    at = load_sample(AppTest.from_file(HOME).run(timeout=60), scenario)
    button(at, "Check my list").click().run(timeout=60)
    assert not at.exception
    return at


def with_report(report: Report) -> AppTest:
    """Results for a hand-made report: an empty list with a matching signature."""
    at = AppTest.from_file(HOME)
    at.session_state["report"] = report
    at.session_state["report_sig"] = components.list_signature([], None)
    return at.run(timeout=60)


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


def test_home_renders_without_results(mock_mode):
    at = AppTest.from_file(HOME).run(timeout=60)
    assert not at.exception
    assert headers(at) == ["Your medicines"]


def test_web_has_no_camera_mobile_has_it(mock_mode):
    assert not AppTest.from_file(HOME).run(timeout=60).get("camera_input")
    at = AppTest.from_file(HOME)
    at.query_params["app"] = "mobile"
    assert at.run(timeout=60).get("camera_input")


def test_sample_check_shows_everything_on_one_page(mock_mode):
    at = checked("warfarin_nsaid")
    report = at.session_state["report"]
    assert all(m.confirmed for m in report.meds) and report.patient.age == 72
    text = text_of(at)
    _, head, _ = components.verdict(report)
    assert head in text  # verdict first
    assert "Take this to your pharmacist" in text
    assert components.questions(report)[0][1] in text  # questions to ask


def test_results_hide_when_the_list_changes(mock_mode):
    at = checked("warfarin_nsaid")
    next(b for b in at.button if b.label == "Remove").click().run(timeout=60)
    assert "Your list changed since the last check" in text_of(at)
    assert "What we found" not in headers(at)


def test_typed_unknown_medicine_is_could_not_check(mock_mode):
    at = AppTest.from_file(HOME).run(timeout=60)
    at.text_input[0].set_value("Mysterol")
    button(at, "Add to my list").click().run(timeout=60)
    button(at, "Check my list").click().run(timeout=60)
    errors = " ".join(e.value for e in at.error)
    assert "Mysterol" in errors and "does NOT mean they are safe" in errors


def test_unchecked_box_never_says_safe(mock_mode):
    at = with_report(_report(unchecked=["Mysterol", "(checker 'ddinter' failed: no db)"]))
    errors = " ".join(e.value for e in at.error)
    assert "Mysterol" in errors and "does NOT mean they are safe" in errors
    assert "Some safety checks did not run" in errors


def test_not_rated_and_missing_directions(mock_mode):
    card = PillCard(med_key="ibuprofen", name="Ibuprofen", what_it_is_for="Pain reliever.", how_to_take=None)
    text = text_of(with_report(_report(pill_cards=[card])))
    assert "Not rated" in text
    assert "We could not read directions on your label" in text


def test_trust_panel_lists_sources_and_labels(mock_mode):
    label = Evidence(source="openFDA", text="Quote.", version="label 2026-06-29", url="https://dailymed.example/x")
    report = _report(data_versions={"ddinter": "2.0", "beers": "2023"})
    report.findings[0].evidence.append(label)
    text = text_of(with_report(report))
    assert "DDInter drug-interaction database: version 2.0" in text
    assert "DailyMed label 2026-06-29" in text
    assert report.id in text


def test_quiz_and_llm_called_once_per_report(mock_mode, monkeypatch):
    calls = []
    real = api.simplify
    monkeypatch.setattr(api, "simplify", lambda r, lang="en": calls.append(lang) or real(r, lang))
    at = checked("warfarin_nsaid")
    quiz = at.session_state["quiz_questions"]
    for r, q in zip(at.radio, quiz, strict=True):  # answer everything right
        r.set_value(q.options[q.correct_index])
    button(at, "Check my answers").click().run(timeout=60)
    assert f"You got {len(quiz)} of {len(quiz)}" in text_of(at)
    assert calls == ["en"]  # quiz clicks reran the page without calling the LLM again


def test_empty_report_never_says_safe():
    meds, patient = api.load_scenario("warfarin_nsaid")
    severity, _, sub = components.verdict(Report(meds=meds, patient=patient))
    assert severity is None and "does not mean your list is safe" in sub


@pytest.mark.parametrize("scenario", api.list_scenarios())
def test_one_page_real_offline(real_mode, scenario, tmp_path, monkeypatch):
    """Real pipeline from data/cache (no network); needs B's DDInter DB, like the integrator's smoke test."""
    from pillwise.config import get_settings

    if not get_settings().ddinter_db.exists():
        pytest.skip("data/ddinter.sqlite not built (make ddinter)")
    monkeypatch.setenv("PILLWISE_AUDIT_DB", str(tmp_path / "audit.sqlite"))
    monkeypatch.setenv("PILLWISE_MODEL_MAIN", "gpt-4.1")  # the cache was warmed with these
    monkeypatch.setenv("PILLWISE_MODEL_FAST", "gpt-4.1-mini")
    at = checked(scenario)
    text = text_of(at)
    assert not at.session_state["report"].is_mock and "mock mode" not in text
    assert "Some safety checks did not run" not in text
    assert "**Audit log** (" in " ".join(str(m.value) for m in at.markdown)
    assert any("what the label says" in e.label for e in at.expander)  # pregnancy / children quotes
    if scenario == "warfarin_nsaid":
        assert "Serious" in text
        at.text_input[-1].set_value("Aleve")
        button(at, "Check against my list").click().run(timeout=60)
        assert "naproxen + warfarin" in text_of(at).lower()

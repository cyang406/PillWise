"""A10: teach-back quiz. Fake LLM."""

from __future__ import annotations

from pillwise import api, explain, llm, mocks
from pillwise.schemas import SAFETY_FOOTER, Evidence, Finding, Report


def _report() -> Report:
    meds, patient = api.load_scenario("warfarin_nsaid")
    return mocks.mock_report(meds, patient)


def _fake(question="What can happen?", correct="You may bleed more.", wrong=("You sleep better.", "Nothing changes.")):
    def f(prompt, output_type, **kw):
        return output_type(question=question, correct=correct, wrong=list(wrong))

    return f


def test_correct_answer_is_placed_by_code(monkeypatch):
    monkeypatch.setattr(llm, "structured", _fake())
    report = _report()
    qs = explain.make_quiz(report, n=3)
    assert qs and len(qs) <= 3
    for q in qs:
        assert q.options[q.correct_index] == "You may bleed more."
        assert len(q.options) == 3
        f = next(f for f in report.findings if f.id == q.source_id)
        assert q.explanation == f"{f.plain_summary} {SAFETY_FOOTER}"
    assert qs[0].source_id == report.sorted_findings()[0].id  # most serious first


def test_same_report_same_quiz(monkeypatch):
    monkeypatch.setattr(llm, "structured", _fake())
    assert explain.make_quiz(_report()) == explain.make_quiz(_report())


def test_dosing_in_answers_falls_back(monkeypatch):
    monkeypatch.setattr(llm, "structured", _fake(correct="Take 1 tablet instead."))
    q = explain.make_quiz(_report(), n=1)[0]
    assert q.options == explain.FALLBACK_OPTIONS and q.correct_index == 1


def test_llm_failure_falls_back(monkeypatch):
    def boom(*a, **kw):
        raise llm.LLMError("down")

    monkeypatch.setattr(llm, "structured", boom)
    q = explain.make_quiz(_report(), n=1)[0]
    assert q.options[q.correct_index] == "Ask my pharmacist or doctor first"


def test_unknown_findings_are_skipped(monkeypatch):
    monkeypatch.setattr(llm, "structured", _fake())
    unknown = Finding(
        kind="interaction",
        severity="unknown",
        drugs=["a", "b"],
        title="Unknown",
        plain_summary="?",
        what_to_do="?",
        evidence=[Evidence(source="DDInter", text="Unknown", version="2.0")],
        checker="ddinter",
    )
    assert explain.make_quiz(Report(meds=[], findings=[unknown])) == []


def test_same_lesson_is_asked_once(monkeypatch):
    monkeypatch.setattr(llm, "structured", _fake())

    def finding(drugs):
        return Finding(
            kind="interaction",
            severity="moderate",
            drugs=drugs,
            title=f"Moderate: {' + '.join(drugs)}",
            plain_summary="These medicines can change how each other work.",
            what_to_do="Ask.",
            evidence=[Evidence(source="DDInter", text="Moderate", version="2.0")],
            checker="ddinter",
        )

    report = Report(meds=[], findings=[finding(["a", "b"]), finding(["a", "c"])])
    assert len(explain.make_quiz(report)) == 1

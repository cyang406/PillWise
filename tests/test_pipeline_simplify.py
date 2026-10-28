"""A8: plain-language summary (English). Fake LLM; textstat is real."""

from __future__ import annotations

import pytest

from pillwise import api, explain, llm, mocks
from pillwise.schemas import SAFETY_FOOTER, PatientContext, Report

HARD = (
    "Concomitant administration of these pharmacological agents substantially potentiates "
    "the probability of clinically significant hemorrhagic complications necessitating intervention."
)
EASY = "Taking these two together can make you bleed more. Ask before you change them."


def _report(name="warfarin_nsaid") -> Report:
    meds, patient = api.load_scenario(name)
    return mocks.mock_report(meds, patient).model_copy(update={"is_mock": False})


def test_sections_follow_findings_with_code_set_severity_and_footer(monkeypatch):
    monkeypatch.setattr(llm, "text", lambda prompt, **kw: EASY)
    report = _report()
    s = explain.simplify(report, "en")
    finding_sections = [x for x in s.sections if x.source_ids]
    assert [x.source_ids[0] for x in finding_sections] == [f.id for f in report.sorted_findings()]
    for sec, f in zip(finding_sections, report.sorted_findings(), strict=True):
        assert sec.title == f"{explain.SEVERITY_WORDS[f.severity]}: {f.title}"
        assert sec.text.endswith(SAFETY_FOOTER)
        assert sec.text.count(SAFETY_FOOTER) == 1
    assert s.language == "en" and s.reading_grade is not None


def test_rewrites_until_easy_enough(monkeypatch):
    replies = iter([HARD, EASY])
    calls = []

    def fake(prompt, **kw):
        calls.append(prompt)
        return next(replies)

    monkeypatch.setattr(llm, "text", fake)
    out = explain.plain_rewrite(HARD, target=6.0)
    assert out == EASY
    assert len(calls) == 2 and "still at grade" in calls[1]


def test_easy_text_is_not_sent_to_llm(monkeypatch):
    monkeypatch.setattr(llm, "text", lambda *a, **kw: pytest.fail("no rewrite needed"))
    assert explain.plain_rewrite("Ask your doctor.", target=6.0) == "Ask your doctor."


def test_rewrite_adding_a_dose_is_rejected(monkeypatch):
    monkeypatch.setattr(llm, "text", lambda prompt, **kw: "Take 2 tablets less. You may bleed.")
    assert explain.plain_rewrite(HARD, target=6.0) == HARD


def test_llm_failure_keeps_checker_text(monkeypatch):
    def boom(*a, **kw):
        raise llm.LLMError("down")

    monkeypatch.setattr(llm, "text", boom)
    report = _report()
    s = explain.simplify(report)
    f = report.sorted_findings()[0]
    assert f.plain_summary in s.sections[0].text


def test_no_findings_is_not_called_safe(monkeypatch):
    monkeypatch.setattr(llm, "text", lambda *a, **kw: pytest.fail("nothing to rewrite"))
    s = explain.simplify(Report(meds=[], patient=PatientContext(age=70)))
    assert s.sections[0].title == "No problems found"
    assert "does not prove they are safe" in s.sections[0].text


def test_unchecked_meds_get_their_own_section(monkeypatch):
    monkeypatch.setattr(llm, "text", lambda prompt, **kw: EASY)
    report = _report().model_copy(update={"unchecked": ["Zzzfakedrug", "(checker 'onc' failed: boom)"]})
    last = explain.simplify(report).sections[-1]
    assert last.title == "Could not check"
    assert "Zzzfakedrug" in last.text and "does not mean they are safe" in last.text
    assert "did not run" in last.text and "boom" not in last.text


def test_translation_not_built_yet():
    with pytest.raises(NotImplementedError):
        explain.simplify(_report(), "es")


def test_rewrite_dropping_a_drug_name_is_rejected_then_retried(monkeypatch):
    source = HARD + " Warfarin users are at particular risk."
    calls = []
    replies = iter(
        ["This medicine can make you bleed more. Ask first.", "Warfarin can make you bleed more. Ask first."]
    )

    def fake(prompt, **kw):
        calls.append(prompt)
        return next(replies)

    monkeypatch.setattr(llm, "text", fake)
    out = explain.plain_rewrite(source, 6.0, {"warfarin", "ibuprofen"})
    assert out.startswith("Warfarin")
    assert "keep them: warfarin" in calls[1]


def test_rewrite_adding_another_drug_is_rejected(monkeypatch):
    monkeypatch.setattr(llm, "text", lambda prompt, **kw: "Ibuprofen and warfarin can make you bleed. Ask first.")
    source = HARD + " Warfarin users are at particular risk."
    assert explain.plain_rewrite(source, 6.0, {"warfarin", "ibuprofen"}) == source


def test_report_names_cover_meds_and_findings():
    names = explain.report_names(_report())
    assert {"warfarin", "ibuprofen", "acetaminophen"} <= names

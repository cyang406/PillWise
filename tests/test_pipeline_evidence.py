"""A4: openFDA label evidence. Recorded labels (tests/fixtures/pipeline/cache/openfda), fake LLM."""

from __future__ import annotations

from pathlib import Path

import pytest

from pillwise import evidence, llm
from pillwise.schemas import Evidence, Finding

CACHE = Path(__file__).parent / "fixtures" / "pipeline" / "cache"


@pytest.fixture(autouse=True)
def offline_fixtures(monkeypatch):
    monkeypatch.setenv("PILLWISE_CACHE_DIR", str(CACHE))
    monkeypatch.setenv("PILLWISE_OFFLINE", "1")


def _finding() -> Finding:
    return Finding(
        kind="interaction",
        severity="major",
        drugs=["warfarin", "ibuprofen"],
        title="Bleeding risk: warfarin + ibuprofen",
        plain_summary="Taking these together can raise the chance of serious bleeding.",
        what_to_do="Do not start or stop either medicine on your own.",
        evidence=[Evidence(source="DDInter", text="Major", version="2.0")],
        checker="ddinter",
    )


def _corpus(prompt: str) -> str:
    return prompt.split("LABEL TEXT:\n", 1)[1]


def _quote_llm(pick):
    def fake(prompt, output_type, **kw):
        return output_type(quote=pick(_corpus(prompt)))

    return fake


def test_fetch_label_picks_single_ingredient_label():
    label = evidence.fetch_label(["diphenhydramine"])
    names = " ".join(label["openfda"]["generic_name"]).lower()
    assert "acetaminophen" not in names
    assert evidence.label_version(label).startswith("label 20")
    assert evidence.label_url(label).startswith("https://dailymed.nlm.nih.gov/")


def test_verify_quote():
    src = "Stomach bleeding warning: This product contains an NSAID,\nwhich may cause severe stomach bleeding."
    assert (
        evidence.verify_quote("This product contains an NSAID, which may", src)
        == "This product contains an NSAID,\nwhich may"
    )
    assert evidence.verify_quote("This product is perfectly safe with warfarin.", src) is None
    assert evidence.verify_quote("bleeding", src) is None  # too short to be a real quote
    assert evidence.verify_quote(None, src) is None


def test_real_quote_is_attached_and_finding_unchanged(monkeypatch):
    def first_bleeding_sentence(corpus):
        i = corpus.lower().find("bleed")
        start = corpus.rfind(".", 0, i) + 1
        end = corpus.find(".", i) + 1
        return corpus[start:end].strip()

    monkeypatch.setattr(llm, "structured", _quote_llm(first_bleeding_sentence))
    f = _finding()
    [g] = evidence.attach_label_evidence([f], [])
    fda = [e for e in g.evidence if e.source == "openFDA"]
    assert fda, "expected at least one openFDA quote"
    for e in fda:
        for drug in g.drugs:
            if e.text in evidence._label_corpus(evidence.fetch_label([drug])):
                break
        else:
            pytest.fail(f"quote is not a substring of any label: {e.text!r}")
        assert e.version.startswith("label ") and e.url
    assert (g.kind, g.severity, g.drugs, g.id) == (f.kind, f.severity, f.drugs, f.id)
    assert g.evidence[0].source == "DDInter"  # checker evidence kept, first


def test_fabricated_quote_is_dropped(monkeypatch):
    monkeypatch.setattr(llm, "structured", _quote_llm(lambda c: "Warfarin and ibuprofen are completely safe together."))
    [g] = evidence.attach_label_evidence([_finding()], [])
    assert [e.source for e in g.evidence] == ["DDInter"]


def test_llm_failure_keeps_finding(monkeypatch):
    def boom(*a, **kw):
        raise llm.LLMError("down")

    monkeypatch.setattr(llm, "structured", boom)
    f = _finding()
    assert evidence.attach_label_evidence([f], []) == [f]


@pytest.mark.parametrize(
    "drug,section",
    [
        ("oxybutynin", "geriatric_use"),
        ("diphenhydramine", "when_using"),
        ("ibuprofen", "ask_doctor"),
        ("warfarin", "contraindications"),
    ],
)
def test_older_adult_and_otc_sections_are_kept(drug, section):
    label = evidence.fetch_label([drug])
    assert evidence.section_text(label, section)
    assert evidence.section_text(label, section) in evidence._label_corpus(label)


def test_dosage_section_is_never_kept():
    for drug in ("ibuprofen", "warfarin"):
        assert "dosage_and_administration" not in evidence.fetch_label([drug])

"""A5: pill cards. Recorded labels, fake LLM."""

from __future__ import annotations

from pathlib import Path

import pytest

from pillwise import evidence, explain, llm
from pillwise.schemas import Medication

CACHE = Path(__file__).parent / "fixtures" / "pipeline" / "cache"
DIRECTIONS = "Take 1 tablet every 4 to 6 hours while symptoms persist."


@pytest.fixture(autouse=True)
def offline_fixtures(monkeypatch):
    monkeypatch.setenv("PILLWISE_CACHE_DIR", str(CACHE))
    monkeypatch.setenv("PILLWISE_OFFLINE", "1")


def _ibuprofen() -> Medication:
    return Medication(name="Advil", ingredients=["ibuprofen"], generic_name="ibuprofen", directions=DIRECTIONS)


def test_card_copies_directions_and_uses_llm_text(monkeypatch):
    monkeypatch.setattr(
        llm,
        "structured",
        lambda prompt, t, **kw: t(
            what_it_is_for="Eases pain and fever.", watch_for=["Stomach bleeding", " ", "a", "b", "c"]
        ),
    )
    [card] = explain.pill_cards([_ibuprofen()])
    assert card.how_to_take == DIRECTIONS
    assert card.med_key == "ibuprofen"
    assert card.what_it_is_for == "Eases pain and fever."
    assert card.watch_for[0] == "Stomach bleeding" and len(card.watch_for) == 4
    label = evidence.fetch_label(["ibuprofen"])
    assert card.evidence and card.evidence[0].source == "openFDA"
    assert any(card.evidence[0].text in evidence.section_text(label, s) for s in evidence.PURPOSE_SECTIONS)


def test_llm_failure_falls_back_to_label_quote(monkeypatch):
    def boom(*a, **kw):
        raise llm.LLMError("down")

    monkeypatch.setattr(llm, "structured", boom)
    [card] = explain.pill_cards([_ibuprofen()])
    assert card.how_to_take == DIRECTIONS
    assert card.what_it_is_for == card.evidence[0].text  # the label's own words


def test_unknown_medicine_gets_no_label_card(monkeypatch):
    monkeypatch.setattr(llm, "structured", lambda *a, **kw: pytest.fail("LLM must not be called without a label"))
    [card] = explain.pill_cards([Medication(name="Zzzfakedrug", directions=None)])
    assert card.what_it_is_for == explain.NO_LABEL
    assert card.how_to_take is None and card.evidence == []

"""A2: photo extraction. llm.structured is faked; no network, no real photo."""

from __future__ import annotations

from pillwise import extract, llm


def _fake_structured(bottles):
    def f(prompt, output_type, **kw):
        assert kw.get("image") is not None
        return output_type(bottles=bottles)

    return f


def test_directions_copied_verbatim(monkeypatch):
    directions = "Take 1 tablet every 4 to 6 hours while symptoms persist."
    monkeypatch.setattr(
        llm,
        "structured",
        _fake_structured(
            [
                {"name": " Advil ", "strength": "200 mg", "directions": directions, "raw_text": "Advil 200 mg"},
                {"name": "Warfarin", "strength": None, "directions": None, "raw_text": "Warfarin"},
            ]
        ),
    )
    meds = extract.extract_from_image(b"img")
    assert [m.name for m in meds] == ["Advil", "Warfarin"]
    assert meds[0].directions == directions
    assert meds[1].directions is None
    assert all(m.source == "photo" and not m.confirmed for m in meds)


def test_blank_names_dropped(monkeypatch):
    monkeypatch.setattr(
        llm, "structured", _fake_structured([{"name": "  ", "strength": None, "directions": None, "raw_text": ""}])
    )
    assert extract.extract_from_image(b"img") == []


def test_llm_failure_returns_empty_list(monkeypatch):
    def boom(*a, **kw):
        raise llm.LLMError("nope")

    monkeypatch.setattr(llm, "structured", boom)
    assert extract.extract_from_image(b"img") == []


def test_empty_image_returns_empty_list():
    assert extract.extract_from_image(b"") == []

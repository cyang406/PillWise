"""explain.group_notes: label quotes about pregnancy, breastfeeding, children, women or men (no network)."""

from pillwise import explain

OTC = {
    "set_id": "abc",
    "effective_time": "20260615",
    "pregnancy_or_breast_feeding": [
        "If pregnant or breast-feeding, ask a health professional before use. It is especially important not to use "
        "aspirin during the last 3 months of pregnancy unless definitely directed to do so by a doctor because it may "
        "cause problems in the unborn child or complications during delivery."
    ],
    "warnings": [
        "Warnings Reye's syndrome : Children and teenagers who have or are recovering from chicken pox or flu-like "
        "symptoms should not use this product. Keep out of reach of children."
    ],
}

RX = {
    "set_id": "def",
    "effective_time": "20260629",
    "pregnancy": [
        "8.1 Pregnancy Risk Summary Warfarin sodium is contraindicated in women who are pregnant except in pregnant "
        "women with mechanical heart valves."
    ],
    "use_in_specific_populations": [
        "8 USE IN SPECIFIC POPULATIONS Pregnant women with mechanical heart valves: Warfarin sodium may cause fetal "
        "harm. ( 8.1 ) Lactation: Monitor breastfeeding infants for bruising or bleeding. ( 8.2 )"
    ],
    "pediatric_use": ["8.4 Pediatric Use Adequate and well-controlled studies have not been conducted in children."],
}


def _by_group(label):
    out = {}
    for n in explain.group_notes(label):
        out.setdefault(n.group, []).append(n.quote)
    return out


def test_quotes_are_exact_label_substrings_with_headings_removed():
    for label in (OTC, RX):
        full = " ".join(" ".join(v) for v in label.values() if isinstance(v, list))
        for note in explain.group_notes(label):
            assert note.quote in full
            assert not note.quote.startswith(("8", "Warnings ", "Lactation:"))
            assert note.evidence.source == "openFDA" and note.evidence.text == note.quote


def test_otc_pregnancy_and_reye_but_not_storage_text():
    g = _by_group(OTC)
    assert len(g["pregnancy"]) == 2 and "last 3 months of pregnancy" in g["pregnancy"][1]
    assert g["children"] == [
        "Reye's syndrome : Children and teenagers who have or are recovering from chicken pox or flu-like symptoms "
        "should not use this product."
    ]
    assert "breastfeeding" not in g  # already covered by the shared pregnancy sentence


def test_rx_groups_do_not_cross():
    g = _by_group(RX)
    assert g["breastfeeding"] == ["Monitor breastfeeding infants for bruising or bleeding."]
    assert g["children"][0].startswith("Adequate and well-controlled studies")
    assert all("pregnan" not in q.lower() for q in g.get("women_men", []))  # pregnancy text stays in pregnancy


def test_no_label_sections_no_notes():
    assert explain.group_notes({"set_id": "x"}) == []

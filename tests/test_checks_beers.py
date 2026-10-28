"""Beers checker against data/beers.json."""

from pillwise.checks.beers import BeersChecker
from pillwise.schemas import Medication, PatientContext


def med(name, *ingredients):
    return Medication(name=name, ingredients=list(ingredients) or [name.lower()])


def kinds(findings):
    return {(f.kind, tuple(f.drugs)): f.severity for f in findings}


def test_sleep_aid_scenario_flags_single_and_combo():
    meds = [med("Diphenhydramine"), med("Oxybutynin"), med("Lisinopril")]
    found = kinds(BeersChecker().check(meds, PatientContext(age=78)))
    assert found[("older_adult_risk", ("diphenhydramine",))] == "caution"
    assert ("older_adult_risk", ("oxybutynin",)) not in found  # Beers 2023: only Table 3/7, not Table 2
    assert found[("older_adult_combo", ("diphenhydramine", "oxybutynin"))] == "moderate"
    assert not any("lisinopril" in drugs for _, drugs in found)


def test_skipped_under_65_and_hedged_when_age_unknown():
    meds = [med("Diphenhydramine")]
    assert BeersChecker().check(meds, PatientContext(age=40)) == []
    [f] = BeersChecker().check(meds, PatientContext())
    assert f.plain_summary.startswith("If you are 65 or older")


def test_pair_tags_opioid_benzo():
    found = kinds(BeersChecker().check([med("Oxycodone"), med("Lorazepam")], PatientContext(age=80)))
    assert ("older_adult_combo", ("lorazepam", "oxycodone")) in found


def test_count_tag_threshold():
    two = [med("Gabapentin"), med("Sertraline")]
    three = two + [med("Zolpidem")]
    assert not any(k == "older_adult_combo" for k, _ in kinds(BeersChecker().check(two, PatientContext(age=70))))
    assert ("older_adult_combo", ("gabapentin", "sertraline", "zolpidem")) in kinds(
        BeersChecker().check(three, PatientContext(age=70))
    )


def test_evidence_is_cited_summary():
    [f] = BeersChecker().check([med("Diphenhydramine")], PatientContext(age=70))
    ev = f.evidence[0]
    assert ev.source == "Beers 2023"
    assert ev.url and "pubmed" in ev.url
    assert "unverified" in ev.version or ev.version == "2023"


def test_safe_list_has_nothing():
    assert BeersChecker().check([med("Acetaminophen"), med("Loratadine")], PatientContext(age=70)) == []

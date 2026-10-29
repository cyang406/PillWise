"""C16: FHIR export of the confirmed list (owner: C)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import fhir_export  # noqa: E402
from pillwise import api  # noqa: E402
from pillwise.schemas import Medication, Report  # noqa: E402


def _report() -> Report:
    meds, patient = api.load_scenario("warfarin_nsaid")
    meds[0] = meds[0].model_copy(update={"rxcui": "855332"})
    meds.append(Medication(name="Mysterol", source="manual", confirmed=True))
    return Report(meds=meds, patient=patient)


def test_statements_copy_label_text_and_carry_no_identity():
    report = _report()
    bundle = fhir_export.medication_statements(report)
    stmts = [e["resource"] for e in bundle["entry"]]
    assert len(stmts) == len(report.meds)
    warfarin = stmts[0]
    assert warfarin["medicationCodeableConcept"]["coding"][0] == {
        "system": fhir_export.RXNORM,
        "code": "855332",
        "display": "warfarin",
    }
    assert warfarin["dosage"] == [{"text": report.meds[0].directions}]  # copied, never generated
    unknown = stmts[-1]
    assert "coding" not in unknown["medicationCodeableConcept"] and "dosage" not in unknown
    assert all(set(s["subject"]) == {"display"} for s in stmts)  # no patient reference or identifier


def test_bundle_is_valid_fhir_r4():
    pytest.importorskip("fhir.resources")
    from fhir.resources.R4B.bundle import Bundle

    Bundle.model_validate(json.loads(fhir_export.to_json(_report())))

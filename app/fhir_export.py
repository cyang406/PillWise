"""C16: the confirmed medicine list as a FHIR R4 Bundle of MedicationStatement resources. Owner: C.

Lets a pharmacy or EHR import what the person confirmed. No identity goes in: the subject is a
display-only reference (safety rule 6), and dosage text is the label's own directions (rule 2).
"""

from __future__ import annotations

import json

from pillwise.schemas import Report

RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"


def medication_statements(report: Report) -> dict:
    asserted = report.generated_at.isoformat()
    entries = []
    for i, m in enumerate(report.meds):
        concept: dict = {"text": " ".join(x for x in (m.name, m.strength) if x)}
        if m.rxcui:
            concept["coding"] = [{"system": RXNORM, "code": m.rxcui, "display": m.generic_name or m.name}]
        statement = {
            "resourceType": "MedicationStatement",
            "id": f"{report.id}-{i}",
            "status": "active",
            "medicationCodeableConcept": concept,
            "subject": {"display": "Not identified (PillWise stores no identity)"},
            "dateAsserted": asserted,
            "informationSource": {"display": "Patient, confirmed in PillWise"},
        }
        if m.directions:
            statement["dosage"] = [{"text": m.directions}]
        entries.append({"resource": statement})
    return {"resourceType": "Bundle", "type": "collection", "timestamp": asserted, "entry": entries}


def to_json(report: Report) -> str:
    return json.dumps(medication_statements(report), indent=2)

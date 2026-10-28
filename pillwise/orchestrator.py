"""Build a Report from a confirmed medicine list. Owner: A.

Contract: build_report(meds, patient) -> Report   (called by pillwise.api.check)

Pipeline (keep this order; it is the safety design):
    1. normalize      names -> RxCUI + ingredients        (A, RxNorm)
    2. checks.run_all  rules/data decide every finding     (B, no LLM)
    3. evidence       attach openFDA label quotes          (A, LLM may only QUOTE)
    4. explain        per-pill cards                       (A, LLM explains label text)
    5. audit          log every claim with source/version  (B)

The LLM never changes a Finding's kind, severity or drugs.
"""

from __future__ import annotations

import logging

from pillwise import audit, checks, evidence, explain, normalize
from pillwise.config import get_settings
from pillwise.schemas import Medication, PatientContext, Report

log = logging.getLogger(__name__)


def build_report(meds: list[Medication], patient: PatientContext) -> Report:
    settings = get_settings()

    meds = normalize.normalize_all(meds)  # TODO(A)
    result = checks.run_all(meds, patient)  # B
    findings = evidence.attach_label_evidence(result.findings, meds)  # TODO(A)
    cards = explain.pill_cards(meds)  # TODO(A)

    unchecked = sorted({m.name for m in meds if m.rxcui is None and not m.ingredients} | set(result.unmatched))
    unchecked += [f"(checker '{name}' failed: {err})" for name, err in result.errors.items()]

    report = Report(
        patient=patient,
        meds=meds,
        findings=findings,
        pill_cards=cards,
        unchecked=unchecked,
        model=settings.model_main,
        data_versions=result.versions,
    )
    try:
        audit.log_report(report)
    except NotImplementedError:
        log.warning("audit.log_report not implemented yet")
    return report

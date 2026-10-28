"""Attach FDA label quotes to findings via the openFDA Drug Label API. Owner: A.

API: https://api.fda.gov/drug/label.json?search=openfda.rxcui:"<rxcui>"&limit=1
Useful fields: drug_interactions, warnings, boxed_warning, indications_and_usage,
               dosage_and_administration, effective_time (use as Evidence.version).

Rules:
- The LLM may only pick the exact sentence(s) that support a finding. Verify the
  quote is a substring of the label text; drop it if not.
- Never change severity, kind or drugs of a finding.

TODO(A):
- [ ] fetch_label(rxcui) with cache (settings.cache_dir/openfda/) and offline mode.
- [ ] attach_label_evidence: for each interaction finding, add Evidence(source="openFDA", text=<quote>).
"""

from __future__ import annotations

from pillwise.schemas import Finding, Medication

OPENFDA_LABEL = "https://api.fda.gov/drug/label.json"


def fetch_label(rxcui: str) -> dict | None:
    raise NotImplementedError("A: implement openFDA label fetch")


def attach_label_evidence(findings: list[Finding], meds: list[Medication]) -> list[Finding]:
    raise NotImplementedError("A: implement label evidence")

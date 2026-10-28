"""Drug-name normalization via the RxNorm REST API (NLM, free, no key). Owner: A.

Endpoints (https://rxnav.nlm.nih.gov/REST/):
    approximateTerm.json?term=<name>&maxEntries=1   -> candidate rxcui
    rxcui/<rxcui>/related.json?tty=IN               -> ingredient(s)
Note: RxNav's drug-drug INTERACTION API was discontinued in Jan 2024; we only use name lookup.

Name contract (docs/PARALLEL_AB.md): `ingredients` = lower-case RxNorm ingredient (TTY=IN)
names, e.g. "diphenhydramine" (never the salt "diphenhydramine hydrochloride").

On any failure the medicine keeps what it already had (e.g. scenario ingredients) and
`rxcui` stays None. The orchestrator then reports it as "could not check" if needed.
"""

from __future__ import annotations

import logging
import re

from pillwise import http_cache
from pillwise.schemas import Medication

log = logging.getLogger(__name__)

RXNAV = "https://rxnav.nlm.nih.gov/REST"

#: Common pharmacy-label abbreviations RxNorm does not understand (whole words only).
#: Fixed table on purpose: no LLM guesses at drug names. Add only unambiguous ones.
ABBREVIATIONS = {
    "apap": "acetaminophen",
    "asa": "aspirin",
    "hctz": "hydrochlorothiazide",
    "hydroco": "hydrocodone",
    "hydrocod": "hydrocodone",
    "oxycod": "oxycodone",
    "smx": "sulfamethoxazole",
    "tmp": "trimethoprim",
    "mtx": "methotrexate",
    "ntg": "nitroglycerin",
    "dph": "diphenhydramine",
    "sod": "sodium",
}
_ABBREV_RE = re.compile(r"\b(" + "|".join(ABBREVIATIONS) + r")\b", re.IGNORECASE)


def expand_abbreviations(name: str) -> str:
    """'HYDROCO/APAP 5-500M' -> 'hydrocodone / acetaminophen 5-500M'. Unchanged if no abbreviation."""
    if not _ABBREV_RE.search(name):
        return name
    out = _ABBREV_RE.sub(lambda m: ABBREVIATIONS[m.group(1).lower()], name)
    return re.sub(r"\s*/\s*", " / ", out)


def approximate_rxcui(term: str) -> str | None:
    data = http_cache.get_json("rxnorm", f"{RXNAV}/approximateTerm.json", {"term": term, "maxEntries": 1})
    cands = (data.get("approximateGroup") or {}).get("candidate") or []
    return cands[0].get("rxcui") if cands else None


def ingredients_for(rxcui: str) -> list[str]:
    data = http_cache.get_json("rxnorm", f"{RXNAV}/rxcui/{rxcui}/related.json", {"tty": "IN"})
    names = {
        p["name"].strip().lower()
        for g in (data.get("relatedGroup") or {}).get("conceptGroup") or []
        for p in g.get("conceptProperties") or []
        if p.get("name")
    }
    return sorted(names)


def _terms(med: Medication) -> list[str]:
    terms = []
    expanded = expand_abbreviations(med.name)
    names = [expanded, med.name] if expanded != med.name else [med.name]  # expanded first: more specific
    for name in names:
        if med.strength:
            terms.append(f"{name} {med.strength}")
        terms.append(name)
    if med.generic_name:
        terms.append(med.generic_name)
    return list(dict.fromkeys(t.strip() for t in terms if t and t.strip()))


def normalize_one(med: Medication) -> Medication:
    if med.rxcui and med.ingredients:
        return med
    for term in _terms(med):
        try:
            rxcui = approximate_rxcui(term)
            if not rxcui:
                continue
            ingredients = ingredients_for(rxcui)
        except Exception as exc:  # noqa: BLE001 - network/cache miss: keep going, never crash
            log.warning("rxnorm lookup failed for %r: %s", term, exc)
            continue
        if ingredients:
            return med.model_copy(
                update={"rxcui": rxcui, "ingredients": ingredients, "generic_name": " / ".join(ingredients)}
            )
    log.info("could not normalize %r", med.name)
    return med


def normalize_all(meds: list[Medication]) -> list[Medication]:
    return [normalize_one(m) for m in meds]

"""Attach FDA label quotes to findings via the openFDA Drug Label API. Owner: A.

API: https://api.fda.gov/drug/label.json?search=openfda.generic_name:"<ingredient>"
(openFDA does not index the ingredient-level RxCUIs RxNorm gives us, so we search by
the normalized ingredient name and pick the best single-ingredient label.)

Rules:
- The LLM may only pick the exact sentence(s) that support a finding. The quote is
  verified in code to be a substring of the label text; otherwise it is dropped.
- Never change severity, kind or drugs of a finding (checked before returning).
- Evidence.version = label effective date; Evidence.url = DailyMed page of the label.
"""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel

from pillwise import http_cache, llm
from pillwise.config import get_settings
from pillwise.schemas import Evidence, Finding, Medication

log = logging.getLogger(__name__)

OPENFDA_LABEL = "https://api.fda.gov/drug/label.json"
DAILYMED = "https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={set_id}"

#: Label sections that can support a safety finding, most specific first.
EVIDENCE_SECTIONS = (
    "boxed_warning",
    "contraindications",  # Rx: when it must not be used (97% of Rx labels)
    "drug_interactions",
    "ask_doctor_or_pharmacist",
    "do_not_use",
    "geriatric_use",  # Rx: older adults (supports Beers findings)
    "when_using",  # OTC: e.g. "marked drowsiness may occur"
    "ask_doctor",  # OTC: conditions to ask about first
    "warnings",
    "warnings_and_cautions",
    "precautions",
    "stop_use",
)
#: Sections that say what the medicine is for (used by explain.pill_cards).
PURPOSE_SECTIONS = ("purpose", "indications_and_usage")

_KEEP = set(EVIDENCE_SECTIONS) | set(PURPOSE_SECTIONS) | {"set_id", "id", "effective_time"}
_MAX_SECTION_CHARS = 8000


# ---------------------------------------------------------------------------
# Label fetch
# ---------------------------------------------------------------------------


def _rank(label: dict, ingredients: list[str]) -> tuple:
    names = " ".join((label.get("openfda") or {}).get("generic_name") or []).lower()
    is_combo = bool(re.search(r",| and |/", names))
    single_match = (len(ingredients) > 1) or not is_combo
    has_interaction_text = any(k in label for k in ("drug_interactions", "ask_doctor_or_pharmacist", "boxed_warning"))
    return (single_match, has_interaction_text, label.get("effective_time", ""), label.get("set_id", ""))


def _slim(ingredients: list[str]):
    def slim(data: dict) -> dict:
        results = data.get("results") or []
        if not results:
            return {}
        best = max(results, key=lambda r: _rank(r, ingredients))
        openfda = best.get("openfda") or {}
        out = {k: v for k, v in best.items() if k in _KEEP}
        out["openfda"] = {k: openfda.get(k) for k in ("generic_name", "brand_name", "product_type") if k in openfda}
        return {"label": out}

    return slim


def fetch_label(ingredients: list[str]) -> dict | None:
    """Best openFDA label for this ingredient set (cached, trimmed), or None."""
    ingredients = sorted({i.strip().lower() for i in ingredients if i and i.strip()})
    if not ingredients:
        return None
    search = " AND ".join(f'openfda.generic_name:"{i}"' for i in ingredients)
    key = get_settings().openfda_api_key
    data = http_cache.get_json(
        "openfda",
        OPENFDA_LABEL,
        {"search": search, "limit": 10},
        timeout=30.0,
        secret_params={"api_key": key} if key else None,
        slim=_slim(ingredients),
    )
    return data.get("label") or None


def section_text(label: dict, section: str) -> str:
    v = label.get(section)
    if isinstance(v, list):
        return "\n".join(str(x) for x in v)
    return str(v or "")


def label_version(label: dict) -> str:
    t = str(label.get("effective_time") or "")
    return f"label {t[:4]}-{t[4:6]}-{t[6:8]}" if len(t) >= 8 else "label (date unknown)"


def label_url(label: dict) -> str | None:
    set_id = label.get("set_id")
    return DAILYMED.format(set_id=set_id) if set_id else None


def label_evidence(label: dict, quote: str) -> Evidence:
    return Evidence(source="openFDA", text=quote, url=label_url(label), version=label_version(label))


# ---------------------------------------------------------------------------
# Quote verification (the safety core of this module)
# ---------------------------------------------------------------------------


def verify_quote(quote: str | None, source: str) -> str | None:
    """Return the exact substring of `source` matching `quote` (whitespace-tolerant), or None."""
    if not quote:
        return None
    words = quote.split()
    if len(words) < 4:
        return None
    if quote in source:
        return quote
    pattern = r"\s+".join(re.escape(w) for w in words)
    m = re.search(pattern, source)
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# Attach evidence to findings
# ---------------------------------------------------------------------------


class _Quote(BaseModel):
    quote: str | None


QUOTE_PROMPT = """Below is text from the official FDA label of {drug}.

Claim to support: "{title}. {summary}"
The other medicine(s) involved: {others}.

Copy, WORD FOR WORD, the one or two sentences from the label text that best support
this claim (for example a sentence naming {others} or its drug class, such as
"NSAIDs", "blood thinners" or "anticoagulants"). Copy exactly; do not shorten, fix or
paraphrase. The quote must be ONE continuous piece of the label text: do not add
headings or table titles, and do not join separate parts. If no sentence in the label
supports the claim, return null.
{retry}
LABEL TEXT:
{text}"""

RETRY_NOTE = """
Your previous answer was NOT found word for word in the label text:
"{bad}"
Try again: copy one continuous span exactly as it appears below, or return null.
"""


def _label_corpus(label: dict) -> str:
    parts = []
    for s in EVIDENCE_SECTIONS:
        t = section_text(label, s)
        if t:
            parts.append(t[:_MAX_SECTION_CHARS])
    return "\n\n".join(parts)


def quote_for(finding: Finding, drug: str) -> Evidence | None:
    label = fetch_label([drug])
    if not label:
        return None
    corpus = _label_corpus(label)
    if not corpus:
        return None
    others = [d for d in finding.drugs if d != drug] or [drug]
    fields = {"drug": drug, "title": finding.title, "summary": finding.plain_summary, "others": ", ".join(others)}

    retry = ""
    for _attempt in range(2):  # one retry when the quote is not in the label
        out = llm.structured(QUOTE_PROMPT.format(**fields, retry=retry, text=corpus), _Quote, fast=True)
        if not out.quote:
            return None
        exact = verify_quote(out.quote, corpus)
        if exact is not None:
            return label_evidence(label, exact)
        retry = RETRY_NOTE.format(bad=out.quote[:500])
    log.warning("dropped unverified quote for %s / %s", finding.id, drug)
    return None


def attach_label_evidence(findings: list[Finding], meds: list[Medication]) -> list[Finding]:
    out: list[Finding] = []
    for f in findings:
        new: list[Evidence] = []
        for drug in f.drugs:
            try:
                ev = quote_for(f, drug)
            except Exception as exc:  # noqa: BLE001 - evidence is extra; never lose the finding
                log.warning("label evidence failed for %s / %s: %s", f.id, drug, exc)
                continue
            if ev is not None and ev.text not in {e.text for e in f.evidence + new}:
                new.append(ev)
        g = f.model_copy(update={"evidence": [*f.evidence, *new]}) if new else f
        assert (g.kind, g.severity, g.drugs, g.id) == (f.kind, f.severity, f.drugs, f.id)
        out.append(g)
    return out

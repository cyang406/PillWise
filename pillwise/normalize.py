"""Drug-name normalization via the RxNorm REST API (NLM, free, no key). Owner: A.

Endpoints (https://rxnav.nlm.nih.gov/REST/):
    approximateTerm.json?term=<name>&maxEntries=1   -> candidate rxcui
    rxcui/<rxcui>/related.json?tty=IN               -> ingredient(s)
Note: RxNav's drug-drug INTERACTION API was discontinued in Jan 2024; we only use name lookup.

TODO(A):
- [ ] normalize_one: set rxcui, generic_name, ingredients (lower case). On failure leave rxcui=None.
- [ ] Cache every response under settings.cache_dir/rxnorm/ via pillwise.http_cache.
- [ ] Respect settings.offline (cache only).
"""

from __future__ import annotations

from pillwise.schemas import Medication

RXNAV = "https://rxnav.nlm.nih.gov/REST"


def normalize_one(med: Medication) -> Medication:
    raise NotImplementedError("A: implement RxNorm normalization")


def normalize_all(meds: list[Medication]) -> list[Medication]:
    return [normalize_one(m) for m in meds]

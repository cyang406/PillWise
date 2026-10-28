# Handoff: A: pipeline and agents (branch `a-pipeline`)

Owner keeps this current. The integration agent reads it before merging.

## Done
- A1 `llm.py`: OpenAI chat completions; `structured()` uses structured outputs (`chat.completions.parse`), `text()` plain; temperature 0 (retried without it for models that reject it). Text-only answers cached in `<cache_dir>/llm/`; image calls are never cached.
- A2 `extract.py`: photo → `list[Medication]` (several bottles per photo, directions copied or `None`, `[]` on any failure, image never logged).
- A3 `normalize.py`: RxNorm `approximateTerm` (name + strength, then name, then generic) → `related?tty=IN`. On failure keeps existing `ingredients` and leaves `rxcui=None`.
- A4 `evidence.py`: openFDA label by **ingredient name** (openFDA does not index RxNorm ingredient-level rxcuis). It picks the best single-ingredient label, the LLM picks a sentence, and the code checks that it is an exact substring of the label before keeping it. Version = label effective date, URL = DailyMed. Severity, kind and drugs are never changed (asserted).
- A5 `explain.pill_cards`: the LLM explains the label's purpose and warnings. `how_to_take` is copied from `directions`. If there is no label: "could not find the label". If the LLM fails: the label's own first purpose sentence.
- A6 `orchestrator.py`: evidence and card steps wrapped; a failure there keeps the findings.
- A7 tests `tests/test_pipeline_*.py` (33 tests, no network): recorded RxNorm and openFDA responses in `tests/fixtures/pipeline/cache/`, fake LLM.
- `http_cache.py`: `secret_params` (API key not part of the cache key), `slim` (cache only the chosen label, ~10 KB instead of ~1 MB), 404 cached as "no match".

## Drug-name list (name contract with B, docs/PARALLEL_AB.md)
Confirmed against RxNorm on 2026-10-28. `ingredients` are lower-case RxNorm IN names:

| Bottle text | `ingredients` |
| --- | --- |
| Warfarin sodium 5 mg | `warfarin` |
| Ibuprofen 200 mg / Advil | `ibuprofen` |
| Acetaminophen 500 mg / Tylenol | `acetaminophen` |
| Loratadine 10 mg | `loratadine` |
| Diphenhydramine HCl 25 mg | `diphenhydramine` |
| Oxybutynin chloride 5 mg | `oxybutynin` |
| Lisinopril 10 mg | `lisinopril` |

## Stubbed or still mock
- Orchestrator tests run on a local copy of `mock_check_result` (B's real checkers come in at CP2).
- `explain.simplify`, `explain.make_quiz`, `agents/clinic.py`: not started (stretch).
- Not yet run live against OpenAI (no key on this machine yet).

## How to run / verify my part
```bash
make check
pytest tests/test_pipeline_*.py
# live, once .env has an OpenAI key and B's DB exists:
PILLWISE_MOCK=0 make scenarios-real
```

## Env vars or data my part needs
- `OPENAI_API_KEY` (read by the OpenAI SDK itself).
- `PILLWISE_MODEL_MAIN=<vision-capable OpenAI model>` and `PILLWISE_MODEL_FAST=<cheap OpenAI model>`. The defaults in `config.py` are Claude names and are rejected with a clear error.
- `OPENFDA_API_KEY` optional.

## Needs from others
- **main (contract, additive):**
  - add `openai_api_key` (and optionally `llm_provider`) to `config.py`, and update `.env.example` defaults to OpenAI models.
  - add `mocks.mock_check_result()` (docs/PARALLEL_AB.md §2).
  - `data/cache/` and `tests/fixtures/pipeline/` go to A in the ownership table.
- **B:** match on the drug-name list above. Add a test that each name is in the DDInter DB.
- **C:**
  - On the Home confirm table, add a hint: "Check each name against the bottle." A look-alike misread (e.g. Hydroxyzine read as Hydralazine) is a valid drug name, so normalize cannot catch it; only the person can.
  - On Results, show what we actually checked, e.g. "Advil → ibuprofen" (`Report.meds[i].name` → `generic_name`). Normalization happens after confirmation, so today the person never sees this mapping.

## Known issues / risks
- Normalize takes RxNorm's top candidate with no score threshold, on purpose. Tested 2026-10-28: misspellings (Lisinoprl, Warfrin, Celebrx, Zyrtek) score ~8 and still map to the right ingredient, while correct names score ~12. A threshold would turn these into "could not check". The real risk is a look-alike misread of another real drug, which scores high; see the C requests above. Optional A follow-up: flag low-score matches in the report ("we read Warfrin as warfarin").
- openFDA label choice can change over time when online. Warming `data/cache/` (A12) and committing it freezes it for the demo.
- The warfarin label's interaction text names "drugs that increase bleeding risk", not ibuprofen by name; the quote may be class-level.
- `PILLWISE_OFFLINE=1` also makes LLM text calls cache-only, so the demo needs the cache warmed with the same models.

# Integration log

Written by the integration agent (see CLAUDE.md, "Integration protocol"). Newest first.

## Template

### <HH:MM> · integration/<HHMM> → main · tag <cp1|cp2|cp3|final>
- Branch heads merged: b-data `<sha>`, a-pipeline `<sha>`, c-ui `<sha>`
- Conflicts and how they were resolved:
- Fixes made on the integration branch (file, why):
- `make check`: pass / fail
- `make scenarios-real`: safe_otc ?, warfarin_nsaid ?, beers_sleep_aid ?
- Still mock:
- Contract requests raised:
- Risks for the demo:

## 13:01 · contract commit on main (docs/PARALLEL_AB.md)
- `mocks.mock_check_result()` added (+ contract test).
- `config.openai_api_key` added (additive). `.env.example` now lists `OPENAI_API_KEY` and OpenAI model names. Code defaults for `model_main` / `model_fast` were left unchanged (additive-only rule after 12:30); set them in `.env`.
- `schemas.Medication.ingredients`: comment only. Lower-case RxNorm IN names.
- Ownership: A gains `data/cache/` and `tests/fixtures/pipeline/`; B gains `pillwise/synthea.py` and `data/photos/`; `pillwise/agents/` is A only. B11 moved to A as A12.
- `tests/conftest.py`: `real_mode` now also sets `PILLWISE_OFFLINE=1`, so real-mode tests never use the network (CLAUDE.md "No network in tests"). Missing cache entries degrade evidence and cards; findings are unaffected.
- Every role branch: run `git merge main` now.

## 12:49 · integration/1249 (local, not yet merged into main) · tag cp1 pending
- Branch heads merged: b-data `ce014fc`, a-pipeline `ad3cda0` (local, not pushed). c-ui: no remote branch yet.
- Conflicts and how they were resolved: none. Both merges were clean.
- Fixes made on the integration branch: none.
- `make check`: pass after each merge (84 passed, 4 skipped after A).
- `make ddinter`: built from the 10 DDInter 2.0 CSVs, 336,075 rows. `tests/test_load_golden_names.py` passes.
- `make scenarios-real` (OpenAI gpt-4.1 / gpt-4.1-mini): safe_otc PASS, warfarin_nsaid PASS, beers_sleep_aid PASS.
- `PILLWISE_MOCK=0 pytest tests/test_scenarios.py`: real-mode tests pass (not skipped).
- `PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 make scenarios-real`: all 3 PASS from `data/cache/` (rxnorm 14, openfda 7, llm 24 files, 224 KB; not committed yet).
- Still mock: nothing on the A/B path. C (UI) is not merged.
- Contract requests raised:
  - `contract:` commit from docs/PARALLEL_AB.md (`mocks.mock_check_result`, ownership of `data/cache/`, `tests/fixtures/pipeline/`, `pillwise/synthea.py`).
  - `config.openai_api_key`.
- Kept on purpose: `data/photos/bottle_*.png` committed by B (Wikimedia Commons, attributed in docs/DATA_SOURCES.md, PII blurred), per B's handoff.
- Observations:
  - Two openFDA quotes for warfarin were dropped by `verify_quote` because the model stitched a table heading and an invented sentence onto real label text. The rule worked as designed. A follow-up retries once and asks for one continuous span.
  - ONC has no warfarin rule (7 verified rules); warfarin + ibuprofen is flagged major by DDInter. Ask B to confirm this matches the source paper.
  - DDInter "Unknown" pairs (acetaminophen + loratadine, acetaminophen + ibuprofen) appear as `unknown` findings. C should style them softly.
- Risks for the demo: live photo extraction not yet tested on B's photos. The cache must be re-warmed if prompts or models change.

## 2026-10-28 · init
- Repo initialized on `main` with shared contracts, mocks, scenarios, UI skeleton.
- `make check` passes in mock mode.

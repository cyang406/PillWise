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

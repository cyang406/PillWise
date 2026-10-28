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

## 2026-10-28 · init
- Repo initialized on `main` with shared contracts, mocks, scenarios, UI skeleton.
- `make check` passes in mock mode.

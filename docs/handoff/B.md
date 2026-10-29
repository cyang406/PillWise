# Handoff: B: data and rules (branch `b-data`)

Owner keeps this current. The integration agent reads it before merging.

## Done
- B3 `data/beers.json`: 14 single-drug + 5 combo entries checked against the 2023 paper and `verified: true` (fixes listed in `docs/DATA_SOURCES.md` verification log). Oxybutynin no longer gets a single-drug card; it is still caught by the anticholinergic combo.
- B1 DDInter 2.0: 10 CSVs (codes A,B,D,H,L,M,N,P,R,V) from https://ddinter2.scbdd.com/static/media/download/ddinter_downloads_code_<X>.csv, headers match the loader; `make ddinter` -> 336,075 rows, 215,570 unique pairs, no level conflicts. Golden names all present as plain RxNorm IN names: no name mapping needed.
- B2 `checks/ddinter.py`: pairwise lookup by `match_names`, DDInter level -> severity, template text, DDInter evidence. Missing DB raises (-> `CheckResult.errors`, "could not check").
- B4 `checks/beers.py`: single-drug (caution) + combo rules `count_tag` / `pair_tags` (moderate); skipped under 65; "If you are 65 or older" when age unknown.
- B5 `checks/onc.py` + `data/onc_high.json`: group_a x group_b pairs -> major; only `verified: true` rules unless `PILLWISE_MOCK=1`. All 7 rules checked against Phansalkar 2012 Table 2 and verified.
- B6 `audit.py`: plain sqlite3 table `audit_events` at `settings.audit_db`; `log_report` / `log_event` / `recent_events` (newest first). Stores no raw_text, photos or age.
- B7 `checks/__init__.py`: `CheckResult.unmatched` = meds whose names no working checker knows (each checker has `known_names()`).
- `pillwise/synthea.py` STUB (PARALLEL_AB seam 3): `list_patients(limit)` / `patient_meds(id)` with 2 hard-coded synthetic patients; real data comes with B12. Test: `tests/test_load_synthea.py`.
- B8 tests: `tests/test_checks_{ddinter,beers,onc,registry,audit}.py`, `tests/test_load_golden_names.py` (golden list from `docs/PARALLEL_AB.md`).

## Stubbed or still mock
- B9: photos in `data/photos/`; committed ones force-added ON PURPOSE past `.gitignore` (integrator: please keep them). `warfarin_nsaid` is fully covered by photos (warfarin, ibuprofen, acetaminophen). Two flat-label images from an unlicensed GitHub dataset stay local only. Details and licenses: `docs/DATA_SOURCES.md` "Test photos".
- DDInter evidence URL is the site root (per-interaction page URL not confirmed).

## How to run / verify my part
```bash
make check
make ddinter          # after the CSVs are in data/raw/ddinter/
pytest tests/test_load_golden_names.py   # must pass (not skip) once the DB exists
```

## Env vars or data my part needs
- `data/raw/ddinter/*.csv` (git-ignored), then `make ddinter`.
- Optional: `PILLWISE_DDINTER_DB`, `PILLWISE_AUDIT_DB` to override paths.

## Needs from others
- A: `normalize` returns lower-case RxNorm IN names (golden list, `docs/PARALLEL_AB.md` seam 1).
- main: the `contract:` commit from `docs/PARALLEL_AB.md` (adds `pillwise/synthea.py` to B in the ownership table). Stub already written early, as the plan's timeline says.

## Known issues / risks
- DDInter lists acetaminophen + loratadine (safe_otc scenario) with level Unknown, so the "safe" demo shows one `unknown` interaction card. The scenario still passes (unknown < minor). C may want to style `unknown` softly.
- DDInter has route variants like `diphenhydramine (topical)`; we match only the plain name.
- If DDInter spells a name differently from RxNorm IN, findings are silently missed; `test_load_golden_names.py` catches this for scenario drugs once the DB is built.

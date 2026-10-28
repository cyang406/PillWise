# Handoff: B: data and rules (branch `b-data`)

Owner keeps this current. The integration agent reads it before merging.

## Done
- B2 `checks/ddinter.py`: pairwise lookup by `match_names`, DDInter level -> severity, template text, DDInter evidence. Missing DB raises (-> `CheckResult.errors`, "could not check").
- B4 `checks/beers.py`: single-drug (caution) + combo rules `count_tag` / `pair_tags` (moderate); skipped under 65; "If you are 65 or older" when age unknown.
- B5 (code) `checks/onc.py`: group_a x group_b pairs -> major; only `verified: true` rules unless `PILLWISE_MOCK=1`.
- B6 `audit.py`: plain sqlite3 table `audit_events` at `settings.audit_db`; `log_report` / `log_event` / `recent_events` (newest first). Stores no raw_text, photos or age.
- B7 `checks/__init__.py`: `CheckResult.unmatched` = meds whose names no working checker knows (each checker has `known_names()`).
- B8 tests: `tests/test_checks_{ddinter,beers,onc,registry,audit}.py`, `tests/test_load_golden_names.py` (golden list from `docs/PARALLEL_AB.md`).

## Stubbed or still mock
- B1 DDInter CSVs not downloaded yet -> `data/ddinter.sqlite` not built; DDInter checker reports "could not check" until then.
- B3 / B5 data: every entry in `data/beers.json` and `data/onc_high.json` is still `verified: false`.
  Beers still runs but evidence version says "2023 (unverified seed)"; ONC emits nothing in real mode.
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
- main: the `contract:` commit from `docs/PARALLEL_AB.md` (B gains `pillwise/synthea.py`) before B writes the synthea stub.

## Known issues / risks
- If DDInter spells a name differently from RxNorm IN, findings are silently missed; `test_load_golden_names.py` catches this for scenario drugs once the DB is built.

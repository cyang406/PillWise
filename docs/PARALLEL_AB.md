# Running A and B in parallel

**Who this is for:** the A (pipeline) and B (data and rules) owners, and the integrator.
**Goal:** A and B work all day without waiting on each other, and meet once,
at CP2 (14:30), when B's real checkers replace the mock inside A's orchestrator.

## Why this mostly works already

The contract (`pillwise/schemas.py`, `pillwise/checks/base.py`) and the mocks
(`pillwise/mocks.py`) already fix the shape of everything A and B exchange:

- B's checkers take `list[Medication]` and return `list[Finding]`. The scenario
  files in `data/scenarios/` already have `ingredients` filled in, so **B never
  needs A's `normalize`** to build and test checkers.
- A's orchestrator calls `checks.run_all()` and `audit.log_report()`. The audit
  call is already wrapped in `try/except NotImplementedError`, so **B's audit
  never blocks A**.

Five places still couple A and B. The rest of this file explains how to fix each one.

## The five seams and how we cut them

### 1. Drug names: one agreed format (the biggest hidden risk)

**Problem:** A fills `Medication.ingredients` from RxNorm, and B matches them
against DDInter, Beers and ONC names. If the two sides spell names differently
(`diphenhydramine` vs `diphenhydramine hydrochloride`), both branches pass their
own tests and the merge silently finds nothing.

**Rule:** `Medication.ingredients` is a list of **lower-case RxNorm ingredient
(TTY=IN) names**. Salts and brand names are never used. `match_names` is what
checkers match on.

- **A:** returns IN names only (never PIN/salt forms) from `normalize`.
- **B:** maps every dataset name to the RxNorm IN name when loading
  (in `scripts/load_ddinter.py`, `data/beers.json`, `data/onc_high.json`),
  so checkers do plain string matching at runtime.

**Golden list:** these are the names in our three scenarios. A confirms them
against RxNorm in the first 10 minutes and posts the result in `docs/handoff/A.md`.
B adds a test that every one of them is found in the DDInter DB.

| Bottle text | Expected `ingredients` |
| --- | --- |
| Warfarin sodium 5 mg | `warfarin` |
| Ibuprofen 200 mg (Advil) | `ibuprofen` |
| Acetaminophen 500 mg (Tylenol) | `acetaminophen` |
| Loratadine 10 mg (Claritin) | `loratadine` |
| Diphenhydramine HCl 25 mg | `diphenhydramine` |
| Oxybutynin chloride 5 mg | `oxybutynin` |
| Lisinopril 10 mg | `lisinopril` |

This is the **only** sync point before CP2.

### 2. A's end-to-end run no longer waits for the DDInter DB

**Problem:** A6 (`build_report` end to end) needs real findings, and these depend
on B's DB and checkers.

**Fix (additive contract change on `main`):**

```python
# pillwise/mocks.py
def mock_check_result(meds: list[Medication], patient: PatientContext) -> CheckResult:
    """Same canned rules as mock_report, returned in the shape of checks.run_all()."""
```

A develops `orchestrator` → `evidence` → `explain` against
`mock_check_result` (in tests, monkeypatch `checks.run_all` with it). At CP2 the
real `checks.run_all` is used, with no code change in A.

### 3. `agents/clinic.py` gets one owner

**Problem:** the file is owned by "A+B", so both would edit it and conflict at merge.

**Fix:** split along the data/logic line.

| File | Owner | Provides |
| --- | --- | --- |
| `pillwise/synthea.py` (new) | B | `list_patients(limit) -> list[tuple[str, int \| None]]` (id, age) and `patient_meds(patient_id) -> list[Medication]` (with `source="synthea"`) |
| `pillwise/agents/clinic.py` | A only | `scan()` / `patient_report()` built on `synthea.py` + `orchestrator.build_report` |

B writes a stub `synthea.py` with those two signatures early (it can return two
hard-coded patients), so A can start A11 at any time.

### 4. `data/cache/` moves to A

**Problem:** `data/cache/` is owned by B, but only A's code (`http_cache`,
`normalize`, `evidence`) writes there. B11 ("warm the cache") would also need A's
finished pipeline.

**Fix:** A owns `data/cache/` and task B11 moves to A (call it A12). B keeps
`data/raw/`, `data/*.sqlite` builders and `data/*.json` rule files.

### 5. Test fixtures get separate folders

**Problem:** `tests/fixtures/` is owned by B, but A's tests need recorded
RxNorm/openFDA responses.

**Fix:** A owns `tests/fixtures/pipeline/`. B keeps the rest of `tests/fixtures/`.

## Timeline

```
          10:15          11:00                 12:30 CP1               14:30 CP2
A   golden list ── llm · extract · normalize ──┬── evidence · explain ──────┬── swap mock → real run_all
     (10 min)                                  │   against mock_check_result │    make scenarios-real
B   ── DDInter download + DB build ── ddinter · beers · onc checkers ── audit ┘
                                       (tested on scenario meds)
```

| Time | A | B |
| --- | --- | --- |
| 10:15–10:25 | Golden name list from RxNorm → handoff | Start DDInter download |
| 10:25–12:30 | A1 `llm`, A2 `extract`, A3 `normalize` | B1 DB build, B2 DDInter checker, `synthea.py` stub |
| 12:30 | CP1 merge | CP1 merge |
| 12:30–14:30 | A4 `evidence`, A5 `pill_cards`, A6 orchestrator on mock, A7 tests | B3–B5 Beers + ONC, B6 audit, B7 `unmatched`, B8 tests, golden-list test |
| 14:30 | CP2: `make scenarios-real` with real checkers | CP2 |
| 14:30–16:30 | Stretch A (simplify, translation), A12 warm cache | B10 food, B12 Synthea data behind `synthea.py` |
| 16:30–17:30 | A11 clinic agents on `synthea.py` | Fix whatever A11 finds |

## Contract changes needed on `main` (one `contract:` commit)

All of these are additive and must be agreed out loud first.

- [ ] `pillwise/mocks.py`: add `mock_check_result()`.
- [ ] `pillwise/schemas.py`: comment only. `ingredients` holds lower-case RxNorm IN names.
- [ ] `CLAUDE.md` ownership table:
  - A gains `data/cache/` and `tests/fixtures/pipeline/`.
  - B gains `pillwise/synthea.py`.
  - `pillwise/agents/` becomes A only.
- [ ] `docs/TASKS.md`:
  - Move B11 to A as A12.
  - A11 depends on `synthea.py`.
  - Add the golden-list test to B8.
- [ ] `docs/ARCHITECTURE.md`: update the clinic line and the storage table.

After the commit, both role branches run `git merge main` right away.

## When something still blocks you

Do not wait. Code against the contract or the mock. Write the request under
"Needs from others" in your `docs/handoff/<role>.md` and say it out loud.

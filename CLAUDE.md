# CLAUDE.md: rules for every agent working on PillWise

Read this file fully before touching code. Then read `docs/ARCHITECTURE.md`
(how the pieces fit) and `docs/TASKS.md` (who does what, by when).

## What PillWise is

A public-facing app: photograph your pill bottles, confirm the list, get each
medicine explained in plain language plus a safety check of the whole list,
with every warning traced to its source. Built in one day for the Solix AI
Hackathon 2026 (AI in Healthcare). Submission deadline: 2026-10-28 19:00 PT.

## Safety rules (never break these)

1. **Rules and data decide; the LLM only reads and explains.** Severity, kind and
   drugs of a `Finding` come only from checkers in `pillwise/checks/`. No LLM
   call may create, drop, upgrade or downgrade a finding.
2. **Directions are copied, never generated.** `Medication.directions` and
   `PillCard.how_to_take` come from the bottle/label text. No dosing advice anywhere.
3. **"Not found" is never "safe".** Anything we could not normalize or check goes
   in `Report.unchecked` and is shown as "could not check".
4. **Every finding has evidence** (`source` + `version`, URL when possible). Quotes
   from openFDA must be exact substrings of the label.
5. **Every `what_to_do` ends with the pharmacist footer** (the schema adds it).
6. **Privacy:** never store photos, raw label text or anything that identifies a
   person. Demo patients are synthetic. Never commit `.env`.
7. **Copyright:** Beers Criteria text is summarized in our own words, with a citation.

## Branches and ownership

| Branch | Role | Owns (only this role edits these) |
| --- | --- | --- |
| `a-pipeline` | A: pipeline and agents | `pillwise/llm.py`, `extract.py`, `normalize.py`, `evidence.py`, `explain.py`, `orchestrator.py`, `http_cache.py`, `pillwise/agents/`, `tests/test_pipeline_*.py`, `requirements/a-pipeline.txt`, `docs/handoff/A.md` |
| `b-data` | B: data and rules | `pillwise/checks/` (except `base.py`), `pillwise/audit.py`, `data/beers.json`, `data/onc_high.json`, `data/scenarios/`, `data/cache/`, `scripts/` (except `run_scenarios.py`), `tests/test_checks_*.py`, `tests/test_load_*.py`, `tests/fixtures/`, `requirements/b-data.txt`, `docs/handoff/B.md`, `docs/DATA_SOURCES.md` |
| `c-ui` | C: UI, demo and pitch | `app/`, `.streamlit/`, `assets/`, `tests/test_app_*.py`, `requirements/c-ui.txt`, `docs/handoff/C.md`, `docs/DEMO.md` |
| `main` | shared contract | `pillwise/schemas.py`, `pillwise/api.py`, `pillwise/config.py`, `pillwise/mocks.py`, `pillwise/checks/base.py`, `scripts/run_scenarios.py`, `tests/test_contracts.py`, `tests/test_scenarios.py`, `tests/conftest.py`, `requirements.txt`, `requirements/base.txt`, `pyproject.toml`, `Makefile`, `.env.example`, `.gitignore`, `README.md`, `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, `docs/INTEGRATION_LOG.md` |

**Working on a role branch:** edit only files your role owns. If you need
something from another role, code against the contract (or the mock) and write
the request in your `docs/handoff/<role>.md` under "Needs from others".

**Contract change** (any file owned by `main`): avoid it. If truly needed:
1. Agree with the team (say it out loud).
2. Commit it on `main` alone, message prefix `contract:`, with tests passing.
3. Every role branch then runs `git merge main` right away.
Only additive changes (new optional fields, new functions) are allowed after 12:30.

## Conventions

- Python 3.11+, type hints, Pydantic v2 models from `pillwise/schemas.py`.
  Never define a second version of a schema model.
- The UI (`app/`) imports only `pillwise.api` and `pillwise.schemas`.
- Settings only via `pillwise.config.get_settings()`; no `os.getenv` elsewhere.
- No network in tests. Use fixtures in `tests/fixtures/` or `data/cache/`.
- `logging`, not `print`, inside `pillwise/` (scripts may print).
- New dependency: add one line to `requirements/<your-role>.txt` (never to `requirements.txt`).
- Commit messages: `<role>: <what>` (e.g. `b: beers combo rules`). Small commits.
- Before every commit: `make fmt` (keeps diffs small and merges clean). Before every push: `make check` (ruff + pytest + scenarios in mock mode) must pass.
- Keep `docs/handoff/<role>.md` current: it is how the integrator learns what you built.

## Commands

```bash
make setup            # install deps + editable package
make check            # lint + tests + scenarios (mock). Must pass before push/merge.
make app              # streamlit run app/Home.py
make scenarios-real   # scenarios through the real pipeline (PILLWISE_MOCK=0)
make ddinter          # build data/ddinter.sqlite from data/raw/ddinter/*.csv
```

## Integration protocol (for the merging agent)

You are asked to merge `b-data`, `a-pipeline` and `c-ui` into `main`. Follow
these steps exactly and record everything in `docs/INTEGRATION_LOG.md`.

### 0. Prepare
```bash
git fetch --all
git checkout main && git pull
git checkout -b integration/<HHMM>
make setup && make check            # baseline must be green; if not, stop and report
```
Read `docs/handoff/A.md`, `B.md`, `C.md` before merging.

### 1. Merge in dependency order: B, then A, then C
B's checkers feed A's orchestrator; A's API backs C's UI.
```bash
git merge --no-ff origin/b-data      -m "merge: b-data"
make check
git merge --no-ff origin/a-pipeline  -m "merge: a-pipeline"
make check
git merge --no-ff origin/c-ui        -m "merge: c-ui"
make check
```
After each merge, if `make check` fails, fix it on the integration branch
(smallest change, in the owner's style) and note it in the log.

### 2. Resolving conflicts
| Situation | Resolution |
| --- | --- |
| File owned by one role (table above) | Take that role's version (`git checkout --theirs` when merging that role). |
| Contract file changed on a role branch (should not happen) | Keep `main`'s version. Move the role's intent into the role's own files if possible; otherwise log it as a "contract request" and ask the humans. |
| `requirements/*.txt` | No conflict expected (one file per role). If `requirements.txt` was edited, restore main's version. |
| `docs/handoff/*.md` | Take the owner's version. |
| Two roles edited the same non-contract file | Keep both changes when they are independent; otherwise prefer the owner, log the other change. |
| Generated files (`*.sqlite`, `__pycache__`) committed by mistake | Delete them from the index (`git rm --cached`) and log it. |

Never resolve a conflict by weakening a safety rule (top of this file), by
deleting a test, or by marking a failing test as skip without logging why.

### 3. Switch from mock to real
```bash
make ddinter                          # needs data/raw/ddinter/*.csv; see docs/DATA_SOURCES.md
make scenarios-real                   # all three scenarios must PASS
PILLWISE_MOCK=0 pytest                # real-mode scenario tests must pass, not skip
PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 make scenarios-real   # proves the demo works without network
```
If a scenario fails, find the responsible module via the ownership table, fix
minimally, and log it. If the real path cannot pass by the deadline, keep
`PILLWISE_MOCK=1` for the parts that fail and say so in the log and README.

### 4. Smoke-test the app
```bash
PILLWISE_MOCK=0 streamlit run app/Home.py --server.headless true &
```
Load each demo scenario from the Home page, confirm, and check the Results page
renders findings, evidence and the "could not check" box. Also check a
`streamlit.testing.v1.AppTest` run if `tests/test_app_*.py` exists.

### 5. Finish
- Update `README.md` (status, how to run the demo) and `docs/INTEGRATION_LOG.md`.
- `git checkout main && git merge --no-ff integration/<HHMM> -m "integrate: <HHMM>"`.
- Tag checkpoint merges: `git tag cp1|cp2|cp3|final`.
- Report back: what merged cleanly, what you fixed, what is still mock, open risks.

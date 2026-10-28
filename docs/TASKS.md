# Tasks: three roles, one day

Hacking ends 19:00 PT. Times assume a 10:15 start on branches; shift rows
equally if late, but keep 17:30 (code freeze) and 18:45 (submit).

Each task has an id (`A1`, `B3`...). Use it in commit messages and in your
handoff file. Tick boxes in your own handoff file, not here.

## Checkpoints (integration merges at each one)

| Time | Checkpoint | Definition of done | Merge |
| --- | --- | --- | --- |
| 12:30 | CP1 | One real photo becomes a normalized `Medication` shown in the UI; DDInter DB builds | B → A → C into main, tag `cp1` |
| 14:30 | CP2 (go / no-go) | `make scenarios-real` passes all 3 scenarios; Results page shows real findings with evidence | tag `cp2`. If red: everyone fixes MVP only until 16:30 |
| 16:30 | CP3 | Stretch A frozen; offline demo works (`PILLWISE_OFFLINE=1`) | tag `cp3` |
| 17:30 | Code freeze | Only bug fixes after this | tag `final` |

## A: pipeline and agents (`a-pipeline`)

**MVP (Must, by 14:30)**
- [ ] A1 `llm.py`: `structured()` and `text()` helpers (Pydantic AI or Anthropic tool-use), models from config.
- [ ] A2 `extract.py`: photo → `list[Medication]`; copy directions verbatim; several bottles per photo; [] when unreadable.
- [ ] A3 `normalize.py`: RxNorm `approximateTerm` → rxcui; `related?tty=IN` → ingredients; cache via `http_cache`.
- [ ] A4 `evidence.py`: openFDA label by rxcui; LLM picks the supporting sentence; verify substring; add `Evidence(source="openFDA")`.
- [ ] A5 `explain.pill_cards`: purpose / how to take (copied) / watch for, from label sections.
- [ ] A6 `orchestrator.build_report` wired end to end; `make scenarios-real` passes (with B's checkers).
- [ ] A7 Tests `tests/test_pipeline_*.py` with cached fixtures (no network).

**Stretch A (Should, 14:30–16:30)**
- [ ] A8 `explain.simplify`: rewrite loop to reading grade ≤ 6 (`textstat`).
- [ ] A9 Translation es/zh + back-translation + drift score (`sentence-transformers` or LLM judge).
- [ ] A10 `explain.make_quiz` (Could).

**Stretch B (Could, 16:30–17:30, with B)**
- [ ] A11 `agents/clinic.py`: planner + reviewer agents over `orchestrator.build_report`; every tool call audited.

## B: data and rules (`b-data`)

**MVP (Must, by 14:30)**
- [ ] B1 Download DDInter 2.0 CSVs into `data/raw/ddinter/`; adjust `scripts/load_ddinter.py` headers if needed; `make ddinter`.
- [ ] B2 `checks/ddinter.py`: pairwise lookup by `match_names`; severity mapping; template text; evidence.
- [ ] B3 `data/beers.json`: verify the 15 seed entries against the paper, add to 20–30; flip `verified`.
- [ ] B4 `checks/beers.py`: single-drug + combo rules (`count_tag`, `pair_tags`); skip if age < 65.
- [ ] B5 `data/onc_high.json`: verify pairs against the paper; `checks/onc.py`.
- [ ] B6 `audit.py`: SQLite table + `log_report` / `log_event` / `recent_events`.
- [ ] B7 Fill `CheckResult.unmatched` in `checks/__init__.py`.
- [ ] B8 Tests `tests/test_checks_*.py` using `tests/fixtures/` (no network).
- [ ] B9 Prepare the 3 real bottles + photos for the scenarios (keep photos out of git).

**Stretch (Should/Could)**
- [ ] B10 Drug-food warnings (`kind="food"`) from DDInter if the download includes them.
- [ ] B11 Warm `data/cache/` for every scenario drug (run the real pipeline once online) and commit it.
- [ ] B12 Synthea 200 patients aged 65+ → `data/synthea.duckdb` (`scripts/gen_synthea.sh`, `load_synthea.py`).

## C: UI, demo and pitch (`c-ui`)

**MVP (Must, by 14:30)**
- [ ] C1 Home: camera + upload + scenario picker; confirm table; age; "Confirm and check" (skeleton exists).
- [ ] C2 Results: severity-colored finding cards with evidence; pill cards; "could not check" box; mock banner.
- [ ] C3 Trust panel: data versions + `audit.recent_events()` (via an `api` function if added on main).
- [ ] C4 Mobile-friendly layout check (judges may scan a QR code).
- [ ] C5 Tests `tests/test_app_*.py` with `streamlit.testing.v1.AppTest` (mock mode).

**Stretch (Should/Could)**
- [ ] C6 Interaction graph (pyvis or Plotly network, edges colored by severity).
- [ ] C7 Printable one-page summary (reportlab / WeasyPrint).
- [ ] C8 Summary page: language toggle, reading grade, drift check (skeleton exists).
- [ ] C9 Teach-back quiz UI; read-aloud (gTTS).
- [ ] C10 Clinic view page (skeleton exists).

**Demo and submission (17:30–18:45)**
- [ ] C11 `docs/DEMO.md`: 2-minute script; record backup video.
- [ ] C12 Slides / Devpost text: problem, solution, architecture diagram, guardrails, data sources.

## Cross-role requests

Write requests in your handoff file under "Needs from others" and say it out loud.
Common ones expected today:
- C needs `api.recent_audit_events()` for the trust panel → contract change on main (additive).
- A needs B's DDInter DB built before A6.
- B needs A's normalize to fill `ingredients` before real-mode checks work.

# PillWise

**Snap your pills. Understand them. Stay safe.**

PillWise lets anyone photograph their pill bottles and get a plain-language
explanation of each medicine plus a safety check of the whole list, with every
warning traced to its source. Rules and curated data decide; the AI only reads
labels and explains.

Solix AI Hackathon 2026 · AI in Healthcare track · UC San Diego

> Educational tool, not medical advice. Uses public drug data and synthetic patients only.

## Status

| Part | State |
| --- | --- |
| Shared contracts, mocks, scenarios, UI skeleton | Done (init) |
| A: extraction, normalization, evidence, pill cards | Not started |
| B: DDInter, Beers, ONC checkers, audit log | Not started |
| C: full UI, graph, PDF, demo | Skeleton on mocks |

The integrator updates this table at each checkpoint.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
make setup                 # pip install -r requirements.txt && pip install -e .
cp .env.example .env       # add ANTHROPIC_API_KEY
make check                 # lint + tests + demo scenarios (mock mode)
make app                   # opens the Streamlit app (mock mode by default)
```

Set `PILLWISE_MOCK=0` in `.env` to use the real pipeline once it exists.

## How it works

```
bottle photo ──► extract (vision LLM) ──► person confirms list
                                              │
                                              ▼
                     normalize (RxNorm) ──► checks (DDInter · ONC · Beers 2023)  ← no LLM
                                              │
                                              ▼
                     evidence (openFDA label quotes) ──► pill cards / plain language (LLM explains)
                                              │
                                              ▼
                               Report ──► UI + audit log (source + version per claim)
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Data: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

## Team workflow

Three role branches, merged by an integration agent:

| Branch | Role | Focus |
| --- | --- | --- |
| `a-pipeline` | A | LLM extraction, RxNorm, openFDA evidence, explanations, agents |
| `b-data` | B | DDInter loader, Beers / ONC rules, audit log, scenarios, Synthea |
| `c-ui` | C | Streamlit UI, graph, PDF, demo script, pitch |

```bash
git checkout -b a-pipeline   # or b-data / c-ui, from main after the init commit
```

Rules, file ownership and the merge protocol live in [CLAUDE.md](CLAUDE.md).
Hour-by-hour tasks and checkpoints: [docs/TASKS.md](docs/TASKS.md).

## Repo layout

```
app/                    Streamlit UI (C)          — imports only pillwise.api + schemas
pillwise/
  schemas.py api.py config.py mocks.py            — shared contract (main)
  checks/base.py                                  — checker protocol (main)
  checks/ddinter.py beers.py onc.py, audit.py     — rules and audit (B)
  extract.py normalize.py evidence.py explain.py
  orchestrator.py llm.py http_cache.py agents/    — pipeline (A)
data/
  beers.json onc_high.json scenarios/ cache/      — B
scripts/                load_ddinter.py, run_scenarios.py, gen_synthea.sh
tests/                  test_contracts.py, test_scenarios.py (+ role tests)
docs/                   ARCHITECTURE, TASKS, DATA_SOURCES, handoff/, INTEGRATION_LOG
```

## Data sources

RxNorm (NLM) · DDInter 2.0 · openFDA Drug Label API · 2023 AGS Beers Criteria (summarized, cited) ·
ONC high-priority DDI list · Synthea (synthetic patients). See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

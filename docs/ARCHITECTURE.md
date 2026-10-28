# Architecture

Shared contract document (owned by `main`). If code and this file disagree, the
code in `pillwise/schemas.py` and `pillwise/api.py` wins; fix this file.

## Data flow

```
                 ┌──────────────────────────── app/ (C) ────────────────────────────┐
                 │ Home: capture → confirm table → "Confirm and check"              │
                 │ Results: findings + evidence + pill cards + "could not check"    │
                 │ Summary (stretch A) · Clinic View (stretch B)                    │
                 └───────────────▲──────────────────────────────┬───────────────────┘
                                 │ Report / SimplifiedSummary    │ list[Medication]
                 ┌───────────────┴────────── pillwise/api.py ────▼───────────────────┐
                 │ mock? → pillwise/mocks.py        real? → modules below            │
                 └───────────────────────────────────┬───────────────────────────────┘
read_bottle ─► extract.py (A, vision LLM) ─► list[Medication] (unconfirmed)
check ───────► orchestrator.build_report (A)
                 1. normalize.normalize_all   (A)  RxNorm → rxcui, ingredients
                 2. checks.run_all            (B)  DDInter · ONC · Beers → findings   (NO LLM)
                 3. evidence.attach_label_evidence (A) openFDA quotes, verified substrings
                 4. explain.pill_cards        (A)  label → plain explanation
                 5. audit.log_report          (B)  source + version per claim
simplify / quiz ─► explain.py (A)                   stretch A
clinic_scan / clinic_patient ─► agents/clinic.py (A) over synthea.py (B)  stretch B
```

## Contracts

### Models (`pillwise/schemas.py`)

| Model | Produced by | Consumed by | Notes |
| --- | --- | --- | --- |
| `Medication` | extract (A), UI manual entry (C), scenarios (B) | everything | `directions` copied; `match_names` is what checkers match on |
| `PatientContext` | UI (C) | checkers (B) | `is_older_adult` is `None` when age unknown |
| `Finding` | checkers (B) | evidence (A), UI (C), audit (B) | needs ≥1 `Evidence`; id and footer auto-filled |
| `Evidence` | checkers (B), evidence.py (A) | UI, audit | `version` always set |
| `PillCard` | explain (A) | UI | `how_to_take` copied |
| `Report` | orchestrator (A) | UI, audit | `unchecked` must list anything not checked |
| `SimplifiedSummary`, `QuizQuestion` | explain (A) | UI | stretch A |
| `ClinicPatientSummary` | agents (A+B) | UI | stretch B |
| `AuditEvent` | audit (B) | UI trust panel | |

### Functions

| Function | Owner | Signature |
| --- | --- | --- |
| `api.*` | main | see `pillwise/api.py` (frozen; tested in `test_contracts.py`) |
| `extract.extract_from_image` | A | `(image_bytes, mime_type) -> list[Medication]` |
| `normalize.normalize_all` | A | `(meds) -> list[Medication]` |
| `checks.run_all` | B | `(meds, patient) -> CheckResult` |
| `Checker.check` | B | `(meds, patient) -> list[Finding]` (protocol in `checks/base.py`) |
| `evidence.attach_label_evidence` | A | `(findings, meds) -> list[Finding]` |
| `explain.pill_cards` / `simplify` / `make_quiz` | A | see `explain.py` |
| `orchestrator.build_report` | A | `(meds, patient) -> Report` |
| `audit.log_report` / `log_event` / `recent_events` | B | see `audit.py` |
| `agents.clinic.scan` / `patient_report` | A (data via B's `synthea.py`) | see `agents/clinic.py` |

### Severity mapping

| Source | Source level | `Severity` |
| --- | --- | --- |
| DDInter | Major / Moderate / Minor / Unknown | major / moderate / minor / unknown |
| ONC high-priority | any rule hit | major |
| Beers single drug | any | caution |
| Beers combination | any | moderate |

Sort with `SEVERITY_RANK`, never by string.

## Mock mode

`PILLWISE_MOCK=1` (default) makes `pillwise/api.py` return canned objects from
`pillwise/mocks.py`, all marked `is_mock=True` / version `MOCK`, and the UI shows a
banner. This lets C build the UI from minute one and gives A and B the exact
target shape. The three scenarios pass in mock mode by construction; passing
them in real mode is checkpoint 2.

## Demo scenarios (`data/scenarios/*.json`)

| File | Story | Must flag |
| --- | --- | --- |
| `safe_otc.json` | acetaminophen + loratadine, age 70 | nothing above minor |
| `warfarin_nsaid.json` | warfarin + OTC ibuprofen + acetaminophen, age 72 | interaction warfarin/ibuprofen ≥ moderate |
| `beers_sleep_aid.json` | diphenhydramine + oxybutynin + lisinopril, age 78 | Beers risk for diphenhydramine; anticholinergic combo |

## Storage

| File | What | Committed? |
| --- | --- | --- |
| `data/ddinter.sqlite` | DDInter interactions table | No (built by `make ddinter`) |
| `data/audit.sqlite` | audit events | No |
| `data/cache/<ns>/*.json` | RxNorm / openFDA / LLM text answers (owner A; never photo calls) | Yes, before the demo (public data) |
| `data/raw/` | downloads (DDInter CSV, Synthea) | No |

# Testing the web app

Five layers, fastest first. Layers 1 and 2 must pass before every push; run 3 to 5 before the demo.

## 1. Automated checks (`make check`, about 10 s, no network)

```bash
uv run --no-project make check     # ruff + pytest + the 3 scenarios in mock mode
```

| Part | What it proves |
| --- | --- |
| `tests/test_contracts.py` | `pillwise.api` signatures and the schema rules (footer, evidence, ids) still hold |
| `tests/test_checks_*.py`, `tests/test_load_*.py` | B's checkers and data (DDInter, Beers, ONC, audit) |
| `tests/test_pipeline_*.py` | A's pipeline on recorded RxNorm / openFDA answers and a fake LLM |
| `tests/test_app_smoke.py` | The one-page UI through Streamlit `AppTest`: sample → check → verdict and questions, results hide when the list changes, typed unknown medicine is "could not check", "Not rated", missing directions, trust panel, quiz with one LLM call per report, web vs mobile camera, and all 3 samples in real offline mode (incl. label quotes and "Can I take this?" with Aleve) |
| `tests/test_app_fhir.py` | The FHIR export validates against the official R4 schema and carries no identity |
| `scripts/run_scenarios.py` | The 3 demo scenarios flag what they must |

The real-offline UI tests skip when `data/ddinter.sqlite` is missing; build it with `make ddinter`.

## 2. Real pipeline, offline (about 10 s)

```bash
PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 PILLWISE_MODEL_MAIN=gpt-4.1 PILLWISE_MODEL_FAST=gpt-4.1-mini \
  uv run --no-project make scenarios-real
```

Runs the real checkers, evidence and explanations from `data/cache/`. This is exactly what the demo shows
without Wi-Fi. If it fails after a prompt or model change, the LLM cache needs re-warming (see `docs/handoff/A.md`).

## 3. In a real browser, with screenshots (about 1 min)

Use the `pillwise-ui-screenshots` skill (`.claude/skills/`), or by hand:

```bash
PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 PILLWISE_MODEL_MAIN=gpt-4.1 PILLWISE_MODEL_FAST=gpt-4.1-mini \
  uv run --no-project streamlit run app/Home.py --server.port 8599 &
uv run --no-project python .claude/skills/pillwise-ui-screenshots/shots.py /tmp/pillwise-shots
```

Look at every image: severity color bars, the "could not check" box above the findings, no sideways
scrolling at 390 px, the disclaimer, no mock banner in real mode.

## 4. Manual checklist (about 10 min, before the demo)

Start the app in real offline mode (`make app` with the variables above) and open http://localhost:8501.

| # | Do | Expect |
| --- | --- | --- |
| 1 | Open the page | Disclaimer; Age box, "Add bottle photos" drop zone, "Type a name", "Try a sample"; no camera (web) |
| 2 | Open `/?app=mobile` | A "Take a photo" camera appears (what the mobile app shows) |
| 3 | Try a sample → Warfarin nsaid | 3 medicine rows, all ticked, age 72 |
| 4 | Untick one row | Orange row and "Please check" reminder |
| 5 | Check my list | Verdict "Ask your pharmacist before taking ibuprofen with warfarin."; red Serious card |
| 6 | Open "Sources" on the red card | DDInter record + FDA quote in quotation marks + DailyMed link that opens |
| 7 | Remove a row | Results disappear: "Your list changed since the last check" |
| 8 | Type "Mysterol", Check my list | Red box "We could not check: Mysterol … does NOT mean they are safe" |
| 9 | About each medicine → Warfarin → "Pregnancy, breastfeeding, children" | Exact FDA label sentences with the label date |
| 10 | Ask your pharmacist | Numbered questions, summary with reading level ≤ 6, quiz with score, both downloads work |
| 11 | "Buying something new?" → Aleve | Aleve → naproxen; Serious with warfarin (works offline too: cached) |
| 12 | "Sources and audit trail" | Data versions, FDA labels, audit entries for this report |
| 13 | Turn Wi-Fi off (`PILLWISE_OFFLINE=1`), repeat 3 to 6 | Same results |
| 14 | Online with `OPENAI_API_KEY`: select `bottle_1.png`, `gen_ibuprofen_200mg.png`, a copy of `bottle_1.png` and a blank image together | Read in parallel (about 4 s); 2 rows, directions copied exactly; "Already on your list" for the copy; "could not read" for the blank, still shown after the next click |

## 5. On a phone

- **Phone browser:** same Wi-Fi, open `http://<laptop LAN IP>:8501`. Check the layout at phone width and that
  "Upload a photo" offers the camera.
- **Mobile app:** see `mobile/README.md` (Expo Go). Check the launch disclaimer, the camera permission, the
  "Take a photo" tab, and that turning Wi-Fi off shows "Can't reach PillWise" with "Try again".

Before merging, run the `pillwise-safety-review` skill on the diff.

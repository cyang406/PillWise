# Handoff: C: UI, demo and pitch (branch `c-ui`)

Owner keeps this current. The integration agent reads it before merging.

## Plan
Revised 13:45 after syncing main (cp2 tagged at 13:24, A and B real path green) and reading the team
planning doc (https://claude.ai/artifact/6iBScr4Fs6hRSCkcddbh4r). C is now the only part not merged, so
the MVP goes first and gets pushed for the next integration. Judging is in person on Thursday 2026-10-29.

**1. MVP (Must, push by ~15:00)**
- [x] C1 Home: camera + upload + scenario picker; confirm table; age; "Confirm and check".
  - Hint above the table: "Check each name against the bottle" (A: look-alike misreads pass normalize).
  - Photo that reads as `[]`: "We could not read this label. Type the medicine in below." (safety rule 3).
  - Replace deprecated `use_container_width` (integration log 13:24).
- [x] C2 Results: severity-colored finding cards with evidence; "could not check" box first; mock banner.
  - Style `unknown` softly (B: safe_otc shows one DDInter "Unknown" card).
  - "What we checked": bottle name → generic name, e.g. "Advil → ibuprofen" (A request).
  - Pill card always shows the how-to-take line, with A's fixed text when `how_to_take` is empty.
- [x] C3 Trust panel: data versions + sources per finding; audit events once `api.recent_audit_events()` exists.
- [x] C4 Layout usable at phone width (390 px); `.streamlit/config.toml`. Base for C13.
- [x] C5 Tests `tests/test_app_*.py` (AppTest, mock and real+offline): scenario → confirm → results,
  unreadable photo, unchecked box, missing directions.

**2. After the MVP (to ~17:00), in this order**
- [x] C8 Summary page: English plain-language summary + reading grade. Hide es / zh
  (A9 translation not built, team decision).
- [x] C9 Teach-back quiz UI on the Summary page (A10 backend done and cached). Read-aloud cut.
- [ ] C14 Public HTTPS URL + QR code for judges.
- [ ] C13 Mobile app shell (below).
- [x] C16 Export the confirmed list as FHIR `MedicationStatement` JSON (`app/fhir.py`, `fhir.resources`).
  Only if C13 is done by 16:45.
- Cut for today: C6 graph, C7 PDF, C10 clinic view (A11 skipped by team decision; page removed in the one-page redesign).

**3. Demo and submission (17:30–18:45)**
- [ ] C11 `docs/DEMO.md`: replace the translation beat with reading grade + quiz; add the phone beat and the
  Solix close line; rehearse with `PILLWISE_MOCK=0 PILLWISE_OFFLINE=1`; backup video.
  Thursday kit: laptop charged, bottles, phone with Expo Go.
- [ ] C12 Slides / Devpost: problem, solution, architecture + platform diagrams (export from the team doc),
  guardrails, "why not ChatGPT" and privacy pitch lines, 3 screenshots (phone + web), data sources.

**Roadmap (after the hackathon)**
- Label-reading evals on the photo datasets (planning doc, Datasets tab); FHIR import.
- On-device OCR in the mobile app that drops the name and Rx lines before upload (privacy level 1).
- Local model for label reading (Ollama); needs a provider switch in `llm.py` (A) and a base-URL setting (main).
- ISMP high-alert badge on pill cards (needs a `PillCard` field: contract change).

### Mobile app for iOS and Android (C13–C15)
Phones are how most people would actually look up their medicines, and a native
app is easier to find and reopen than a URL.

- [x] **C13 (Should)** `mobile/`: Expo (React Native) app for iOS and
  Android that opens the PillWise web app in a full-screen WebView:
  - camera and photo-library permissions so "Take a photo" and "Upload" work in the app;
  - photos stay in memory only: nothing saved to the gallery or app storage (safety rule 6);
  - disclaimer on the launch screen, an offline / error screen with a retry button;
  - app name, icon and splash screen from `assets/`.
  Demo: scan the Expo Go QR code on any iPhone or Android phone, so no store review is needed.
- [ ] **C14 (Should, before C13)** Public HTTPS URL for the web app (Streamlit
  Community Cloud, or a tunnel on demo day). Phone cameras only work over HTTPS. `OPENAI_API_KEY` goes in
  the host's secrets store, never in git. Scenarios work offline from `data/cache/`; live photos need the key.
- [ ] **C15 (Could, after the hackathon)** Native screens over a small REST API,
  store builds with EAS, then App Store / Play Store submission.

Why a WebView shell first: the safety-critical rendering (severity, evidence,
pharmacist footer, "could not check" box) lives in one place (`app/components.py`).
Native screens would mean a second copy that could drift from it, plus a new HTTP API
(a contract change). That isn't worth the risk in one day.

## Done
- C1 Home: name-check hint, unreadable-photo message, same photo never added twice, editor resets when the list is replaced, empty rows ignored, "Start over"; `use_container_width` replaced.
- C2 Results: "could not check" box first (checker errors shown separately), count line by severity, severity color bar per card (`st-key-sev-*` CSS), `unknown` shown as "Not rated" and faded, openFDA quotes in quotation marks, pill card always shows how-to-take (A's fixed text when missing), "What we checked" (name -> ingredients).
- C3 Trust panel ("Sources and audit trail" on Results): data versions with readable names, every quoted FDA label (DailyMed link), report id, time and model. Shows the audit log for this report automatically once `api.recent_audit_events` exists (see Needs).
- C4 `.streamlit/config.toml`: teal primary color (red is reserved for "Serious"), developer toolbar hidden, 25 MB upload limit. Confirm-table column widths keep directions visible at 390 px. Checked with Playwright screenshots at 390 px and 1280 px.
- C5 `tests/test_app_smoke.py` (14 tests): Home renders with the name-check hint; scenario -> confirm -> report; Start over; unchecked box never says safe; "Not rated"; missing directions; trust panel; Results for all 3 scenarios in real offline mode (skips without `data/ddinter.sqlite`). Results opens via Home + `switch_page` (page links need Home as main script). Not covered: the unreadable-photo message, because AppTest cannot set a camera or upload value.

- C8 Summary page: A's English summary with reading level (target 6 or lower), sections colored by the finding they came from; es / zh hidden ("coming"). LLM calls run once per report (cached in session state), so quiz clicks never call the model again.
- C9 Teach-back quiz: 3 questions in a form, right / not quite with the checker's own explanation, score.
- Contract (repo final after A and B finished, 14:20): `api.recent_audit_events` + contract test; trust panel now shows this report's audit entries (9 per real report). CLAUDE.md: C owns `mobile/`, `.claude/skills/`, `.mcp.json`. TASKS.md: C13-C16. `.gitignore`: Expo build files, `.claude/settings.local.json`.
- Merged the last 2 b-data commits (generated test photos) that were not on main yet.
- Team tooling from the planning doc's MCP tab (research only, never in the app's runtime path): `.mcp.json` with openFDA, Context7, Kaggle and Hugging Face MCP servers (versions pinned, at least two weeks old); skills `pillwise-safety-review` (7 safety rules + CDC Clear Communication Index checks on a diff) and `pillwise-ui-screenshots` (Playwright, phone + desktop).
- C13 `mobile/` (Expo SDK 58, see `mobile/README.md`): launch screen with the disclaimer, camera permission, WebView in incognito (no cookies, cache or storage kept), offline screen with "Try again", Android back button. `npx tsc --noEmit` and `npx expo-doctor` (20/20) pass. NOT yet run on a phone: this Mac has no Xcode simulator or Android emulator.
- C16 `app/fhir_export.py`: "Download my list for my pharmacy (FHIR)" on Results; FHIR R4 Bundle of MedicationStatement, RxNorm coding when normalized, dosage text = label directions, subject is display-only (no identity). `tests/test_app_fhir.py` validates against `fhir.resources` R4B.
- Local label reader (roadmap, measured): `scripts/eval_label_reading.py` + `data/eval/label_truth.json` score an Ollama vision model on the committed photos. `qwen3-vl:8b-instruct`: names 10/10, strength 10/10, directions 9/10 (one cut-off label joined into a direction), ~5 s per photo on an M5 Pro. The default `qwen3-vl:8b` tag is the thinking model: `think: false` is ignored and it takes 30-360 s per photo.
- C11 `docs/DEMO.md` rewritten for the current app (no translation beat; phone, quiz, trust beats; judge Q&A; Thursday checklist).

- One-page redesign (15:45, design canvas https://claude.ai/artifact/BYwCYuwXWeDSMW7s7uATzG): `app/Home.py` is the whole app; Results, Summary and Clinic View pages removed. Verdict sentence, connections and questions for the pharmacist are built from findings by fixed rules in `app/components.py` (never re-rate). Medicine rows with "Matches my bottle" (unticked = orange), several photos read on upload, results hidden when the list changes, "Can I take this?" checks one new medicine against the list, larger-text toggle, summary download. Theme: Atkinson Hyperlegible, teal.
- All ages: copy no longer says "65+ checks"; `PillCard.special_groups` (contract, additive) quotes FDA label sentences about pregnancy, breastfeeding, children and women/men, picked by code from the label's population sections (`explain.group_notes`, tests in `tests/test_pipeline_groups.py`). No gender field: no rule uses it. `data/cache/` re-warmed online (labels now keep those sections; naproxen added for the Aleve demo).
- English user guide for the demo: https://claude.ai/artifact/8XNEENcSHW8WRqhTyRoQuP. `docs/DEMO.md` rewritten for the 5-minute recorded demo.

- Design v4 (17:00): age and medicines in one block; no "Matches my bottle" checkbox (unmatched names flagged by the RxNorm badge and a warning); results as a heatmap of the person's medicines (diagonal = the medicine alone, e.g. Beers), hover or tap a square for the finding and both medicines' purpose, tap a name on the left for "About this medicine"; full finding cards with sources in an expander. `mobile/README.md`: step-by-step phone use and iPhone Mirroring demo.

## Stubbed or still mock
- 

## How to run / verify my part
```bash
make check
make app                                   # mock mode
PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 make app   # real pipeline from data/cache (needs data/ddinter.sqlite and OpenAI model names in .env)
```

## Env vars or data my part needs
- 

## Needs from others
- main: done (see Done).
- A: the head-to-head number vs a plain chatbot, if built. B: a FAERS polypharmacy figure for the problem slide.

## Known issues / risks
- C13 needs a test on a real iPhone and Android phone (Expo Go) before Thursday.
- C14 (public HTTPS URL) not done: needs a tunnel or a host chosen by the team.
- C13 depends on C14 (public HTTPS URL) and on C4 (layout usable at phone width).

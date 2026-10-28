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
- [ ] C3 Trust panel: data versions + sources per finding; audit events once `api.recent_audit_events()` exists.
- [ ] C4 Layout usable at phone width (390 px); `.streamlit/config.toml`. Base for C13.
- [ ] C5 Tests `tests/test_app_*.py` (AppTest, mock and real+offline): scenario → confirm → results,
  unreadable photo, unchecked box, missing directions.

**2. After the MVP (to ~17:00), in this order**
- [ ] C8 Summary page: English plain-language summary + reading grade. Hide es / zh
  (A9 translation not built, team decision).
- [ ] C9 Teach-back quiz UI on the Summary page (A10 backend done and cached). Read-aloud cut.
- [ ] C14 Public HTTPS URL + QR code for judges.
- [ ] C13 Mobile app shell (below).
- [ ] C16 Export the confirmed list as FHIR `MedicationStatement` JSON (`app/fhir.py`, `fhir.resources`).
  Only if C13 is done by 16:45.
- Cut for today: C6 graph, C7 PDF, C10 clinic view (A11 skipped by team decision).

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

- [ ] **C13 (Should)** `mobile/`: Expo (React Native) app for iOS and
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
- Tests: `tests/test_app_smoke.py` opens Results via Home + `switch_page` (page links need Home as main script); 6 tests.

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
- main: `api.recent_audit_events(limit)` wrapping B's `audit.recent_events` for the trust panel (C3), additive.
- main (for C13): add `mobile/` to C's row in the CLAUDE.md ownership table; add
  `node_modules/` and `.expo/` to `.gitignore`; add C13–C16 to `docs/TASKS.md`.
- A: the head-to-head number vs a plain chatbot, if built. B: a FAERS polypharmacy figure for the problem slide.

## Known issues / risks
- C13 depends on C14 (public HTTPS URL) and on C4 (layout usable at phone width).

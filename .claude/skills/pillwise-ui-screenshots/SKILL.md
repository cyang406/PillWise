---
name: pillwise-ui-screenshots
description: Run the PillWise Streamlit app headless and take screenshots of the one-page app (list, results, trust panel) at phone (390 px) and desktop (1280 px) width with Playwright. Use to check a UI change visually, to check the phone layout, or to make Devpost / slide screenshots.
---

# PillWise UI screenshots

1. Make sure Playwright is in the venv (once): `uv pip install playwright && uv run --no-project python -m playwright install chromium`.
   It is a dev tool, so do not add it to `requirements/`.
2. Start the app in real offline mode (needs `data/ddinter.sqlite`; `make ddinter` builds it):
   ```bash
   PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 PILLWISE_MODEL_MAIN=gpt-4.1 PILLWISE_MODEL_FAST=gpt-4.1-mini \
     uv run --no-project streamlit run app/Home.py --server.headless true --server.port 8599
   ```
   Run it in the background and wait until `curl -sf localhost:8599/_stcore/health` succeeds.
   Use `PILLWISE_MOCK=1` instead when the DB is missing; the results then show the mock banner.
3. Take the shots (save them outside the repo, e.g. the scratchpad; screenshots are not committed):
   ```bash
   uv run --no-project python .claude/skills/pillwise-ui-screenshots/shots.py <OUT_DIR> --scenario "Warfarin nsaid"
   ```
   Sample labels are the file names in `data/scenarios/` with `_` as spaces, first letter capitalized.
4. Look at every image before reporting. Check: severity bands and icons, the verdict banner, the "could not check" box above the
   findings, no horizontal page scroll at 390 px, the disclaimer, and no mock banner in real mode.
5. Stop the app: `pkill -f "server.port 8599"`.

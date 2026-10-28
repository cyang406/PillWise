"""Click Home -> demo scenario -> Confirm -> Results and save screenshots at phone and desktop width.

usage: python shots.py OUT_DIR [--url http://localhost:8599] [--scenario "Warfarin nsaid"]
Needs: pip install playwright && python -m playwright install chromium; the app already running.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

SIZES = {"phone": (390, 844), "desktop": (1280, 900)}

ap = argparse.ArgumentParser()
ap.add_argument("out", type=Path)
ap.add_argument("--url", default="http://localhost:8599")
ap.add_argument("--scenario", default="Warfarin nsaid")
args = ap.parse_args()
args.out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (w, h) in SIZES.items():
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(args.url)
        page.get_by_text("Demo scenario").click()
        page.get_by_role("combobox").first.click()
        page.get_by_role("option", name=args.scenario).click()
        page.get_by_role("button", name="Load scenario").click()
        page.wait_for_timeout(1500)
        page.screenshot(path=args.out / f"home_{name}.png", full_page=True)
        page.get_by_role("button", name="Confirm and check").click()
        page.get_by_text("Your medicine check").wait_for(timeout=60000)
        page.wait_for_timeout(2000)
        page.screenshot(path=args.out / f"results_{name}.png", full_page=True)
        page.get_by_text("Sources and audit trail").click()
        page.wait_for_timeout(800)
        page.get_by_text("Sources and audit trail").scroll_into_view_if_needed()
        page.screenshot(path=args.out / f"trust_{name}.png")
        page.close()
    browser.close()
print(f"saved to {args.out}")

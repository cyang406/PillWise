---
name: pillwise-safety-review
description: Review a PillWise diff or branch against the seven safety rules in CLAUDE.md and the plain-language rules for patient-facing text. Use before every commit that touches pillwise/, app/ or data/, and before every merge into main.
---

# PillWise safety review

Review the change (default: `git diff main...HEAD`; or the diff, branch or PR the user names) and report
every violation with `file:line`, the rule it breaks, and the smallest fix. Report "no findings" only after
checking every rule below. Never weaken a rule to make a change pass.

## 1. Safety rules (CLAUDE.md), with what to look for

| Rule | Violation looks like |
| --- | --- |
| 1. Rules and data decide; the LLM only reads and explains | Any code where an LLM output sets, drops, upgrades or downgrades a `Finding` (its `severity`, `kind`, `drugs`), or creates a `Finding` outside `pillwise/checks/` |
| 2. Directions are copied, never generated | `Medication.directions` or `PillCard.how_to_take` filled from an LLM rewrite, an FDA label or a template; any dosing advice in UI text, prompts or summaries |
| 3. "Not found" is never "safe" | A medicine that could not be normalized or checked missing from `Report.unchecked`; UI text that says "safe", "no risk" or "all clear"; an empty list shown as reassurance |
| 4. Every finding has evidence | A `Finding` without `Evidence` (source + version); an openFDA quote that is not verified as an exact substring of the label |
| 5. Pharmacist footer | Code that strips or rewrites `SAFETY_FOOTER` from `what_to_do` |
| 6. Privacy | Photos, raw label text, names, Rx numbers or ages written to disk, logs, cache or audit; image calls cached; `.env` or keys committed |
| 7. Copyright | Beers Criteria text copied verbatim instead of summarized with a citation |

Also check: no network in tests (`tests/` must use `data/cache/` or `tests/fixtures/`); `app/` imports only
`pillwise.api`, `pillwise.schemas` (and `pillwise.config` for the mock caption); `logging`, not `print`, in
`pillwise/`.

Quick searches to start from (each hit still needs reading in context):

```bash
git diff main...HEAD -- pillwise app data | grep -nE '^\+.*(severity|kind|drugs)\s*=' 
git diff main...HEAD -- app pillwise | grep -niE '^\+.*\b(safe|no risk|all clear)\b'
git diff main...HEAD -- app pillwise | grep -nE '^\+.*(how_to_take|directions)\s*='
git diff main...HEAD | grep -nE '^\+.*(print\(|os\.getenv)' 
git diff main...HEAD --name-only | grep -E '\.env$|\.(jpg|jpeg|png|heic)$'
```

## 2. Patient-facing text (UI copy, finding texts, summaries)

Grounded in the CDC Clear Communication Index (https://www.cdc.gov/ccindex/) and AHRQ PEMAT
(https://www.ahrq.gov/health-literacy/patient-education/pemat1.html):

- The main message comes first, in one short sentence.
- One clear action for the reader ("Ask your pharmacist before taking these together").
- Plain words; explain any medical term the first time it appears.
- Sentences under about 20 words; active voice.
- Numbers only when the reader needs them, and never as a dose.
- Severity is shown with a word, not only a color (color-blind readers).

## Output

A table: `file:line` · rule · what is wrong · smallest fix. Then one line: "safe to merge" or "fix before merge".

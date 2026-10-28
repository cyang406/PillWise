# Data sources

Owner: B. Every source used in the app must be listed here with its license
note and the version shown in `Evidence.version`.

| Need | Source | Access | License / use notes | Used in |
| --- | --- | --- | --- | --- |
| Drug name → RxCUI, ingredients | [RxNorm API (NLM)](https://lhncbc.nlm.nih.gov/RxNav/) | REST, free, no key | Public. RxNav's interaction API was discontinued Jan 2, 2024; we only use name lookup | `normalize.py` |
| Drug-drug interactions, severity | [DDInter 2.0](https://ddinter2.scbdd.com) ([paper](https://academic.oup.com/nar/article/53/D1/D1356/7740584)) | CSV download, no registration | Free for academic use; check the site's Terms page before the demo and note it here | `checks/ddinter.py` |
| Label text for quotes | [openFDA Drug Label API](https://open.fda.gov/apis/drug/label/) | REST, key optional | Public domain | `evidence.py`, `explain.py` |
| Always-flag pairs | ONC high-priority DDI list ([Phansalkar 2012, JAMIA](https://doi.org/10.1136/amiajnl-2011-000612)) | hand-coded `data/onc_high.json` | Summarized in our words, cited | `checks/onc.py` |
| Older-adult risk | [2023 AGS Beers Criteria](https://pubmed.ncbi.nlm.nih.gov/37139824/) | hand-coded `data/beers.json` | Copyrighted: our own summaries + citation only | `checks/beers.py` |
| Synthetic patients (stretch B) | [Synthea](https://synthetichealth.github.io/synthea/) | Java generator | Apache 2.0; synthetic only | `agents/clinic.py` |

## Test photos (`data/photos/`, B9)

Committed on purpose with `git add -f` (the folder is git-ignored by default). All from
Wikimedia Commons under Creative Commons licenses; attribution below. No personal data:
names are blacked out in the source or blurred by us.

| File | Shows | Author / source | License | Changes |
| --- | --- | --- | --- | --- |
| `bottle_1.png` | Warfarin sodium 5 mg (Rx) | [Walgreens Prescription Bottle](https://commons.wikimedia.org/wiki/File:Walgreens_Prescription_Bottle.jpg) | CC BY-SA 3.0 | none |
| `bottle_2_blurred.png` | Prednisone 20 mg, amoxicillin 500 mg, hydrocodone/APAP 5-500 | Bart Szyszka via Flickr, [Commons](https://commons.wikimedia.org/wiki/File:ClearRx_prescription_bottles_-_Flickr_-_bartsz.jpg) | CC BY 2.0 | name and address blurred |
| `bottle_3.png` | Oxycodone 5 mg | Cindy Shebley via Flickr, [Commons](https://commons.wikimedia.org/wiki/File:Oxycodone_Prescription_Bottle_with_Pills_Spilling_Out._(41201105871).jpg) | CC BY 2.0 | none |
| `bottle_4.png` | Nateglinide 60 mg | Grendelkhan, [Commons](https://commons.wikimedia.org/wiki/File:Nateglinide_60_mg_bottle,_Zydus,_front_view.jpg) | CC BY-SA 4.0 | none |
| `bottle_5.png` | Jardiance (empagliflozin) 10 mg | Grendelkhan, [Commons](https://commons.wikimedia.org/wiki/File:Jardiance_10mg_bottle,_front_view.jpg) | CC BY-SA 4.0 | none |
| `bottle_7.png` | Ibuprofen 200 mg (Safeway generic, OTC) | Wikimedia Commons (Safeway generic ibuprofen) | CC0 | none |

`bottle_1.png` (warfarin) + `bottle_7.png` (ibuprofen) cover the main demo scenario (`warfarin_nsaid`). The others are for testing label reading (A2).
Optional, not found yet: acetaminophen, diphenhydramine, oxybutynin, lisinopril, loratadine (the scenarios work without photos).

## DDInter download steps

1. Open https://ddinter2.scbdd.com → Download.
2. Save the interaction CSV file(s) into `data/raw/ddinter/` (git-ignored).
3. Open one file and confirm the header; edit `COLUMN_ALIASES` in `scripts/load_ddinter.py` if needed.
4. `make ddinter` → `data/ddinter.sqlite`.

## Verification checklist (B3 / B5)

A person checks each entry against the paper, ticks it here, then flips
`"verified": true` in the JSON (or edits / deletes the entry). The notes are hints on
where to look and what we are unsure about; they are not the verification.

For every entry check: (1) the paper really lists it, (2) the drug names in our list
are covered by it (remove any that are not), (3) our `risk` / `advice` text says the
same thing in our own words and does not add anything.

### Beers 2023: `data/beers.json` → [paper](https://pubmed.ncbi.nlm.nih.gov/37139824/)

Single drugs (`drugs`; most are in Table 2, "potentially inappropriate medications"):

- [x] `first_gen_antihistamines`: Table 2, first-generation antihistamines. Check that all 5 names are listed.
- [x] `benzodiazepines`: Table 2.
- [x] `z_drugs`: Table 2, nonbenzodiazepine hypnotics.
- [x] `nsaids_nonselective`: Table 2, "avoid chronic use". Check each of the 10 names; check the wording about stomach protection.
- [x] `aspirin_primary_prevention`: Table 2 (wording changed in 2023). Check our "started at an older age" phrasing.
- [x] `sulfonylureas`: Table 2 (2023 widened this to all sulfonylureas). Check the 3 names.
- [x] `muscle_relaxants`: Table 2, skeletal muscle relaxants. Check all 5 names.
- [x] `ppis_long_term`: Table 2, "avoid scheduled use > 8 weeks" unless high risk. Check the 6 names.
- [x] `warfarin_first_line`: Table 2 (new in 2023): avoid starting warfarin as first choice for AF / VTE. Check wording.
- [x] `anticholinergic_antidepressants`: Table 2, antidepressants with strong anticholinergic activity. Check the 4 names.
- [x] `bladder_antimuscarinics`: **removed.** Not a Table 2 criterion; only Table 3 (delirium, dementia, falls) and Table 7. The drugs stay in `tags.anticholinergic`.
- [x] `metoclopramide`: Table 2.
- [x] `meperidine`: Table 2.
- [x] `megestrol`: Table 2.
- [x] `mineral_oil_oral`: Table 2.

Combinations (`combos`; Table 5, "drug-drug interactions to avoid"):

- [x] `two_anticholinergics`: Table 5, anticholinergic + anticholinergic. Also check the `tags.anticholinergic` list against Table 7 (strong anticholinergic drugs).
- [x] `three_cns_active`: Table 5, three or more CNS-active drugs. Check `tags.cns_active` against the classes the paper names.
- [x] `opioid_benzodiazepine`: Table 5.
- [x] `opioid_gabapentinoid`: Table 5. Check `tags.gabapentinoid`.
- [x] `warfarin_antibiotic`: Table 5, warfarin + certain antibiotics. Check which antibiotics are named (`tags.warfarin_risky_antibiotic`).

### ONC high-priority list: `data/onc_high.json` → [paper](https://doi.org/10.1136/amiajnl-2011-000612)

Checked against Table 2 (final accepted interactions). The paper says its class lists are not complete.

- [x] `statin_cyp3a4`: all names in Table 2. Summary reworded (the muscle-damage text belonged to a different pair).
- [x] `methotrexate_trimethoprim`: **removed.** Not in the paper.
- [x] `tizanidine_cyp1a2`: names in Table 2. Summary reworded (no symptoms stated in the paper).
- [x] `maoi_serotonergic`: **split into 3 rules** matching Table 2: `maoi_amphetamine_derivatives` (pseudoephedrine; selegiline left out because the paper flags its MAO-B selectivity there), `maoi_serotonergic` (SSRIs/SNRIs), `maoi_narcotic` (tramadol, meperidine, dextromethorphan). Summaries reworded.
- [x] `atazanavir_ppi`: names in Table 2. Summary reworded (no mechanism stated in the paper).
- [x] `ramelteon_fluvoxamine`: in Table 2. Summary reworded.

After flipping a flag, run `make check` and `make scenarios-real` (the `safe_otc`
scenario must still show nothing above minor).

## Verification log

| Date | Item | Checked against | By |
| --- | --- | --- | --- |
| 2026-10-28 | Beers: all 15 single-drug + 5 combo entries | 2023 AGS Beers Criteria, Tables 2, 3, 5, 7, 8 | B (team member) |
| 2026-10-28 | Beers fixes: ketoprofen removed (moved to Table 8); `bladder_antimuscarinics` removed; meperidine risk reworded; `warfarin_antibiotic` risk/advice reworded; conditions/exceptions added to sulfonylureas, PPIs, warfarin, metoclopramide, opioid + gabapentinoid; "do not stop suddenly" dropped where the criterion does not say it; `cns_active` / `opioid` tags extended (fentanyl, tapentadol, meperidine, metaxalone, orphenadrine) | same | B |
| 2026-10-28 | ONC: all rules; methotrexate + trimethoprim removed; MAOI rule split into 3; every summary reduced to "on an expert list of pairs that should not be prescribed together" | Phansalkar 2012, Table 2 | B |

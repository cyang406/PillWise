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

## DDInter download steps

1. Open https://ddinter2.scbdd.com → Download.
2. Save the interaction CSV file(s) into `data/raw/ddinter/` (git-ignored).
3. Open one file and confirm the header; edit `COLUMN_ALIASES` in `scripts/load_ddinter.py` if needed.
4. `make ddinter` → `data/ddinter.sqlite`.

## Verification log

| Date | Item | Checked against | By |
| --- | --- | --- | --- |
| | | | |

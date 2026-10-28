#!/usr/bin/env bash
# Stretch B: generate a synthetic 65+ population with Synthea. Owner: B.
# Needs Java 17+. Output goes to data/raw/synthea/ (git-ignored).
#
# TODO(B):
#   - Download the Synthea jar (https://github.com/synthetichealth/synthea/releases).
#   - Run, e.g.: java -jar synthea-with-dependencies.jar -p 200 -a 65-95 --exporter.csv.export=true
#   - Write scripts/load_synthea.py: CSVs -> data/synthea.duckdb (tables: patients, medications).
set -euo pipefail
echo "gen_synthea.sh: not implemented yet (stretch B)" >&2
exit 1

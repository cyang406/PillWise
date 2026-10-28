"""Build data/ddinter.sqlite from DDInter CSV downloads. Owner: B.

Usage:
    python scripts/load_ddinter.py                      # reads data/raw/ddinter/*.csv
    python scripts/load_ddinter.py path/a.csv path/b.csv
    python scripts/load_ddinter.py tests/fixtures/ddinter_sample.csv --db /tmp/test.sqlite

Expected CSV columns (case-insensitive): DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level.
B: open one downloaded file first and adjust COLUMN_ALIASES if the headers differ.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pillwise.config import DATA_DIR, get_settings  # noqa: E402

COLUMN_ALIASES = {
    "id_a": ["ddinterid_a", "id_a"],
    "drug_a": ["drug_a", "drug a"],
    "id_b": ["ddinterid_b", "id_b"],
    "drug_b": ["drug_b", "drug b"],
    "level": ["level", "severity"],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS interactions (
    drug_a TEXT NOT NULL,   -- lower-case name, alphabetically <= drug_b
    drug_b TEXT NOT NULL,
    level  TEXT NOT NULL,   -- major | moderate | minor | unknown
    id_a   TEXT,
    id_b   TEXT,
    source_file TEXT,
    PRIMARY KEY (drug_a, drug_b)
);
CREATE INDEX IF NOT EXISTS idx_b ON interactions(drug_b);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


def _resolve(header: list[str]) -> dict[str, int]:
    lower = [h.strip().lower() for h in header]
    out = {}
    for key, aliases in COLUMN_ALIASES.items():
        for a in aliases:
            if a in lower:
                out[key] = lower.index(a)
                break
        else:
            if key in ("drug_a", "drug_b", "level"):
                raise SystemExit(f"Missing column for {key}; header was {header}")
    return out


def load(csv_paths: list[Path], db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    n = 0
    for p in csv_paths:
        with p.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            cols = _resolve(next(reader))
            for row in reader:
                a, b = row[cols["drug_a"]].strip().lower(), row[cols["drug_b"]].strip().lower()
                if not a or not b:
                    continue
                if a > b:
                    a, b = b, a
                level = row[cols["level"]].strip().lower() or "unknown"
                con.execute(
                    "INSERT OR REPLACE INTO interactions VALUES (?,?,?,?,?,?)",
                    (
                        a,
                        b,
                        level,
                        row[cols["id_a"]] if "id_a" in cols else None,
                        row[cols["id_b"]] if "id_b" in cols else None,
                        p.name,
                    ),
                )
                n += 1
    con.execute("INSERT OR REPLACE INTO meta VALUES ('version', '2.0')")
    con.commit()
    con.close()
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="*", type=Path)
    ap.add_argument("--db", type=Path, default=None)
    args = ap.parse_args()
    paths = args.csv or sorted((DATA_DIR / "raw" / "ddinter").glob("*.csv"))
    if not paths:
        raise SystemExit("No CSVs found. Download DDInter CSVs into data/raw/ddinter/ (see docs/DATA_SOURCES.md).")
    db = args.db or get_settings().ddinter_db
    n = load(paths, db)
    print(f"Loaded {n} rows from {len(paths)} file(s) into {db}")


if __name__ == "__main__":
    main()

"""Score a local Ollama vision model on reading our bottle photos (roadmap: local label reader).

Not part of `make check` (needs Ollama running). Example:
    ollama pull qwen3-vl:8b-instruct
    python scripts/eval_label_reading.py qwen3-vl:8b-instruct
    python scripts/eval_label_reading.py qwen3-vl:8b-instruct --no-validate   # model output as is

Scores per medicine on the label: name found, strength digits match, directions exact (or both null).
A wrong non-null direction is the dangerous error (safety rule 2), so it is counted separately.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRUTH = ROOT / "data" / "eval" / "label_truth.json"
PHOTOS = ROOT / "data" / "photos"

PROMPT = """You transcribe medicine labels from a photo. List every medicine whose label you can read.

For each medicine:
- name: the medicine name exactly as printed (brand or generic). Not the pharmacy, not the patient.
- strength: only the amount with its unit as printed, e.g. "5MG", "200 mg", "5-500". Nothing else.
- directions: ONLY the instruction that tells the patient how to take or use it, copied word for word,
  e.g. "TAKE 1 TABLET BY MOUTH EVERY DAY". It almost always starts with a verb such as Take, Use,
  Apply, Chew, Inhale or Place.
  These are NOT directions, so use null for them: what the medicine is for ("Pain Reliever / Fever
  Reducer"), warning or caution stickers ("May cause drowsiness", "Take this medicine with food" on a
  colored sticker), quantity, refills, dates, and anything cut off or partly hidden.

Rules: copy text exactly; never complete a cut-off word; never guess. Use null when unsure.
If no label is readable, return an empty list."""

SCHEMA = {
    "type": "object",
    "properties": {
        "medicines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {k: {"type": ["string", "null"]} for k in ("name", "strength", "directions")},
                "required": ["name", "strength", "directions"],
            },
        }
    },
    "required": ["medicines"],
}

DOSING_VERB = re.compile(
    r"^\s*(take|use|apply|chew|inhale|place|insert|dissolve|swallow|instill|inject|give|spray|mix|rub)\b", re.I
)


def validate(med: dict) -> dict:
    """Code check after the model: directions must start with a dosing verb, else null (safe failure)."""
    d = med.get("directions")
    return {**med, "directions": d if d and DOSING_VERB.match(d) else None}


def norm(s: str | None) -> str:
    return " ".join((s or "").lower().split())


def digits(s: str | None) -> str:
    return "".join(re.findall(r"[\d.\-]+", s or ""))


def read(model: str, photo: Path) -> tuple[list[dict], float]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT, "images": [base64.b64encode(photo.read_bytes()).decode()]}],
        "format": SCHEMA,
        "think": False,
        "stream": False,
        "keep_alive": "30m",
        "options": {"temperature": 0, "num_ctx": 8192},
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    t = time.time()
    out = json.loads(urllib.request.urlopen(req, timeout=900).read())
    return json.loads(out["message"]["content"] or '{"medicines": []}')["medicines"], time.time() - t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--no-validate", action="store_true", help="score the raw model output")
    args = ap.parse_args()
    truth = {k: v for k, v in json.loads(TRUTH.read_text()).items() if not k.startswith("_")}

    totals = {"meds": 0, "name": 0, "strength": 0, "directions": 0, "wrong_directions": 0}
    seconds = []
    for photo, expected in truth.items():
        got, secs = read(args.model, PHOTOS / photo)
        seconds.append(secs)
        if not args.no_validate:
            got = [validate(m) for m in got]
        print(f"== {photo} ({secs:.1f}s)")
        for exp in expected:
            match = next((g for g in got if exp["name"] in norm(g.get("name"))), None)
            totals["meds"] += 1
            if match is None:
                print(f"   MISSING {exp['name']}")
                continue
            ok_s = digits(match.get("strength")) == digits(exp["strength"])
            ok_d = norm(match.get("directions")) == norm(exp["directions"])
            wrong_d = match.get("directions") is not None and not ok_d
            totals["name"] += 1
            totals["strength"] += ok_s
            totals["directions"] += ok_d
            totals["wrong_directions"] += wrong_d
            flag = "  <-- WRONG DIRECTIONS" if wrong_d else ""
            print(f"   {exp['name']}: strength {'ok' if ok_s else 'x'} | directions {'ok' if ok_d else 'x'}{flag}")
            if not ok_d:
                print(f"      got: {match.get('directions')!r}")
    n = totals["meds"]
    print(
        f"\n{args.model}: names {totals['name']}/{n}, strength {totals['strength']}/{n}, "
        f"directions {totals['directions']}/{n}, wrong (non-null) directions {totals['wrong_directions']}, "
        f"median {sorted(seconds)[len(seconds) // 2]:.1f}s per photo"
    )


if __name__ == "__main__":
    main()

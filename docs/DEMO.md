# Demo script (owner: C)

Two minutes. Judging is in person on Thursday 2026-10-29. Rehearse in real offline mode, so the demo
does not depend on venue Wi-Fi for the scripted scenarios:

```bash
PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 uv run --no-project make app
```

Live photo reading still needs network and `OPENAI_API_KEY`; if the network fails, use the
"Demo scenario" tab (same results, served from `data/cache/`).

1. **Hook (15 s):** many older adults take medicines from several doctors; nobody sees the whole list.
   Hold up the bottles.
2. **Capture (30 s):** on the phone (Expo Go app), photograph the warfarin bottle; the list appears.
   Point at the hint "Check each name against the bottle" and correct one field to show the confirm step.
   Add ibuprofen and acetaminophen (photo or "Demo scenario" → Warfarin nsaid).
3. **Red flag (30 s):** the red "Serious" card: warfarin + ibuprofen. Open "Where this comes from":
   the DDInter record and the exact FDA label sentence, with its version and DailyMed link.
   Show the "Not rated" card: we say what the database does not know instead of guessing.
4. **Understand (20 s):** "Read a plain-language summary": reading level 5.1 (target 6 or lower),
   then answer one teach-back question.
5. **Trust (15 s):** "Sources and audit trail": every data version, every FDA label quoted, and the audit
   log entries for this report. Line: "The AI only reads and explains; rules and data decide."
6. **Close (10 s):** "Governed data in, explained and sourced answers out: the same pattern Solix applies
   to enterprise data, pointed at a patient's kitchen table."

## If a judge asks

- **Why not just ChatGPT?** A chatbot's answers can change between runs and it can't show where they
  came from. PillWise gives the same answer every time, cites the FDA label or a curated database for
  every warning, and says "we couldn't check this" instead of guessing.
- **Privacy?** The safety checks never need your name, so they run locally. Only label reading and
  plain-language rewriting use a model, and photos are never stored or cached.
- **Could it run on a local model?** We measured it (`scripts/eval_label_reading.py`): Qwen3-VL 8B on a
  laptop read 10 of 10 names and strengths in about 5 seconds a photo, but on one cut-off label it joined
  two fragments into a direction. That is exactly why a person confirms the list and why directions are
  only ever copied, never generated. A local model is on the roadmap.

## Checklist for Thursday

- [ ] Laptop charged; `data/ddinter.sqlite` built; `make check` green.
- [ ] Bottles packed (warfarin, ibuprofen, acetaminophen).
- [ ] Phone with Expo Go installed; app opens over the public URL (C13, C14).
- [ ] Offline rehearsal done with Wi-Fi off.

Backup: recorded video link here:

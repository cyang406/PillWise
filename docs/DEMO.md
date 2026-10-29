# Demo script (owner: C)

**Submission rules (2026-10-28):** one 5-minute recorded demo per team; Devpost draft by 18:00, final submit
by 19:00. Judging is in person on Thursday 2026-10-29.

User guide with screenshots (share it on Devpost and in the video description):
https://claude.ai/artifact/8XNEENcSHW8WRqhTyRoQuP (private until shared from its Share menu).

## Before recording

```bash
uv run --no-project make check                                  # green
PILLWISE_MOCK=0 uv run --no-project make app                    # live: needs OPENAI_API_KEY in .env
# no network? PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 ... make app   # samples + "Aleve" work from data/cache
```

Have ready: `data/photos/bottle_1.png` (warfarin) and `data/photos/gen_ibuprofen_200mg.png`, the phone with
Expo Go (see `mobile/README.md`), browser zoom at 125% so text reads on video.

## Script (5:00)

| Time | Beat | Show | Say |
| --- | --- | --- | --- |
| 0:00 | Problem | Bottles on the table | Many people take medicines from several doctors and the pharmacy shelf. Nobody sees the whole list, and a chatbot can't show where its answer came from. |
| 0:40 | Add | Type the age, upload both photos at once; names appear with "Matched: …". Type "Acetaminophen 500 mg". | Labels are read by AI and every name is looked up in RxNorm; one we can't match is flagged before anything is checked. Photos are never stored. |
| 1:40 | Verdict | Check my list. The verdict banner, then the heatmap: hover the red square. | One sentence says what to do today. The level comes from DDInter, not from the AI; hover shows what was found and what each medicine is for; the findings list has the DDInter record and the exact FDA label sentence. |
| 2:30 | Understand | Tap "Warfarin" on the left of the heatmap (About this medicine): directions copied from the label, the pregnancy quotes; the summary at reading level 5.1; answer one quiz question. | Anyone can use this, at any age, with no pharmacology background. Directions are copied, never generated; what the label says about pregnancy and children is quoted exactly. |
| 3:20 | Act | Questions to ask; Share; Pharmacy file (FHIR). Then "Buying something new?" with Aleve. | You leave with questions for your pharmacist, a file for family and one their system can import. Before buying Aleve: it is Serious with warfarin. |
| 4:10 | Trust + phone | Sources and audit trail; then the phone app: launch disclaimer, Take a photo. | Every claim has a source, a version and an audit entry. Same page on iPhone and Android. |
| 4:40 | Close | Verdict banner | Rules and data decide; AI only reads and explains. Governed data in, sourced answers out: the pattern Solix applies to enterprise data, pointed at a kitchen table. |

## Phone part of the demo (iPhone)

Step by step, including iPhone Mirroring: `mobile/README.md`. In short: Expo Go on the iPhone, the web app
on the Mac, `EXPO_PUBLIC_PILLWISE_URL=http://<Mac IP>:8501 npx expo start`, scan the QR code; then lock the
iPhone and open iPhone Mirroring on the Mac to drive and screen-record it. The camera doesn't work while
mirroring, so pick bottle photos from the library there, and record the live-camera shot separately
with QuickTime (iPhone by cable as the camera).

## If a judge asks

- **Why not just ChatGPT?** A chatbot's answers can change between runs and can't show where they came from.
  PillWise gives the same answer every time, cites the FDA label or a curated database for every warning,
  and says "we couldn't check this" instead of guessing.
- **Privacy?** The checks never need your name. Photos are only read, never stored or cached; the audit log
  keeps sources and versions, not label text or age.
- **Could it run on a local model?** We measured it (`scripts/eval_label_reading.py`): Qwen3-VL 8B on a
  laptop read 10 of 10 names and strengths in about 5 seconds a photo, but on one cut-off label it joined
  two fragments into a direction. That is exactly why a person confirms the list and why directions are
  only ever copied, never generated. A local model is on the roadmap.
- **Why no gender field?** No rule in our sources changes with it, so asking would collect data we don't
  use. What labels say about pregnancy, breastfeeding and children is quoted on every medicine card.

## Checklist for Thursday

- [ ] Laptop charged; `data/ddinter.sqlite` built; `make check` green.
- [ ] Bottles packed (warfarin, ibuprofen, acetaminophen).
- [ ] Phone with Expo Go; app opens over the public URL (C13, C14).
- [ ] Offline rehearsal done with Wi-Fi off.

Backup: recorded video link here:

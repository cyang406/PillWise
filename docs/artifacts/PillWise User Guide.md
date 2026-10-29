PillWise

# Snap your pills. Understand them. Stay safe.

Photograph your medicine bottles, confirm the list, and get one page that says what to ask your pharmacist, explains each medicine in plain words, and shows where every warning comes from.

Rules and data decide every warning. AI only reads labels and explains.

Anyone, any ageNo pharmacology background neededPeople taking several medicinesCaregivers and familyShoppers choosing an over-the-counter medicine

## Everything on one page

Your medicines at the top, what we found in the middle, and what to take to your pharmacist at the bottom. The same page runs in a web browser and inside the PillWise phone app for iPhone and Android.

![PillWise on a laptop: the verdict banner, a red Serious card for ibuprofen with warfarin, and a side panel showing how the medicines connect](img/desktop.jpg)

## How to use it

Screenshots show the sample list "Warfarin nsaid": a 72-year-old taking warfarin (a blood thinner), ibuprofen and acetaminophen.

01

### Add your medicines

- Add bottle photos: pick one or several photos. Each label is read as soon as it arrives. On a phone browser, this also offers the camera.
- Take a photo: in the phone app, point the camera at the label.
- Type a medicine: enter the name, and the strength and directions if you have them.
- Try a sample list: three ready-made lists to see how it works.

Photos are used only to read the label and are never stored. If a label can't be read, PillWise says so and asks you to type it in. It never guesses.

![The start of the page: disclaimer, Add bottle photos, Type a medicine, Try a sample list](img/1_start.jpg)

02

### Check each name against the bottle

Every medicine gets its own row with the directions copied from the label. Tick Matches my bottle once you have compared it. A misread letter can turn one real medicine into another, so an unticked row stays outlined in orange.

- Edit fixes a name, strength or directions. Remove drops a row.
- Age is optional. Some checks depend on it, such as extra care at 65 or older. It is never saved.
- Nothing is checked until you press Check my list. If you change the list later, the old results disappear until you check again.

![Medicine rows: ibuprofen ticked, acetaminophen not ticked and outlined in orange, a reminder to check it, and the Check my list button](img/2_list.jpg)

03

### Read the verdict first

One sentence tells you what to do today, built from the most serious finding. Below it, the count of findings at each level:

Serious Important Extra care Not rated

Each level also has its own icon shape, so color is never the only cue. If a medicine could not be checked, a red box lists it and says plainly that this does **not** mean it is safe. When nothing is found, the page still says that this is not a promise of safety.

![Verdict: Ask your pharmacist about ibuprofen with warfarin before your next dose. 1 Serious, 1 Important, 2 Extra care, 1 Not rated](img/3_verdict.jpg)

04

### See why, and where it comes from

Every finding card says what it means and what to do, and ends with “Talk to your pharmacist or doctor before changing anything.” Open Where this comes from to see the source:

- **DDInter 2.0**: the drug-interaction record and its level.
- **FDA label**: the exact sentence, in quotation marks, with the label date and a DailyMed link. Code checks that each quote really appears in the label.
- **AGS Beers Criteria 2023**: older-adult guidance, summarized in our own words with a citation.

![Serious card for ibuprofen and warfarin with the DDInter record and an exact FDA label quote](img/4_finding.jpg)

05

### See how your medicines connect

A short list shows which two of your medicines interact and how seriously. Next to it, What we checked shows the active ingredient each name was matched to (for example Advil → ibuprofen). If a match looks wrong, fix the name and check again.

![How your medicines connect: ibuprofen and warfarin Serious, acetaminophen and warfarin Important, acetaminophen and ibuprofen Not rated](img/5_connect.jpg)

06

### Each medicine, in plain words

- **For**: what the medicine treats, from its FDA label.
- **How to take, from your label**: copied word for word from your bottle. PillWise never writes dosing advice. If your label had no directions, it says so.
- **Watch for**: the key warnings from the label.
- Chips such as Serious with ibuprofen link the medicine to its findings.
- Pregnancy, breastfeeding, children: what the label says: the FDA label's own sentences for these groups, quoted exactly. PillWise asks nothing about you to show them.

![Warfarin card: how to take from the label, watch for, chips, and exact FDA label quotes about pregnancy](img/6_pill.jpg)

07

### Take this to your pharmacist

- **Questions to ask**: one question per finding, most important first.
- **In short**: a plain-language summary checked to a 6th-grade reading level or lower (this one is 5.1).
- **Check your understanding**: three quick questions to make sure the main points landed.
- Download a summary to share with family, or File for the pharmacy (FHIR), a standard health-record file with no personal details.

![Questions to ask, numbered and tagged by level, and the plain-language summary with its reading level](img/7_pharmacist.jpg)

08

### Can I take this with my list?

Standing in the pharmacy aisle? Type the name of a new medicine, for example Aleve. PillWise checks it against your list without changing the list, and shows only what involves the new medicine. Here, Aleve (naproxen) is Serious with warfarin and Important with the ibuprofen already on the list.

![Thinking of buying something new: Aleve becomes naproxen, with a Serious card for naproxen and warfarin](img/8_newmed.jpg)

09

### Check the sources yourself

Sources and audit trail at the bottom lists every data source and version, every FDA label quoted, the report ID, the AI model used (which only reads labels and explains), and the audit-log entries recorded for this report.

![Sources and audit trail: DDInter 2.0, ONC list, Beers 2023, FDA labels, report details and audit log entries](img/9_sources.jpg)

## Built so the AI can't make up a warning

Each feature has a guardrail behind it.

| Feature | What you see | The guardrail |
| --- | --- | --- |
| Reading labels | Several bottles at once | Photos are never stored, cached or logged |
| Confirm step | A tick per medicine | Nothing is checked until you confirm |
| Findings | Serious, Important, Extra care, Not rated | Levels come only from DDInter, the ONC list and Beers 2023; AI can't add, drop or change one |
| Verdict and questions | What to do today, what to ask | Built from the findings by fixed rules, not written by AI |
| Sources | Exact FDA quotes with versions | Each quote is verified as an exact substring of the label |
| Could not check | A red box | “Not found” is never shown as “safe” |
| How to take | Directions from your label | Copied, never generated; no dosing advice |
| Pregnancy and children | Label quotes for these groups | Quoted exactly; no personal data asked |
| Plain-language summary | Reading level 6 or lower | Rewrites can't add or drop a medicine name or add a dose |
| Audit trail | Source and version per claim | Stores sources and versions only: no photos, label text or age |

## Web and phone

### Web

Open PillWise in any browser. Use Add bottle photos for pictures; on a phone browser it also offers the camera.

### iPhone and Android app

The same page in a native app, with a Take a photo button, a launch screen with the disclaimer, and an offline screen. For the demo it runs in Expo Go: install Expo Go and scan the QR code.

## A 5-minute demo path

For the recorded demo. It runs offline from cached data, except for the live photo in step 2.

1. 0:00**The problem.** Many people take medicines from several doctors and the pharmacy shelf, and nobody sees the whole list.
2. 0:40**Add.** Upload two bottle photos (warfarin, ibuprofen) and show the names being read. Type acetaminophen. Untick one row to show the orange check, then tick it.
3. 1:40**Verdict.** Check my list. Read the one-line verdict, then open the red card's sources: the DDInter record and the exact FDA sentence.
4. 2:30**Understand.** Show the connections, a medicine card with label directions and the pregnancy quotes, the plain-language summary (reading level 5.1) and one quiz answer.
5. 3:20**Act.** Questions to ask, download for family, the FHIR file. Then “Can I take this?” with Aleve: Serious with warfarin.
6. 4:10**Trust and phone.** Sources and audit trail; then the same page in the phone app taking a photo.
7. 4:40**Close.** Rules and data decide, AI only reads and explains, and every claim is sourced and audited.

## What PillWise does not do (yet)

- It is an educational tool, not medical advice, and does not replace a pharmacist or doctor.
- English only for now.
- It checks medicines against each other and, at 65 or older, against the Beers Criteria. It does not yet know your diagnoses, kidney function or allergies.
- Reading a new photo needs an internet connection.

Data: DDInter 2.0 · ONC high-priority drug interaction list (Phansalkar et al., 2012) · 2023 AGS Beers Criteria (our summaries, cited) · FDA drug labels via openFDA · RxNorm (NLM). Solix AI Hackathon 2026 · AI in Healthcare. Screenshots taken 2026-10-28 from the working app.
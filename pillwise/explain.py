"""Per-pill cards (MVP) and plain language / translation / quiz (stretch A). Owner: A.

Contracts:
    pill_cards(meds) -> list[PillCard]                         # MVP
    simplify(report, language) -> SimplifiedSummary            # stretch A
    make_quiz(report, n) -> list[QuizQuestion]                 # stretch A (could)

Rules:
- Explain only what the label says; `how_to_take` is copied from Medication.directions.
- simplify(): English only for now (es/zh raise NotImplementedError; the UI shows "Coming soon").
  Rewrites each finding until textstat.flesch_kincaid_grade <= settings.target_reading_grade
  (max 3 tries). Severity words, section order, the footer and the "could not check"
  text are set by code; the LLM only rewords. A rewrite that adds dose-like numbers is rejected.
- make_quiz(): the LLM writes the question and answers; code places the correct answer,
  the explanation is the checker's own summary, and a fixed question is used on any failure.
- Keep every SimplifiedSection.source_ids pointing at the Finding it came from.
"""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel

from pillwise import evidence, llm
from pillwise.config import get_settings
from pillwise.schemas import (
    SAFETY_FOOTER,
    GroupNote,
    Language,
    Medication,
    PillCard,
    QuizQuestion,
    Report,
    SimplifiedSection,
    SimplifiedSummary,
)

log = logging.getLogger(__name__)

NO_LABEL = "We could not find the official label for this medicine. Ask your pharmacist what it is for."

CARD_SECTIONS = (
    "boxed_warning",
    "warnings",
    "warnings_and_cautions",
    "do_not_use",
    "contraindications",
    "ask_doctor_or_pharmacist",
    "when_using",
    "geriatric_use",
    "stop_use",
)


class _CardText(BaseModel):
    what_it_is_for: str
    watch_for: list[str]


CARD_PROMPT = """You explain a medicine to an older adult, in plain words (about 6th-grade reading level).

Use ONLY the FDA label text below for "{name}". Do not add facts that are not in it.
Never give doses or tell the person how much or how often to take it.

- what_it_is_for: one or two short sentences: what this medicine is used for.
- watch_for: up to 4 short items (under 15 words each): the most important warnings
  or side effects from the label that the person should watch for.
  Each item is ONE warning and must make sense on its own.

IMPORTANT: the label text below lost its bullet points. After openers such as
"Do not use", "Ask a doctor before use if you have", "Ask a doctor or pharmacist before
use if you are", "When using this product" or "Stop use and ask a doctor if", the phrases
that follow are SEPARATE list items run together. Never combine two of them into one item.
Example: "Do not use for children under 12 years of age with any other product containing
X" is two items: "Not for children under 12" and "Do not use with other products that
contain X".

WHAT IT IS FOR (label):
{purpose}

WARNINGS (label):
{warnings}"""


#: A "watch for" item longer than this is almost always two label items run together: drop it.
_MAX_ITEM_WORDS = 20


def _first_sentence(text: str, limit: int = 300) -> str | None:
    """First sentence of `text`, as an exact substring (safe to show as a label quote)."""
    text = text.strip()
    if not text:
        return None
    m = re.search(r"[.!?](\s|$)", text)
    s = text[: m.end()].strip() if m else text
    return s if len(s) <= limit else None


def _purpose_quote(label: dict) -> str | None:
    for sec in evidence.PURPOSE_SECTIONS:
        q = _first_sentence(evidence.section_text(label, sec))
        if q and len(q.split()) >= 2:
            return q
    return None


#: (group, label sections to search in order, a sentence must mention, must not mention, max quotes).
#: Matching sentences are quoted exactly; code picks them, no LLM, and nothing here changes a finding.
GROUP_RULES = (
    (
        "pregnancy",
        ("pregnancy_or_breast_feeding", "pregnancy", "use_in_specific_populations", "warnings"),
        r"pregnan",
        None,
        2,
    ),
    (
        "breastfeeding",
        ("lactation", "nursing_mothers", "use_in_specific_populations", "pregnancy_or_breast_feeding"),
        r"breast-?feed|lactation|nursing",
        None,
        1,
    ),
    (
        "children",
        ("pediatric_use", "warnings", "do_not_use", "ask_doctor"),
        r"\b(children|teenagers?|pediatric)\b",
        r"pregnan|unborn",
        1,
    ),
    (
        "women_men",
        ("females_and_males_of_reproductive_potential", "warnings_and_cautions", "warnings"),
        r"\b(women|men|females?|males?)\b",
        r"pregnan|breast",
        1,
    ),
)
#: Generic storage text, not about children taking the medicine.
_GROUP_SKIP = re.compile(r"keep (this and all drugs )?out of (the )?reach of children", re.I)
#: Section headings and cross-references that openFDA runs into the first sentence.
_GROUP_LEAD = re.compile(
    r"^(?:[\s•·:]+|\(\s*[\d.]+\s*\)|\d+(?:\.\d+)*(?=\s)|"
    r"(?:USE IN SPECIFIC POPULATIONS|Pregnancy Risk Summary|Pregnancy|Lactation Risk Summary|Lactation|"
    r"Nursing Mothers|Pediatric Use|Females and Males of Reproductive Potential|Warnings)\b)*",
    re.I,
)
_GROUP_MAX_CHARS = 320


def _group_sentences(text: str):
    for raw in re.split(r"(?<=[.!?])\s+", text):
        s = _GROUP_LEAD.sub("", raw, count=1).strip()
        if 25 <= len(s) <= _GROUP_MAX_CHARS and s in text:
            yield s


def group_notes(label: dict) -> list[GroupNote]:
    """Label sentences about pregnancy, breastfeeding, children, women or men: exact quotes, few per group."""
    notes: list[GroupNote] = []
    seen: set[str] = set()
    for group, sections, pattern, exclude, most in GROUP_RULES:
        found = 0
        for sec in sections:
            for s in _group_sentences(evidence.section_text(label, sec)):
                if found == most:
                    break
                if s in seen or not re.search(pattern, s, re.I) or _GROUP_SKIP.search(s):
                    continue
                if exclude and re.search(exclude, s, re.I):
                    continue
                notes.append(GroupNote(group=group, quote=s, evidence=evidence.label_evidence(label, s)))
                seen.add(s)
                found += 1
    return notes


def pill_card(med: Medication) -> PillCard:
    base = {"med_key": med.key, "name": med.name, "how_to_take": med.directions}  # COPIED, never generated
    try:
        label = evidence.fetch_label(med.match_names)
    except Exception as exc:  # noqa: BLE001
        log.warning("label fetch failed for %s: %s", med.key, exc)
        label = None
    if not label:
        return PillCard(**base, what_it_is_for=NO_LABEL)

    base["special_groups"] = group_notes(label)
    quote = _purpose_quote(label)
    ev = [evidence.label_evidence(label, quote)] if quote else []
    purpose = "\n".join(evidence.section_text(label, s) for s in evidence.PURPOSE_SECTIONS).strip()
    warnings = "\n".join(evidence.section_text(label, s)[:3000] for s in CARD_SECTIONS).strip()
    try:
        out = llm.structured(
            CARD_PROMPT.format(
                name=med.generic_name or med.name, purpose=purpose[:3000], warnings=warnings or "(none)"
            ),
            _CardText,
            fast=True,
        )
        return PillCard(
            **base,
            what_it_is_for=out.what_it_is_for.strip() or (quote or NO_LABEL),
            watch_for=[w.strip() for w in out.watch_for if w.strip() and len(w.split()) <= _MAX_ITEM_WORDS][:4],
            evidence=ev,
        )
    except Exception as exc:  # noqa: BLE001 - fall back to the label's own words
        log.warning("card explanation failed for %s: %s", med.key, exc)
        return PillCard(**base, what_it_is_for=quote or NO_LABEL, evidence=ev)


def pill_cards(meds: list[Medication]) -> list[PillCard]:
    return [pill_card(m) for m in meds]


# ---------------------------------------------------------------------------
# Stretch A8: plain-language summary (English only for now)
# ---------------------------------------------------------------------------

#: How serious, in plain words. Decided by the checker's severity, never by the LLM.
SEVERITY_WORDS = {
    "major": "Serious",
    "moderate": "Important",
    "caution": "Be careful",
    "minor": "Minor",
    "unknown": "Unclear",
}

NOTHING_FOUND = (
    "Our check did not find problems between these medicines. "
    "This does not prove they are safe for you: our lists do not cover everything."
)

SIMPLIFY_PROMPT = """Rewrite this medicine warning for an older adult with limited reading skills.

Rules:
- Use short sentences and everyday words (6th-grade reading level or easier).
- Keep EVERY fact. Do not add facts, numbers, doses, drug names or advice that are not in the text.
- Keep every medicine name that appears in the text, spelled the same way.
- Do not make the warning sound weaker or stronger than it is.
- At most 3 sentences. Return only the rewritten text.
{hint}
WARNING:
{text}"""

#: A dose-like number in the rewrite that was not in the source = the LLM added dosing.
_DOSE_RE = re.compile(r"\d+(\.\d+)?\s*(mg|mcg|g|ml|tablets?|caplets?|pills?|times|hours?)\b", re.IGNORECASE)


def _grade(text: str) -> float:
    import textstat

    return float(textstat.flesch_kincaid_grade(text))


def _strip_footer(text: str) -> str:
    return text.replace(SAFETY_FOOTER, "").strip()


def _adds_dosing(rewrite: str, source: str) -> bool:
    src = {m.group(0).lower() for m in _DOSE_RE.finditer(source)}
    return any(m.group(0).lower() not in src for m in _DOSE_RE.finditer(rewrite))


def _has_name(name: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(name)}\b", text, re.IGNORECASE) is not None


def _name_problem(rewrite: str, source: str, names: set[str]) -> str | None:
    """Why the rewrite changed which medicines are named, or None if it kept them exactly."""
    dropped = sorted(n for n in names if _has_name(n, source) and not _has_name(n, rewrite))
    added = sorted(n for n in names if _has_name(n, rewrite) and not _has_name(n, source))
    if dropped:
        return f"You left out these medicine names; keep them: {', '.join(dropped)}."
    if added:
        return f"You named medicines that are not in the warning; remove them: {', '.join(added)}."
    return None


def report_names(report: Report) -> set[str]:
    """Every medicine name in the report (ingredients, display and generic names), lower case."""
    names: set[str] = set()
    for m in report.meds:
        names.update(i.lower() for i in m.ingredients)
        names.update(n.strip().lower() for n in (m.name, m.generic_name) if n and n.strip())
    for f in report.findings:
        names.update(f.drugs)
    return {n for n in names if len(n) >= 3}


def plain_rewrite(source: str, target: float, names: set[str] | frozenset[str] = frozenset()) -> str:
    """Rewrite `source` until its reading grade <= target (max 3 tries). Returns the easiest safe version.

    A rewrite is rejected if it adds a dose-like number or changes which medicines from
    `names` are mentioned (a dropped or added name could attach a warning to the wrong drug).
    """
    best, best_grade = source, _grade(source)
    hint = ""
    for _ in range(3):
        if best_grade <= target:
            break
        try:
            out = llm.text(SIMPLIFY_PROMPT.format(hint=hint, text=source), fast=True).strip()
        except Exception as exc:  # noqa: BLE001 - fall back to the checker's own words
            log.warning("simplify rewrite failed: %s", exc)
            break
        if not out or _adds_dosing(out, source):
            log.warning("rejected rewrite (empty or added dosing)")
            continue
        problem = _name_problem(out, source, set(names))
        if problem:
            log.warning("rejected rewrite (medicine names changed)")
            hint = f"\n{problem}\n"
            continue
        g = _grade(out)
        if g < best_grade:
            best, best_grade = out, g
        hint = f"\nYour last version was still at grade {g:.1f}. Use even shorter sentences and simpler words.\n"
    return best


def _unchecked_section(report: Report) -> SimplifiedSection | None:
    names = [u for u in report.unchecked if not u.startswith("(checker")]
    failed = len(names) != len(report.unchecked)
    if not names and not failed:
        return None
    parts = []
    if names:
        parts.append(f"We could not check: {', '.join(names)}. This does not mean they are safe.")
    if failed:
        parts.append("Part of our check did not run, so some problems may be missing.")
    parts.append("Ask your pharmacist about these.")
    return SimplifiedSection(title="Could not check", text=" ".join(parts))


def simplify(report: Report, language: Language = "en") -> SimplifiedSummary:
    if language != "en":
        raise NotImplementedError("translation (es/zh) is not built yet")
    target = get_settings().target_reading_grade
    names = report_names(report)

    sections: list[SimplifiedSection] = []
    for f in report.sorted_findings():
        source = f"{f.plain_summary} {_strip_footer(f.what_to_do)}".strip()
        text = f"{plain_rewrite(source, target, names)} {SAFETY_FOOTER}"  # footer added by code, always
        sections.append(
            SimplifiedSection(title=f"{SEVERITY_WORDS[f.severity]}: {f.title}", text=text, source_ids=[f.id])
        )

    if not report.findings:
        sections.append(SimplifiedSection(title="No problems found", text=f"{NOTHING_FOUND} {SAFETY_FOOTER}"))
    unchecked = _unchecked_section(report)
    if unchecked:
        sections.append(unchecked)

    body = " ".join(_strip_footer(s.text) for s in sections)
    return SimplifiedSummary(language="en", sections=sections, reading_grade=round(_grade(body), 1))


# ---------------------------------------------------------------------------
# Stretch A10: teach-back quiz
# ---------------------------------------------------------------------------


class _Quiz(BaseModel):
    question: str
    correct: str
    wrong: list[str]


QUIZ_PROMPT = """Write one simple teach-back quiz question for an older adult about this medicine warning.

WARNING: {title}. {summary}

- question: a short question that checks they understood the warning.
- correct: the right answer, saying ONLY what the warning says (under 15 words).
- wrong: exactly 2 wrong answers that are clearly wrong according to the warning (under 15 words each).
No numbers, doses or new medical facts in any answer."""

FALLBACK_OPTIONS = [
    "Stop taking my medicines today",
    "Ask my pharmacist or doctor first",
    "Nothing, it does not matter",
]


def _order(f_id: str, n: int) -> int:
    """Stable position for the correct answer (same report -> same quiz)."""
    return int(f_id[:8], 16) % n


def quiz_question(f) -> QuizQuestion:
    explanation = f"{f.plain_summary} {SAFETY_FOOTER}"
    try:
        q = llm.structured(QUIZ_PROMPT.format(title=f.title, summary=f.plain_summary), _Quiz, fast=True)
        correct = q.correct.strip()
        wrong = [w.strip() for w in q.wrong if w.strip() and w.strip().lower() != correct.lower()][:2]
        if not q.question.strip() or not correct or len(wrong) < 2:
            raise ValueError("incomplete quiz from model")
        if any(_DOSE_RE.search(t) for t in [correct, *wrong]):
            raise ValueError("quiz answer contains dosing")
        options = list(wrong)
        idx = _order(f.id, 3)
        options.insert(idx, correct)
        return QuizQuestion(
            question=q.question.strip(), options=options, correct_index=idx, explanation=explanation, source_id=f.id
        )
    except Exception as exc:  # noqa: BLE001 - fixed question instead
        log.warning("quiz generation failed for %s: %s", f.id, exc)
        return QuizQuestion(
            question=f"What should you do about this: {f.title}?",
            options=FALLBACK_OPTIONS,
            correct_index=1,
            explanation=explanation,
            source_id=f.id,
        )


def make_quiz(report: Report, n: int = 3) -> list[QuizQuestion]:
    """One question per lesson, most serious first.

    'unknown' findings carry no lesson, and findings with the same summary text (e.g. B's
    template for every moderate interaction) would repeat the same question, so skip them.
    """
    seen: set[str] = set()
    findings = []
    for f in report.sorted_findings():
        if f.severity == "unknown" or f.plain_summary in seen:
            continue
        seen.add(f.plain_summary)
        findings.append(f)
    return [quiz_question(f) for f in findings[:n]]

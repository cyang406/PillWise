"""Reusable Streamlit UI pieces for the one-page PillWise app. Owner: C.

The UI imports ONLY `pillwise.api` and `pillwise.schemas` from the backend.
Every sentence built here (verdict, questions, connections) restates a Finding; none adds,
drops or re-rates one (safety rule 1).
"""

from __future__ import annotations

import streamlit as st

from pillwise.schemas import AuditEvent, Finding, GroupNote, Medication, PillCard, Report

# severity -> (label people read, header tint, header ink, card border)
SEVERITY_STYLE = {
    "major": ("Serious", "#FBE9E7", "#8C1D18", "#F1C3BE"),
    "moderate": ("Important", "#FDEEE0", "#8A3A00", "#F0CDA9"),
    "caution": ("Extra care", "#FFF5D6", "#6B4A00", "#E5CF85"),
    "minor": ("Minor", "#E5EEFA", "#1E4A8A", "#C3D5EE"),
    "unknown": ("Not rated", "#EEF1F0", "#46524F", "#D9E1DE"),
}

# Stroke icons (no emoji): shape differs per severity, so color is never the only cue.
_ICON_PATHS = {
    "major": '<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86"/>'
    '<line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    "moderate": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
    '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "caution": '<circle cx="12" cy="7" r="4"/><path d="M5.5 21a6.5 6.5 0 0 1 13 0"/>',
    "minor": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "unknown": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
    '<line x1="12" y1="17" x2="12.01" y2="17"/>',
}

GROUP_LABELS = {
    "pregnancy": "Pregnancy",
    "breastfeeding": "Breastfeeding",
    "children": "Children and teens",
    "women_men": "Women or men",
}

DISCLAIMER = (
    "PillWise is an educational tool, not medical advice. It does not replace your pharmacist or doctor. "
    "If you have urgent symptoms, call emergency services (911 in the US)."
)

NO_DIRECTIONS = "We could not read directions on your label. Follow the package directions, or ask your pharmacist."

MOBILE_APP_UA = "PillWiseMobile"  # mobile/App.tsx appends this to the WebView's User-Agent


def in_mobile_app() -> bool:
    """True inside the PillWise mobile app (User-Agent), or with ?app=mobile to try its layout in a browser."""
    ss = st.session_state
    if st.query_params.get("app") == "mobile":
        ss.mobile_app = True  # remembered for the session
    try:
        user_agent = st.context.headers.get("User-Agent", "")
    except Exception:  # no request context (e.g. AppTest)
        user_agent = ""
    return MOBILE_APP_UA in user_agent or ss.get("mobile_app", False)


def icon(severity: str, size: int = 22) -> str:
    return (
        f'<svg aria-hidden="true" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        f"{_ICON_PATHS[severity]}</svg>"
    )


def inject_css(large_text: bool = False) -> None:
    sev_rules = "\n".join(
        f'[class*="st-key-sev-{s}-"] {{ border-color: {border} !important; background: #FFFFFF; }}\n'
        f'[class*="st-key-verdict-{s}"] {{ background: {tint} !important; border-color: {border} !important; }}\n'
        f".pw-band-{s} {{ background: {tint}; color: {ink}; }}\n"
        f".pw-ink-{s} {{ color: {ink}; }}\n"
        f".pw-chip-{s} {{ background: {tint}; color: {ink}; border: 1px solid {border}; }}"
        for s, (_, tint, ink, border) in SEVERITY_STYLE.items()
    )
    st.markdown(
        f"""<style>
html {{ font-size: {"19px" if large_text else "16px"}; }}
.block-container {{ max-width: 1160px; padding-top: 1.5rem; }}
{sev_rules}
.pw-band {{ display: flex; align-items: center; gap: .5rem; margin: -1rem -1rem .75rem; padding: .55rem 1rem;
  border-radius: .5rem .5rem 0 0; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; font-size: .85rem; }}
.pw-chip {{ display: inline-block; padding: .1rem .6rem; margin: 0 .3rem .3rem 0; border-radius: 999px;
  font-size: .85rem; font-weight: 700; }}
.pw-steps a {{ display: inline-block; margin: 0 .4rem .4rem 0; padding: .35rem .8rem; border-radius: 999px;
  background: #E3F1EE; color: #0A4F49; text-decoration: none; font-weight: 700; font-size: .9rem; }}
.pw-brand {{ display: flex; align-items: center; gap: .5rem; font-size: 1.6rem; font-weight: 700; color: #15201E; }}
.pw-verdict {{ display: flex; gap: 1rem; align-items: flex-start; }}
.pw-verdict h2 {{ margin: 0; padding: 0; font-size: 1.75rem; line-height: 1.25; }}
.pw-pair {{ display: flex; justify-content: space-between; gap: .5rem; padding: .5rem .75rem; margin-bottom: .35rem;
  border-radius: .6rem; }}
.pw-quote {{ margin: 0 0 .6rem; padding-left: .75rem; border-left: 3px solid #C5D1CD; color: #2E3B38; }}
.pw-src {{ font-size: .8rem; color: #4A5754; }}
[class*="st-key-med-"][class*="-check"] {{ border: 2px solid #B54708 !important; background: #FFF8F1; }}
[class*="st-key-newmed"] {{ background: #13302C; border-radius: 1rem; }}
[class*="st-key-newmed"] h2, [class*="st-key-newmed"] p, [class*="st-key-newmed"] label {{ color: #F2F7F5 !important; }}
</style>""",
        unsafe_allow_html=True,
    )


def disclaimer() -> None:
    st.caption(DISCLAIMER)


def mock_banner(report: Report | None = None) -> None:
    if report is not None and report.is_mock:
        st.warning("Demo data (mock mode). Results are placeholders, not real checks.")


def list_signature(meds: list[Medication], age: int | None) -> tuple:
    """What a report was made from; results are hidden when the list changes after the check."""
    return tuple((m.name, m.strength, m.directions) for m in meds), age


# --- sentences built from findings (restate, never re-rate) ----------------------------


def _names(f: Finding, joiner: str) -> str:
    return joiner.join(f.drugs)


def verdict(report: Report) -> tuple[str | None, str, str]:
    """(severity, headline, subline): what to do today, from the most serious finding."""
    fs = report.sorted_findings()
    if not fs:
        return (
            None,
            "No problems found in our sources.",
            "That does not mean your list is safe. Keep your pharmacist up to date with everything you take.",
        )
    top = fs[0]
    pair = _names(top, " with ")
    both = _names(top, " and ")
    head = {
        "major": f"Ask your pharmacist about {pair} before your next dose.",
        "moderate": f"Ask your pharmacist about {pair} soon.",
        "caution": f"Ask your pharmacist whether {both} is still right for you.",
        "minor": f"Mention {pair} to your pharmacist at your next visit.",
        "unknown": f"Ask your pharmacist about {pair} at your next visit.",
    }[top.severity]
    n = len(fs)
    sub = f"We found {n} thing{'s' if n != 1 else ''} to talk about. Do not stop or change any medicine on your own."
    return top.severity, head, sub


def questions(report: Report) -> list[tuple[str, str]]:
    """(severity, question) to ask the pharmacist, one per finding, most serious first."""
    out: list[tuple[str, str]] = []
    for f in report.sorted_findings():
        d = f.drugs
        if f.kind == "interaction" and len(d) == 2:
            q = {
                "major": f"Is it OK for me to take {d[0]} and {d[1]} together?",
                "moderate": f"Does taking {d[0]} with {d[1]} need any extra checks?",
                "unknown": f"{d[0].capitalize()} and {d[1]} are listed together. Is that something to watch?",
            }.get(f.severity, f"Is the mix of {d[0]} and {d[1]} something to watch?")
        elif f.kind == "older_adult_risk":
            q = f"At my age, is {_names(f, ' and ')} still right for me?"
        elif f.kind == "older_adult_combo":
            q = f"I take {_names(f, ' and ')}. Is that combination OK at my age?"
        elif f.kind == "duplicate":
            q = f"Am I getting {_names(f, ' and ')} from more than one product?"
        elif f.kind == "food":
            q = f"Is there food or drink I should avoid with {_names(f, ' and ')}?"
        else:
            q = f"Can you explain this for me: {f.title}?"
        if q not in (x for _, x in out):
            out.append((f.severity, q))
    return out


def connections(report: Report) -> list[tuple[str, str, str]]:
    """(drug a, drug b, severity) for every interaction between two of the person's medicines."""
    return [
        (f.drugs[0], f.drugs[1], f.severity)
        for f in report.sorted_findings()
        if f.kind == "interaction" and len(f.drugs) == 2
    ]


def summary_text(report: Report) -> str:
    """Plain text to share with family or bring to the pharmacy."""
    _, head, sub = verdict(report)
    lines = ["PillWise check", head, sub, "", "Medicines:"]
    lines += [f"- {m.name} {m.strength or ''}".rstrip() for m in report.meds]
    lines += ["", "Things to talk about:"]
    lines += [f"- [{SEVERITY_STYLE[f.severity][0]}] {f.title}: {f.what_to_do}" for f in report.sorted_findings()]
    if report.unchecked:
        lines += ["", "Could not check (this does NOT mean safe): " + ", ".join(_unchecked_names(report))]
    lines += ["", "Questions to ask:"] + [f"- {q}" for _, q in questions(report)]
    lines += ["", DISCLAIMER]
    return "\n".join(lines)


# --- blocks ----------------------------------------------------------------------------


def verdict_banner(report: Report) -> None:
    sev, head, sub = verdict(report)
    with st.container(border=True, key=f"verdict-{sev or 'none'}"):
        ink = f"pw-ink-{sev}" if sev else ""
        svg = icon(sev, 40) if sev else ""
        st.markdown(
            f'<div class="pw-verdict"><span class="{ink}">{svg}</span>'
            f'<div><h2 class="{ink}">{head}</h2><p style="margin:.4rem 0 0">{sub}</p></div></div>',
            unsafe_allow_html=True,
        )
        counts: dict[str, int] = {}
        for f in report.sorted_findings():
            counts[f.severity] = counts.get(f.severity, 0) + 1
        chips = "".join(
            f'<span class="pw-chip pw-chip-{s}">{n} {SEVERITY_STYLE[s][0]}</span>' for s, n in counts.items()
        )
        if chips:
            st.markdown(chips, unsafe_allow_html=True)


def finding_card(f: Finding, where: str = "main") -> None:
    label = SEVERITY_STYLE[f.severity][0]
    with st.container(border=True, key=f"sev-{f.severity}-{where}-{f.id}"):
        st.markdown(
            f'<div class="pw-band pw-band-{f.severity}">{icon(f.severity, 20)}{label}</div>', unsafe_allow_html=True
        )
        st.markdown(f"#### {f.title}")
        st.write(f.plain_summary)
        st.markdown(f"**What to do:** {f.what_to_do}")
        with st.expander("Where this comes from", expanded=f.severity == "major"):
            for ev in f.evidence:
                link = f" · [open source]({ev.url})" if ev.url else ""
                st.markdown(
                    f'<span class="pw-src">{ev.source} · version {ev.version}</span>{link}', unsafe_allow_html=True
                )
                # openFDA text is an exact label quote; other sources are our summaries.
                st.markdown(f"> “{ev.text}”" if ev.source == "openFDA" else f"> {ev.text}")


def connections_box(report: Report) -> None:
    pairs = connections(report)
    with st.container(border=True):
        st.markdown("#### How your medicines connect")
        if not pairs:
            st.caption("No interactions between your medicines were found in our sources.")
            return
        rows = "".join(
            f'<div class="pw-pair pw-band-{s}"><span>{a.capitalize()} + {b.capitalize()}</span>'
            f"<strong>{SEVERITY_STYLE[s][0]}</strong></div>"
            for a, b, s in pairs
        )
        st.markdown(rows, unsafe_allow_html=True)


def checked_as(report: Report) -> None:
    """What each bottle name was checked as (e.g. Advil -> ibuprofen); normalization runs after confirm."""
    with st.container(border=True):
        st.markdown("#### What we checked")
        st.caption("Each name is matched to its active ingredient. If one looks wrong, fix the name above.")
        st.markdown(
            "\n".join(
                f"- {m.name} → {', '.join(m.ingredients) or m.generic_name}"
                if (m.ingredients or m.generic_name)
                else f"- {m.name} → *not matched (see “could not check”)*"
                for m in report.meds
            )
        )


def _unchecked_names(report: Report) -> list[str]:
    return [u for u in report.unchecked if not u.startswith("(")]


def unchecked_box(report: Report) -> None:
    """Rule 3: anything not checked is shown as 'could not check', never as safe."""
    names = _unchecked_names(report)
    problems = [u.strip("()") for u in report.unchecked if u.startswith("(")]
    if names:
        st.error(
            "**We could not check:** "
            + ", ".join(names)
            + ". This does NOT mean they are safe. Ask your pharmacist about them."
        )
    if problems:
        st.error("**Some safety checks did not run**, so this list may be incomplete. Ask your pharmacist.")
        with st.expander("Details"):
            st.markdown("\n".join(f"- {p}" for p in problems))


def _group_quotes(notes: list[GroupNote]) -> None:
    for group, label in GROUP_LABELS.items():
        mine = [n for n in notes if n.group == group]
        if not mine:
            continue
        st.markdown(f"**{label}**")
        for n in mine:
            link = f" · [open]({n.evidence.url})" if n.evidence.url else ""
            st.markdown(f'<p class="pw-quote">“{n.quote}”</p>', unsafe_allow_html=True)
        st.markdown(f'<span class="pw-src">FDA label · {mine[0].evidence.version}</span>{link}', unsafe_allow_html=True)


def pill_card(c: PillCard, med: Medication | None, report: Report) -> None:
    names = set(med.match_names) if med else {c.med_key}
    with st.container(border=True):
        strength = f" {med.strength}" if med and med.strength else ""
        st.markdown(f"#### {c.name}{strength}")
        st.markdown(f"**For:** {c.what_it_is_for}")
        st.markdown(
            f"**How to take, from your label:** {c.how_to_take}"
            if c.how_to_take
            else f"**How to take:** {NO_DIRECTIONS}"
        )
        if c.watch_for:
            st.markdown("**Watch for:**\n" + "\n".join(f"- {w}" for w in c.watch_for))
        chips = "".join(
            f'<span class="pw-chip pw-chip-{f.severity}">{SEVERITY_STYLE[f.severity][0]} with '
            f"{', '.join(d for d in f.drugs if d not in names)}</span>"
            for f in report.sorted_findings()
            if f.kind == "interaction" and names & set(f.drugs)
        )
        if chips:
            st.markdown(chips, unsafe_allow_html=True)
        if c.special_groups:
            with st.expander("Pregnancy, breastfeeding, children: what the label says"):
                _group_quotes(c.special_groups)


def trust_panel(report: Report, audit_events: list[AuditEvent] | None = None) -> None:
    """Every source and version behind this report, plus its audit trail."""
    names = {
        "ddinter": "DDInter drug-interaction database",
        "onc": "ONC high-priority interaction list (Phansalkar 2012)",
        "beers": "AGS Beers Criteria 2023 (our summaries)",
        "mock": "Mock data",
    }
    with st.expander("Sources and audit trail"):
        st.markdown("**Data used for the checks**")
        st.markdown(
            "\n".join(f"- {names.get(k, k)}: version {v}" for k, v in report.data_versions.items()) or "- none recorded"
        )
        labels = {ev.url: ev for f in report.findings for ev in f.evidence if ev.source == "openFDA" and ev.url}
        if labels:
            st.markdown("**FDA labels quoted**")
            st.markdown("\n".join(f"- DailyMed {ev.version} ([open]({url}))" for url, ev in labels.items()))
        st.markdown("**This report**")
        st.markdown(
            f"- id `{report.id}`\n- made {report.generated_at:%Y-%m-%d %H:%M} UTC\n"
            f"- AI model (reads labels and explains only): `{report.model}`"
        )
        if audit_events is None:
            st.caption("Every report is written to the audit log with the source and version of each claim.")
        else:
            mine = [e for e in audit_events if e.report_id == report.id]
            st.markdown(f"**Audit log** ({len(mine)} entries for this report)")
            for e in mine:
                src = f" · {e.source} {e.source_version or ''}" if e.source else ""
                st.markdown(f"- {e.timestamp:%H:%M:%S} · {e.event}{src}")

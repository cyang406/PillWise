"""Reusable Streamlit UI pieces for the one-page PillWise app (design canvas v2). Owner: C.

The UI imports ONLY `pillwise.api` and `pillwise.schemas` from the backend.
Every sentence built here (verdict, questions, connections) restates a Finding; none adds,
drops or re-rates one (safety rule 1).
"""

from __future__ import annotations

import streamlit as st

from pillwise.schemas import AuditEvent, Finding, GroupNote, Medication, PillCard, Report

# severity -> (label people read, tint, ink)
SEVERITY_STYLE = {
    "major": ("Serious", "#FEF2F2", "#B42318"),
    "moderate": ("Important", "#FFEDD5", "#9A3412"),
    "caution": ("Age 65+", "#FEF9C3", "#854D0E"),
    "minor": ("Minor", "#EFF4FF", "#1D4ED8"),
    "unknown": ("Not rated", "#F1F5F9", "#475569"),
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

PILL_ICON = (
    '<svg aria-hidden="true" width="30" height="30" viewBox="0 0 48 48"><rect x="7" y="17" width="34" height="14" '
    'rx="7" transform="rotate(-25 24 24)" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2"/></svg>'
)
LOGO = (
    '<span class="pw-logo"><svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" '
    'stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M10.5 20.5a4.95 4.95 0 0 1-7-7l10-10a4.95 4.95 0 0 1 7 7z"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/>'
    "</svg></span>"
)

GROUP_LABELS = {
    "pregnancy": "Pregnancy",
    "breastfeeding": "Breastfeeding",
    "children": "Children and teens",
    "women_men": "Women or men",
}

DISCLAIMER = "For information only, not medical advice. Always check the label and ask a pharmacist or doctor."

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
        f'[class*="st-key-verdict-{s}"] {{ background: {tint} !important; border: 0 !important; }}\n'
        f".pw-ink-{s} {{ color: {ink}; }}\n"
        f".pw-chip-{s} {{ background: #FFFFFF; color: {ink}; }}\n"
        f".pw-cell-{s} {{ background: {tint}; color: {ink}; }}"
        for s, (_, tint, ink) in SEVERITY_STYLE.items()
    )
    st.markdown(
        f"""<style>
html {{ font-size: {"19px" if large_text else "16px"}; }}
.block-container {{ max-width: 1120px; padding-top: 1.25rem; }}
h1, h2, h3, h4 {{ letter-spacing: -0.02em; }}
{sev_rules}
.pw-chip-major {{ background: #B42318; color: #FFFFFF; }}
.pw-cell-major {{ background: #B42318; color: #FFFFFF; }}
.pw-brand {{ display: flex; align-items: center; gap: .6rem; font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; }}
.pw-logo {{ width: 34px; height: 34px; border-radius: 10px; background: #2563EB; display: inline-flex;
  align-items: center; justify-content: center; }}
.pw-steps a {{ display: inline-block; margin: .3rem .3rem 0 0; padding: .35rem .8rem; border-radius: 999px;
  background: #EFF4FF; color: #1D4ED8; text-decoration: none; font-weight: 600; font-size: .9rem; }}
.pw-hero {{ font-size: clamp(2rem, 4.5vw, 3rem); line-height: 1.1; font-weight: 700; letter-spacing: -0.03em; margin: .5rem 0 .25rem; }}
.pw-step {{ font-weight: 600; }} .pw-step b {{ color: #2563EB; }}
.pw-chip {{ display: inline-block; padding: .2rem .7rem; margin: .4rem .35rem 0 0; border-radius: 999px;
  font-size: .85rem; font-weight: 600; }}
.pw-badge {{ display: inline-block; padding: .05rem .5rem; border-radius: 6px; font-size: .8rem; font-weight: 600;
  background: #EFF4FF; color: #1D4ED8; }}
.pw-badge-check {{ background: #FFFFFF; color: #92400E; }}
.pw-sev {{ font-size: .8rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; display: flex;
  align-items: center; gap: .4rem; }}
.pw-verdict {{ display: flex; gap: 1rem; align-items: flex-start; }}
.pw-verdict h2 {{ margin: 0; padding: 0; font-size: 1.7rem; line-height: 1.25; }}
.pw-matrix {{ display: grid; gap: 4px; font-size: .8rem; text-align: center; }}
.pw-matrix span {{ padding: .55rem .1rem; border-radius: 8px; font-size: .74rem; overflow-wrap: normal; word-break: normal; hyphens: auto; }}
.pw-matrix .h {{ font-weight: 600; }} .pw-matrix .r {{ text-align: left; font-weight: 600; }}
.pw-matrix .e {{ background: #F5F7FB; }}
.pw-quote {{ margin: 0 0 .6rem; padding-left: .75rem; border-left: 3px solid #CBD5E1; color: #334155; }}
.pw-src {{ font-size: .8rem; color: #475569; }}
[class*="st-key-sev-"] {{ background: #F5F7FB; border: 0 !important; }}
[class*="st-key-med-"] {{ background: #F5F7FB; border: 0 !important; }}
[class*="st-key-med-"][class*="-check"] {{ background: #FFF8EB; border: 1px solid #F5C99B !important; }}
[class*="st-key-agebox"], [class*="st-key-pharm"] {{ background: #F5F7FB; border: 0 !important; }}
[class*="st-key-newmed"] {{ background: #2563EB; border: 0 !important; }}
[class*="st-key-newmed"] h4, [class*="st-key-newmed"] [data-testid="stWidgetLabel"] p {{ color: #FFFFFF !important; }}
[class*="st-key-open_"] button {{ background: #EFF4FF; color: #1D4ED8; border: 0; font-weight: 600; }}
[class*="st-key-detail-"] {{ background: #F5F7FB; border: 0 !important; }}
[class*="st-key-detail-caution"] {{ background: #FFF8EB; color: #78350F; }}
[class*="st-key-detail-with"] {{ background: #FFFFFF; border: 1px solid #E2E8F0 !important; }}
.pw-ask {{ display: flex; align-items: center; justify-content: center; min-height: 2.6rem; border-radius: .75rem;
  background: #2563EB; color: #FFFFFF !important; font-weight: 700; text-decoration: none; }}
[data-testid="stFileUploaderDropzone"] {{ border: 2px dashed #BFD0F8; background: #F8FAFF; }}
</style>""",
        unsafe_allow_html=True,
    )


def disclaimer() -> None:
    st.caption(DISCLAIMER + " If you have urgent symptoms, call emergency services (911 in the US).")


def mock_banner(report: Report | None = None) -> None:
    if report is not None and report.is_mock:
        st.warning("Demo data (mock mode). Results are placeholders, not real checks.")


def list_signature(meds: list[Medication], age: int | None) -> tuple:
    """What a report was made from; results are hidden when the list changes after the check."""
    return tuple((m.name, m.strength, m.directions) for m in meds), age


def match_badge(m: Medication) -> str:
    """Whether RxNorm matched the name: a real lookup, not a made-up confidence score."""
    if m.ingredients or m.generic_name:
        return f'<span class="pw-badge">Matched: {", ".join(m.ingredients) or m.generic_name}</span>'
    return '<span class="pw-badge pw-badge-check">Please check this name</span>'


# --- sentences built from findings (restate, never re-rate) ----------------------------


def _names(f: Finding, joiner: str) -> str:
    return joiner.join(f.drugs)


def short_title(f: Finding) -> str:
    """'Ibuprofen + warfarin' for interactions; the checker's own title otherwise."""
    if f.kind == "interaction" and len(f.drugs) == 2:
        return " + ".join(d.capitalize() for d in f.drugs)
    return f.title


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
        "major": f"Ask your pharmacist before taking {pair}.",
        "moderate": f"Ask your pharmacist about {pair} soon.",
        "caution": f"Ask your pharmacist whether {both} is still right for you.",
        "minor": f"Mention {pair} to your pharmacist at your next visit.",
        "unknown": f"Ask your pharmacist about {pair} at your next visit.",
    }[top.severity]
    return top.severity, head, "Don’t stop any medicine on your own."


def questions(report: Report) -> list[tuple[str, str]]:
    """(severity, question) to ask the pharmacist, one per finding, most serious first."""
    out: list[tuple[str, str]] = []
    for f in report.sorted_findings():
        d = f.drugs
        if f.kind == "interaction" and len(d) == 2:
            q = {
                "major": f"Is {d[0]} OK with my {d[1]}?",
                "moderate": f"Do I need extra checks for {d[0]} with {d[1]}?",
                "unknown": f"{d[0].capitalize()} and {d[1]} are listed together. Should I watch for anything?",
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
            f'<div><h2 class="{ink}">{head}</h2><p style="margin:.3rem 0 0">{sub}</p></div></div>',
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
            f'<div class="pw-sev pw-ink-{f.severity}">{icon(f.severity, 18)}{label}</div>', unsafe_allow_html=True
        )
        st.markdown(f"#### {short_title(f)}")
        st.write(f.plain_summary)
        st.markdown(f"**What to do:** {f.what_to_do}")
        with st.expander("Sources", expanded=False):
            for ev in f.evidence:
                link = f" · [open source]({ev.url})" if ev.url else ""
                st.markdown(
                    f'<span class="pw-src">{ev.source} · version {ev.version}</span>{link}', unsafe_allow_html=True
                )
                # openFDA text is an exact label quote; other sources are our summaries.
                st.markdown(f"> “{ev.text}”" if ev.source == "openFDA" else f"> {ev.text}")


def connections_box(report: Report) -> None:
    """Matrix of the person's medicines (design v3); tap a medicine name to open "About this medicine"."""
    with st.container(border=True, key="connect"):
        st.markdown("#### How they connect")
        st.caption("Tap a medicine name to learn about it.")
        meds = [m for m in report.meds if m.match_names]
        pair_sev = {frozenset((a, b)): s for a, b, s in connections(report)}

        def sev(i: int, j: int) -> str | None:
            for a in meds[i].match_names:
                for b in meds[j].match_names:
                    if frozenset((a, b)) in pair_sev:
                        return pair_sev[frozenset((a, b))]
            return None

        if not pair_sev:
            st.caption("No interactions between your medicines were found in our sources.")
        elif len(meds) <= 5:
            cols = f"grid-template-columns: minmax(0, 1.25fr) repeat({len(meds)}, minmax(0, 1fr))"
            cells = ['<span class="h"></span>'] + [f'<span class="h">{m.name}</span>' for m in meds]
            for i, m in enumerate(meds):
                cells.append(f'<span class="r">{m.name}</span>')
                for j in range(len(meds)):
                    s = sev(i, j) if i != j else None
                    cells.append(
                        f'<span class="pw-cell-{s}">{SEVERITY_STYLE[s][0]}</span>' if s else '<span class="e"></span>'
                    )
            st.markdown(
                f'<div class="pw-matrix" lang="en" style="{cols}" role="table" aria-label="Interactions between your medicines">'
                + "".join(cells)
                + "</div>",
                unsafe_allow_html=True,
            )
            st.caption("Not rated = listed together, but how serious is unknown. Empty = nothing found in our sources.")
        else:
            for a, b, s in connections(report):
                st.markdown(f"{a.capitalize()} + {b.capitalize()}: **{SEVERITY_STYLE[s][0]}**")
        by_key = {m.key: m for m in report.meds}
        with st.container(horizontal=True, wrap=True, gap="small"):
            for i, c in enumerate(report.pill_cards):
                if st.button(c.name, key=f"open_{report.id}_{i}", icon=":material/info:"):
                    medicine_dialog(c, by_key.get(c.med_key), report)


def checked_as(report: Report) -> None:
    """What each bottle name was checked as (e.g. Advil -> ibuprofen); normalization runs after confirm."""
    st.caption(
        "What we checked: "
        + "; ".join(
            f"{m.name} → {', '.join(m.ingredients) or m.generic_name}"
            if (m.ingredients or m.generic_name)
            else f"{m.name} → not matched"
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
            st.markdown(f'<p class="pw-quote">“{n.quote}”</p>', unsafe_allow_html=True)
        link = f" · [open]({mine[0].evidence.url})" if mine[0].evidence.url else ""
        st.markdown(f'<span class="pw-src">FDA label · {mine[0].evidence.version}</span>{link}', unsafe_allow_html=True)


def _medicine_body(c: PillCard, med: Medication | None, report: Report) -> None:
    names = set(med.match_names) if med else {c.med_key}
    strength = f" {med.strength}" if med and med.strength else ""
    badge = match_badge(med) if med else ""
    st.markdown(
        f'<div style="display:flex;gap:.9rem;align-items:center">{PILL_ICON}<div>{badge}'
        f'<div style="font-size:1.4rem;font-weight:700;letter-spacing:-0.02em">{c.name}{strength}</div></div></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="detail-for"):
        st.markdown(f"**WHAT IT’S FOR**  \n{c.what_it_is_for}")
    with st.container(border=True, key="detail-how"):
        st.markdown(f"**HOW TO TAKE · FROM YOUR LABEL**  \n{c.how_to_take or NO_DIRECTIONS}")
    if c.watch_for:
        with st.container(border=True, key="detail-caution"):
            st.markdown("**CAUTION**\n" + "\n".join(f"- {w}" for w in c.watch_for))
    others = [
        f'<li><strong class="pw-ink-{f.severity}">{SEVERITY_STYLE[f.severity][0]}</strong> with '
        f"{', '.join(d for d in f.drugs if d not in names)}</li>"
        for f in report.sorted_findings()
        if f.kind == "interaction" and names & set(f.drugs)
    ]
    with st.container(border=True, key="detail-with"):
        st.markdown(
            "**WITH YOUR OTHER PILLS**"
            + (
                f'<ul style="list-style:none;padding:0;margin:.3rem 0 0">{"".join(others)}</ul>'
                if others
                else "  \nNothing found in our sources."
            ),
            unsafe_allow_html=True,
        )
    if c.special_groups:
        with st.expander("Pregnancy, breastfeeding, children: what the label says"):
            _group_quotes(c.special_groups)


@st.dialog("About this medicine", width="medium")
def medicine_dialog(c: PillCard, med: Medication | None, report: Report) -> None:
    _medicine_body(c, med, report)
    b1, b2 = st.columns([1, 1.4])
    if b1.button("Close", width="stretch"):
        st.rerun()
    b2.markdown(
        '<a class="pw-ask" href="#ask-your-pharmacist" target="_self">Ask pharmacist</a>', unsafe_allow_html=True
    )


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

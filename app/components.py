"""Reusable Streamlit UI pieces. Owner: C.

The UI imports ONLY `pillwise.api` and `pillwise.schemas` from the backend.
"""

from __future__ import annotations

import streamlit as st

from pillwise.schemas import AuditEvent, Finding, PillCard, Report

# severity -> (icon, label, accent color). Labels are what people read; never show raw severity words.
SEVERITY_STYLE = {
    "major": ("🔴", "Serious", "#c62828"),
    "moderate": ("🟠", "Important", "#e65100"),
    "caution": ("🟡", "Extra care at 65+", "#b28704"),
    "minor": ("🔵", "Minor", "#1565c0"),
    "unknown": ("⚪", "Not rated", "#9e9e9e"),
}

DISCLAIMER = (
    "PillWise is an educational tool, not medical advice. It does not replace your pharmacist or doctor. "
    "If you have urgent symptoms, call emergency services."
)

NO_DIRECTIONS = (
    "**How to take:** We could not read directions on your label. "
    "Follow the package directions, or ask your pharmacist."
)


def inject_css() -> None:
    """Severity accents for finding cards (containers keyed `sev-<severity>-<id>`)."""
    rules = "\n".join(
        f'[class*="st-key-sev-{sev}-"] {{ border-left: 6px solid {color} !important; }}'
        for sev, (_, _, color) in SEVERITY_STYLE.items()
    )
    st.markdown(
        f"""<style>
{rules}
[class*="st-key-sev-unknown-"] {{ opacity: 0.85; }}
</style>""",
        unsafe_allow_html=True,
    )


MOBILE_APP_UA = "PillWiseMobile"  # mobile/App.tsx appends this to the WebView's User-Agent


def in_mobile_app() -> bool:
    """True inside the PillWise mobile app (User-Agent), or with ?app=mobile to try its layout in a browser."""
    ss = st.session_state
    if st.query_params.get("app") == "mobile":
        ss.mobile_app = True  # remembered for the session; page links drop the query string
    try:
        user_agent = st.context.headers.get("User-Agent", "")
    except Exception:  # no request context (e.g. AppTest)
        user_agent = ""
    return MOBILE_APP_UA in user_agent or ss.get("mobile_app", False)


def disclaimer() -> None:
    st.info(DISCLAIMER)


def mock_banner(report: Report | None = None) -> None:
    if report is not None and report.is_mock:
        st.warning("Demo data (mock mode). Results are placeholders, not real checks.")


def summary_line(report: Report) -> None:
    """One line under the title: how many findings at each level, most serious first."""
    findings = report.sorted_findings()
    if not findings:
        st.success("No problems found in our sources. This is not a promise that the list is safe.")
        return
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    parts = [f"{SEVERITY_STYLE[s][0]} {n} {SEVERITY_STYLE[s][1].lower()}" for s, n in counts.items()]
    st.markdown(" · ".join(parts))


def finding_card(f: Finding) -> None:
    icon, label, _ = SEVERITY_STYLE[f.severity]
    # Some checker titles already start with the label (e.g. "Extra care at 65+: ibuprofen"); don't repeat it.
    heading = f.title if f.title.lower().startswith(label.lower()) else f"{label} · {f.title}"
    with st.container(border=True, key=f"sev-{f.severity}-{f.id}"):
        st.markdown(f"**{icon} {heading}**")
        st.write(f.plain_summary)
        st.markdown(f"**What to do:** {f.what_to_do}")
        with st.expander("Where this comes from"):
            for ev in f.evidence:
                link = f" · [open source]({ev.url})" if ev.url else ""
                st.markdown(f"**{ev.source}** (version {ev.version}){link}")
                # openFDA text is an exact label quote; other sources are our summaries.
                st.markdown(f"> “{ev.text}”" if ev.source == "openFDA" else f"> {ev.text}")


def pill_card(c: PillCard) -> None:
    with st.container(border=True):
        st.markdown(f"**💊 {c.name}**")
        st.write(c.what_it_is_for)
        st.markdown(f"**How to take (from your label):** {c.how_to_take}" if c.how_to_take else NO_DIRECTIONS)
        if c.watch_for:
            st.markdown("**Watch for:**\n" + "\n".join(f"- {w}" for w in c.watch_for))


def checked_as(report: Report) -> None:
    """Show what each bottle name was checked as (e.g. Advil -> ibuprofen); normalization runs after confirm."""
    lines = []
    for m in report.meds:
        generic = ", ".join(m.ingredients) or m.generic_name
        if generic:
            lines.append(f"- {m.name} → {generic}")
        else:
            lines.append(f"- {m.name} → *not matched (see “could not check”)*")
    with st.expander("What we checked"):
        st.caption("We match each name to its active ingredients. If one looks wrong, go back and fix the name.")
        st.markdown("\n".join(lines))


DATA_SOURCE_NAMES = {
    "ddinter": "DDInter drug-interaction database",
    "onc": "ONC high-priority interaction list (Phansalkar 2012)",
    "beers": "AGS Beers Criteria 2023 (our summaries)",
    "mock": "Mock data",
}


def trust_panel(report: Report, audit_events: list[AuditEvent] | None = None) -> None:
    """C3: every source and version behind this report, plus the audit trail when the API provides it."""
    with st.expander("Sources and audit trail"):
        st.markdown("**Data used for the checks**")
        st.markdown(
            "\n".join(f"- {DATA_SOURCE_NAMES.get(k, k)}: version {v}" for k, v in report.data_versions.items())
            or "- none recorded"
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


def unchecked_box(report: Report) -> None:
    """Rule 3: anything not checked is shown as 'could not check', never as safe."""
    names = [u for u in report.unchecked if not u.startswith("(")]
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

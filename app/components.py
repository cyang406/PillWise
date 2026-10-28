"""Reusable Streamlit UI pieces. Owner: C.

The UI imports ONLY `pillwise.api` and `pillwise.schemas` from the backend.
"""

from __future__ import annotations

import streamlit as st

from pillwise.schemas import Finding, PillCard, Report

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

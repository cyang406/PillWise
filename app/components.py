"""Reusable Streamlit UI pieces. Owner: C.

The UI imports ONLY `pillwise.api` and `pillwise.schemas` from the backend.
"""

from __future__ import annotations

import streamlit as st

from pillwise.schemas import Finding, PillCard, Report

SEVERITY_STYLE = {
    "major": ("🔴", "Serious"),
    "moderate": ("🟠", "Important"),
    "caution": ("🟡", "Extra care at 65+"),
    "minor": ("🔵", "Minor"),
    "unknown": ("⚪", "Unknown"),
}

DISCLAIMER = (
    "PillWise is an educational tool, not medical advice. It does not replace your pharmacist or doctor. "
    "If you have urgent symptoms, call emergency services."
)


def disclaimer() -> None:
    st.info(DISCLAIMER)


def mock_banner(report: Report | None = None) -> None:
    if report is not None and report.is_mock:
        st.warning("Demo data (mock mode). Results are placeholders, not real checks.")


def finding_card(f: Finding) -> None:
    icon, label = SEVERITY_STYLE[f.severity]
    with st.container(border=True):
        st.markdown(f"**{icon} {label} · {f.title}**")
        st.write(f.plain_summary)
        st.markdown(f"**What to do:** {f.what_to_do}")
        with st.expander("Where this comes from"):
            for ev in f.evidence:
                link = f" ([link]({ev.url}))" if ev.url else ""
                st.markdown(f"- **{ev.source}** (version {ev.version}){link}: {ev.text}")


def pill_card(c: PillCard) -> None:
    with st.container(border=True):
        st.markdown(f"**{c.name}**")
        st.write(c.what_it_is_for)
        if c.how_to_take:
            st.markdown(f"**How to take (from your label):** {c.how_to_take}")
        if c.watch_for:
            st.markdown("**Watch for:** " + "; ".join(c.watch_for))


def unchecked_box(report: Report) -> None:
    if report.unchecked:
        st.error(
            "We could not check: "
            + ", ".join(report.unchecked)
            + ". This does NOT mean they are safe. Ask your pharmacist about them."
        )

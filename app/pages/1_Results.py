"""Results: findings sorted by severity, per-pill cards, sources. Owner: C."""

from __future__ import annotations

import streamlit as st

from components import (
    checked_as,
    disclaimer,
    finding_card,
    inject_css,
    mock_banner,
    pill_card,
    summary_line,
    trust_panel,
    unchecked_box,
)
from pillwise import api

st.set_page_config(page_title="PillWise · Results", page_icon="💊", layout="centered")
inject_css()
st.title("Your medicine check")
report = st.session_state.get("report")
if report is None:
    st.info("No results yet. Add your medicines on the Home page.")
    st.page_link("Home.py", label="Go to Home", icon="🏠")
    st.stop()

mock_banner(report)
unchecked_box(report)
summary_line(report)

findings = report.sorted_findings()
st.subheader(f"{len(findings)} thing(s) to talk about with your pharmacist" if findings else "Nothing flagged")
for f in findings:
    finding_card(f)

st.subheader("Your medicines, explained")
for c in report.pill_cards:
    pill_card(c)
checked_as(report)

trust_panel(report, None if report.is_mock else api.recent_audit_events(200))

st.page_link("pages/2_Summary.py", label="Read a plain-language summary", icon="📝")
st.page_link("Home.py", label="Check another list", icon="🏠")
disclaimer()

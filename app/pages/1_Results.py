"""Results: findings sorted by severity, per-pill cards, sources. Owner: C."""

from __future__ import annotations

import streamlit as st

from components import disclaimer, finding_card, mock_banner, pill_card, unchecked_box

st.title("Your medicine check")
report = st.session_state.get("report")
if report is None:
    st.info("No results yet. Add your medicines on the Home page.")
    st.stop()

mock_banner(report)
unchecked_box(report)

findings = report.sorted_findings()
st.subheader(f"{len(findings)} thing(s) to talk about" if findings else "No problems found in our sources")
for f in findings:
    finding_card(f)

st.subheader("Your medicines, explained")
for c in report.pill_cards:
    pill_card(c)

with st.expander("Data sources and versions"):
    st.json(
        {
            "report_id": report.id,
            "generated_at": str(report.generated_at),
            "model": report.model,
            "data_versions": report.data_versions,
        }
    )

# TODO(C): interaction graph (pyvis/plotly), printable PDF, language toggle -> pages/2_Summary.py
disclaimer()

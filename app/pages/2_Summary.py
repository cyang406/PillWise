"""Stretch A: plain-language / translated summary and teach-back quiz. Owner: C."""

from __future__ import annotations

import streamlit as st

from components import disclaimer, mock_banner
from pillwise import api

st.title("Plain-language summary")
report = st.session_state.get("report")
if report is None:
    st.info("Run a check first.")
    st.stop()
mock_banner(report)

lang = st.radio(
    "Language", ["en", "es", "zh"], horizontal=True, format_func={"en": "English", "es": "Español", "zh": "中文"}.get
)
try:
    summary = api.simplify(report, lang)
except NotImplementedError:
    st.info("Coming soon.")
    st.stop()

for s in summary.sections:
    st.markdown(f"**{s.title}**")
    st.write(s.text)
cols = st.columns(2)
if summary.reading_grade is not None:
    cols[0].metric("Reading grade", f"{summary.reading_grade:.1f}")
if summary.drift_score is not None:
    cols[1].metric("Translation check", f"{summary.drift_score:.0%}", "OK" if summary.drift_ok else "Review")

# TODO(C, could): teach-back quiz with api.quiz(report); print/PDF button.
disclaimer()

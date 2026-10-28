"""Plain-language summary (C8) and teach-back quiz (C9). Owner: C."""

from __future__ import annotations

import streamlit as st

from components import disclaimer, inject_css, mock_banner
from pillwise import api

st.set_page_config(page_title="PillWise · Summary", page_icon="💊", layout="centered")
inject_css()
st.title("Plain-language summary")
ss = st.session_state
report = ss.get("report")
if report is None:
    st.info("Run a check first.")
    st.page_link("Home.py", label="Go to Home", icon="🏠")
    st.stop()
mock_banner(report)

# The LLM calls run once per report; quiz clicks rerun this page and must not call them again.
if ss.get("summary_for") != report.id:
    with st.spinner("Writing your summary in plain words..."):
        ss.summary = api.simplify(report, "en")
        try:
            ss.quiz_questions = api.quiz(report, 3)
        except NotImplementedError:
            ss.quiz_questions = []
    ss.summary_for = report.id
summary = ss.summary

st.caption("English only for now. Spanish and Chinese are coming.")
if summary.reading_grade is not None:
    st.metric(
        "Reading level (US school grade)",
        f"{summary.reading_grade:.1f}",
        "target: 6 or lower" if summary.reading_grade <= 6 else "above target",
        delta_color="normal" if summary.reading_grade <= 6 else "inverse",
    )

severity_of = {f.id: f.severity for f in report.findings}
for i, s in enumerate(summary.sections):
    sev = next((severity_of[sid] for sid in s.source_ids if sid in severity_of), None)
    with st.container(border=True, key=f"sev-{sev}-sum-{i}" if sev else None):
        st.markdown(f"**{s.title}**")
        st.write(s.text)

# --- C9 teach-back ---------------------------------------------------------------
if ss.quiz_questions:
    st.subheader("Check what you learned")
    st.caption("Three quick questions. It helps you remember what to ask your pharmacist.")
    with st.form("quiz"):
        answers = [
            st.radio(f"{n}. {q.question}", q.options, index=None, key=f"quiz_{report.id}_{n}")
            for n, q in enumerate(ss.quiz_questions, start=1)
        ]
        submitted = st.form_submit_button("Check my answers", type="primary")
    if submitted:
        right = 0
        for n, (q, a) in enumerate(zip(ss.quiz_questions, answers, strict=True), start=1):
            ok = a == q.options[q.correct_index]
            right += ok
            box = st.success if ok else st.warning
            box(f"**{n}. {'Right' if ok else 'Not quite'}.** {q.explanation}")
        st.markdown(f"**You got {right} of {len(ss.quiz_questions)}.**")

st.page_link("pages/1_Results.py", label="Back to your results", icon="📋")
disclaimer()

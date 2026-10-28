"""Stretch B: clinic / caregiver view over a synthetic population. Owner: C (UI) + A/B (backend)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import finding_card
from pillwise import api

st.title("Clinic view (synthetic patients)")
st.caption("Synthetic data generated with Synthea. No real patients.")
try:
    rows = api.clinic_scan(200)
except NotImplementedError:
    st.info("Coming soon (stretch B).")
    st.stop()

df = pd.DataFrame([r.model_dump() for r in rows])
st.dataframe(df, use_container_width=True, hide_index=True)
pid = st.selectbox("Open a patient", [""] + df["patient_id"].tolist())
if pid:
    for f in api.clinic_patient(pid).sorted_findings():
        finding_card(f)

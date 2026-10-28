"""PillWise home: disclaimer -> capture -> confirm -> check. Owner: C.

Run:  streamlit run app/Home.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import disclaimer
from pillwise import api
from pillwise.config import get_settings
from pillwise.schemas import Medication, PatientContext

st.set_page_config(page_title="PillWise", page_icon="💊", layout="centered")
st.title("💊 PillWise")
st.caption("Snap your pills. Understand them. Stay safe.")
disclaimer()
if get_settings().mock:
    st.caption("Running in mock mode (PILLWISE_MOCK=1).")

ss = st.session_state
ss.setdefault("meds", [])
ss.setdefault("report", None)

# --- 1. Capture -----------------------------------------------------------------
st.subheader("1. Add your medicines")
tab_photo, tab_upload, tab_demo = st.tabs(["Take a photo", "Upload", "Demo scenario"])
with tab_photo:
    shot = st.camera_input("Point the camera at the bottle label")
with tab_upload:
    upload = st.file_uploader("Bottle photo", type=["jpg", "jpeg", "png", "webp"])
with tab_demo:
    scenario = st.selectbox("Scenario", [""] + api.list_scenarios())
    if scenario and st.button("Load scenario"):
        meds, patient = api.load_scenario(scenario)
        ss.meds, ss.age = meds, patient.age

image = shot or upload
if image is not None and st.button("Read this label"):
    with st.spinner("Reading the label..."):
        ss.meds = ss.meds + api.read_bottle(image.getvalue(), image.type or "image/jpeg")

# --- 2. Confirm -----------------------------------------------------------------
st.subheader("2. Check what we read")
st.caption("Fix anything that looks wrong. Nothing is checked until you confirm.")
cols = ["name", "strength", "directions"]
df = pd.DataFrame([m.model_dump(include=set(cols)) for m in ss.meds], columns=cols)
edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="med_editor")
age = st.number_input(
    "Age (optional, used for 65+ checks)", min_value=0, max_value=120, value=ss.get("age") or 0, step=1
)

# --- 3. Check -------------------------------------------------------------------
if st.button("Confirm and check", type="primary", disabled=edited.dropna(subset=["name"]).empty):
    by_name = {m.name: m for m in ss.meds}
    confirmed: list[Medication] = []
    for row in edited.dropna(subset=["name"]).to_dict("records"):
        base = by_name.get(row["name"])
        data = base.model_dump() if base else {"name": row["name"], "source": "manual"}
        data.update({k: (v if pd.notna(v) else None) for k, v in row.items()}, confirmed=True)
        confirmed.append(Medication(**data))
    with st.spinner("Checking your list..."):
        ss.report = api.check(confirmed, PatientContext(age=int(age) or None))
    st.switch_page("pages/1_Results.py")

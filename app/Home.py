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
ss.setdefault("read_ids", set())  # photos already read, so a rerun never adds the same bottle twice
ss.setdefault("editor_version", 0)  # new editor key whenever ss.meds is replaced, so stale edits never apply


def set_meds(meds: list[Medication]) -> None:
    ss.meds = meds
    ss.editor_version += 1


# --- 1. Capture -----------------------------------------------------------------
st.subheader("1. Add your medicines")
tab_photo, tab_upload, tab_demo = st.tabs(["Take a photo", "Upload", "Demo scenario"])
with tab_photo:
    shot = st.camera_input("Point the camera at the bottle label")
with tab_upload:
    upload = st.file_uploader("Bottle photo", type=["jpg", "jpeg", "png", "webp"])
with tab_demo:
    scenario = st.selectbox(
        "Scenario", [""] + api.list_scenarios(), format_func=lambda s: s.replace("_", " ").capitalize()
    )
    if scenario and st.button("Load scenario"):
        meds, patient = api.load_scenario(scenario)
        set_meds(meds)
        ss.age = patient.age

image = shot or upload
if image is not None:
    if image.file_id in ss.read_ids:
        st.caption("This photo is already in your list.")
    elif st.button("Read this label"):
        with st.spinner("Reading the label..."):
            found = api.read_bottle(image.getvalue(), image.type or "image/jpeg")
        if found:
            ss.read_ids.add(image.file_id)
            set_meds(ss.meds + found)
            st.success(f"Found {len(found)} medicine(s). Check them below.")
        else:
            st.warning("We could not read a medicine on this photo. Type it in the table below, or try another photo.")

# --- 2. Confirm -----------------------------------------------------------------
st.subheader("2. Check what we read")
st.markdown(
    "**Check each name against the bottle.** A misread letter can turn one medicine into another. "
    "Fix anything that looks wrong; nothing is checked until you confirm."
)
cols = ["name", "strength", "directions"]
df = pd.DataFrame([m.model_dump(include=set(cols)) for m in ss.meds], columns=cols)
edited = st.data_editor(
    df,
    num_rows="dynamic",
    width="stretch",
    key=f"med_editor_{ss.editor_version}",
    column_config={
        "name": st.column_config.TextColumn("Medicine name", required=True),
        "strength": st.column_config.TextColumn("Strength"),
        "directions": st.column_config.TextColumn("Directions (as on the label)"),
    },
)
age = st.number_input(
    "Age (optional, used for 65+ checks)", min_value=0, max_value=120, value=ss.get("age") or 0, step=1
)

# --- 3. Check -------------------------------------------------------------------
rows = [r for r in edited.to_dict("records") if isinstance(r["name"], str) and r["name"].strip()]
if st.button("Confirm and check", type="primary", disabled=not rows):
    by_name = {m.name: m for m in ss.meds}
    confirmed: list[Medication] = []
    for row in rows:
        base = by_name.get(row["name"])
        data = base.model_dump() if base else {"name": row["name"].strip(), "source": "manual"}
        data.update({k: (v.strip() or None) if isinstance(v, str) else None for k, v in row.items() if k != "name"})
        data["confirmed"] = True
        confirmed.append(Medication(**data))
    with st.spinner("Checking your list..."):
        ss.report = api.check(confirmed, PatientContext(age=int(age) or None))
    st.switch_page("pages/1_Results.py")

if ss.meds and st.button("Start over"):
    set_meds([])
    ss.report, ss.age = None, None
    ss.read_ids = set()
    st.rerun()

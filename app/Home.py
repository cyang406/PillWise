"""PillWise, one page: your medicines -> what we found -> take this to your pharmacist. Owner: C.

Run:  streamlit run app/Home.py
"""

from __future__ import annotations

import uuid

import streamlit as st

import fhir_export
from components import (
    SEVERITY_STYLE,
    checked_as,
    connections_box,
    disclaimer,
    finding_card,
    in_mobile_app,
    inject_css,
    list_signature,
    mock_banner,
    pill_card,
    questions,
    summary_text,
    trust_panel,
    unchecked_box,
    verdict_banner,
)
from pillwise import api
from pillwise.config import get_settings
from pillwise.schemas import Medication, PatientContext

st.set_page_config(page_title="PillWise", page_icon=":material/medication:", layout="wide")

ss = st.session_state
ss.setdefault("items", [])  # [{"id", "med": Medication, "ok": bool}]; ok = "matches my bottle"
ss.setdefault("report", None)
ss.setdefault("report_sig", None)
ss.setdefault("read_ids", set())  # photos already read, so a rerun never reads the same bottle twice
ss.setdefault("large_text", False)

inject_css(ss.large_text)


def add_meds(meds: list[Medication], ok: bool = False) -> None:
    ss["items"] = ss["items"] + [{"id": uuid.uuid4().hex[:8], "med": m, "ok": ok} for m in meds]


def read_photo(f) -> None:
    if f.file_id in ss.read_ids:
        return
    with st.spinner(f"Reading {f.name or 'the label'}..."):
        found = api.read_bottle(f.getvalue(), f.type or "image/jpeg")
    if found:
        ss.read_ids.add(f.file_id)
        add_meds(found)
        st.toast(f"Found {len(found)} medicine(s) on {f.name or 'the photo'}. Check them below.")
    else:
        st.warning(f"We could not read a medicine on {f.name or 'this photo'}. Type it in, or try a clearer photo.")


# --- top bar ---------------------------------------------------------------------------
top_l, top_r = st.columns([3, 1], vertical_alignment="center")
with top_l:
    st.markdown(
        '<div class="pw-brand"><svg aria-hidden="true" width="30" height="30" viewBox="0 0 24 24" fill="none" '
        'stroke="#0F6B63" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M10.5 20.5a4.95 4.95 0 0 1-7-7l10-10a4.95 4.95 0 0 1 7 7z"/>'
        '<line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/></svg>PillWise</div>'
        '<nav class="pw-steps" aria-label="Steps"><a href="#your-medicines">1 Your medicines</a>'
        '<a href="#what-we-found">2 What we found</a><a href="#take-this-to-your-pharmacist">3 Talk to your pharmacist</a></nav>',
        unsafe_allow_html=True,
    )
with top_r:
    st.toggle("Larger text", key="large_text")
disclaimer()
if get_settings().mock:
    st.caption("Running in mock mode (PILLWISE_MOCK=1).")

# --- 1. Your medicines -------------------------------------------------------------------
with st.container(border=True):
    st.header("Your medicines", anchor="your-medicines")
    st.caption("Add every medicine you take, including ones you buy without a prescription. Photos are not stored.")

    if in_mobile_app():
        shot = st.camera_input("Take a photo of a bottle label")
        if shot is not None:
            read_photo(shot)
    photos = st.file_uploader(
        "Add bottle photos (you can choose several)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True
    )
    for f in photos or []:
        read_photo(f)

    add_l, add_r = st.columns(2)
    with add_l, st.popover("Type a medicine", icon=":material/edit:", width="stretch"):
        with st.form("type_med", clear_on_submit=True):
            name = st.text_input("Medicine name (as on the bottle)")
            strength = st.text_input("Strength, e.g. 200 mg (optional)")
            directions = st.text_input("Directions, copied from the label (optional)")
            if st.form_submit_button("Add to my list", type="primary") and name.strip():
                add_meds(
                    [
                        Medication(
                            name=name.strip(), strength=strength.strip() or None, directions=directions.strip() or None
                        )
                    ],
                    ok=True,
                )
                st.rerun()
    with add_r, st.popover("Try a sample list", icon=":material/science:", width="stretch"):
        for sc in api.list_scenarios():
            if st.button(sc.replace("_", " ").capitalize(), key=f"sc_{sc}", width="stretch"):
                meds, patient = api.load_scenario(sc)
                ss["items"] = []
                add_meds(meds, ok=True)
                ss.age = patient.age
                st.rerun()

    if ss["items"]:
        st.markdown("**Check each name against the bottle.** A misread letter can turn one medicine into another.")
    for it in list(ss["items"]):
        m: Medication = it["med"]
        with st.container(border=True, key=f"med-{it['id']}-{'ok' if it['ok'] else 'check'}"):
            c_ok, c_info, c_act = st.columns([1.3, 4, 1.2], vertical_alignment="center")
            it["ok"] = c_ok.checkbox("Matches my bottle", value=it["ok"], key=f"ok_{it['id']}")
            source = {"photo": "From photo", "scenario": "Sample", "manual": "Typed"}.get(m.source, m.source)
            c_info.markdown(
                f"**{m.name}** {m.strength or ''}  \n"
                + (f"Directions on the label: {m.directions}" if m.directions else "*No directions read*")
                + f"  \n<span class='pw-src'>{source}</span>",
                unsafe_allow_html=True,
            )
            with c_act.popover("Edit", icon=":material/edit:"):
                with st.form(f"edit_{it['id']}"):
                    new_name = st.text_input("Medicine name", m.name)
                    new_strength = st.text_input("Strength", m.strength or "")
                    new_dir = st.text_input("Directions (from the label)", m.directions or "")
                    if st.form_submit_button("Save", type="primary"):
                        changed_name = new_name.strip() != m.name
                        data = {
                            "name": new_name.strip() or m.name,
                            "strength": new_strength.strip() or None,
                            "directions": new_dir.strip() or None,
                        }
                        if changed_name:  # a new name is a new medicine: drop what we matched for the old one
                            data.update(generic_name=None, ingredients=[], rxcui=None, source="manual")
                        it["med"] = m.model_copy(update=data)
                        it["ok"] = True
                        st.rerun()
            if c_act.button("Remove", key=f"rm_{it['id']}", icon=":material/delete:"):
                ss["items"] = [x for x in ss["items"] if x["id"] != it["id"]]
                st.rerun()

    age = st.number_input(
        "Your age (optional)", min_value=0, max_value=120, value=ss.get("age"), step=1, placeholder="e.g. 45"
    )
    st.caption("Some checks depend on age, for example extra care at 65 or older. Not saved.")
    not_ticked = [it["med"].name for it in ss["items"] if not it["ok"]]
    if not_ticked:
        st.warning("Not ticked yet: " + ", ".join(not_ticked) + ". Check these names against the bottles.")
    if st.button("Check my list", type="primary", disabled=not ss["items"], icon=":material/fact_check:"):
        confirmed = [it["med"].model_copy(update={"confirmed": True}) for it in ss["items"]]
        with st.spinner("Checking your list..."):
            ss.report = api.check(confirmed, PatientContext(age=int(age) if age else None))
        ss.report_sig = list_signature([it["med"] for it in ss["items"]], int(age) if age else None)
        for k in ("summary_for", "summary", "quiz_questions", "newmed"):
            ss.pop(k, None)

report = ss.report
current = list_signature([it["med"] for it in ss["items"]], int(age) if age else None)
if report is None:
    st.stop()
if ss.report_sig != current:
    st.info("Your list changed since the last check. Press **Check my list** to see new results.")
    st.stop()

# --- 2. What we found --------------------------------------------------------------------
st.header("What we found", anchor="what-we-found")
mock_banner(report)
verdict_banner(report)
unchecked_box(report)
left, right = st.columns([2, 1], gap="medium")
with left:
    for f in report.sorted_findings():
        finding_card(f)
with right:
    connections_box(report)
    checked_as(report)

st.subheader("Each medicine, in plain words")
by_key = {m.key: m for m in report.meds}
cols = st.columns(min(3, max(1, len(report.pill_cards))))
for i, c in enumerate(report.pill_cards):
    with cols[i % len(cols)]:
        pill_card(c, by_key.get(c.med_key), report)

# --- 3. Take this to your pharmacist ------------------------------------------------------
with st.container(border=True):
    st.header("Take this to your pharmacist", anchor="take-this-to-your-pharmacist")
    q_col, s_col = st.columns([1.2, 1], gap="large")
    with q_col:
        st.markdown("#### Questions to ask")
        st.caption("Tick each one once you have asked it.")
        for i, (sev, q) in enumerate(questions(report)):
            st.checkbox(f"{q}  ·  *{SEVERITY_STYLE[sev][0]}*", key=f"q_{report.id}_{i}")
        if not report.findings:
            st.markdown("- Is there anything on my list I should keep an eye on?")
    with s_col:
        # The LLM calls run once per report; quiz clicks rerun the page and must not call them again.
        if ss.get("summary_for") != report.id:
            with st.spinner("Writing a plain-language summary..."):
                try:
                    ss.summary = api.simplify(report, "en")
                except Exception:  # noqa: BLE001 - the page still works without it
                    ss.summary = None
                try:
                    ss.quiz_questions = api.quiz(report, 3)
                except Exception:  # noqa: BLE001
                    ss.quiz_questions = []
            ss.summary_for = report.id
        summary = ss.summary
        if summary and summary.sections:
            st.markdown("#### In short")
            if summary.reading_grade is not None:
                st.caption(f"Reading level {summary.reading_grade:.1f} (US school grade; we aim for 6 or lower)")
            st.write(summary.sections[0].text)
            if len(summary.sections) > 1:
                with st.expander("Read the whole summary"):
                    for s in summary.sections:
                        st.markdown(f"**{s.title}**")
                        st.write(s.text)
        if ss.get("quiz_questions"):
            with st.form("quiz"):
                st.markdown("#### Check your understanding")
                answers = [
                    st.radio(q.question, q.options, index=None, key=f"quiz_{report.id}_{n}")
                    for n, q in enumerate(ss.quiz_questions)
                ]
                submitted = st.form_submit_button("Check my answers")
            if submitted:
                right_n = 0
                for q, a in zip(ss.quiz_questions, answers, strict=True):
                    ok = a == q.options[q.correct_index]
                    right_n += ok
                    (st.success if ok else st.warning)(f"**{'Right' if ok else 'Not quite'}.** {q.explanation}")
                st.markdown(f"**You got {right_n} of {len(ss.quiz_questions)}.**")
    b1, b2 = st.columns(2)
    b1.download_button(
        "Download a summary to share",
        summary_text(report),
        file_name="pillwise-summary.txt",
        icon=":material/share:",
        width="stretch",
    )
    b2.download_button(
        "File for the pharmacy (FHIR)",
        fhir_export.to_json(report),
        file_name="pillwise-medications.fhir.json",
        mime="application/fhir+json",
        icon=":material/download:",
        width="stretch",
        help="A standard health-record file (FHIR R4 MedicationStatement) a pharmacy or clinic system can import.",
    )

# --- Can I take this? ----------------------------------------------------------------------
with st.container(border=True, key="newmed"):
    st.header("Thinking of buying something new?", anchor="new-medicine")
    st.markdown("Check one medicine against your list before you buy it. Your list stays as it is.")
    with st.form("newmed_form"):
        new_name = st.text_input("Medicine name, e.g. Aleve")
        go = st.form_submit_button("Check against my list", type="primary")
    if go and new_name.strip():
        extra = Medication(name=new_name.strip(), source="manual", confirmed=True)
        with st.spinner("Checking..."):
            ss.newmed = api.check(list(report.meds) + [extra], report.patient)
    nm = ss.get("newmed")
    if nm is not None:
        new = nm.meds[-1]
        mine = set(new.match_names)
        if new.name in nm.unchecked or not (new.ingredients or new.generic_name):
            st.error(f"**We could not check {new.name}.** This does NOT mean it is safe. Ask your pharmacist.")
        else:
            related = [f for f in nm.sorted_findings() if mine & set(f.drugs)]
            st.caption(f"{new.name} → {', '.join(new.ingredients) or new.generic_name}")
            if related:
                for f in related:
                    finding_card(f, where="new")
            else:
                st.success(
                    f"No problems found between {new.name} and your list in our sources. "
                    "That does not mean it is safe for you. Ask your pharmacist."
                )

trust_panel(report, None if report.is_mock else api.recent_audit_events(200))
st.caption("Rules and data decide every warning. AI only reads labels and explains.")

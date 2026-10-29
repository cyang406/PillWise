"""PillWise, one page (design canvas v4): you & your pills -> results -> ask your pharmacist. Owner: C.

Run:  streamlit run app/Home.py
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

import fhir_export
from components import (
    LOGO,
    PILL_ICON,
    SEVERITY_STYLE,
    checked_as,
    disclaimer,
    finding_card,
    heatmap,
    in_mobile_app,
    inject_css,
    list_signature,
    match_badge,
    mock_banner,
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
ss.setdefault("items", [])  # [{"id", "med": Medication}]
ss.setdefault("report", None)
ss.setdefault("report_sig", None)
ss.setdefault("read_ids", set())  # photos already read, so a rerun never reads the same bottle twice
ss.setdefault("large_text", False)

inject_css(ss.large_text)


def _matched(meds: list[Medication]) -> list[Medication]:
    """Look each name up in RxNorm now, so a name we can't match is flagged before the check."""
    try:
        return api.match_names(meds)
    except Exception:  # noqa: BLE001 - unmatched names are flagged, never treated as safe
        return meds


def add_meds(meds: list[Medication]) -> None:
    ss["items"] = ss["items"] + [{"id": uuid.uuid4().hex[:8], "med": m} for m in _matched(meds)]


def _is_matched(m: Medication) -> bool:
    return bool(m.ingredients or m.generic_name)


def _same_med(m: Medication) -> tuple[str, str]:
    return m.name.strip().lower(), (m.strength or "").replace(" ", "").lower()


def _read_one(blob: tuple[bytes, str]) -> list[Medication]:
    try:
        return api.read_bottle(*blob)
    except Exception:  # noqa: BLE001 - one bad photo must not stop the others
        return []


def read_photos(files: list) -> None:
    """Read every new photo at once (in parallel), add what was found, skip bottles already on the list."""
    new = [f for f in files if f is not None and f.file_id not in ss.read_ids]
    if not new:
        return
    # Each photo is tried once; a failed one stays failed until it is removed and added again (no repeat API calls).
    ss.read_ids.update(f.file_id for f in new)
    blobs = [(f.getvalue(), f.type or "image/jpeg") for f in new]
    with st.spinner(f"Reading {len(new)} photo{'s' if len(new) > 1 else ''}..."):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(_read_one, blobs))
    have = {_same_med(it["med"]) for it in ss["items"]}
    added, dupes, failed = [], [], []
    for f, found in zip(new, results, strict=True):
        if not found:
            failed.append(f.name or "a photo")
        for m in found:
            (dupes if _same_med(m) in have else added).append(m)
            have.add(_same_med(m))
    add_meds(added)
    if added:
        st.toast(f"Found {len(added)} medicine(s) on {len(new)} photo(s). Check them below.")
    # Shown until the next photos are read, so a failed photo is not missed after the page reruns.
    ss.photo_notes = []
    if dupes:
        ss.photo_notes.append(
            ("info", "Already on your list, so not added again: " + ", ".join(m.name for m in dupes) + ".")
        )
    if failed:
        ss.photo_notes.append(
            (
                "warning",
                "We could not read a medicine on: "
                + ", ".join(failed)
                + ". Type it in, or remove the photo and try a clearer one.",
            )
        )


# --- header ----------------------------------------------------------------------------
h_l, h_r = st.columns([4, 1.3], vertical_alignment="center")
with h_l:
    st.markdown(
        f'<div class="pw-brand">{LOGO}PillWise</div>'
        '<nav class="pw-steps" aria-label="Steps"><a href="#you-and-your-pills">1 You &amp; your pills</a>'
        '<a href="#results">2 Results</a><a href="#ask-your-pharmacist">3 Pharmacist</a></nav>',
        unsafe_allow_html=True,
    )
with h_r:
    a_col, s_col = st.columns(2)
    a_col.toggle("A+", key="large_text", help="Larger text")
    if s_col.button("Start over", width="stretch"):
        for k in ("items", "report", "report_sig", "age", "photo_notes", "summary_for", "newmed"):
            ss.pop(k, None)
        ss.read_ids = set()
        st.rerun()

# --- 1. You & your pills -------------------------------------------------------------------
st.markdown(
    '<h1 class="pw-hero" id="you-and-your-pills">Do your pills mix well? Snap a photo.</h1>', unsafe_allow_html=True
)
st.markdown("Photograph each bottle. We explain each one in plain words and tell you what to ask your pharmacist.")
if get_settings().mock:
    st.caption("Running in mock mode (PILLWISE_MOCK=1).")

with st.container(border=True, key="startbox"):
    a_l, a_r = st.columns([1, 2.4], vertical_alignment="bottom")
    with a_l:
        st.markdown('<div class="pw-step"><b>Step 1 ·</b> Your age</div>', unsafe_allow_html=True)
        age = st.number_input(
            "Your age (optional)",
            min_value=0,
            max_value=120,
            value=ss.get("age"),
            step=1,
            placeholder="e.g. 45",
            label_visibility="collapsed",
        )
    a_r.caption("Optional. Some medicines need extra care after 65. Not saved.")

    st.markdown('<div class="pw-step"><b>Step 2 ·</b> Your medicines</div>', unsafe_allow_html=True)
    if in_mobile_app():
        shot = st.camera_input("Take a photo of a bottle label")
        if shot is not None:
            read_photos([shot])
    photos = st.file_uploader(
        "Add bottle photos: drop several at once (or ⌘/Ctrl + click). Photos aren’t stored.",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )
    read_photos(photos or [])
    for kind, text in ss.get("photo_notes", []):
        (st.info if kind == "info" else st.warning)(text)

    for it in list(ss["items"]):
        m: Medication = it["med"]
        with st.container(border=True, key=f"med-{it['id']}-{'ok' if _is_matched(m) else 'check'}"):
            c_info, c_act = st.columns([4, 2], vertical_alignment="center")
            note = m.directions or "No directions read from the label"
            c_info.markdown(
                f'<div style="display:flex;gap:.8rem;align-items:center">{PILL_ICON}<div>'
                f"{match_badge(m)}<br><b>{m.name}</b> {m.strength or ''}"
                f'<br><span class="pw-src">{note}</span></div></div>',
                unsafe_allow_html=True,
            )
            e_col, r_col = c_act.columns(2)
            with e_col.popover("Edit", icon=":material/edit:"):
                with st.form(f"edit_{it['id']}"):
                    new_name = st.text_input("Medicine name", m.name)
                    new_strength = st.text_input("Strength", m.strength or "")
                    new_dir = st.text_input("Directions (from the label)", m.directions or "")
                    if st.form_submit_button("Save", type="primary"):
                        data = {
                            "name": new_name.strip() or m.name,
                            "strength": new_strength.strip() or None,
                            "directions": new_dir.strip() or None,
                        }
                        if data["name"] != m.name:  # a new name is a new medicine: match it again
                            data.update(generic_name=None, ingredients=[], rxcui=None, source="manual")
                            it["med"] = _matched([m.model_copy(update=data)])[0]
                        else:
                            it["med"] = m.model_copy(update=data)
                        st.rerun()
            if r_col.button("Remove", key=f"rm_{it['id']}", icon=":material/delete:"):
                ss["items"] = [x for x in ss["items"] if x["id"] != it["id"]]
                st.rerun()

    t_col, s_col2 = st.columns(2)
    with t_col, st.popover("Type a name", icon=":material/edit:", width="stretch"):
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
                    ]
                )
                st.rerun()
    with s_col2, st.popover("Try a sample", icon=":material/science:", width="stretch"):
        for sc in api.list_scenarios():
            if st.button(sc.replace("_", " ").capitalize(), key=f"sc_{sc}", width="stretch"):
                meds, patient = api.load_scenario(sc)
                ss["items"] = []
                add_meds(meds)
                ss.age = patient.age
                st.rerun()

    unmatched = [it["med"].name for it in ss["items"] if not _is_matched(it["med"])]
    if unmatched:
        st.warning(
            "We could not match: " + ", ".join(unmatched) + ". Check the spelling against the bottle; "
            "otherwise it will be listed as “could not check”."
        )
    if st.button("Check my list", type="primary", disabled=not ss["items"], width="stretch"):
        confirmed = [it["med"].model_copy(update={"confirmed": True}) for it in ss["items"]]
        with st.spinner("Checking your list..."):
            ss.report = api.check(confirmed, PatientContext(age=int(age) if age else None))
        ss.report_sig = list_signature([it["med"] for it in ss["items"]], int(age) if age else None)
        for k in ("summary_for", "summary", "quiz_questions", "newmed"):
            ss.pop(k, None)
disclaimer()

report = ss.report
current = list_signature([it["med"] for it in ss["items"]], int(age) if age else None)
if report is None:
    st.stop()
if ss.report_sig != current:
    st.info("Your list changed since the last check. Press **Check my list** to see new results.")
    st.stop()

# --- 2. Results ----------------------------------------------------------------------------
st.header("Results", anchor="results")
mock_banner(report)
verdict_banner(report)
unchecked_box(report)
heatmap(report)
with st.expander(f"All {len(report.findings)} findings, with what to do and sources"):
    for f in report.sorted_findings():
        finding_card(f)
checked_as(report)

# --- 3. Ask your pharmacist ---------------------------------------------------------------
with st.container(border=True, key="pharm"):
    t_l, t_r = st.columns([1.4, 1], vertical_alignment="center")
    with t_l:
        st.header("Ask your pharmacist", anchor="ask-your-pharmacist")
        st.caption("Show this list. Most important first.")
    with t_r:
        d1, d2 = st.columns(2)
        d1.download_button(
            "Share",
            summary_text(report),
            file_name="pillwise-summary.txt",
            icon=":material/share:",
            width="stretch",
            help="Download a plain-text summary to send to family or print.",
        )
        d2.download_button(
            "Pharmacy file",
            fhir_export.to_json(report),
            file_name="pillwise-medications.fhir.json",
            mime="application/fhir+json",
            icon=":material/download:",
            width="stretch",
            help="A standard health-record file (FHIR R4 MedicationStatement) a pharmacy or clinic system can import.",
        )
    q_col, n_col = st.columns([1.3, 1], gap="large")
    with q_col:
        qs = questions(report) or [("unknown", "Is there anything on my list I should keep an eye on?")]
        st.markdown(
            "\n".join(
                f'{i}. {q} <span class="pw-chip pw-cell-{sev}">{SEVERITY_STYLE[sev][0]}</span>'
                for i, (sev, q) in enumerate(qs, start=1)
            ),
            unsafe_allow_html=True,
        )
    with n_col, st.container(border=True, key="newmed"):
        st.markdown("#### Buying something new?")
        with st.form("newmed_form"):
            new_name = st.text_input("Medicine name, e.g. Aleve")
            go = st.form_submit_button("Check")
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
            st.markdown(f"**{new.name} = {', '.join(new.ingredients) or new.generic_name}**")
            if related:
                for f in related:
                    finding_card(f, where="new")
            else:
                st.success(
                    f"No problems found between {new.name} and your list in our sources. "
                    "That does not mean it is safe for you. Ask your pharmacist."
                )

    with st.expander("Plain-language summary and a quick check"):
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
            if summary.reading_grade is not None:
                st.caption(f"Reading level {summary.reading_grade:.1f} (US school grade; we aim for 6 or lower)")
            for s in summary.sections:
                st.markdown(f"**{s.title}**")
                st.write(s.text)
        if ss.get("quiz_questions"):
            with st.form("quiz"):
                st.markdown("**Check your understanding**")
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

trust_panel(report, None if report.is_mock else api.recent_audit_events(200))
st.caption(
    "Rules and data decide every warning. AI only reads labels and explains. "
    + "DDInter 2.0 · ONC list · Beers 2023 · FDA labels"
)

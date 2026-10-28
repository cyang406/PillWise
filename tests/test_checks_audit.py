"""Audit log round trip (pillwise/audit.py)."""

from pillwise import audit, mocks
from pillwise.schemas import AuditEvent, Medication, PatientContext


def test_empty_when_no_db(tmp_path, monkeypatch):
    monkeypatch.setenv("PILLWISE_AUDIT_DB", str(tmp_path / "audit.sqlite"))
    assert audit.recent_events() == []


def test_log_report_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("PILLWISE_AUDIT_DB", str(tmp_path / "audit.sqlite"))
    meds = [
        Medication(name="Warfarin", ingredients=["warfarin"], raw_text="SECRET LABEL TEXT"),
        Medication(name="Ibuprofen", ingredients=["ibuprofen"]),
    ]
    report = mocks.mock_report(meds, PatientContext(age=72))
    audit.log_report(report)
    audit.log_event(AuditEvent(report_id=report.id, event="simplified", detail="en"))

    events = audit.recent_events()
    assert events[0].event == "simplified"  # newest first
    kinds = [e.event for e in events]
    assert kinds.count("report_created") == 1
    assert kinds.count("finding") == len(report.findings)
    assert kinds.count("pill_card") == len(report.pill_cards)
    assert {e.finding_id for e in events if e.event == "finding"} == {f.id for f in report.findings}
    assert all(e.report_id == report.id for e in events)
    assert not any("SECRET" in e.detail for e in events)
    assert len(audit.recent_events(limit=2)) == 2

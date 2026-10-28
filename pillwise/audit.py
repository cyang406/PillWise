"""Audit log: which source and version stands behind every claim. Owner: B.

Contract with A (do not change these signatures):
    log_report(report) -> None          # one report_created event + one event per finding / pill card
    log_event(event: AuditEvent) -> None
    recent_events(limit=100) -> list[AuditEvent]   # used by the UI's "Trust" panel

Storage: SQLite at settings.audit_db via SQLModel (or plain sqlite3).
Never store photos, raw_text or anything that identifies a person.

TODO(B):
- [ ] Create the table on first use.
- [ ] Implement the three functions below.
"""

from __future__ import annotations

from pillwise.schemas import AuditEvent, Report


def log_event(event: AuditEvent) -> None:
    raise NotImplementedError("B: implement audit storage")


def log_report(report: Report) -> None:
    raise NotImplementedError("B: implement audit storage")


def recent_events(limit: int = 100) -> list[AuditEvent]:
    raise NotImplementedError("B: implement audit storage")

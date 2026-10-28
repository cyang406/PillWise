"""Audit log: which source and version stands behind every claim. Owner: B.

Contract with A (do not change these signatures):
    log_report(report) -> None          # one report_created event + one event per finding / pill card
    log_event(event: AuditEvent) -> None
    recent_events(limit=100) -> list[AuditEvent]   # used by the UI's "Trust" panel

Storage: plain sqlite3 at settings.audit_db, table created on first use.
Never store photos, raw_text, age or anything that identifies a person: only
ids, kinds, severities, titles and source versions.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from pillwise.config import get_settings
from pillwise.schemas import AuditEvent, Report

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    report_id TEXT NOT NULL,
    event TEXT NOT NULL,
    finding_id TEXT,
    source TEXT,
    source_version TEXT,
    model TEXT,
    detail TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_report ON audit_events(report_id);
"""

_COLS = ("timestamp", "report_id", "event", "finding_id", "source", "source_version", "model", "detail")


def _connect() -> sqlite3.Connection:
    path = get_settings().audit_db
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(_SCHEMA)
    return con


def _row(e: AuditEvent) -> tuple:
    return (
        e.timestamp.isoformat(),
        e.report_id,
        e.event,
        e.finding_id,
        e.source,
        e.source_version,
        e.model,
        e.detail,
    )


def _insert(events: list[AuditEvent]) -> None:
    con = _connect()
    try:
        with con:
            con.executemany(
                f"INSERT INTO audit_events ({','.join(_COLS)}) VALUES ({','.join('?' * len(_COLS))})",
                [_row(e) for e in events],
            )
    finally:
        con.close()


def log_event(event: AuditEvent) -> None:
    _insert([event])


def _joined(values: list[str]) -> str | None:
    unique = list(dict.fromkeys(v for v in values if v))
    return ", ".join(unique) or None


def log_report(report: Report) -> None:
    events = [
        AuditEvent(
            report_id=report.id,
            event="report_created",
            source=_joined(list(report.data_versions)),
            source_version=_joined([f"{k}={v}" for k, v in report.data_versions.items()]),
            model=report.model,
            detail=f"{len(report.meds)} meds, {len(report.findings)} findings, {len(report.unchecked)} unchecked"
            + (" (mock)" if report.is_mock else ""),
        )
    ]
    for f in report.findings:
        events.append(
            AuditEvent(
                report_id=report.id,
                event="finding",
                finding_id=f.id,
                source=_joined([e.source for e in f.evidence]),
                source_version=_joined([e.version for e in f.evidence]),
                model=report.model,
                detail=f"{f.checker}: {f.kind}/{f.severity}: {f.title}",
            )
        )
    for card in report.pill_cards:
        events.append(
            AuditEvent(
                report_id=report.id,
                event="pill_card",
                finding_id=card.med_key,
                source=_joined([e.source for e in card.evidence]),
                source_version=_joined([e.version for e in card.evidence]),
                model=report.model,
                detail=f"pill card: {card.name}",
            )
        )
    for item in report.unchecked:
        if item.startswith("(checker"):
            events.append(AuditEvent(report_id=report.id, event="error", detail=item))
    _insert(events)


def recent_events(limit: int = 100) -> list[AuditEvent]:
    if not get_settings().audit_db.exists():
        return []
    con = _connect()
    try:
        rows = con.execute(f"SELECT {','.join(_COLS)} FROM audit_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    finally:
        con.close()
    return [AuditEvent(**{**dict(zip(_COLS, r, strict=True)), "timestamp": datetime.fromisoformat(r[0])}) for r in rows]

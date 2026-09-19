"""Append-only JSONL event history with a tamper-detection head commitment."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_path, resolve_project_root
from .format import EventValidationError, canonical_json, make_event, validate_event


class EventLogIntegrityError(ValueError):
    """Raised when event history is malformed or no longer matches its head."""


class EventLog:
    def __init__(self, project_root: str | os.PathLike[str]) -> None:
        self.project_root = resolve_project_root(project_root)
        self.events_path = resolve_project_path(self.project_root, ".idd/state/events.jsonl")
        self.head_path = resolve_project_path(self.project_root, ".idd/state/events.head.json")
        self.events_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_raw(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.events_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    raise EventLogIntegrityError(f"blank event line at {line_number}")
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise EventLogIntegrityError(f"invalid JSON at line {line_number}") from exc
                if not isinstance(value, dict):
                    raise EventLogIntegrityError(f"event at line {line_number} is not an object")
                try:
                    validate_event(value)
                except EventValidationError as exc:
                    raise EventLogIntegrityError(f"invalid event at line {line_number}: {exc}") from exc
                if line.rstrip("\n") != canonical_json(value):
                    raise EventLogIntegrityError(f"non-canonical event encoding at line {line_number}")
                records.append(value)
        return records

    def verify(self) -> list[dict[str, Any]]:
        records = self._read_raw()
        seen: set[str] = set()
        previous_id: str | None = None
        previous_hash: str | None = None
        for record in records:
            if record["event_id"] in seen:
                raise EventLogIntegrityError(f"duplicate event_id: {record['event_id']}")
            if record["previous_event_id"] != previous_id:
                raise EventLogIntegrityError("event chain previous_event_id mismatch")
            if record["previous_event_hash"] != previous_hash:
                raise EventLogIntegrityError("event chain previous_event_hash mismatch")
            seen.add(record["event_id"])
            previous_id = record["event_id"]
            previous_hash = record["event_hash"]
        if self.head_path.exists():
            try:
                head = json.loads(self.head_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise EventLogIntegrityError("invalid head commitment JSON") from exc
            expected = {
                "schema_version": 1,
                "event_count": len(records),
                "last_event_id": previous_id,
                "last_event_hash": previous_hash,
            }
            if head != expected:
                raise EventLogIntegrityError("event history does not match head commitment")
        elif records:
            raise EventLogIntegrityError("event history has no head commitment")
        return records

    def new_event(self, **fields: Any) -> dict[str, Any]:
        records = self.verify()
        previous = records[-1] if records else None
        return make_event(
            previous_event_id=previous["event_id"] if previous else None,
            previous_event_hash=previous["event_hash"] if previous else None,
            **fields,
        )

    def append(self, event: dict[str, Any]) -> None:
        records = self.verify()
        previous = records[-1] if records else None
        try:
            validate_event(event)
        except EventValidationError as exc:
            raise EventLogIntegrityError(f"candidate event failed validation: {exc}") from exc
        if event["previous_event_id"] != (previous["event_id"] if previous else None):
            raise EventLogIntegrityError("new event has incorrect previous_event_id")
        if event["previous_event_hash"] != (previous["event_hash"] if previous else None):
            raise EventLogIntegrityError("new event has incorrect previous_event_hash")
        if any(item["event_id"] == event["event_id"] for item in records):
            raise EventLogIntegrityError(f"duplicate event_id: {event['event_id']}")
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(canonical_json(event) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        head = {
            "schema_version": 1,
            "event_count": len(records) + 1,
            "last_event_id": event["event_id"],
            "last_event_hash": event["event_hash"],
        }
        self.head_path.write_text(canonical_json(head) + "\n", encoding="utf-8")

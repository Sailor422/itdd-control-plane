import json
from pathlib import Path

import pytest

from control.events import EventLog, EventLogIntegrityError, EventValidationError, make_event, validate_event


def event(log: EventLog, event_id: str, value: str):
    return log.new_event(
        event_id=event_id,
        event_type="state.set",
        timestamp="2026-09-19T18:00:00Z",
        project_id="itdd-test",
        actor_type="human",
        actor_id="test-operator",
        payload={"key": "status", "value": value},
    )


def test_event_is_machine_readable_deterministic_and_chainable(tmp_path: Path):
    log = EventLog(tmp_path)
    first = event(log, "evt-001", "ready")
    log.append(first)
    second = event(log, "evt-002", "verified")
    log.append(second)
    records = log.verify()
    assert [record["event_id"] for record in records] == ["evt-001", "evt-002"]
    assert second["previous_event_id"] == first["event_id"]
    assert second["previous_event_hash"] == first["event_hash"]
    assert json.loads(log.events_path.read_text().splitlines()[0]) == first
    assert log.events_path.read_text().count("\n") == 2


def test_schema_rejects_missing_and_unknown_fields():
    with pytest.raises(EventValidationError):
        validate_event({})
    valid = make_event(
        event_id="evt-001",
        event_type="state.set",
        timestamp="2026-09-19T18:00:00Z",
        project_id="itdd-test",
        actor_type="human",
        actor_id="test-operator",
        previous_event_id=None,
        previous_event_hash=None,
        payload={"key": "x", "value": 1},
    )
    valid["unexpected"] = True
    with pytest.raises(EventValidationError):
        validate_event(valid)


def test_broken_chain_is_rejected(tmp_path: Path):
    log = EventLog(tmp_path)
    log.append(event(log, "evt-001", "ready"))
    second = event(log, "evt-002", "verified")
    second["previous_event_id"] = "wrong"
    with pytest.raises(EventLogIntegrityError):
        log.append(second)

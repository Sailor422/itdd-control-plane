from pathlib import Path

import pytest

from control.events import EventLog, EventLogIntegrityError


def append_two(log: EventLog):
    first = log.new_event(
        event_id="evt-001", event_type="state.set", timestamp="2026-09-19T18:00:00Z",
        project_id="p", actor_type="human", actor_id="h", payload={"key": "a", "value": 1}
    )
    log.append(first)
    second = log.new_event(
        event_id="evt-002", event_type="state.set", timestamp="2026-09-19T18:01:00Z",
        project_id="p", actor_type="human", actor_id="h", payload={"key": "b", "value": 2}
    )
    log.append(second)


def test_prior_event_modification_is_detected(tmp_path: Path):
    log = EventLog(tmp_path)
    append_two(log)
    text = log.events_path.read_text().replace('"value":1', '"value":99', 1)
    log.events_path.write_text(text)
    with pytest.raises(EventLogIntegrityError):
        log.verify()


def test_tail_deletion_is_detected_by_head_commitment(tmp_path: Path):
    log = EventLog(tmp_path)
    append_two(log)
    lines = log.events_path.read_text().splitlines()
    log.events_path.write_text(lines[0] + "\n")
    with pytest.raises(EventLogIntegrityError):
        log.verify()


def test_reordering_is_detected(tmp_path: Path):
    log = EventLog(tmp_path)
    append_two(log)
    lines = log.events_path.read_text().splitlines()
    log.events_path.write_text("\n".join(reversed(lines)) + "\n")
    with pytest.raises(EventLogIntegrityError):
        log.verify()


def test_malformed_injection_is_detected(tmp_path: Path):
    log = EventLog(tmp_path)
    append_two(log)
    with log.events_path.open("a") as stream:
        stream.write("not-json\n")
    with pytest.raises(EventLogIntegrityError):
        log.verify()


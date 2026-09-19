import json
import subprocess
import sys
from pathlib import Path

from control.events import EventLog, reconstruct_state


def test_restart_reconstructs_same_state(tmp_path: Path):
    log = EventLog(tmp_path)
    for event_id, key, value in (("evt-001", "phase", "ready"), ("evt-002", "count", 2)):
        log.append(log.new_event(
            event_id=event_id,
            event_type="state.set",
            timestamp="2026-09-19T18:00:00Z",
            project_id="restart-test",
            actor_type="human",
            actor_id="test-operator",
            payload={"key": key, "value": value},
        ))
    expected = reconstruct_state(log.verify())
    script = """
import json, sys
from control.events import EventLog, reconstruct_state
log = EventLog(sys.argv[1])
print(json.dumps(reconstruct_state(log.verify()), sort_keys=True))
"""
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == expected


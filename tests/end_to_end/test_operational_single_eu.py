import subprocess
from pathlib import Path

from control.human import HumanGateController
from control.models.store import StageCStore
from control.operational import OperationalController


class Builder:
    def run(self, *, project_root, worktree, execution_id, context_packet, capability):
        (worktree / "src").mkdir(exist_ok=True)
        (worktree / "src" / "feature.py").write_text("VALUE = 42\n")
        return {"runtime_provenance": {"runtime":"test-builder", "execution_id":execution_id,
                                        "context_packet_id":context_packet["context_packet_id"],
                                        "capability_id":capability["capability_id"]}}


def init_project(root: Path):
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests/test_feature.py").write_text("from src.feature import VALUE\n\ndef test_value():\n    assert VALUE == 42\n")
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=ITDD", "-c", "user.email=itdd@example.invalid", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=ITDD", "-c", "user.email=itdd@example.invalid", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
    timestamp = "2026-09-20T05:00:00Z"
    store = StageCStore(root)
    store.create_intent_draft({"intent_id":"I-001","version":1,"status":"DRAFT","created_at":timestamp,"created_by":"human","project_id":"demo","title":"feature","purpose":"controlled feature","requirements":[{"requirement_id":"REQ-001","text":"A feature value is exposed."}],"constraints":[],"acceptance_summary":"value is 42","source_event_id":"intent-created","schema_version":1}, event_id="intent-created", timestamp=timestamp, actor_type="human", actor_id="human")
    store.approve_intent("I-001", 1, event_id="intent-approved", timestamp=timestamp, actor_type="human", actor_id="human")
    return timestamp


def test_controller_runs_single_eu_to_verified_without_routine_human_gate(tmp_path):
    timestamp = init_project(tmp_path)
    controller = OperationalController(tmp_path)
    graph = {"graph_id":"G-001","version":1,"project_id":"demo","intent_id":"I-001","intent_version":1,"status":"ACTIVE","created_at":timestamp,"created_by":"planner","nodes":[{"eu_id":"EU-001","requirement_ids":["REQ-001"]}],"edges":[],"reason":"one vertical EU","source_event_id":"graph-created","schema_version":1}
    controller.propose_plan(operation_id="OP-001", project_id="demo", graph=graph, eu_paths={"EU-001":["src/feature.py"]}, timestamp=timestamp, event_prefix="op")
    result = controller.run_eu("OP-001", eu_id="EU-001", builder=Builder(), spec_command="python3 -m pytest -q tests/test_feature.py", standards_command="python3 -m pytest -q tests/test_feature.py", timestamp=timestamp, event_prefix="op")
    assert result["status"] == "VERIFIED"
    assert result["gate_id"] is None
    assert not any(event["event_type"] == "human.gate.created" for event in controller.operations.events.verify())

from pathlib import Path

from control.events import EventLog
from control.operational import OperationalController
from control.view import open_visualization
from tests.end_to_end.test_operational_single_eu import init_project


def _graph(timestamp):
    return {"graph_id":"G-001","version":1,"project_id":"demo","intent_id":"I-001","intent_version":1,"status":"ACTIVE","created_at":timestamp,"created_by":"planner","nodes":[{"eu_id":"EU-001","requirement_ids":["REQ-001"]}],"edges":[],"reason":"one vertical EU","source_event_id":"graph-created","schema_version":1}


def test_graph_evaluator_activates_valid_plan_without_human_graph_gate(tmp_path: Path):
    timestamp = init_project(tmp_path)
    controller = OperationalController(tmp_path)
    item = controller.propose_plan(operation_id="OP-001", project_id="demo", graph=_graph(timestamp),
                                   eu_paths={"EU-001":["src/feature.py"]}, timestamp=timestamp,
                                   event_prefix="op")

    assert item["status"] == "ACTIVE"
    assert item["graph_evaluator_result"] == "PASS"
    assert item["graph_evaluator_execution_id"] != item["planner_execution_id"]
    events = EventLog(tmp_path).verify()
    assert not any(event["event_type"] == "human.gate.created" for event in events)
    assert not any(event["event_type"] == "plan.approved" for event in events)
    assert any(event["event_type"] == "graph.evaluated" for event in events)


def test_viewing_active_graph_is_observational(tmp_path: Path):
    timestamp = init_project(tmp_path)
    controller = OperationalController(tmp_path)
    controller.propose_plan(operation_id="OP-001", project_id="demo", graph=_graph(timestamp),
                            eu_paths={"EU-001":["src/feature.py"]}, timestamp=timestamp,
                            event_prefix="op")
    before = (tmp_path / ".idd/state/events.jsonl").read_bytes()
    open_visualization(tmp_path, launch=False)
    assert (tmp_path / ".idd/state/events.jsonl").read_bytes() == before
    assert controller.operations.read("OP-001")["status"] == "ACTIVE"

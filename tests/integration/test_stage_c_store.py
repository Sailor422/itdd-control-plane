from pathlib import Path

from control.models.store import StageCStore


def draft(event_id="evt-intent-created"):
    return {
        "intent_id": "I-001", "version": 1, "status": "DRAFT",
        "created_at": "2026-09-19T18:00:00Z", "created_by": "operator", "project_id": "stage-c-test",
        "title": "Test destination", "purpose": "Prove durable intent authority.",
        "requirements": [{"requirement_id": f"REQ-00{i}", "text": f"Requirement {i}"} for i in range(1, 4)],
        "constraints": ["No hidden global state."], "acceptance_summary": "Intent and graph remain distinct.",
        "source_event_id": event_id, "schema_version": 1,
    }


def graph(version=1, source_event="evt-graph-created", edges=None):
    result = {
        "graph_id": "G-001", "version": version, "project_id": "stage-c-test", "intent_id": "I-001", "intent_version": 1,
        "status": "ACTIVE", "created_at": f"2026-09-19T18:{version * 2:02d}:00Z", "created_by": "planner",
        "nodes": [{"eu_id": f"EU-00{i}", "requirement_ids": [f"REQ-00{i}"]} for i in range(1, 4)],
        "edges": edges if edges is not None else [{"from": "EU-001", "to": "EU-003"}],
        "reason": "Initial graph" if version == 1 else "Replan after discovery",
        "source_event_id": source_event, "schema_version": 1,
    }
    if version > 1:
        result["previous_version"] = version - 1
    return result


def approve(store: StageCStore):
    store.create_intent_draft(draft(), event_id="evt-intent-created", timestamp="2026-09-19T18:00:00Z", actor_type="agent", actor_id="operator")
    store.approve_intent("I-001", 1, event_id="evt-intent-approved", timestamp="2026-09-19T18:01:00Z", actor_type="human", actor_id="operator")


def test_intent_graph_revision_preserves_approved_destination(tmp_path: Path):
    store = StageCStore(tmp_path)
    approve(store)
    store.create_graph(graph(), event_id="evt-graph-created", timestamp="2026-09-19T18:02:00Z", actor_type="agent", actor_id="planner")
    original_intent = store.read_intent("I-001", 1)
    original_graph = store.read_graph("G-001", 1)
    revised = graph(2, "evt-graph-revised", [{"from": "EU-001", "to": "EU-002"}])
    store.revise_graph(revised, event_id="evt-graph-revised", timestamp="2026-09-19T18:04:00Z", actor_type="agent", actor_id="planner")
    state = store.reconstruct()
    assert store.read_intent("I-001", 1) == original_intent
    assert store.read_graph("G-001", 1) == original_graph
    assert state["active_graph"]["version"] == 2
    assert state["graphs"][("G-001", 1)] == original_graph
    assert state["graphs"][("G-001", 2)] == revised
    store.verify_materialized_artifacts()

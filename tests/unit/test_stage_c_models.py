import json
from pathlib import Path

import pytest

from control.models.graph import GraphValidationError, validate_graph
from control.models.intent import IntentValidationError, validate_intent


def intent() -> dict:
    return {
        "intent_id": "I-001", "version": 1, "status": "DRAFT",
        "created_at": "2026-09-19T18:00:00Z", "created_by": "operator",
        "project_id": "stage-c-test", "title": "Test destination",
        "purpose": "Prove durable intent authority.",
        "requirements": [
            {"requirement_id": "REQ-001", "text": "Keep the destination durable."},
            {"requirement_id": "REQ-002", "text": "Allow the plan to evolve."},
            {"requirement_id": "REQ-003", "text": "Record independent proof."},
        ],
        "constraints": ["No hidden global state."],
        "acceptance_summary": "Intent and graph remain distinct.",
        "source_event_id": "evt-intent-created", "schema_version": 1,
    }


def approved_intent() -> dict:
    result = intent()
    result.update({"status": "APPROVED", "approved_by": "operator", "approved_at": "2026-09-19T18:01:00Z", "approval_event_id": "evt-intent-approved"})
    return result


def graph() -> dict:
    return {
        "graph_id": "G-001", "version": 1, "project_id": "stage-c-test",
        "intent_id": "I-001", "intent_version": 1, "status": "ACTIVE",
        "created_at": "2026-09-19T18:02:00Z", "created_by": "planner",
        "nodes": [
            {"eu_id": "EU-001", "requirement_ids": ["REQ-001"]},
            {"eu_id": "EU-002", "requirement_ids": ["REQ-002"]},
            {"eu_id": "EU-003", "requirement_ids": ["REQ-003"]},
        ], "edges": [{"from": "EU-001", "to": "EU-003"}],
        "reason": "Initial graph", "source_event_id": "evt-graph-created", "schema_version": 1,
    }


def test_schemas_are_valid_json():
    for name in ("intent.schema.json", "graph.schema.json"):
        json.loads(Path("schemas", name).read_text())


def test_intent_requires_stable_requirement_ids():
    model = intent()
    model["requirements"][1]["requirement_id"] = "the second bullet"
    with pytest.raises(IntentValidationError):
        validate_intent(model)


def test_graph_validates_against_exact_intent_binding():
    validate_intent(approved_intent())
    validate_graph(graph(), approved_intent())
    wrong = graph()
    wrong["intent_version"] = 2
    with pytest.raises(GraphValidationError):
        validate_graph(wrong, approved_intent())


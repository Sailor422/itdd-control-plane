from pathlib import Path

import pytest

from control.models.graph import GraphValidationError, validate_graph
from control.models.store import AgentApprovalError, ArtifactMutationError, ImmutableIntentError, StageCStore
from tests.integration.test_stage_c_store import approve, draft, graph


def test_agent_cannot_approve_intent(tmp_path: Path):
    store = StageCStore(tmp_path)
    store.create_intent_draft(draft(), event_id="evt-intent-created", timestamp="2026-09-19T18:00:00Z", actor_type="agent", actor_id="operator")
    with pytest.raises(AgentApprovalError):
        store.approve_intent("I-001", 1, event_id="evt-agent-approval", timestamp="2026-09-19T18:01:00Z", actor_type="agent", actor_id="planner")
    assert store.read_intent("I-001", 1)["status"] == "DRAFT"


def test_approved_intent_mutation_is_rejected(tmp_path: Path):
    store = StageCStore(tmp_path)
    approve(store)
    changed = store.read_intent("I-001", 1)
    changed["purpose"] = "Silent replacement"
    with pytest.raises(ImmutableIntentError):
        store.update_draft(changed, event_id="evt-illegal", timestamp="2026-09-19T18:05:00Z", actor_type="agent", actor_id="builder")


@pytest.mark.parametrize("mutator", [
    lambda g: g["nodes"].append({"eu_id": "EU-004", "requirement_ids": ["REQ-999"]}),
    lambda g: g["nodes"].append({"eu_id": "EU-001", "requirement_ids": ["REQ-001"]}),
    lambda g: g["edges"].append({"from": "EU-999", "to": "EU-001"}),
    lambda g: g["edges"].append({"from": "EU-001", "to": "EU-001"}),
    lambda g: g["edges"].extend([{"from": "EU-001", "to": "EU-002"}, {"from": "EU-002", "to": "EU-001"}]),
])
def test_invalid_graphs_are_rejected(mutator, tmp_path: Path):
    store = StageCStore(tmp_path)
    approve(store)
    candidate = graph()
    mutator(candidate)
    with pytest.raises(GraphValidationError):
        validate_graph(candidate, store.read_intent("I-001", 1))


def test_graph_revision_cannot_change_intent_binding(tmp_path: Path):
    store = StageCStore(tmp_path)
    approve(store)
    store.create_graph(graph(), event_id="evt-graph-created", timestamp="2026-09-19T18:02:00Z", actor_type="agent", actor_id="planner")
    candidate = graph(2, "evt-graph-revised")
    candidate["intent_version"] = 2
    with pytest.raises(GraphValidationError):
        store.revise_graph(candidate, event_id="evt-graph-revised", timestamp="2026-09-19T18:04:00Z", actor_type="agent", actor_id="planner")


def test_graph_history_cannot_be_overwritten(tmp_path: Path):
    store = StageCStore(tmp_path)
    approve(store)
    store.create_graph(graph(), event_id="evt-graph-created", timestamp="2026-09-19T18:02:00Z", actor_type="agent", actor_id="planner")
    altered = graph()
    altered["reason"] = "overwrite"
    altered["source_event_id"] = "evt-graph-created-2"
    with pytest.raises(ArtifactMutationError):
        store.create_graph(altered, event_id="evt-graph-created-2", timestamp="2026-09-19T18:02:00Z", actor_type="agent", actor_id="planner")

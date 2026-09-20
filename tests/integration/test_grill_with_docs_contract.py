import hashlib
from pathlib import Path

from control.authorization.capabilities import CapabilityIssuer
from control.events.format import canonical_json
from control.skills import ClarificationProposalStore, create_clarification_proposal


def _capability(root: Path) -> dict:
    return CapabilityIssuer(root).issue(
        {
            "capability_id": "CAP-001",
            "schema_version": 1,
            "project_id": "project-1",
            "role": "CONVERSATIONAL",
            "execution_id": "EXEC-1",
            "issued_at": "2026-09-20T10:00:00Z",
            "baseline_sha": "a" * 40,
            "allowed_reads": ["CONTEXT.md"],
            "allowed_writes": [".idd/skills"],
            "allowed_executes": [],
            "allowed_operations": ["REQUEST_CLARIFICATION", "CREATE_ARTIFACT"],
            "forbidden_operations": ["INTENT_APPROVAL", "STATE_TRANSITION"],
            "allowed_request_types": ["clarification"],
            "scope_bindings": {"intent_id": "I-001", "intent_version": 1},
            "version": 1,
        },
        event_id="evt-cap-001",
        timestamp="2026-09-20T10:00:00Z",
    )


def test_human_invocation_creates_provenance_bound_clarification_proposal(tmp_path: Path):
    capability = _capability(tmp_path)
    request = {
        "project_id": "project-1",
        "execution_id": "EXEC-1",
        "intent_id": "I-001",
        "intent_version": 1,
        "baseline_sha": "a" * 40,
        "source_inputs": ["CONTEXT.md"],
        "terms": [{"term": "candidate", "meaning": "a frozen controller-owned commit"}],
        "assumptions": ["the approved intent remains unchanged"],
        "open_questions": ["which EU is next"],
    }

    proposal = create_clarification_proposal(
        tmp_path,
        request=request,
        capability=capability,
        actor_type="human",
        actor_id="operator-1",
        timestamp="2026-09-20T10:01:00Z",
        event_id="evt-proposal-001",
    )

    assert proposal["version"] == 1
    assert proposal["proposal_type"] == "grill-with-docs.clarification"
    assert proposal["project_id"] == "project-1"
    assert proposal["execution_id"] == "EXEC-1"
    assert proposal["intent_id"] == "I-001"
    assert proposal["intent_version"] == 1
    assert proposal["baseline_sha"] == "a" * 40
    assert proposal["source_inputs"] == ["CONTEXT.md"]
    assert proposal["skill_source"] == "grill-with-docs"
    assert proposal["capability_id"] == "CAP-001"
    assert proposal["status"] == "PROPOSED"
    assert proposal["source_event_id"] == "evt-proposal-001"
    assert proposal["authority_effect"] == "NONE"
    assert proposal["terms"] == request["terms"]
    assert proposal["assumptions"] == request["assumptions"]
    assert proposal["open_questions"] == request["open_questions"]
    assert ClarificationProposalStore(tmp_path).read(proposal["proposal_id"], 1) == proposal

    events = ClarificationProposalStore(tmp_path).event_log.verify()
    assert events[-1]["event_type"] == "skill.clarification.proposed"
    assert events[-1]["payload"]["proposal"] == proposal


def test_proposal_identity_is_deterministic_for_same_inputs(tmp_path: Path):
    capability = _capability(tmp_path)
    request = {
        "project_id": "project-1", "execution_id": "EXEC-1", "intent_id": "I-001",
        "intent_version": 1, "baseline_sha": "a" * 40, "source_inputs": ["CONTEXT.md"],
        "terms": [], "assumptions": [], "open_questions": [],
    }
    first = create_clarification_proposal(tmp_path, request=request, capability=capability,
        actor_type="human", actor_id="operator-1", timestamp="2026-09-20T10:01:00Z", event_id="evt-proposal-001")
    assert first["proposal_id"] == "CLAR-" + hashlib.sha256(canonical_json({
        "project_id": "project-1", "execution_id": "EXEC-1", "intent_id": "I-001",
        "intent_version": 1, "baseline_sha": "a" * 40, "source_inputs": ["CONTEXT.md"],
        "skill_source": "grill-with-docs", "capability_id": "CAP-001", "version": 1,
    }).encode()).hexdigest()[:20]

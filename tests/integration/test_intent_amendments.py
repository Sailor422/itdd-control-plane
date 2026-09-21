from pathlib import Path

import pytest

import control.human_decisions as decisions
from control.human_decisions import HumanDecisionController
from control.human_decisions import HumanDecisionError
from control.human import HumanGateStore
from control.intent_amendments import IntentAmendmentController, IntentAmendmentStore
from control.models.store import StageCStore


def amendment_document_fixture():
    source = {
        "intent_id": "I-999", "version": 1, "project_id": "amendment-proof",
        "purpose": "same destination", "title": "proof", "requirements": [],
        "constraints": [], "acceptance_summary": "same acceptance",
    }
    amendment = {
        "amendment_id": "IA-999", "amendment_version": 1, "status": "PENDING",
        "project_id": "amendment-proof",
        "authority_change": {
            "removed_language": ["old authority"],
            "replacement_language": "new authority",
            "human_authority_after_approval": ["new authority question"],
        },
        "preserved_scope": {
            "completed_eu_work": ["EU-001"],
            "graph_history": [],
            "verified_integration": {
                "candidate_sha": "a" * 40,
                "tree": "b" * 40,
                "verifier_result": "VR-999",
            },
        },
    }
    return source, amendment


def test_amendment_uses_the_canonical_human_decision_presenter(tmp_path: Path, monkeypatch):
    source, amendment = amendment_document_fixture()
    calls = []

    def present(path):
        calls.append(path)
        return "VS Code"

    monkeypatch.setattr(decisions, "open_decision_document", present)
    path = HumanDecisionController(tmp_path).create_amendment(
        decision_id="HD-999", amendment=amendment, source_intent=source,
        timestamp="2026-09-20T00:00:00Z", open_document=True,
    )
    assert calls == [path]
    assert path.exists()


def test_amendment_presentation_failure_is_fail_closed_with_exact_path(tmp_path: Path, monkeypatch):
    source, amendment = amendment_document_fixture()
    monkeypatch.setattr(decisions, "open_decision_document", lambda path: None)
    with pytest.raises(HumanDecisionError, match=r"VS CODE PRESENTATION FAILED: .*/HD-999\.md"):
        HumanDecisionController(tmp_path).create_amendment(
            decision_id="HD-999", amendment=amendment, source_intent=source,
            timestamp="2026-09-20T00:00:00Z", open_document=True,
        )


def test_amendment_module_has_no_viewer_or_launcher_path():
    source = Path("control/intent_amendments.py").read_text(encoding="utf-8")
    assert "open_decision_document" not in source
    assert "subprocess" not in source
    assert "shutil.which" not in source


def test_authority_amendment_is_separate_and_preserves_approved_intent(tmp_path: Path):
    intent = {
        "intent_id": "I-901", "version": 1, "status": "DRAFT",
        "created_at": "2026-09-20T00:00:00Z", "created_by": "human",
        "project_id": "amendment-proof", "title": "proof", "purpose": "same destination",
        "requirements": [{"requirement_id": "REQ-901", "text": "preserve scope"}],
        "constraints": ["same constraints"], "acceptance_summary": "same acceptance",
        "source_event_id": "intent-901", "schema_version": 1,
    }
    StageCStore(tmp_path).create_intent_draft(intent, event_id="intent-901", timestamp=intent["created_at"], actor_type="controller", actor_id="human")
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    path.write_text(path.read_text().replace("Decision: PENDING", "Decision: APPROVE"))
    HumanDecisionController(tmp_path).resolve("HD-001", timestamp="2026-09-20T00:00:01Z")
    before = StageCStore(tmp_path).read_intent("I-901", 1)
    amendment_path, decision_path = IntentAmendmentController(tmp_path).create_authority_amendment(
        amendment_id="IA-901", source_intent_id="I-901", source_intent_version=1,
        timestamp="2026-09-20T00:00:02Z", decision_id="HD-002",
    )
    assert amendment_path == tmp_path / ".idd/intent_amendments/IA-901/v1.json"
    assert decision_path == tmp_path / ".idd/human_decisions/pending/HD-002.md"
    assert StageCStore(tmp_path).read_intent("I-901", 1) == before
    assert "HUMAN DEVELOPS INTENT" in decision_path.read_text()
    assert "HD-007" in decision_path.read_text()
    assert "IN-1001" in decision_path.read_text()


def test_approved_amendment_does_not_consume_gate_or_promote(tmp_path: Path):
    # Exercise the amendment transition with a minimal approved intent.
    intent = {
        "intent_id": "I-902", "version": 1, "status": "DRAFT", "created_at": "2026-09-20T00:00:00Z", "created_by": "human",
        "project_id": "amendment-proof", "title": "proof", "purpose": "same", "requirements": [{"requirement_id": "REQ-902", "text": "scope"}], "constraints": [], "acceptance_summary": "done", "source_event_id": "intent-902", "schema_version": 1,
    }
    StageCStore(tmp_path).create_intent_draft(intent, event_id="intent-902", timestamp=intent["created_at"], actor_type="controller", actor_id="human")
    p = tmp_path / ".idd/human_decisions/pending/HD-001.md"; p.write_text(p.read_text().replace("Decision: PENDING", "Decision: APPROVE")); HumanDecisionController(tmp_path).resolve("HD-001", timestamp="2026-09-20T00:00:01Z")
    IntentAmendmentController(tmp_path).create_authority_amendment(amendment_id="IA-902", source_intent_id="I-902", source_intent_version=1, timestamp="2026-09-20T00:00:02Z", decision_id="HD-002")
    p = tmp_path / ".idd/human_decisions/pending/HD-002.md"; p.write_text(p.read_text().replace("Decision: PENDING", "Decision: APPROVE"))
    HumanDecisionController(tmp_path).resolve("HD-002", timestamp="2026-09-20T00:00:03Z")
    assert IntentAmendmentStore(tmp_path).read("IA-902", 1)["status"] == "APPROVED"
    assert StageCStore(tmp_path).read_intent("I-902", 1)["status"] == "APPROVED"


def test_approved_amendment_reconciles_only_obsolete_waiting_gates(tmp_path: Path):
    project = "reconciliation-proof"
    amendment = {
        "amendment_id": "IA-903", "schema_version": 1, "status": "APPROVED",
        "project_id": project, "source_intent": {"intent_id": "I-903", "version": 1},
        "amendment_version": 1, "created_at": "2026-09-20T00:00:00Z", "created_by": "controller",
        "authority_change": {
            "removed_language": ["HUMAN_ONLY integration approval is required before promoting the integrated result."],
            "replacement_language": "controller continuation",
            "human_authority_after_approval": ["new authority question"],
        },
        "preserved_scope": {"historical_records": ["HG-903", "HD-903"]},
        "source_event_id": "amendment-IA-903-created",
    }
    amendment_path = IntentAmendmentStore(tmp_path).create(amendment)
    gates = HumanGateStore(tmp_path)
    common = {
        "schema_version": 1, "project_id": project, "subject_type": "INTEGRATION",
        "subject_id": "IN-903", "required_state": "INTEGRATION_VERIFIED",
        "created_at": "2026-09-20T00:00:01Z", "status": "WAITING", "decision_event_id": None,
        "related_intent": {"intent_id": "I-903", "version": 1}, "related_graph": {"graph_id": "G-903", "version": 1},
        "related_eu": {"eu_id": "IN-903"}, "related_candidate": {"candidate_sha": "a" * 40, "baseline_sha": "b" * 40},
        "evidence": {"integration_execution_id": "EXEC-903", "integration_result_id": "VR-903"},
        "approval_capability_id": "CAP-903",
    }
    obsolete = {"gate_id": "HG-903", "gate_type": "INTEGRATION_APPROVAL", **common}
    unrelated = {**common, "gate_id": "HG-904", "gate_type": "INTEGRATION_APPROVAL", "related_intent": {"intent_id": "I-OTHER", "version": 1}}
    gates.create(obsolete, event_id="gate-903-created", timestamp=common["created_at"])
    gates.create(unrelated, event_id="gate-904-created", timestamp=common["created_at"])
    decision_path = HumanDecisionController(tmp_path).create_gate(decision_id="HD-903", gate_id="HG-903", timestamp="2026-09-20T00:00:02Z")
    original_decision = decision_path.read_bytes()

    retired = IntentAmendmentController(tmp_path).reconcile_obsolete_gates(amendment, timestamp="2026-09-20T00:00:03Z")
    assert [gate["gate_id"] for gate in retired] == ["HG-903"]
    current = gates.reconstruct()
    assert current["HG-903"]["status"] == "SUPERSEDED"
    assert current["HG-903"]["superseded_by"] == {"amendment_id": "IA-903", "amendment_version": 1}
    assert current["HG-904"]["status"] == "WAITING"
    assert decision_path.read_bytes() == original_decision
    assert not (tmp_path / ".idd/human_decisions/resolved/HD-903.md").exists()
    assert "intent-amendment-IA-903-gate-HG-903-superseded" in [event["event_id"] for event in gates.events.verify()]
    assert amendment_path.exists()

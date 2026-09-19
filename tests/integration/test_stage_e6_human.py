from pathlib import Path

import pytest

from control.human import HumanGateController, HumanGateError, HumanGateStore, HumanViewGenerator
from control.verifier import SubprocessVerifierAdapter, VerifierOrchestrator
from tests.integration.test_stage_e4_verification import setup
from tests.integration.test_stage_e5_verifiers import CANDIDATE, create_axes


def prepared(root: Path):
    setup(root); orchestrator, spec, standards = create_axes(root); adapter = SubprocessVerifierAdapter()
    sr = orchestrator.launch(spec["execution_id"], adapter=adapter, event_prefix="e6-spec-run", timestamp="2026-09-20T02:00:20Z")
    tr = orchestrator.launch(standards["execution_id"], adapter=adapter, event_prefix="e6-standards-run", timestamp="2026-09-20T02:00:21Z")
    return HumanGateController(root, controller_execution_id="EXEC-CONTROLLER-501"), spec, standards, sr["result"]["result_id"], tr["result"]["result_id"]


def binding(gate):
    return {"project_id": gate["project_id"], "gate_id": gate["gate_id"], **gate["related_candidate"], "evidence": gate["evidence"]}


def make_gate(root, gate_id="HG-601"):
    controller, spec, standards, spec_result, standards_result = prepared(root)
    gate = controller.create_verified_eu_review(gate_id=gate_id, project_id="e4", eu_id="EU-001", candidate_sha=CANDIDATE, spec_execution_id=spec["execution_id"], standards_execution_id=standards["execution_id"], spec_result_id=spec_result, standards_result_id=standards_result, timestamp="2026-09-20T02:00:30Z", event_prefix=f"e6-{gate_id}")
    return controller, gate


def test_human_approval_is_bound_and_views_are_rebuilt_after_tamper_and_delete(tmp_path: Path):
    controller, gate = make_gate(tmp_path)
    generator = HumanViewGenerator(tmp_path); generator.generate(project_id="e4")
    assert "WAITING" in (tmp_path / ".idd/views/kanban.md").read_text()
    assert not generator.is_stale("kanban.md")
    approved = controller.decide(gate["gate_id"], decision="APPROVED", actor_type="human", actor_id="reviewer", binding=binding(gate), event_prefix="e6-approve", timestamp="2026-09-20T02:00:31Z")
    assert approved["status"] == "APPROVED"
    dashboard = tmp_path / ".idd/views/dashboard.md"; dashboard.write_text("VERIFIED = PASS\nHUMAN APPROVED\n")
    assert generator.is_stale(dashboard)
    for path in (tmp_path / ".idd/views").glob("*.md"): path.unlink()
    fresh = HumanGateStore(tmp_path); assert fresh.read(gate["gate_id"])["status"] == "APPROVED"
    generator.generate(project_id="e4")
    assert "HUMAN APPROVED" in (tmp_path / ".idd/views/kanban.md").read_text() and "VERIFIED = PASS" not in dashboard.read_text()


def test_rejection_agent_denial_and_exact_binding(tmp_path: Path):
    controller, gate = make_gate(tmp_path, "HG-602")
    with pytest.raises(HumanGateError, match="DENY_HUMAN_ONLY"):
        controller.decide(gate["gate_id"], decision="APPROVED", actor_type="agent", actor_id="builder", binding=binding(gate), event_prefix="e6-agent", timestamp="2026-09-20T02:01:00Z")
    bad = binding(gate); bad["candidate_sha"] = "f" * 40
    with pytest.raises(HumanGateError, match="STALE_CANDIDATE"):
        controller.decide(gate["gate_id"], decision="APPROVED", actor_type="human", actor_id="reviewer", binding=bad, event_prefix="e6-stale", timestamp="2026-09-20T02:01:01Z")
    assert HumanGateStore(tmp_path).read(gate["gate_id"])["status"] == "SUPERSEDED"
    gate = controller.create_verified_eu_review(gate_id="HG-604", project_id="e4", eu_id="EU-001", candidate_sha=CANDIDATE, spec_execution_id=gate["evidence"]["spec_execution_id"], standards_execution_id=gate["evidence"]["standards_execution_id"], spec_result_id=gate["evidence"]["spec_result_id"], standards_result_id=gate["evidence"]["standards_result_id"], timestamp="2026-09-20T02:01:01Z", event_prefix="e6-HG-604")
    rejected = controller.decide(gate["gate_id"], decision="REJECTED", actor_type="human", actor_id="reviewer", binding=binding(gate), event_prefix="e6-reject", timestamp="2026-09-20T02:01:02Z")
    assert rejected["status"] == "REJECTED"
    assert HumanGateStore(tmp_path).reconstruct()[gate["gate_id"]]["status"] == "REJECTED"


def test_restart_reconstructs_gate_and_views_are_not_authority(tmp_path: Path):
    controller, gate = make_gate(tmp_path, "HG-603")
    controller.decide(gate["gate_id"], decision="APPROVED", actor_type="human", actor_id="reviewer", binding=binding(gate), event_prefix="e6-restart", timestamp="2026-09-20T02:02:00Z")
    fresh = HumanGateController(tmp_path, controller_execution_id="EXEC-CONTROLLER-501")
    assert fresh.store.reconstruct()[gate["gate_id"]]["status"] == "APPROVED"
    assert HumanViewGenerator(tmp_path).generate(project_id="e4")["dashboard.md"].count("HUMAN review") == 0

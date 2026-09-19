from pathlib import Path

import pytest

from control.console import ConsoleError, HumanConsole, discover_project
from control.human import HumanGateController, HumanGateStore
from tests.integration.test_stage_e4_verification import setup


def test_project_discovery_and_no_project_rejection(tmp_path: Path):
    setup(tmp_path)
    assert discover_project(tmp_path / "src") == tmp_path
    empty = tmp_path.parent / f"{tmp_path.name}-empty"
    empty.mkdir()
    with pytest.raises(ConsoleError, match="No ITDD project"):
        discover_project(empty)


def test_graph_review_gate_blocks_eu_until_human_approval(tmp_path: Path):
    setup(tmp_path); console = HumanConsole(tmp_path)
    state = console.state(); assert state["actions"][0]["action"] == "REVIEW_GRAPH"
    with pytest.raises(ConsoleError, match="graph approval"):
        console.assert_eu_eligible("EU-001")
    answers = iter(["no"]); console = HumanConsole(tmp_path, input_fn=lambda _: next(answers), output_fn=lambda _: None); console.review_graph()
    gates = HumanGateStore(tmp_path).reconstruct(); graph_gate = next(g for g in gates.values() if g["gate_type"] == "GRAPH_APPROVAL")
    with pytest.raises(Exception, match="DENY_HUMAN_ONLY"):
        console.controller.decide(graph_gate["gate_id"], decision="APPROVED", actor_type="agent", actor_id="builder", binding={"project_id":"e4","gate_id":graph_gate["gate_id"],**graph_gate["related_candidate"],"evidence":graph_gate["evidence"]}, event_prefix="e8-agent", timestamp="2026-09-20T05:00:00Z")
    approvals = iter(["APPROVE", "APPROVE"]); console = HumanConsole(tmp_path, input_fn=lambda _: next(approvals), output_fn=lambda _: None); console.review_graph()
    assert console.state()["graph_approved"] is True
    console.assert_eu_eligible("EU-001")


def test_console_status_is_projection_and_restartable(tmp_path: Path):
    setup(tmp_path); first = HumanConsole(tmp_path); before = first.status_json(); first.render(); restarted = HumanConsole(tmp_path)
    assert restarted.status_json() == before
    assert "PROMOTION" in "\n".join(restarted.render()) and "NOT IMPLEMENTED" in "\n".join(restarted.render())


def test_console_cannot_approve_with_navigation_or_unconfirmed_input(tmp_path: Path):
    setup(tmp_path); console = HumanConsole(tmp_path, input_fn=lambda _: "", output_fn=lambda _: None); console.review_graph()
    gate = next(g for g in HumanGateStore(tmp_path).reconstruct().values() if g["gate_type"] == "GRAPH_APPROVAL")
    assert HumanGateStore(tmp_path).read(gate["gate_id"])["status"] == "WAITING"

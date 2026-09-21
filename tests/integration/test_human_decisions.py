import json
import re
import subprocess
from pathlib import Path

import pytest

import control.human_decisions as decisions
from control.human_decisions import HumanDecisionController, HumanDecisionError
from control.human import HumanViewGenerator
from control.events import EventLog
from control.models.store import StageCStore


def draft(root: Path) -> None:
    intent = {
        "intent_id": "I-701", "version": 1, "status": "DRAFT",
        "created_at": "2026-09-20T00:00:00Z", "created_by": "operator",
        "project_id": "decision-docs", "title": "Decision document proof",
        "purpose": "prove saved human decisions", "requirements": [{"requirement_id": "REQ-701", "text": "A human can review this exact intent"}],
        "constraints": ["No promotion from intent approval"], "acceptance_summary": "bound approval",
        "source_event_id": "intent-701", "schema_version": 1,
    }
    StageCStore(root).create_intent_draft(intent, event_id="intent-701", timestamp=intent["created_at"], actor_type="controller", actor_id="operator")


def test_intent_decision_document_is_bound_and_resolves_saved_approval(tmp_path: Path):
    draft(tmp_path)
    controller = HumanDecisionController(tmp_path, controller_execution_id="EXEC-CONTROLLER-501")
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    text = path.read_text()
    assert "decision-docs" in text and "I-701 v1" in text and "REQ-701" in text
    assert "Decision: PENDING" in text
    path.write_text(text.replace("Decision: PENDING", "Decision: APPROVE").replace("Comment: \n", "Comment: exact intent approved\n"))
    result = controller.resolve("HD-001", timestamp="2026-09-20T00:00:02Z")
    assert result["decision"] == "APPROVE"
    assert StageCStore(tmp_path).read_intent("I-701", 1)["status"] == "APPROVED"
    assert not path.exists() and Path(result["path"]).exists()
    assert any(e["event_type"] == "intent.approved" for e in controller.events.verify())


def test_resolved_decision_document_remains_readable_after_controller_resolution(tmp_path: Path):
    draft(tmp_path)
    controller = HumanDecisionController(tmp_path, controller_execution_id="EXEC-CONTROLLER-501")
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    path.write_text(path.read_text().replace("Decision: PENDING", "Decision: APPROVE"))
    controller.resolve("HD-001", timestamp="2026-09-20T00:00:03Z")
    resolved = controller.store.read("HD-001")
    assert resolved["resolved"] is True
    assert resolved["resolved_decision"] == "APPROVE"
    assert resolved["nonce"] == json.loads(
        (tmp_path / ".idd/human_decisions/registry/HD-001.json").read_text()
    )["nonce"]


def test_pending_or_edited_metadata_cannot_be_resolved_and_old_response_is_not_reusable(tmp_path: Path):
    draft(tmp_path)
    controller = HumanDecisionController(tmp_path, controller_execution_id="EXEC-CONTROLLER-501")
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    with pytest.raises(HumanDecisionError, match="PENDING"):
        controller.resolve("HD-001", timestamp="2026-09-20T00:00:02Z")
    path.write_text(re.sub(r'"nonce":"[^"]+"', '"nonce":"forged"', path.read_text(), count=1).replace("Decision: PENDING", "Decision: APPROVE"))
    with pytest.raises(HumanDecisionError, match="registry"):
        controller.resolve("HD-001", timestamp="2026-09-20T00:00:02Z")


def test_changes_requested_is_authoritative_but_does_not_approve(tmp_path: Path):
    draft(tmp_path)
    controller = HumanDecisionController(tmp_path)
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    path.write_text(path.read_text().replace("Decision: PENDING", "Decision: CHANGES_REQUESTED").replace("Comment: \n", "Comment: clarify the acceptance boundary\n"))
    controller.resolve("HD-001", timestamp="2026-09-20T00:00:02Z")
    assert StageCStore(tmp_path).read_intent("I-701", 1)["status"] == "DRAFT"
    events = controller.events.verify()
    event = events[-1]
    assert event["event_type"] == "human.decision.changes_requested"
    assert event["payload"]["comment"] == "clarify the acceptance boundary"


def test_ordinary_markdown_does_not_have_response_semantics(tmp_path: Path):
    draft(tmp_path)
    views = tmp_path / ".idd/views"
    views.mkdir(parents=True, exist_ok=True)
    (views / "intent.md").write_text("# YOUR RESPONSE\n\nDecision: APPROVE\n")
    assert (tmp_path / ".idd/human_decisions/pending/HD-001.md").exists()
    assert HumanDecisionController(tmp_path).scan(timestamp="2026-09-20T00:00:02Z") == []


def test_viewer_reports_only_when_exact_decision_document_is_visible_in_vscode(tmp_path: Path, monkeypatch):
    target = tmp_path / "HD-901.md"
    target.write_text("decision")
    calls = []

    monkeypatch.setattr(decisions.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(decisions.time, "sleep", lambda _: None)

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "osascript":
            return subprocess.CompletedProcess(command, 0, "HD-901.md - project", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(decisions.subprocess, "run", fake_run)
    assert decisions.open_decision_document(target, viewer="vscode") == "VS Code"
    assert calls[0] == ["code", "--reuse-window", "--goto", str(target.resolve())]
    assert calls[1][0] == "osascript"


def test_viewer_failure_does_not_launch_another_application(tmp_path: Path, monkeypatch):
    target = tmp_path / "HD-902.md"
    target.write_text("decision")
    app_calls = []
    monkeypatch.setattr(decisions.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(decisions.time, "sleep", lambda _: None)

    def fake_run(command, **kwargs):
        app_calls.append(command)
        if command[0] == "osascript":
            return subprocess.CompletedProcess(command, 0, "other.md", "")
        return subprocess.CompletedProcess(command, 1, "", "viewer failed")

    monkeypatch.setattr(decisions.subprocess, "run", fake_run)
    assert decisions.open_decision_document(target, viewer="vscode") is None
    assert app_calls == [["code", "--reuse-window", "--goto", str(target.resolve())]]


def test_view_regeneration_cannot_erase_saved_response_or_recreate_identity(tmp_path: Path):
    draft(tmp_path)
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    path.write_text(path.read_text().replace("Decision: PENDING", "Decision: APPROVE"))
    before = path.read_bytes()
    HumanViewGenerator(tmp_path).generate(project_id="decision-docs")
    assert path.read_bytes() == before
    controller = HumanDecisionController(tmp_path)
    with pytest.raises(HumanDecisionError, match="identity already exists"):
        controller.create_intent(decision_id="HD-001", intent_id="I-701", version=1, timestamp="2026-09-20T00:00:01Z")


def test_gate_package_binds_after_final_event_and_stales_on_later_authority_change(tmp_path: Path):
    from tests.integration.test_stage_e6_human import make_gate

    gate_controller, gate = make_gate(tmp_path, "HG-801")
    events = EventLog(tmp_path)
    final = events.new_event(event_id="eu-801-verified", event_type="eu.verified", timestamp="2026-09-20T03:00:00Z", project_id="e4", actor_type="controller", actor_id="controller", payload={"gate_id": gate["gate_id"], "candidate_sha": gate["related_candidate"]["candidate_sha"]})
    events.append(final)
    controller = HumanDecisionController(tmp_path, controller_execution_id="EXEC-CONTROLLER-501")
    path = controller.create_gate(decision_id="HD-003", gate_id=gate["gate_id"], timestamp="2026-09-20T03:00:01Z")
    package = controller.store.read("HD-003")
    assert package["authoritative_event_head"] == {"event_id": final["event_id"], "event_hash": final["event_hash"]}
    path.write_text(path.read_text().replace("Decision: PENDING", "Decision: APPROVE"))
    resolved = controller.resolve("HD-003", timestamp="2026-09-20T03:00:02Z")
    assert resolved["decision"] == "APPROVE"

    stale_root = tmp_path / "stale"
    stale_root.mkdir()
    _, stale_gate = make_gate(stale_root, "HG-802")
    stale_events = EventLog(stale_root)
    before = stale_events.new_event(event_id="eu-802-verified", event_type="eu.verified", timestamp="2026-09-20T03:01:00Z", project_id="e4", actor_type="controller", actor_id="controller", payload={"gate_id": stale_gate["gate_id"], "candidate_sha": stale_gate["related_candidate"]["candidate_sha"]})
    stale_events.append(before)
    stale_controller = HumanDecisionController(stale_root, controller_execution_id="EXEC-CONTROLLER-501")
    stale = stale_controller.create_gate(decision_id="HD-003", gate_id=stale_gate["gate_id"], timestamp="2026-09-20T03:01:01Z")
    later = stale_events.new_event(event_id="unrelated-authority-change", event_type="eu.verified", timestamp="2026-09-20T03:01:02Z", project_id="e4", actor_type="controller", actor_id="controller", payload={"gate_id": "OTHER"})
    stale_events.append(later)
    stale.write_text(stale.read_text().replace("Decision: PENDING", "Decision: APPROVE"))
    with pytest.raises(HumanDecisionError, match="STALE_DECISION"):
        stale_controller.resolve("HD-003", timestamp="2026-09-20T03:01:03Z")


def test_malformed_response_is_repaired_in_place_without_authority(tmp_path: Path):
    draft(tmp_path)
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    original = path.read_text()
    malformed = original.replace("--------------------------------------------------\nEDIT ONLY BELOW THIS LINE\n\nDecision: PENDING\nComment: \n\nEDIT ONLY ABOVE THIS LINE\n--------------------------------------------------\nThis is the only authoritative response section. Save this file after editing.\n", '- Gate: "APPROVE"\nComment: preserve this safe comment\n')
    path.write_text(malformed)
    controller = HumanDecisionController(tmp_path)
    with pytest.raises(HumanDecisionError, match="MALFORMED_RESPONSE"):
        controller.scan(timestamp="2026-09-20T04:00:00Z")
    before_events = controller.events.verify()
    controller.store.repair("HD-001", repaired_at="2026-09-20T04:00:01Z")
    repaired = controller.store.read("HD-001")
    assert repaired["decision_id"] == "HD-001"
    assert repaired["intent"] == {"intent_id": "I-701", "version": 1}
    assert repaired["response_decision"] == "PENDING"
    assert repaired["response_comment"] == "preserve this safe comment"
    assert controller.events.verify() == before_events
    assert list((tmp_path / ".idd/human_decisions/diagnostics").glob("HD-001-*.md"))
    path.write_text(path.read_text().replace("Decision: PENDING", "Decision: APPROVE"))
    assert controller.resolve("HD-001", timestamp="2026-09-20T04:00:02Z")["decision"] == "APPROVE"


def test_ambiguous_decision_text_is_not_recovered_as_approval(tmp_path: Path):
    draft(tmp_path)
    path = tmp_path / ".idd/human_decisions/pending/HD-001.md"
    path.write_text(path.read_text().replace("Decision: PENDING", "Decision: approved"))
    controller = HumanDecisionController(tmp_path)
    with pytest.raises(HumanDecisionError):
        controller.scan(timestamp="2026-09-20T04:01:00Z")
    controller.store.repair("HD-001", repaired_at="2026-09-20T04:01:01Z")
    assert controller.store.read("HD-001")["response_decision"] == "PENDING"


def test_scan_skips_preserved_superseded_packages(tmp_path: Path):
    draft(tmp_path)
    controller = HumanDecisionController(tmp_path)
    controller.store.invalidate("HD-001", replacement_id="HD-002", invalidated_at="2026-09-20T04:02:00Z", reason="creator binding defect")
    with pytest.raises(HumanDecisionError, match="SUPERSEDED"):
        controller.resolve("HD-001", timestamp="2026-09-20T04:02:01Z")
    assert controller.scan(timestamp="2026-09-20T04:02:01Z") == []

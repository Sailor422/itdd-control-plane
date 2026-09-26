from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from control.proposal_approvals import ProposalApprovalController, ProposalApprovalError
import subprocess


def artifacts(root: Path):
    proposal = root / "work/proposal.md"
    proposal.parent.mkdir(parents=True)
    proposal.write_bytes(b"# Exact proposal\nDo this only.\n")
    report = root / "work/review.md"
    report.write_bytes(b"Independent review: PASS\n")
    scope = "Implement bounded change only"
    pdigest = hashlib.sha256(proposal.read_bytes()).hexdigest()
    scope_digest = hashlib.sha256(scope.encode()).hexdigest()
    review = {
        "schema_version": 1, "review_id": "REV-1", "proposal_id": "PROP-1",
        "proposal_sha256": pdigest, "scope_sha256": scope_digest, "verdict": "PASS",
        "reviewer_execution_id": "EXEC-REVIEW-1", "report_path": "work/review.md",
        "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
    }
    receipt = root / "work/review.json"
    receipt.write_text(json.dumps(review))
    return {"proposal_id": "PROP-1", "proposal_path": "work/proposal.md", "scope": scope,
            "proposal_sha256": pdigest}, "work/review.json"


def invocation():
    return {"command": "/approved", "source": "interactive", "invocation_id": "TURN-123"}


def test_exact_approval_records_once_and_replays_receipt(tmp_path):
    proposal, review = artifacts(tmp_path)
    controller = ProposalApprovalController(tmp_path, project_id="project-test")
    first = controller.record(proposal=proposal, review_path=review, invocation=invocation(), timestamp="2026-09-26T00:00:00Z")
    second = controller.record(proposal=proposal, review_path=review, invocation=invocation(), timestamp="2026-09-26T00:00:00Z")
    assert first == second
    assert first["persisted"] is True
    assert len([e for e in controller.events.verify() if e["event_type"] == "proposal.approval.recorded"]) == 1
    assert controller.read(first["approval_id"]) == first


def test_changed_proposal_or_reviewer_is_not_persisted(tmp_path):
    proposal, review = artifacts(tmp_path)
    controller = ProposalApprovalController(tmp_path, project_id="project-test")
    first = controller.record(proposal=proposal, review_path=review, invocation=invocation(), timestamp="2026-09-26T00:00:00Z")
    changed = invocation() | {"invocation_id": "TURN-124"}
    with pytest.raises(ProposalApprovalError, match="already recorded"):
        controller.record(proposal=proposal, review_path=review, invocation=changed, timestamp="2026-09-26T00:00:01Z")
    assert len(controller.events.verify()) == 1


@pytest.mark.parametrize("failure", ["proposal_bytes", "proposal_scope", "review_fail", "review_missing", "traversal"])
def test_invalid_artifacts_leave_event_authority_unchanged(tmp_path, failure):
    proposal, review = artifacts(tmp_path)
    if failure == "proposal_bytes":
        (tmp_path / proposal["proposal_path"]).write_bytes(b"changed")
    elif failure == "proposal_scope":
        proposal["scope"] = "changed scope"
    elif failure == "review_fail":
        p = tmp_path / review
        value = json.loads(p.read_text()); value["verdict"] = "FAIL"; p.write_text(json.dumps(value))
    elif failure == "review_missing":
        (tmp_path / review).unlink()
    elif failure == "traversal":
        proposal["proposal_path"] = "../outside"
    controller = ProposalApprovalController(tmp_path, project_id="project-test")
    with pytest.raises(ProposalApprovalError):
        controller.record(proposal=proposal, review_path=review, invocation=invocation(), timestamp="2026-09-26T00:00:00Z")
    assert controller.events.verify() == []


def test_approval_does_not_execute_or_mutate_proposal(tmp_path):
    proposal, review = artifacts(tmp_path)
    path = tmp_path / proposal["proposal_path"]
    before = path.read_bytes()
    result = ProposalApprovalController(tmp_path, project_id="project-test").record(proposal=proposal, review_path=review, invocation=invocation(), timestamp="2026-09-26T00:00:00Z")
    assert path.read_bytes() == before and result["executed"] is False


def test_event_append_failure_reports_not_persisted(tmp_path, monkeypatch):
    proposal, review = artifacts(tmp_path)
    controller = ProposalApprovalController(tmp_path, project_id="project-test")
    def fail_append(event):
        raise OSError("simulated storage failure")
    monkeypatch.setattr(controller.events, "append", fail_append)
    with pytest.raises(OSError, match="storage failure"):
        controller.record(proposal=proposal, review_path=review, invocation=invocation(), timestamp="2026-09-26T00:00:00Z")
    assert controller.events.verify() == []


@pytest.mark.parametrize("bad_invocation", [None, {}, {"command": "/approved", "source": "interactive", "invocation_id": ""}, {"command": "approved", "source": "interactive", "invocation_id": "TURN"}])
def test_bad_invocation_metadata_leaves_log_unchanged(tmp_path, bad_invocation):
    proposal, review = artifacts(tmp_path)
    controller = ProposalApprovalController(tmp_path, project_id="project-test")
    with pytest.raises(ProposalApprovalError):
        controller.record(proposal=proposal, review_path=review, invocation=bad_invocation, timestamp="2026-09-26T00:00:00Z")
    assert controller.events.verify() == []


def test_documented_command_records_and_returns_receipt(tmp_path):
    proposal, review = artifacts(tmp_path)
    proposal_file = tmp_path / "work/proposal-input.json"
    proposal_file.write_text(json.dumps(proposal))
    # The project identity is explicitly supplied from the active project context.
    result = subprocess.run([
        "uv", "run", "python", str(Path(__file__).parents[2] / "tools/itdd.py"),
        "proposal-approval", "record", "--project-root", str(tmp_path),
        "--project-id", "project-test", "--proposal-json", str(proposal_file),
        "--review", review, "--invocation-id", "TURN-123",
        "--timestamp", "2026-09-26T00:00:00Z",
    ], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["persisted"] is True and receipt["executed"] is False
    assert len([e for e in ProposalApprovalController(tmp_path, project_id="project-test").events.verify() if e["event_type"] == "proposal.approval.recorded"]) == 1


def test_blank_project_id_rejected_before_event_log_created(tmp_path):
    with pytest.raises(ProposalApprovalError, match="project_id"):
        ProposalApprovalController(tmp_path, project_id="  ")
    assert not (tmp_path / ".idd/state/events.jsonl").exists()

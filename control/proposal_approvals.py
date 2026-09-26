"""Controller-owned durable records for skill-mediated proposal approval."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_root
from control.events import EventLog
from control.events.format import canonical_json


class ProposalApprovalError(ValueError):
    """Approval cannot be recorded safely."""


class ProposalApprovalController:
    """Record metadata delivered by the trusted human-only /approved skill.

    This adapter is not an authenticator. Only the installed skill is the
    supported invocation boundary; it checks the host's current-turn marker.
    """
    def __init__(self, project_root: str | Path, *, project_id: str) -> None:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ProposalApprovalError("project_id from the active project is required")
        self.project_id = project_id
        self.project_root = resolve_project_root(project_root)
        self.events = EventLog(self.project_root)

    def _file(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative:
            raise ProposalApprovalError("artifact path is required")
        path = (self.project_root / relative).resolve()
        try:
            path.relative_to(self.project_root)
        except ValueError as exc:
            raise ProposalApprovalError("artifact path escapes project root") from exc
        if not path.is_file():
            raise ProposalApprovalError("artifact is missing")
        return path

    def _payload(self, proposal: dict[str, Any], review_path: str, invocation: dict[str, Any]) -> dict[str, Any]:
        required = {"proposal_id", "proposal_path", "scope", "proposal_sha256"}
        if not isinstance(proposal, dict) or set(proposal) != required:
            raise ProposalApprovalError("proposal identity, path, scope, and hash are required")
        if not all(isinstance(proposal[k], str) and proposal[k].strip() for k in required):
            raise ProposalApprovalError("proposal fields must be nonempty strings")
        proposal_file = self._file(proposal["proposal_path"])
        proposal_hash = hashlib.sha256(proposal_file.read_bytes()).hexdigest()
        if proposal_hash != proposal["proposal_sha256"]:
            raise ProposalApprovalError("proposal bytes changed or hash mismatch")
        scope_hash = hashlib.sha256(proposal["scope"].encode("utf-8")).hexdigest()
        review_file = self._file(review_path)
        try:
            review = json.loads(review_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ProposalApprovalError("review receipt is invalid JSON") from exc
        keys = {"schema_version", "review_id", "proposal_id", "proposal_sha256", "scope_sha256", "verdict", "reviewer_execution_id", "report_path", "report_sha256"}
        if not isinstance(review, dict) or set(review) != keys or review.get("schema_version") != 1:
            raise ProposalApprovalError("review receipt schema is invalid")
        if review.get("verdict") != "PASS" or not isinstance(review.get("reviewer_execution_id"), str) or not review["reviewer_execution_id"].strip():
            raise ProposalApprovalError("independent review is not PASS")
        if review["proposal_id"] != proposal["proposal_id"] or review["proposal_sha256"] != proposal_hash or review["scope_sha256"] != scope_hash:
            raise ProposalApprovalError("review does not bind this proposal and scope")
        report = self._file(review["report_path"])
        if hashlib.sha256(report.read_bytes()).hexdigest() != review["report_sha256"]:
            raise ProposalApprovalError("review report bytes changed or hash mismatch")
        if not isinstance(invocation, dict) or set(invocation) != {"command", "source", "invocation_id"} or invocation.get("command") != "/approved" or invocation.get("source") != "interactive" or not isinstance(invocation.get("invocation_id"), str) or not invocation["invocation_id"].strip():
            raise ProposalApprovalError("invocation metadata must come from the Prime interactive /approved invocation checked by the skill")
        return {"proposal_id": proposal["proposal_id"], "proposal_path": proposal["proposal_path"], "proposal_sha256": proposal_hash, "scope": proposal["scope"], "scope_sha256": scope_hash, "review_path": review_path, "review": review, "invocation": invocation}

    def record(self, *, proposal: dict[str, Any], review_path: str, invocation: dict[str, Any], timestamp: str) -> dict[str, Any]:
        payload = self._payload(proposal, review_path, invocation)
        existing = [e for e in self.events.verify() if e["event_type"] == "proposal.approval.recorded" and e["payload"].get("proposal_id") == payload["proposal_id"]]
        if existing:
            if len(existing) != 1 or existing[0]["payload"] != payload:
                raise ProposalApprovalError("approval already recorded with different binding")
            return self._receipt(existing[0])
        digest = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
        event = self.events.new_event(event_id=f"proposal-approval-{digest[:32]}", event_type="proposal.approval.recorded", timestamp=timestamp, project_id=self.project_id, actor_type="human", actor_id=invocation["invocation_id"], execution_id=invocation["invocation_id"], payload=payload)
        self.events.append(event)
        return self._receipt(event)

    @staticmethod
    def _receipt(event: dict[str, Any]) -> dict[str, Any]:
        return {"persisted": True, "approval_id": event["event_id"], "event_hash": event["event_hash"], "project_id": event["project_id"], "recorded_at": event["timestamp"], "actor_type": event["actor_type"], "actor_id": event["actor_id"], "execution_id": event.get("execution_id"), **event["payload"], "executed": False, "message": "Approval recorded; no work was executed or promoted."}

    def read(self, approval_id: str) -> dict[str, Any]:
        matches = [e for e in self.events.verify() if e["event_type"] == "proposal.approval.recorded" and e["event_id"] == approval_id]
        if len(matches) != 1:
            raise ProposalApprovalError("approval record not found or ambiguous")
        return self._receipt(matches[0])

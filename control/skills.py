"""Controller-boundary contract for human clarification proposals."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_path, resolve_project_root
from control.authorization.controller import ControllerAuthorizer
from control.events import EventLog
from control.events.format import canonical_json


class SkillContractError(ValueError):
    """Raised when a skill request cannot be accepted at the controller seam."""


class ClarificationProposalStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)
        self.event_log = EventLog(self.project_root)

    def _path(self, proposal_id: str, version: int) -> Path:
        return resolve_project_path(self.project_root, f".idd/skills/grill-with-docs/{proposal_id}/v{version}.json")

    def read(self, proposal_id: str, version: int = 1) -> dict[str, Any]:
        path = self._path(proposal_id, version)
        if not path.exists():
            raise SkillContractError("clarification proposal does not exist")
        proposal = json.loads(path.read_text(encoding="utf-8"))
        validate_clarification_proposal(proposal)
        return proposal

    def write_new(self, proposal: dict[str, Any]) -> None:
        validate_clarification_proposal(proposal)
        path = self._path(proposal["proposal_id"], proposal["version"])
        serialized = canonical_json(proposal) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != serialized:
                raise SkillContractError("clarification proposal is immutable")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")


def validate_clarification_proposal(proposal: dict[str, Any]) -> None:
    required = {
        "proposal_id", "proposal_type", "version", "status", "project_id", "execution_id",
        "intent_id", "intent_version", "baseline_sha", "source_inputs", "skill_source",
        "capability_id", "terms", "assumptions", "open_questions", "authority_effect",
        "source_event_id",
    }
    if not isinstance(proposal, dict) or set(proposal) != required:
        raise SkillContractError("proposal has missing or unknown fields")
    if proposal["proposal_type"] != "grill-with-docs.clarification" or proposal["version"] != 1:
        raise SkillContractError("unsupported clarification proposal version")
    if proposal["status"] != "PROPOSED" or proposal["authority_effect"] != "NONE":
        raise SkillContractError("proposal must remain non-authoritative")
    for field in ("proposal_id", "project_id", "execution_id", "intent_id", "baseline_sha", "skill_source", "capability_id", "source_event_id"):
        if not isinstance(proposal[field], str) or not proposal[field].strip():
            raise SkillContractError(f"{field} must be a non-empty string")
    if not isinstance(proposal["intent_version"], int) or proposal["intent_version"] < 1:
        raise SkillContractError("intent_version must be positive")
    if not isinstance(proposal["source_inputs"], list) or not all(isinstance(item, str) and item for item in proposal["source_inputs"]):
        raise SkillContractError("source_inputs must be a list of strings")
    if not all(isinstance(proposal[field], list) for field in ("terms", "assumptions", "open_questions")):
        raise SkillContractError("clarification content must be lists")


def _proposal_id(request: dict[str, Any], capability: dict[str, Any]) -> str:
    identity = {
        "project_id": request["project_id"], "execution_id": request["execution_id"],
        "intent_id": request["intent_id"], "intent_version": request["intent_version"],
        "baseline_sha": request["baseline_sha"], "source_inputs": request["source_inputs"],
        "skill_source": "grill-with-docs", "capability_id": capability["capability_id"], "version": 1,
    }
    return "CLAR-" + hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()[:20]


def create_clarification_proposal(
    project_root: str | Path,
    *,
    request: dict[str, Any],
    capability: dict[str, Any],
    actor_type: str,
    actor_id: str,
    timestamp: str,
    event_id: str,
) -> dict[str, Any]:
    required = {"project_id", "execution_id", "intent_id", "intent_version", "baseline_sha", "source_inputs", "terms", "assumptions", "open_questions"}
    if set(request) != required:
        raise SkillContractError("clarification request has missing or unknown fields")
    if actor_type != "human" or not actor_id:
        raise SkillContractError("grill-with-docs requires a human actor")
    if capability.get("role") != "CONVERSATIONAL":
        raise SkillContractError("clarification requires the CONVERSATIONAL role")
    root = resolve_project_root(project_root)
    current_state = {"project_id": request["project_id"], "execution_id": request["execution_id"], "baseline_sha": request["baseline_sha"], "project_root": str(root)}
    decision = ControllerAuthorizer(root).authorize(
        capability["capability_id"],
        {"request_id": event_id, "project_id": request["project_id"], "execution_id": request["execution_id"], "baseline_sha": request["baseline_sha"], "role": "CONVERSATIONAL", "operation": "REQUEST_CLARIFICATION", "actor_type": actor_type, "intent_id": request["intent_id"], "intent_version": request["intent_version"]},
        current_state,
    )
    if decision.decision != "ALLOW":
        raise SkillContractError(decision.reason)
    proposal = {
        "proposal_id": _proposal_id(request, capability), "proposal_type": "grill-with-docs.clarification", "version": 1, "status": "PROPOSED",
        "project_id": request["project_id"], "execution_id": request["execution_id"], "intent_id": request["intent_id"], "intent_version": request["intent_version"],
        "baseline_sha": request["baseline_sha"], "source_inputs": deepcopy(request["source_inputs"]), "skill_source": "grill-with-docs", "capability_id": capability["capability_id"],
        "terms": deepcopy(request["terms"]), "assumptions": deepcopy(request["assumptions"]), "open_questions": deepcopy(request["open_questions"]), "authority_effect": "NONE", "source_event_id": event_id,
    }
    store = ClarificationProposalStore(root)
    store.write_new(proposal)
    event = store.event_log.new_event(event_id=event_id, event_type="skill.clarification.proposed", timestamp=timestamp, project_id=request["project_id"], actor_type=actor_type, actor_id=actor_id, execution_id=request["execution_id"], payload={"proposal": proposal})
    store.event_log.append(event)
    return proposal

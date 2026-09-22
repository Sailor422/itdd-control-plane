"""Fail-closed discovery and execution for project-local ITDD skills.

This module deliberately implements a small, deterministic skill boundary. It
does not import or search any global skill collection and it has no lifecycle
authority APIs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class SkillRuntimeError(RuntimeError):
    """Raised for any malformed, unauthorized, stale, or unsafe skill request."""


_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_AUTHORITY_ACTIONS = {
    "intent.approve",
    "intent.mutate",
    "graph.approve",
    "execution.activate",
    "lifecycle.advance",
    "human-authority.create",
    "promotion.execute",
    "capability.grant",
    "filesystem.escape",
}
_ALLOWED_ROLES = {"human"}
_ALLOWED_SKILL_CAPABILITIES = {"project.artifact.write"}


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SkillRuntimeError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise SkillRuntimeError(f"JSON object required: {path}")
    return value


def _safe_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise SkillRuntimeError(f"invalid {field}")
    return value


@dataclass(frozen=True)
class CapabilityGrant:
    execution_id: str
    project_root: Path
    capabilities: frozenset[str]

    def intersect(self, requested: set[str]) -> frozenset[str]:
        return frozenset(requested).intersection(self.capabilities)


@dataclass(frozen=True)
class SkillInvocation:
    project_id: str
    execution_id: str
    draft_id: str
    role: str
    inputs: Mapping[str, Any]


class SkillRuntime:
    """Discover and invoke only contracts rooted at the supplied project."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.skills_root = self.project_root / "skills"
        self.manifest_path = self.skills_root / "manifest.json"

    def discover(self) -> dict[str, dict[str, Any]]:
        if not self.skills_root.is_dir() or self.skills_root.is_symlink() or self.manifest_path.is_symlink():
            raise SkillRuntimeError("project-local skills directory is missing or symlinked")
        manifest = _read_json(self.manifest_path)
        if manifest.get("manifest_version") != "1.0" or manifest.get("project_local_only") is not True:
            raise SkillRuntimeError("invalid skills manifest")
        entries = manifest.get("skills")
        if not isinstance(entries, list) or not entries:
            raise SkillRuntimeError("skills manifest must contain entries")
        found: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise SkillRuntimeError("malformed skills manifest entry")
            skill_id = _safe_id(entry.get("id"), "skill id")
            contract_ref = entry.get("contract")
            if not isinstance(contract_ref, str) or Path(contract_ref).is_absolute():
                raise SkillRuntimeError("skill contract must be relative")
            contract_path = (self.skills_root / contract_ref).resolve()
            if self.skills_root not in contract_path.parents or contract_path.is_symlink():
                raise SkillRuntimeError("skill contract escapes project-local skills root")
            contract = _read_json(contract_path)
            self._validate_contract(skill_id, contract)
            if skill_id in found:
                raise SkillRuntimeError("duplicate skill id")
            found[skill_id] = {
                "id": skill_id,
                "contract": contract,
                "contract_path": str(contract_path),
                "contract_hash": _sha256(contract),
                "manifest_hash": _sha256(manifest),
                "disposition": entry.get("disposition"),
            }
        return found

    def _validate_contract(self, manifest_id: str, contract: Mapping[str, Any]) -> None:
        required = {
            "skill_id", "name", "version", "purpose", "allowed_roles", "required_inputs", "input_schema",
            "produced_artifacts", "required_capabilities", "allowed_capabilities",
            "forbidden_actions", "deterministic_behavior", "agent_reasoned_behavior",
            "invocation", "evidence", "failure_semantics", "telemetry", "provenance",
        }
        if not required.issubset(contract):
            raise SkillRuntimeError("skill contract is missing required fields")
        if contract["skill_id"] != manifest_id or not _ID.fullmatch(str(contract["name"])):
            raise SkillRuntimeError("skill identity mismatch")
        if contract["version"] != "1.0.0":
            raise SkillRuntimeError("unsupported skill contract version")
        if set(contract["allowed_roles"]) != _ALLOWED_ROLES:
            raise SkillRuntimeError("skill role envelope is not the v1 human-only envelope")
        requested = set(contract["required_capabilities"])
        allowed = set(contract["allowed_capabilities"])
        forbidden = set(contract["forbidden_actions"])
        if not requested.issubset(allowed) or not allowed.issubset(_ALLOWED_SKILL_CAPABILITIES):
            raise SkillRuntimeError("skill capability envelope is too broad")
        if not _AUTHORITY_ACTIONS.issubset(forbidden):
            raise SkillRuntimeError("skill contract does not forbid authority actions")
        invocation = contract["invocation"]
        if invocation != {"human_invoked": True, "requires_execution_binding": True, "project_root_must_match": True}:
            raise SkillRuntimeError("skill invocation contract is not fail-closed")
        if contract["provenance"].get("authority_rule") != "SKILL != AUTHORITY":
            raise SkillRuntimeError("skill authority provenance is missing")

    def invoke(self, skill_id: str, invocation: SkillInvocation, grant: CapabilityGrant) -> dict[str, Any]:
        skills = self.discover()
        if skill_id not in skills:
            raise SkillRuntimeError("unknown project-local skill")
        record = skills[skill_id]
        contract = record["contract"]
        self._validate_invocation(contract, invocation, grant)
        telemetry_dir = self.project_root / ".idd" / "skills" / "telemetry"
        evidence_dir = self.project_root / ".idd" / "skills" / "evidence"
        artifact_dir = self.project_root / ".idd" / "skills" / "artifacts"
        for directory in (telemetry_dir, evidence_dir, artifact_dir):
            directory.mkdir(parents=True, exist_ok=True)
        event_id = str(uuid.uuid4())
        # Event identity is deliberately per invocation. It belongs in
        # telemetry/evidence, not in the proposal bytes, so rerunning the
        # same bound request remains byte-stable.
        base = {
            "skill_id": skill_id,
            "skill_version": contract["version"],
            "project_id": invocation.project_id,
            "execution_id": invocation.execution_id,
            "draft_id": invocation.draft_id,
            "role": invocation.role,
            "contract_hash": record["contract_hash"],
            "manifest_hash": record["manifest_hash"],
        }
        event_base = {**base, "event_id": event_id}
        self._append_telemetry(telemetry_dir / "events.jsonl", {**event_base, "event": "invocation_started"})
        try:
            source_inputs = invocation.inputs["source_inputs"]
            normalized = sorted(
                ({"source_id": item["source_id"], "text": item["text"].strip()} for item in source_inputs),
                key=lambda item: item["source_id"],
            )
            proposal_identity = {
                **base,
                "source_inputs": normalized,
                "artifact_type": "clarification-proposal",
            }
            proposal_id = "CLAR-" + _sha256(proposal_identity)[:20]
            artifact = {
                **base,
                "proposal_id": proposal_id,
                "artifact_type": "clarification-proposal",
                "status": "PROPOSAL_ONLY",
                "source_inputs": normalized,
                "clarification": {
                    "terms": sorted({word for item in normalized for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]*", item["text"].lower())}),
                    "open_questions": ["Which terms require human confirmation before intent approval?"],
                },
                "capabilities": sorted(grant.intersect(set(contract["required_capabilities"]))),
                "authority": "none",
            }
            artifact_path = artifact_dir / f"{invocation.execution_id}.json"
            artifact_path.write_bytes(_canonical(artifact))
            evidence = {**event_base, "proposal_id": proposal_id, "artifact_sha256": _sha256(artifact), "artifact_path": str(artifact_path.relative_to(self.project_root)), "result": "success"}
            (evidence_dir / f"{invocation.execution_id}.json").write_bytes(_canonical(evidence))
            self._append_telemetry(telemetry_dir / "events.jsonl", {**event_base, "event": "invocation_succeeded", "artifact_sha256": evidence["artifact_sha256"]})
            # Return the invocation envelope to the caller, while keeping the
            # persisted proposal free of per-invocation identity.
            return {**artifact, "event_id": event_id}
        except Exception as exc:
            self._append_telemetry(telemetry_dir / "events.jsonl", {**event_base, "event": "invocation_failed", "error": type(exc).__name__})
            raise

    def _validate_invocation(self, contract: Mapping[str, Any], invocation: SkillInvocation, grant: CapabilityGrant) -> None:
        if invocation.role not in contract["allowed_roles"] or invocation.role != "human":
            raise SkillRuntimeError("role is not authorized for skill")
        _safe_id(invocation.project_id, "project id")
        _safe_id(invocation.execution_id, "execution id")
        _safe_id(invocation.draft_id, "draft id")
        if invocation.execution_id != grant.execution_id:
            raise SkillRuntimeError("execution binding mismatch")
        if grant.project_root.resolve() != self.project_root:
            raise SkillRuntimeError("project root binding mismatch")
        if set(invocation.inputs) != set(contract["required_inputs"]):
            raise SkillRuntimeError("input contract mismatch")
        if invocation.inputs["project_id"] != invocation.project_id or invocation.inputs["execution_id"] != invocation.execution_id or invocation.inputs["draft_id"] != invocation.draft_id:
            raise SkillRuntimeError("input execution binding mismatch")
        source_inputs = invocation.inputs["source_inputs"]
        if not isinstance(source_inputs, list) or not source_inputs or any(
            not isinstance(item, dict) or set(item) != {"source_id", "text"} or not isinstance(item["text"], str) or not item["text"].strip() or not _ID.fullmatch(str(item["source_id"]))
            for item in source_inputs
        ):
            raise SkillRuntimeError("source input contract mismatch")
        effective = grant.intersect(set(contract["required_capabilities"]))
        if effective != set(contract["required_capabilities"]):
            raise SkillRuntimeError("controller grant does not satisfy skill capability envelope")

    def discover_workflow(self) -> dict[str, Any]:
        """Return the controller-owned registration for the supported flow.

        Workflow registration is deliberately data-only.  It describes routing
        and authority; it does not execute a skill or grant lifecycle power.
        """
        if self.manifest_path.is_symlink() or not self.manifest_path.is_file():
            raise SkillRuntimeError("workflow registration manifest is missing or symlinked")
        manifest = _read_json(self.manifest_path)
        workflow = manifest.get("workflows")
        if not isinstance(workflow, dict):
            raise SkillRuntimeError("workflow registration is missing")
        required = {"workflow_id", "version", "steps", "controller_boundary", "worker_boundary"}
        if set(workflow) != required or workflow["workflow_id"] != "wayfinder-to-review" or workflow["version"] != "1.0":
            raise SkillRuntimeError("invalid workflow registration")
        expected = ["wayfinder", "to-spec", "to-tickets", "implement", "tdd", "code-review"]
        steps = workflow["steps"]
        if not isinstance(steps, list) or [s.get("name") for s in steps] != expected:
            raise SkillRuntimeError("workflow steps are incomplete or out of order")
        for step in steps:
            if set(step) != {"name", "skill", "mode", "authority"} or step["mode"] != "controller-routed" or step["authority"] != "controller":
                raise SkillRuntimeError("workflow step grants non-controller authority")
            skill_path = self.skills_root / step["skill"] / "SKILL.md"
            if not skill_path.is_file() or skill_path.is_symlink():
                raise SkillRuntimeError("workflow skill is not project-local")
        if workflow["controller_boundary"] != {"accepts": "approved-contract", "owns": ["routing", "evidence", "lifecycle", "promotion"]}:
            raise SkillRuntimeError("controller boundary is invalid")
        if workflow["worker_boundary"] != {"roles": ["BUILD", "TEST", "VERIFY"], "isolated": True, "skills_authority": False}:
            raise SkillRuntimeError("worker boundary is invalid")
        return workflow

    def validate_workflow_acceptance(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Validate an observation at the controller acceptance seam.

        This method only returns a decision.  It cannot advance lifecycle state,
        promote a candidate, or turn worker output into authority.
        """
        self.discover_workflow()
        required = {"project_id", "execution_id", "role", "baseline_sha", "candidate_sha", "steps", "approved_contract"}
        if set(request) != required:
            raise SkillRuntimeError("workflow acceptance request shape mismatch")
        if request["role"] != "controller":
            raise SkillRuntimeError("workflow acceptance is controller-only")
        if request["project_id"] != self.project_root.name or not _ID.fullmatch(str(request["execution_id"])):
            raise SkillRuntimeError("workflow acceptance binding mismatch")
        if not request["approved_contract"] or not isinstance(request["approved_contract"], str):
            raise SkillRuntimeError("approved execution contract is required")
        expected = ["wayfinder", "to-spec", "to-tickets", "implement", "tdd", "code-review"]
        if request["steps"] != expected:
            raise SkillRuntimeError("workflow acceptance steps mismatch")
        for field in ("baseline_sha", "candidate_sha"):
            if not isinstance(request[field], str) or not re.fullmatch(r"[0-9a-f]{40}", request[field]):
                raise SkillRuntimeError("workflow acceptance identity is invalid")
        return {"decision": "OBSERVED", "authority": "controller", "lifecycle_effect": "none", "promotion_effect": "none", "execution_id": request["execution_id"], "candidate_sha": request["candidate_sha"]}

    @staticmethod
    def _append_telemetry(path: Path, event: Mapping[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical(dict(event)).decode())

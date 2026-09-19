"""Durable, immutable Stage D capability envelopes and trusted issuance."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from control.authority.paths import AuthorityError, resolve_project_path, resolve_project_root
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json
from .roles import ROLE_DEFINITIONS


class CapabilityError(ValueError):
    pass


class AccessType:
    READ = "READ"; WRITE = "WRITE"; EXECUTE = "EXECUTE"
    STATE_TRANSITION = "STATE_TRANSITION"; CREATE_ARTIFACT = "CREATE_ARTIFACT"
    APPEND_EVENT = "APPEND_EVENT"; REQUEST_CONTEXT = "REQUEST_CONTEXT"
    REQUEST_REPLAN = "REQUEST_REPLAN"; REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    RESOLVE_CONTEXT = "RESOLVE_CONTEXT"


HUMAN_ONLY = {"INTENT_APPROVAL", "GRAPH_APPROVAL", "MAINTENANCE_MODE_ENTRY", "BREAK_GLASS_ENTRY", "BREAK_GLASS_APPROVAL"}
_CAPABILITY_ID = re.compile(r"^CAP-[0-9]{3,}$")
_EXECUTION_ID = re.compile(r"^EXEC-[A-Za-z0-9._-]+$")
_ACCESS = {getattr(AccessType, name) for name in dir(AccessType) if name.isupper()}


def _integrity_document(envelope: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(envelope); result.pop("integrity_hash", None); return result


def _integrity_hash(envelope: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(_integrity_document(envelope)).encode()).hexdigest()


def validate_capability(envelope: dict[str, Any], *, verify_integrity: bool = True) -> None:
    required = {"capability_id", "schema_version", "project_id", "role", "execution_id", "issued_at", "baseline_sha", "allowed_reads", "allowed_writes", "allowed_executes", "allowed_operations", "forbidden_operations", "allowed_request_types", "scope_bindings", "version", "issued_by", "integrity_hash"}
    missing = required - set(envelope)
    if missing: raise CapabilityError(f"missing capability fields: {sorted(missing)}")
    if set(envelope) - required: raise CapabilityError("unknown capability fields")
    if not _CAPABILITY_ID.fullmatch(envelope["capability_id"]): raise CapabilityError("invalid capability_id")
    if envelope["schema_version"] != 1 or envelope["version"] < 1: raise CapabilityError("unsupported capability version")
    if envelope["role"] not in ROLE_DEFINITIONS: raise CapabilityError("unknown role")
    if not _EXECUTION_ID.fullmatch(envelope["execution_id"]): raise CapabilityError("invalid execution_id")
    if not isinstance(envelope["baseline_sha"], str) or not re.fullmatch(r"[0-9a-f]{40,64}", envelope["baseline_sha"]): raise CapabilityError("invalid baseline_sha")
    try: datetime.fromisoformat(envelope["issued_at"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc: raise CapabilityError("issued_at must be ISO-8601") from exc
    for field in ("allowed_reads", "allowed_writes", "allowed_executes", "allowed_operations", "forbidden_operations", "allowed_request_types"):
        if not isinstance(envelope[field], list) or any(not isinstance(value, str) or not value for value in envelope[field]): raise CapabilityError(f"{field} must be a list of strings")
    if any(value not in _ACCESS for value in envelope["allowed_operations"]): raise CapabilityError("unknown allowed operation")
    if not isinstance(envelope["scope_bindings"], dict): raise CapabilityError("scope_bindings must be an object")
    if verify_integrity and envelope["integrity_hash"] != _integrity_hash(envelope): raise CapabilityError("capability integrity hash mismatch")


class CapabilityStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)
        self.event_log = EventLog(self.project_root)

    def _path(self, capability_id: str, version: int) -> Path:
        return resolve_project_path(self.project_root, f".idd/capabilities/{capability_id}/v{version}.json")

    def read(self, capability_id: str, version: int = 1) -> dict[str, Any]:
        path = self._path(capability_id, version)
        if not path.exists(): raise CapabilityError("capability does not exist")
        envelope = json.loads(path.read_text())
        validate_capability(envelope)
        return envelope

    def reconstruct(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for event in self.event_log.verify():
            if event["event_type"] == "capability.issued":
                envelope = event["payload"]["capability"]
                validate_capability(envelope)
                if envelope["capability_id"] != event["payload"]["capability"]["capability_id"]: raise EventLogIntegrityError("capability identity mismatch")
                result[envelope["capability_id"]] = envelope
        return result

    def verify_materialized(self) -> None:
        for capability in self.reconstruct().values():
            if self.read(capability["capability_id"], capability["version"]) != capability: raise EventLogIntegrityError("capability diverges from event history")


class CapabilityIssuer:
    def __init__(self, project_root: str | Path) -> None:
        self.store = CapabilityStore(project_root)

    def issue(self, envelope: dict[str, Any], *, event_id: str, timestamp: str, issuer_role: str = "CONTROLLER", actor_type: str = "human") -> dict[str, Any]:
        if issuer_role != "CONTROLLER" or actor_type not in {"human", "controller"}: raise CapabilityError("only an authorized controller/human path may issue capabilities")
        candidate = deepcopy(envelope)
        candidate["issued_by"] = candidate.get("issued_by", "controller")
        candidate["integrity_hash"] = _integrity_hash(candidate)
        validate_capability(candidate)
        path = self.store._path(candidate["capability_id"], candidate["version"])
        if path.exists(): raise CapabilityError("capability versions are immutable")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(canonical_json(candidate) + "\n")
        event = self.store.event_log.new_event(event_id=event_id, event_type="capability.issued", timestamp=timestamp, project_id=candidate["project_id"], actor_type=actor_type, actor_id=candidate["issued_by"], execution_id=candidate["execution_id"], payload={"capability": candidate})
        self.store.event_log.append(event)
        return candidate

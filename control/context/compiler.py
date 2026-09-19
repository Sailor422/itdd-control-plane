"""Stage E1 bounded context compilation and durable context requests."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from control.authority.paths import AuthorityError, resolve_project_path, resolve_project_root
from control.authorization import ControllerAuthorizer
from control.authorization.capabilities import CapabilityError, CapabilityStore
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json


class ContextCompilationError(ValueError):
    pass


class ContextRequestError(ValueError):
    pass


_ID = re.compile(r"^CP-[0-9]{3,}$")
_REQUEST_ID = re.compile(r"^CR-[0-9]{3,}$")
_ROLES = {"CONVERSATIONAL", "PLANNER", "GRAPH_EVALUATOR", "SCOUT", "CONTEXT_COMPILER", "BUILDER", "SPEC_VERIFIER", "STANDARDS_REVIEWER", "INTEGRATOR", "INTEGRATION_VERIFIER", "PROMOTER", "CONTROLLER"}
_REQUEST_TYPES = {"MISSING_RESOURCE", "MISSING_INTERFACE", "CLARIFICATION"}
_REQUEST_STATUSES = {"REQUESTED", "GRANTED", "DENIED", "SUPERSEDED"}


def _without_hash(document: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(document); result.pop("packet_hash", None); return result


def _packet_hash(packet: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(_without_hash(packet)).encode()).hexdigest()


def _iso(value: Any, name: str) -> None:
    try: datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc: raise ContextCompilationError(f"{name} must be ISO-8601") from exc


def _validate_resource(resource: dict[str, Any]) -> None:
    required = {"resource_id", "path", "purpose", "authority", "reason_included", "source", "freshness_or_version"}
    if not required <= set(resource): raise ContextCompilationError("resource is missing required provenance")
    if set(resource) - required - {"symbols", "line_or_section_hint", "content_hash"}: raise ContextCompilationError("resource has unknown fields")
    if not all(isinstance(resource[key], str) and resource[key] for key in required): raise ContextCompilationError("resource fields must be non-empty strings")
    if resource["authority"] not in {"READ", "WRITE", "EXECUTE"}: raise ContextCompilationError("invalid resource authority")


def validate_context_packet(packet: dict[str, Any], *, verify_hash: bool = True) -> None:
    required = {"context_packet_id", "schema_version", "project_id", "execution_id", "role", "baseline_sha", "intent_binding", "graph_binding", "eu_binding", "capability_id", "created_at", "authority_context", "working_context", "knowledge_context", "evidence_context", "context_budget", "packet_hash"}
    missing = required - set(packet)
    if missing: raise ContextCompilationError(f"packet is missing fields: {sorted(missing)}")
    if set(packet) - required - {"version", "supersedes_packet_id"}: raise ContextCompilationError("packet has unknown fields")
    if not _ID.fullmatch(packet["context_packet_id"]): raise ContextCompilationError("invalid context_packet_id")
    if packet["schema_version"] != 1 or packet.get("version", 1) < 1: raise ContextCompilationError("unsupported packet version")
    if packet["role"] not in _ROLES: raise ContextCompilationError("invalid packet role")
    for key in ("project_id", "execution_id", "baseline_sha", "capability_id"): 
        if not isinstance(packet[key], str) or not packet[key]: raise ContextCompilationError(f"{key} must be non-empty")
    _iso(packet["created_at"], "created_at")
    for key in ("intent_binding", "graph_binding", "eu_binding", "authority_context", "context_budget"):
        if not isinstance(packet[key], dict): raise ContextCompilationError(f"{key} must be an object")
    for key in ("working_context", "knowledge_context", "evidence_context"):
        if not isinstance(packet[key], list): raise ContextCompilationError(f"{key} must be a list")
        for resource in packet[key]: _validate_resource(resource)
    if not isinstance(packet["context_budget"].get("max_bytes"), int) or packet["context_budget"]["max_bytes"] < 0: raise ContextCompilationError("context budget max_bytes must be non-negative")
    if verify_hash and packet["packet_hash"] != _packet_hash(packet): raise ContextCompilationError("packet hash mismatch")


def validate_context_request(request: dict[str, Any]) -> None:
    required = {"context_request_id", "schema_version", "project_id", "execution_id", "role", "context_packet_id", "request_type", "requested_resource_or_question", "reason", "expected_use", "created_at", "status", "capability_id", "source_event_id"}
    missing = required - set(request)
    if missing: raise ContextRequestError(f"request is missing fields: {sorted(missing)}")
    if not _REQUEST_ID.fullmatch(request["context_request_id"]): raise ContextRequestError("invalid context_request_id")
    if request["schema_version"] != 1 or request["request_type"] not in _REQUEST_TYPES or request["status"] not in _REQUEST_STATUSES: raise ContextRequestError("invalid context request value")
    for key in ("project_id", "execution_id", "role", "context_packet_id", "requested_resource_or_question", "reason", "expected_use", "capability_id", "source_event_id"):
        if not isinstance(request[key], str) or not request[key]: raise ContextRequestError(f"{key} must be non-empty")
    if request["role"] not in _ROLES: raise ContextRequestError("invalid request role")
    _iso(request["created_at"], "created_at")


class ContextStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)
        self.event_log = EventLog(self.project_root)
        self.capabilities = CapabilityStore(self.project_root)

    def _packet_path(self, packet_id: str, version: int) -> Path:
        return resolve_project_path(self.project_root, f".idd/context/packets/{packet_id}/v{version}.json")

    def _request_path(self, request_id: str) -> Path:
        return resolve_project_path(self.project_root, f".idd/context/requests/{request_id}.json")

    def read_packet(self, packet_id: str, version: int = 1) -> dict[str, Any]:
        path = self._packet_path(packet_id, version)
        if not path.exists(): raise ContextCompilationError("context packet does not exist")
        packet = json.loads(path.read_text(encoding="utf-8")); validate_context_packet(packet); return packet

    def read_request(self, request_id: str) -> dict[str, Any]:
        path = self._request_path(request_id)
        if not path.exists(): raise ContextRequestError("context request does not exist")
        request = json.loads(path.read_text(encoding="utf-8")); validate_context_request(request); return request

    def reconstruct(self) -> dict[str, dict[str, Any]]:
        packets: dict[str, dict[str, Any]] = {}; requests: dict[str, dict[str, Any]] = {}
        for event in self.event_log.verify():
            if event["event_type"] == "context.packet.created":
                packet = event["payload"]["packet"]; validate_context_packet(packet)
                if packet.get("source_event_id", event["event_id"]) != event["event_id"]: raise EventLogIntegrityError("packet source event mismatch")
                packets[packet["context_packet_id"]] = packet
            elif event["event_type"] == "context.request.created":
                request = event["payload"]["request"]; validate_context_request(request)
                if request["source_event_id"] != event["event_id"]: raise EventLogIntegrityError("request source event mismatch")
                requests[request["context_request_id"]] = request
        return {"packets": packets, "requests": requests}

    def verify_materialized(self) -> None:
        state = self.reconstruct()
        for packet in state["packets"].values():
            if self.read_packet(packet["context_packet_id"], packet.get("version", 1)) != packet: raise EventLogIntegrityError("packet diverges from event history")
        for request in state["requests"].values():
            if self.read_request(request["context_request_id"]) != request: raise EventLogIntegrityError("request diverges from event history")

    def load_for_execution(self, packet_id: str, state: dict[str, Any]) -> dict[str, Any]:
        """Load only a packet whose durable bindings match the current execution."""
        self.verify_materialized()
        packet = self.read_packet(packet_id)
        for key in ("project_id", "execution_id", "baseline_sha"):
            if packet[key] != state.get(key): raise ContextCompilationError("context packet binding mismatch")
        if packet["capability_id"] not in self.capabilities.reconstruct(): raise ContextCompilationError("packet capability is not durable")
        return packet


class ContextCompiler:
    def __init__(self, project_root: str | Path) -> None:
        self.store = ContextStore(project_root)
        self.project_root = self.store.project_root
        self.authorizer = ControllerAuthorizer(self.project_root)

    def load_for_execution(self, packet_id: str, state: dict[str, Any]) -> dict[str, Any]:
        return self.store.load_for_execution(packet_id, state)

    def _capability(self, capability_id: str, state: dict[str, Any]) -> dict[str, Any]:
        capability = self.store.capabilities.reconstruct().get(capability_id)
        if capability is None: raise ContextCompilationError("capability does not exist in durable history")
        if capability["project_id"] != state.get("project_id") or capability["execution_id"] != state.get("execution_id") or capability["baseline_sha"] != state.get("baseline_sha"): raise ContextCompilationError("capability binding does not match current state")
        return capability

    def compile(self, packet: dict[str, Any], *, capability_id: str, state: dict[str, Any], event_id: str, timestamp: str) -> dict[str, Any]:
        capability = self._capability(capability_id, state)
        candidate = deepcopy(packet); candidate.update({"capability_id": capability_id, "created_at": timestamp, "project_id": capability["project_id"], "execution_id": capability["execution_id"], "role": capability["role"], "baseline_sha": capability["baseline_sha"], "schema_version": 1, "version": candidate.get("version", 1)})
        candidate.pop("packet_hash", None)
        if candidate.get("authority_context", {}).get("allowed_operations"):
            if not set(candidate["authority_context"]["allowed_operations"]) <= set(capability["allowed_operations"]): raise ContextCompilationError("packet grants authority beyond capability")
        for binding_key in ("intent_binding", "graph_binding", "eu_binding"):
            supplied = candidate.get(binding_key, {})
            if not isinstance(supplied, dict): raise ContextCompilationError(f"{binding_key} must be an object")
            for key, value in supplied.items():
                if capability["scope_bindings"].get(key) != value: raise ContextCompilationError(f"{binding_key} exceeds capability scope")
        for collection in ("working_context", "knowledge_context", "evidence_context"):
            for resource in candidate.get(collection, []):
                _validate_resource(resource)
                action = {"request_id": "context-compiler", "project_id": state["project_id"], "execution_id": state["execution_id"], "baseline_sha": state["baseline_sha"], "role": state.get("role", capability["role"]), "operation": resource["authority"], "path": resource["path"], **capability["scope_bindings"]}
                decision = self.authorizer.authorize(capability_id, action, {**state, "project_root": str(self.project_root)})
                if decision.decision != "ALLOW": raise ContextCompilationError(f"resource rejected: {decision.reason}")
                try: resource["path"] = str(resolve_project_path(self.project_root, resource["path"]))
                except AuthorityError as exc: raise ContextCompilationError("resource path is outside project root") from exc
        candidate["context_budget"] = candidate.get("context_budget", {"max_bytes": 0})
        candidate["packet_hash"] = _packet_hash(candidate)
        validate_context_packet(candidate)
        encoded = canonical_json(candidate).encode()
        if len(encoded) > candidate["context_budget"]["max_bytes"]: raise ContextCompilationError("CONTEXT_COMPILATION_FAILED: REQUIRED_CONTEXT_EXCEEDS_BUDGET")
        path = self.store._packet_path(candidate["context_packet_id"], candidate["version"])
        if path.exists(): raise ContextCompilationError("context packet versions are immutable")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(canonical_json(candidate) + "\n", encoding="utf-8")
        event = self.store.event_log.new_event(event_id=event_id, event_type="context.packet.created", timestamp=timestamp, project_id=candidate["project_id"], actor_type="controller", actor_id="context-compiler", execution_id=candidate["execution_id"], payload={"packet": candidate, "resource_count": sum(len(candidate[key]) for key in ("working_context", "knowledge_context", "evidence_context")), "packet_bytes": len(encoded)})
        self.store.event_log.append(event)
        return candidate

    def request_context(self, request: dict[str, Any], *, capability_id: str, state: dict[str, Any], event_id: str, timestamp: str) -> dict[str, Any]:
        try:
            capability = self._capability(capability_id, state)
        except ContextCompilationError as exc:
            raise ContextRequestError(str(exc)) from exc
        action = {"request_id": request["context_request_id"], "project_id": state["project_id"], "execution_id": state["execution_id"], "baseline_sha": state["baseline_sha"], "role": state.get("role", capability["role"]), "operation": "REQUEST_CONTEXT", **capability["scope_bindings"]}
        decision = self.authorizer.authorize(capability_id, action, {**state, "project_root": str(self.project_root)})
        if decision.decision != "ALLOW": raise ContextRequestError(f"context request denied: {decision.reason}")
        candidate = deepcopy(request); candidate.update({"capability_id": capability_id, "project_id": capability["project_id"], "execution_id": capability["execution_id"], "role": capability["role"], "created_at": timestamp, "status": "REQUESTED", "schema_version": 1, "source_event_id": event_id})
        validate_context_request(candidate)
        path = self.store._request_path(candidate["context_request_id"])
        if path.exists(): raise ContextRequestError("context request is immutable")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(canonical_json(candidate) + "\n", encoding="utf-8")
        event = self.store.event_log.new_event(event_id=event_id, event_type="context.request.created", timestamp=timestamp, project_id=candidate["project_id"], actor_type="controller", actor_id="context-compiler", execution_id=candidate["execution_id"], payload={"request": candidate})
        self.store.event_log.append(event)
        return candidate

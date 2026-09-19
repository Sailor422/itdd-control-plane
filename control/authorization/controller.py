"""Deterministic controller-side capability authorization."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from control.authority.paths import AuthorityError, resolve_project_path
from control.events import EventLog
from .capabilities import CapabilityError, CapabilityStore, HUMAN_ONLY, validate_capability


@dataclass(frozen=True)
class AuthorizationDecision:
    decision: str
    reason: str
    capability_id: str
    request_id: str

    def as_dict(self) -> dict[str, str]: return asdict(self)


def _deny(reason: str, capability_id: str, request_id: str) -> AuthorizationDecision:
    return AuthorizationDecision("DENY", reason, capability_id, request_id)


def authorize(capability_envelope: dict[str, Any], requested_action: dict[str, Any], current_state: dict[str, Any]) -> AuthorizationDecision:
    request_id = requested_action.get("request_id", "unknown")
    capability_id = capability_envelope.get("capability_id", "unknown")
    try: validate_capability(capability_envelope)
    except CapabilityError: return _deny("DENY_CAPABILITY_TAMPERED", capability_id, request_id)
    if requested_action.get("project_id") != capability_envelope["project_id"] or current_state.get("project_id") != capability_envelope["project_id"]: return _deny("DENY_PROJECT_MISMATCH", capability_id, request_id)
    if requested_action.get("execution_id") != capability_envelope["execution_id"] or current_state.get("execution_id") != capability_envelope["execution_id"]: return _deny("DENY_EXECUTION_MISMATCH", capability_id, request_id)
    if requested_action.get("baseline_sha") != capability_envelope["baseline_sha"] or current_state.get("baseline_sha") != capability_envelope["baseline_sha"]: return _deny("DENY_BASELINE_MISMATCH", capability_id, request_id)
    if requested_action.get("role") != capability_envelope["role"]: return _deny("DENY_ROLE_MISMATCH", capability_id, request_id)
    operation = requested_action.get("operation")
    if operation in HUMAN_ONLY and requested_action.get("actor_type") != "human": return _deny("DENY_HUMAN_ONLY", capability_id, request_id)
    if operation not in capability_envelope["allowed_operations"]: return _deny("DENY_OPERATION_NOT_GRANTED", capability_id, request_id)
    path = requested_action.get("path")
    if path is not None:
        field = {"READ": "allowed_reads", "WRITE": "allowed_writes", "CREATE_ARTIFACT": "allowed_writes", "EXECUTE": "allowed_executes"}.get(operation)
        if field is None: return _deny("DENY_PATH_NOT_GRANTED", capability_id, request_id)
        try:
            target = resolve_project_path(current_state["project_root"], path)
            grants = [resolve_project_path(current_state["project_root"], item) for item in capability_envelope[field]]
        except (AuthorityError, KeyError): return _deny("DENY_SCOPE_ESCAPE", capability_id, request_id)
        if not any(target == grant for grant in grants): return _deny("DENY_PATH_NOT_GRANTED", capability_id, request_id)
    binding = capability_envelope["scope_bindings"]
    for key in ("intent_id", "intent_version", "graph_id", "graph_version", "eu_id"):
        if key in binding and requested_action.get(key) != binding[key]: return _deny("DENY_SCOPE_ESCAPE", capability_id, request_id)
    return AuthorizationDecision("ALLOW", "ALLOW", capability_id, request_id)


class ControllerAuthorizer:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(); self.store = CapabilityStore(self.project_root); self.event_log = EventLog(self.project_root)

    def authorize(self, capability_id: str, requested_action: dict[str, Any], current_state: dict[str, Any], *, event_id: str | None = None, timestamp: str | None = None) -> AuthorizationDecision:
        try:
            self.store.verify_materialized()
            envelope = self.store.reconstruct().get(capability_id)
        except (CapabilityError, Exception) as exc:
            # A controller must fail closed if durable authority and its event
            # history diverge. Keep the public result deterministic.
            envelope = None
            decision = _deny("DENY_CAPABILITY_TAMPERED", capability_id, requested_action.get("request_id", "unknown"))
        else:
            decision = _deny("DENY_NO_CAPABILITY", capability_id, requested_action.get("request_id", "unknown")) if envelope is None else authorize(envelope, requested_action, current_state)
        if event_id:
            stamp = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            event = self.event_log.new_event(event_id=event_id, event_type="authorization.decision", timestamp=stamp, project_id=current_state["project_id"], actor_type="controller", actor_id="controller", execution_id=current_state["execution_id"], payload={"decision": decision.as_dict(), "operation": requested_action.get("operation"), "state": {"project_id": current_state["project_id"], "execution_id": current_state["execution_id"], "baseline_sha": current_state["baseline_sha"]}})
            self.event_log.append(event)
        return decision

"""Stage E2 bounded deterministic Scout/Resolver."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from control.authority.paths import AuthorityError, resolve_project_path
from control.authorization import ControllerAuthorizer
from control.authorization.capabilities import CapabilityError, CapabilityStore
from control.events import EventLog
from control.events.format import canonical_json

from .compiler import ContextCompilationError, ContextRequestError, ContextStore


class ResolutionError(ValueError):
    pass


_ID = re.compile(r"^SR-[0-9]{3,}$")
_STATUSES = {"RESOLVED", "PARTIALLY_RESOLVED", "NOT_FOUND", "AMBIGUOUS", "DENIED"}


def validate_resolution(resolution: dict[str, Any]) -> None:
    required = {"resolution_id", "schema_version", "context_request_id", "project_id", "execution_id", "baseline_sha", "scout_execution_id", "created_at", "query_or_need", "search_scope", "candidates", "selected_findings", "excluded_findings", "status", "reasoning_summary", "source_event_id"}
    missing = required - set(resolution)
    if missing: raise ResolutionError(f"resolution missing fields: {sorted(missing)}")
    if not _ID.fullmatch(resolution["resolution_id"]): raise ResolutionError("invalid resolution_id")
    if resolution["schema_version"] != 1 or resolution.get("version", 1) < 1: raise ResolutionError("unsupported resolution version")
    if resolution["status"] not in _STATUSES: raise ResolutionError("invalid resolution status")
    for key in ("context_request_id", "project_id", "execution_id", "baseline_sha", "scout_execution_id", "created_at", "query_or_need", "reasoning_summary", "source_event_id"):
        if not isinstance(resolution[key], str) or not resolution[key]: raise ResolutionError(f"{key} must be non-empty")
    if not isinstance(resolution["search_scope"], dict) or not isinstance(resolution["candidates"], list) or not isinstance(resolution["selected_findings"], list) or not isinstance(resolution["excluded_findings"], list): raise ResolutionError("resolution collections have invalid shape")
    for finding in resolution["candidates"] + resolution["selected_findings"] + resolution["excluded_findings"]:
        required_finding = {"path", "resource_type", "why_relevant", "confidence_or_match_type", "source"}
        if not required_finding <= set(finding): raise ResolutionError("finding lacks provenance")
        if set(finding) - required_finding - {"symbol", "line_or_section_hint", "content_hash_or_version", "resource_id"}: raise ResolutionError("finding has unknown fields")
        if not all(isinstance(finding[key], str) and finding[key] for key in required_finding): raise ResolutionError("finding fields must be non-empty strings")


class ScoutResolver:
    def __init__(self, project_root: str | Path) -> None:
        self.store = ContextStore(project_root)
        self.project_root = self.store.project_root
        self.authorizer = ControllerAuthorizer(self.project_root)

    def _scout_capability(self, capability_id: str, project_id: str, baseline_sha: str) -> dict[str, Any]:
        capability = self.store.capabilities.reconstruct().get(capability_id)
        if capability is None or capability["role"] != "SCOUT": raise ResolutionError("Scout capability is missing or wrong role")
        if capability["project_id"] != project_id or capability["baseline_sha"] != baseline_sha: raise ResolutionError("Scout capability project/baseline mismatch")
        if "RESOLVE_CONTEXT" not in capability["allowed_operations"] or "CREATE_ARTIFACT" not in capability["allowed_operations"]: raise ResolutionError("Scout capability lacks resolution authority")
        return capability

    def resolve(self, request_id: str, *, scout_capability_id: str, scout_state: dict[str, Any], search_scope: dict[str, Any], query_or_need: str, resolution_id: str, event_id: str, timestamp: str, budget: dict[str, int] | None = None) -> dict[str, Any]:
        requests = self.store.reconstruct()["requests"]
        request = requests.get(request_id)
        if request is None: raise ResolutionError("context request is not durable")
        if request["status"] not in {"REQUESTED", "RESOLVING"}: raise ResolutionError("context request is stale or closed")
        if request["project_id"] != scout_state.get("project_id") or request.get("baseline_sha") != scout_state.get("baseline_sha"): raise ResolutionError("request project/baseline mismatch")
        capability = self._scout_capability(scout_capability_id, request["project_id"], request.get("baseline_sha", scout_state["baseline_sha"]))
        scope_root = search_scope.get("root") if isinstance(search_scope, dict) else None
        if not isinstance(scope_root, str) or not scope_root: raise ResolutionError("search scope must name an explicit root")
        state = {**scout_state, "project_root": str(self.project_root), "role": "SCOUT"}
        decision = self.authorizer.authorize(scout_capability_id, {"request_id": request_id, "project_id": request["project_id"], "execution_id": capability["execution_id"], "baseline_sha": request.get("baseline_sha", scout_state["baseline_sha"]), "role": "SCOUT", "operation": "RESOLVE_CONTEXT", "path": scope_root, **capability["scope_bindings"]}, state)
        if decision.decision != "ALLOW": raise ResolutionError(f"search scope denied: {decision.reason}")
        try: root = resolve_project_path(self.project_root, scope_root)
        except AuthorityError as exc: raise ResolutionError("search scope escapes project") from exc
        limits = {"max_files_examined": 100, "max_bytes_examined": 100000, "max_results": 20}; limits.update(budget or {})
        if any(not isinstance(value, int) or value < 1 for value in limits.values()): raise ResolutionError("search budget must be positive integers")
        candidates: list[dict[str, Any]] = []; files_examined = 0; bytes_examined = 0; exhausted = False
        paths = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())
        query = query_or_need.strip()
        for path in paths:
            if files_examined >= limits["max_files_examined"] or bytes_examined >= limits["max_bytes_examined"] or len(candidates) >= limits["max_results"]:
                exhausted = True; break
            try: canonical = resolve_project_path(self.project_root, path)
            except AuthorityError: continue
            read_decision = self.authorizer.authorize(scout_capability_id, {"request_id": request_id, "project_id": request["project_id"], "execution_id": capability["execution_id"], "baseline_sha": request.get("baseline_sha", scout_state["baseline_sha"]), "role": "SCOUT", "operation": "READ", "path": str(canonical), **capability["scope_bindings"]}, state)
            if read_decision.decision != "ALLOW": continue
            raw = path.read_bytes(); files_examined += 1
            if bytes_examined + len(raw) > limits["max_bytes_examined"]:
                exhausted = True; break
            bytes_examined += len(raw)
            text = raw.decode("utf-8", errors="replace")
            rel = str(canonical.relative_to(self.project_root))
            if query in rel or query in text:
                candidates.append({"resource_id": f"RES-{resolution_id[3:]}-{len(candidates)+1:03d}", "path": str(canonical), "symbol": query if query in text else "", "resource_type": "source_file", "why_relevant": "deterministic filename or text match", "confidence_or_match_type": "exact_text_match" if query in text else "filename_match", "source": "deterministic_project_search", "content_hash_or_version": hashlib.sha256(raw).hexdigest()})
        if exhausted: status = "PARTIALLY_RESOLVED"
        elif not candidates: status = "NOT_FOUND"
        elif len(candidates) > 1: status = "AMBIGUOUS"
        else: status = "RESOLVED"
        selected = candidates[:1] if status == "RESOLVED" else []
        excluded = candidates[1:] if status == "RESOLVED" else []
        resolution = {"resolution_id": resolution_id, "schema_version": 1, "version": 1, "context_request_id": request_id, "project_id": request["project_id"], "execution_id": request["execution_id"], "baseline_sha": request.get("baseline_sha", scout_state["baseline_sha"]), "scout_execution_id": capability["execution_id"], "scout_capability_id": scout_capability_id, "created_at": timestamp, "query_or_need": query_or_need, "search_scope": {"root": str(root)}, "candidates": candidates, "selected_findings": selected, "excluded_findings": excluded, "status": status, "reasoning_summary": "Deterministic project-local search; no semantic retrieval or external stores used.", "search_trace": {"files_examined": files_examined, "bytes_examined": bytes_examined, "max_files_examined": limits["max_files_examined"], "max_bytes_examined": limits["max_bytes_examined"], "max_results": limits["max_results"], "budget_exhausted": exhausted}, "source_event_id": event_id}
        validate_resolution(resolution)
        path = resolve_project_path(self.project_root, f".idd/context/resolutions/{resolution_id}/v1.json")
        if path.exists(): raise ResolutionError("resolution is immutable")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(canonical_json(resolution) + "\n", encoding="utf-8")
        event = self.store.event_log.new_event(event_id=event_id, event_type="context.resolution.completed", timestamp=timestamp, project_id=request["project_id"], actor_type="scout", actor_id=capability["execution_id"], execution_id=capability["execution_id"], payload={"resolution": resolution})
        self.store.event_log.append(event)
        return resolution

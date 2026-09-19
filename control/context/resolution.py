"""Stage E2 bounded Scout resolution with optional E3 map-first lookup."""

from __future__ import annotations
import hashlib
import re
from pathlib import Path
from typing import Any
from control.authority.paths import AuthorityError, resolve_project_path
from control.authorization import ControllerAuthorizer
from control.events.format import canonical_json
from control.project_map import ProjectMapError, ProjectMapStore
from .compiler import ContextStore

class ResolutionError(ValueError): pass
_ID = re.compile(r"^SR-[0-9]{3,}$")
_STATUSES = {"RESOLVED", "PARTIALLY_RESOLVED", "NOT_FOUND", "AMBIGUOUS", "DENIED"}

def validate_resolution(resolution: dict[str, Any]) -> None:
    required = {"resolution_id", "schema_version", "context_request_id", "project_id", "execution_id", "baseline_sha", "scout_execution_id", "created_at", "query_or_need", "search_scope", "candidates", "selected_findings", "excluded_findings", "status", "reasoning_summary", "source_event_id"}
    if required - set(resolution): raise ResolutionError(f"resolution missing fields: {sorted(required - set(resolution))}")
    if set(resolution) - required - {"version", "scout_capability_id", "search_trace", "resolution_source", "project_map_id", "project_map_hash"}: raise ResolutionError("resolution has unknown fields")
    if not _ID.fullmatch(resolution["resolution_id"]): raise ResolutionError("invalid resolution_id")
    if resolution["schema_version"] != 1 or resolution.get("version", 1) < 1 or resolution["status"] not in _STATUSES: raise ResolutionError("invalid resolution value")
    for key in ("context_request_id", "project_id", "execution_id", "baseline_sha", "scout_execution_id", "created_at", "query_or_need", "reasoning_summary", "source_event_id"):
        if not isinstance(resolution[key], str) or not resolution[key]: raise ResolutionError(f"{key} must be non-empty")
    for key in ("candidates", "selected_findings", "excluded_findings"):
        if not isinstance(resolution[key], list): raise ResolutionError("resolution collections have invalid shape")
        for finding in resolution[key]:
            required_finding = {"path", "resource_type", "why_relevant", "confidence_or_match_type", "source"}
            if not required_finding <= set(finding): raise ResolutionError("finding lacks provenance")
            if set(finding) - required_finding - {"symbol", "line_or_section_hint", "content_hash_or_version", "resource_id"}: raise ResolutionError("finding has unknown fields")

class ScoutResolver:
    def __init__(self, project_root: str | Path) -> None:
        self.store = ContextStore(project_root); self.project_root = self.store.project_root
        self.authorizer = ControllerAuthorizer(self.project_root); self.project_maps = ProjectMapStore(self.project_root)

    def _scout_capability(self, capability_id: str, project_id: str, baseline_sha: str) -> dict[str, Any]:
        capability = self.store.capabilities.reconstruct().get(capability_id)
        if capability is None or capability["role"] != "SCOUT": raise ResolutionError("Scout capability is missing or wrong role")
        if capability["project_id"] != project_id or capability["baseline_sha"] != baseline_sha: raise ResolutionError("Scout capability project/baseline mismatch")
        if "RESOLVE_CONTEXT" not in capability["allowed_operations"] or "CREATE_ARTIFACT" not in capability["allowed_operations"]: raise ResolutionError("Scout capability lacks resolution authority")
        return capability

    def _persist(self, resolution: dict[str, Any], request: dict[str, Any], capability: dict[str, Any], event_id: str, timestamp: str) -> dict[str, Any]:
        validate_resolution(resolution); path = resolve_project_path(self.project_root, f".idd/context/resolutions/{resolution['resolution_id']}/v1.json")
        if path.exists(): raise ResolutionError("resolution is immutable")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(canonical_json(resolution) + "\n", encoding="utf-8")
        event = self.store.event_log.new_event(event_id=event_id, event_type="context.resolution.completed", timestamp=timestamp, project_id=request["project_id"], actor_type="scout", actor_id=capability["execution_id"], execution_id=capability["execution_id"], payload={"resolution": resolution})
        self.store.event_log.append(event); return resolution

    def resolve(self, request_id: str, *, scout_capability_id: str, scout_state: dict[str, Any], search_scope: dict[str, Any], query_or_need: str, resolution_id: str, event_id: str, timestamp: str, budget: dict[str, int] | None = None) -> dict[str, Any]:
        request = self.store.reconstruct()["requests"].get(request_id)
        if request is None: raise ResolutionError("context request is not durable")
        if request["status"] not in {"REQUESTED", "RESOLVING"}: raise ResolutionError("context request is stale or closed")
        if request["project_id"] != scout_state.get("project_id") or request.get("baseline_sha") != scout_state.get("baseline_sha"): raise ResolutionError("request project/baseline mismatch")
        baseline = request.get("baseline_sha", scout_state["baseline_sha"]); capability = self._scout_capability(scout_capability_id, request["project_id"], baseline)
        scope_root = search_scope.get("root") if isinstance(search_scope, dict) else None
        if not isinstance(scope_root, str) or not scope_root: raise ResolutionError("search scope must name an explicit root")
        state = {**scout_state, "project_root": str(self.project_root), "role": "SCOUT"}
        action = {"request_id": request_id, "project_id": request["project_id"], "execution_id": capability["execution_id"], "baseline_sha": baseline, "role": "SCOUT", "operation": "RESOLVE_CONTEXT", "path": scope_root, **capability["scope_bindings"]}
        if self.authorizer.authorize(scout_capability_id, action, state).decision != "ALLOW": raise ResolutionError("search scope denied")
        try: root = resolve_project_path(self.project_root, scope_root)
        except AuthorityError as exc: raise ResolutionError("search scope escapes project") from exc
        map_id = search_scope.get("project_map_id")
        if map_id:
            try: project_map = self.project_maps.read(map_id, expected_baseline_sha=baseline)
            except ProjectMapError as exc:
                if str(exc) == "STALE_MAP": raise ResolutionError("STALE_MAP") from exc
                project_map = None
            if project_map:
                exact = [item for item in project_map["symbols"] if item["name"] == query_or_need.strip()]
                if len(exact) == 1:
                    symbol = exact[0]; entry = next(item for item in project_map["files"] if item["file_id"] == symbol["file"])
                    finding = {"resource_id": f"RES-{resolution_id[3:]}-001", "path": entry["canonical_path"], "symbol": symbol["name"], "resource_type": "symbol", "why_relevant": "exact Project Map symbol match", "confidence_or_match_type": "exact", "source": f"project-map:{map_id}", "line_or_section_hint": str(symbol["line"]), "content_hash_or_version": entry["content_hash"]}
                    return self._persist({"resolution_id": resolution_id, "schema_version": 1, "version": 1, "context_request_id": request_id, "project_id": request["project_id"], "execution_id": request["execution_id"], "baseline_sha": baseline, "scout_execution_id": capability["execution_id"], "scout_capability_id": scout_capability_id, "created_at": timestamp, "query_or_need": query_or_need, "search_scope": {"root": str(root), "project_map_id": map_id}, "candidates": [finding], "selected_findings": [finding], "excluded_findings": [], "status": "RESOLVED", "reasoning_summary": "Exact structural match from valid current Project Map; no broader search performed.", "search_trace": {"files_examined": 0, "bytes_examined": 0, "max_files_examined": 0, "max_bytes_examined": 0, "max_results": 1, "budget_exhausted": False}, "resolution_source": "PROJECT_MAP", "project_map_id": map_id, "project_map_hash": project_map["map_hash"], "source_event_id": event_id}, request, capability, event_id, timestamp)
        limits = {"max_files_examined": 100, "max_bytes_examined": 100000, "max_results": 20}; limits.update(budget or {})
        if any(not isinstance(value, int) or value < 1 for value in limits.values()): raise ResolutionError("search budget must be positive integers")
        candidates: list[dict[str, Any]] = []; files_examined = 0; bytes_examined = 0; exhausted = False; query = query_or_need.strip()
        paths = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())
        for path in paths:
            if files_examined >= limits["max_files_examined"] or bytes_examined >= limits["max_bytes_examined"] or len(candidates) >= limits["max_results"]: exhausted = True; break
            try: canonical = resolve_project_path(self.project_root, path)
            except AuthorityError: continue
            read = self.authorizer.authorize(scout_capability_id, {"request_id": request_id, "project_id": request["project_id"], "execution_id": capability["execution_id"], "baseline_sha": baseline, "role": "SCOUT", "operation": "READ", "path": str(canonical), **capability["scope_bindings"]}, state)
            if read.decision != "ALLOW": continue
            raw = path.read_bytes(); files_examined += 1
            if bytes_examined + len(raw) > limits["max_bytes_examined"]: exhausted = True; break
            bytes_examined += len(raw); text = raw.decode("utf-8", errors="replace"); rel = str(canonical.relative_to(self.project_root))
            if query in rel or query in text: candidates.append({"resource_id": f"RES-{resolution_id[3:]}-{len(candidates)+1:03d}", "path": str(canonical), "symbol": query if query in text else "", "resource_type": "source_file", "why_relevant": "deterministic filename or text match", "confidence_or_match_type": "exact_text_match" if query in text else "filename_match", "source": "deterministic_project_search", "content_hash_or_version": hashlib.sha256(raw).hexdigest()})
        status = "PARTIALLY_RESOLVED" if exhausted else ("NOT_FOUND" if not candidates else ("AMBIGUOUS" if len(candidates) > 1 else "RESOLVED")); selected = candidates[:1] if status == "RESOLVED" else []; excluded = candidates[1:] if status == "RESOLVED" else []
        return self._persist({"resolution_id": resolution_id, "schema_version": 1, "version": 1, "context_request_id": request_id, "project_id": request["project_id"], "execution_id": request["execution_id"], "baseline_sha": baseline, "scout_execution_id": capability["execution_id"], "scout_capability_id": scout_capability_id, "created_at": timestamp, "query_or_need": query_or_need, "search_scope": {"root": str(root), **({"project_map_id": map_id} if map_id else {})}, "candidates": candidates, "selected_findings": selected, "excluded_findings": excluded, "status": status, "reasoning_summary": "Deterministic project-local search; no semantic retrieval or external stores used.", "search_trace": {"files_examined": files_examined, "bytes_examined": bytes_examined, "max_files_examined": limits["max_files_examined"], "max_bytes_examined": limits["max_bytes_examined"], "max_results": limits["max_results"], "budget_exhausted": exhausted}, "resolution_source": "DETERMINISTIC_SEARCH", "source_event_id": event_id}, request, capability, event_id, timestamp)

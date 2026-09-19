"""Stage E3 deterministic, project-local derived Project Map."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_path, resolve_project_root
from control.events.format import canonical_json
from control.models.store import StageCStore


class ProjectMapError(ValueError):
    pass


_PM_ID = re.compile(r"^PM-[0-9]{3,}$")
_SHA = re.compile(r"^[0-9a-f]{40,64}$")
_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".tox", ".mypy_cache", ".pytest_cache"}
_PRIVATE_DIRS = {"private", "secrets", "tmp", "temp"}


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _node(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def _map_hash(document: dict[str, Any]) -> str:
    copy = dict(document)
    copy.pop("map_hash", None)
    return _sha(canonical_json(copy).encode())


def _classification(relative: str) -> str:
    name = Path(relative).name.lower()
    if relative.startswith(".idd/evidence/"): return "evidence"
    if relative.startswith(".idd/"): return "ITDD state"
    if "/tests/" in f"/{relative}/" or name.startswith("test_") or name.endswith("_test.py"): return "test"
    if name.endswith((".schema.json", ".schema.yaml", ".schema.yml")): return "schema"
    if name.endswith((".md", ".rst", ".txt")): return "documentation"
    if name in {"pyproject.toml", "package.json", "requirements.txt", "setup.cfg", "makefile"} or name.startswith("."): return "configuration"
    if name.endswith((".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs")): return "source"
    return "other"


def _python_structure(path: Path, relative: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    symbols: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    tests: list[dict[str, Any]] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return symbols, relationships, tests
    file_id = _node("file", relative)
    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef): kind = "class"
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)): kind = "function"
        else: kind = None
        if kind:
            symbol_id = _node("symbol", f"{relative}#{item.name}")
            symbols.append({"symbol_id": symbol_id, "name": item.name, "kind": kind, "file": file_id, "line": item.lineno})
            relationships.append({"type": "DEFINED_IN", "from": symbol_id, "to": file_id})
            if relative.startswith("tests/") or Path(relative).name.startswith("test_"):
                tests.append({"test_file": file_id, "test_name": item.name, "target": "UNKNOWN"})
        elif isinstance(item, ast.Import):
            for alias in item.names: relationships.append({"type": "IMPORTS", "from": file_id, "to": _node("module", alias.name)})
        elif isinstance(item, ast.ImportFrom) and item.module:
            relationships.append({"type": "IMPORTS", "from": file_id, "to": _node("module", item.module)})
    return symbols, relationships, tests


def validate_project_map(document: dict[str, Any], *, expected_baseline_sha: str | None = None) -> None:
    required = {"project_map_id", "schema_version", "project_id", "baseline_sha", "created_at", "generator_version", "files", "symbols", "relationships", "intent_bindings", "graph_bindings", "test_bindings", "map_hash"}
    if set(document) != required: raise ProjectMapError("map fields do not match schema")
    if not _PM_ID.fullmatch(document["project_map_id"]): raise ProjectMapError("invalid project_map_id")
    if document["schema_version"] != 1 or not isinstance(document["project_id"], str) or not _SHA.fullmatch(document["baseline_sha"]): raise ProjectMapError("invalid map identity")
    if expected_baseline_sha is not None and document["baseline_sha"] != expected_baseline_sha: raise ProjectMapError("STALE_MAP")
    for field in ("files", "symbols", "relationships", "intent_bindings", "graph_bindings", "test_bindings"):
        if not isinstance(document[field], list): raise ProjectMapError(f"{field} must be a list")
    files = {item.get("file_id") for item in document["files"]}; symbols = {item.get("symbol_id") for item in document["symbols"]}
    modules = {item.get("to") for item in document["relationships"] if item.get("to", "").startswith("module:")}
    nodes = files | symbols | modules
    seen: set[str] = set()
    for item in document["files"]:
        if set(item) != {"file_id", "canonical_path", "relative_path", "file_type", "content_hash", "size", "classification"}: raise ProjectMapError("invalid file entry")
        if item["file_id"] in seen: raise ProjectMapError("duplicate file identity")
        seen.add(item["file_id"])
        relative = Path(item["relative_path"])
        if relative.is_absolute() or ".." in relative.parts: raise ProjectMapError("invalid relative path")
    for relationship in document["relationships"]:
        if set(relationship) != {"type", "from", "to"}: raise ProjectMapError("invalid relationship")
        if relationship["from"] not in nodes or relationship["to"] not in nodes: raise ProjectMapError("relationship references nonexistent node")
    if document["map_hash"] != _map_hash(document): raise ProjectMapError("map hash mismatch")


class ProjectMapStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)

    def path(self, project_map_id: str, version: int = 1) -> Path:
        return resolve_project_path(self.project_root, f".idd/project_map/{project_map_id}/v{version}.json")

    def read(self, project_map_id: str, *, expected_baseline_sha: str | None = None) -> dict[str, Any]:
        path = self.path(project_map_id)
        if not path.exists(): raise ProjectMapError("project map does not exist")
        try: document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise ProjectMapError("project map is unreadable") from exc
        validate_project_map(document, expected_baseline_sha=expected_baseline_sha)
        return document

    def verify_materialized(self, project_map_id: str, *, expected_baseline_sha: str | None = None) -> None:
        self.read(project_map_id, expected_baseline_sha=expected_baseline_sha)


class ProjectMapBuilder:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)
        self.store = ProjectMapStore(self.project_root)

    def _excluded(self, path: Path, relative: str) -> bool:
        if path.is_symlink(): return True
        parts = set(Path(relative).parts)
        if parts & (_SKIP_DIRS | _PRIVATE_DIRS): return True
        if path.is_dir() and (path / ".git").is_dir(): return True
        return relative.startswith((".idd/project_map/", ".codex/", ".claude/", ".hermes/")) or Path(relative).name in {".env", ".env.local", ".env.secret"}

    def build(self, *, project_map_id: str, project_id: str, baseline_sha: str, created_at: str, generator_version: str = "e3-v1") -> dict[str, Any]:
        if not _PM_ID.fullmatch(project_map_id) or not _SHA.fullmatch(baseline_sha): raise ProjectMapError("invalid map identity")
        state = StageCStore(self.project_root).reconstruct(); intent = state.get("approved_intent"); graph = state.get("active_graph")
        if intent and intent["project_id"] != project_id: raise ProjectMapError("intent project mismatch")
        if graph and graph["project_id"] != project_id: raise ProjectMapError("graph project mismatch")
        files: list[dict[str, Any]] = []; symbols: list[dict[str, Any]] = []; relationships: list[dict[str, Any]] = []; tests: list[dict[str, Any]] = []
        for root, dirs, names in os.walk(self.project_root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not self._excluded(Path(root) / d, str((Path(root) / d).relative_to(self.project_root))))
            for name in sorted(names):
                path = Path(root) / name; relative = path.relative_to(self.project_root).as_posix()
                if self._excluded(path, relative) or not path.is_file(): continue
                raw = path.read_bytes(); file_id = _node("file", relative)
                files.append({"file_id": file_id, "canonical_path": str(path.resolve()), "relative_path": relative, "file_type": path.suffix.lower() or "<none>", "content_hash": _sha(raw), "size": len(raw), "classification": _classification(relative)})
                if path.suffix == ".py":
                    found_symbols, found_relationships, found_tests = _python_structure(path, relative); symbols.extend(found_symbols); relationships.extend(found_relationships); tests.extend(found_tests)
        modules = {Path(item["relative_path"]).with_suffix("").as_posix().replace("/", "."): item["file_id"] for item in files if item["relative_path"].endswith(".py")}
        for relationship in relationships:
            if relationship["type"] == "IMPORTS" and relationship["to"].split(":", 1)[1] in modules: relationship["to"] = modules[relationship["to"].split(":", 1)[1]]
        intent_bindings: list[dict[str, Any]] = []; graph_bindings: list[dict[str, Any]] = []
        if intent and graph:
            for node in graph["nodes"]:
                for req in sorted(node["requirement_ids"]): intent_bindings.append({"requirement_id": req, "eu_id": node["eu_id"], "intent_id": intent["intent_id"], "intent_version": intent["version"]})
            graph_bindings = [{"from": edge["from"], "to": edge["to"], "graph_id": graph["graph_id"], "graph_version": graph["version"]} for edge in graph["edges"]]
        document = {"project_map_id": project_map_id, "schema_version": 1, "project_id": project_id, "baseline_sha": baseline_sha, "created_at": created_at, "generator_version": generator_version, "files": sorted(files, key=lambda x: x["relative_path"]), "symbols": sorted(symbols, key=lambda x: x["symbol_id"]), "relationships": sorted(relationships, key=lambda x: (x["type"], x["from"], x["to"])), "intent_bindings": sorted(intent_bindings, key=lambda x: (x["requirement_id"], x["eu_id"])), "graph_bindings": sorted(graph_bindings, key=lambda x: (x["from"], x["to"])), "test_bindings": sorted(tests, key=lambda x: (x["test_file"], x["test_name"])), "map_hash": ""}
        document["map_hash"] = _map_hash(document); validate_project_map(document, expected_baseline_sha=baseline_sha); return document

    def write(self, document: dict[str, Any]) -> dict[str, Any]:
        validate_project_map(document); path = self.store.path(document["project_map_id"]); path.parent.mkdir(parents=True, exist_ok=True); encoded = canonical_json(document) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != encoded: raise ProjectMapError("project map artifact is immutable")
        if not path.exists(): path.write_text(encoded, encoding="utf-8")
        return document

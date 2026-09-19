"""Versioned execution graph model and semantic validation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class GraphValidationError(ValueError):
    """Raised when a graph is malformed or violates intent binding rules."""


REQUIRED_KEYS = {
    "graph_id",
    "version",
    "project_id",
    "intent_id",
    "intent_version",
    "status",
    "created_at",
    "created_by",
    "nodes",
    "edges",
    "reason",
    "source_event_id",
    "schema_version",
}
OPTIONAL_KEYS = {"previous_version"}


def _timestamp(value: Any) -> None:
    if not isinstance(value, str):
        raise GraphValidationError("created_at must be ISO-8601")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GraphValidationError("created_at must be ISO-8601") from exc


def validate_graph(graph: dict[str, Any], intent: dict[str, Any]) -> None:
    if not isinstance(graph, dict):
        raise GraphValidationError("graph must be an object")
    missing = REQUIRED_KEYS - set(graph)
    if missing:
        raise GraphValidationError(f"missing required keys: {sorted(missing)}")
    unknown = set(graph) - REQUIRED_KEYS - OPTIONAL_KEYS
    if unknown:
        raise GraphValidationError(f"unknown keys: {sorted(unknown)}")
    if not isinstance(graph["graph_id"], str) or not re.fullmatch(r"G-[0-9]+", graph["graph_id"]):
        raise GraphValidationError("graph_id must use G-NNN identity")
    if not isinstance(graph["version"], int) or graph["version"] < 1:
        raise GraphValidationError("version must be a positive integer")
    if graph["status"] != "ACTIVE":
        raise GraphValidationError("Stage C graph status must be ACTIVE")
    _timestamp(graph["created_at"])
    for field in ("project_id", "intent_id", "created_by", "reason", "source_event_id"):
        if not isinstance(graph[field], str) or not graph[field].strip():
            raise GraphValidationError(f"{field} must be a non-empty string")
    if graph["schema_version"] != 1:
        raise GraphValidationError("unsupported graph schema_version")
    if graph["project_id"] != intent["project_id"] or graph["intent_id"] != intent["intent_id"]:
        raise GraphValidationError("graph is bound to the wrong project or intent")
    if graph["intent_version"] != intent["version"]:
        raise GraphValidationError("graph is bound to the wrong intent version")
    if graph["version"] == 1 and graph.get("previous_version") is not None:
        raise GraphValidationError("initial graph cannot have previous_version")
    if graph["version"] > 1 and graph.get("previous_version") != graph["version"] - 1:
        raise GraphValidationError("graph revision must identify the immediately previous version")
    requirement_ids = {item["requirement_id"] for item in intent["requirements"]}
    if not isinstance(graph["nodes"], list):
        raise GraphValidationError("nodes must be a list")
    node_ids: set[str] = set()
    for node in graph["nodes"]:
        if not isinstance(node, dict) or set(node) != {"eu_id", "requirement_ids"}:
            raise GraphValidationError("each node must contain eu_id and requirement_ids")
        eu_id = node["eu_id"]
        if not isinstance(eu_id, str) or not re.fullmatch(r"EU-[0-9]+", eu_id):
            raise GraphValidationError("eu_id must use EU-NNN identity")
        if eu_id in node_ids:
            raise GraphValidationError(f"duplicate EU identity: {eu_id}")
        node_ids.add(eu_id)
        refs = node["requirement_ids"]
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) for ref in refs):
            raise GraphValidationError("requirement_ids must be a non-empty list of strings")
        if not set(refs) <= requirement_ids:
            raise GraphValidationError("node references a nonexistent requirement")
    if not isinstance(graph["edges"], list):
        raise GraphValidationError("edges must be a list")
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for edge in graph["edges"]:
        if not isinstance(edge, dict) or set(edge) != {"from", "to"}:
            raise GraphValidationError("each edge must contain from and to")
        source, target = edge["from"], edge["to"]
        if source not in node_ids or target not in node_ids:
            raise GraphValidationError("edge references a nonexistent EU")
        if source == target:
            raise GraphValidationError("self-dependency is not allowed")
        adjacency[source].add(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise GraphValidationError("cyclic graph is not allowed")
        if node_id in visited:
            return
        visiting.add(node_id)
        for child in adjacency[node_id]:
            visit(child)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in node_ids:
        visit(node_id)


"""Durable Stage C intent/graph artifacts integrated with the Stage B event log."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_path, resolve_project_root
from control.events import EventLog, EventLogIntegrityError, reconstruct_state as reconstruct_events
from control.events.format import canonical_json

from .graph import GraphValidationError, validate_graph
from .intent import IntentValidationError, validate_intent


class StageCError(ValueError):
    """Base error for Stage C control operations."""


class ImmutableIntentError(StageCError):
    """Raised when normal APIs try to mutate an approved intent version."""


class AgentApprovalError(StageCError):
    """Raised when an agent attempts a human-only approval operation."""


class ArtifactMutationError(StageCError):
    """Raised when an immutable artifact path would be overwritten."""


class StageCStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)
        self.event_log = EventLog(self.project_root)

    def _path(self, kind: str, identity: str, version: int) -> Path:
        return resolve_project_path(self.project_root, f".idd/{kind}/{identity}/v{version}.json")

    @staticmethod
    def _write_new(path: Path, document: dict[str, Any]) -> None:
        serialized = canonical_json(document) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != serialized:
                raise ArtifactMutationError(f"immutable artifact would be overwritten: {path}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")

    @staticmethod
    def _write_transition(path: Path, document: dict[str, Any], old_status: str) -> None:
        if not path.exists():
            raise StageCError(f"artifact does not exist: {path}")
        current = json.loads(path.read_text(encoding="utf-8"))
        if current.get("status") != old_status:
            raise ImmutableIntentError("approved intent cannot be mutated")
        path.write_text(canonical_json(document) + "\n", encoding="utf-8")

    def _append_transition(
        self,
        *,
        event_id: str,
        event_type: str,
        timestamp: str,
        actor_type: str,
        actor_id: str,
        project_id: str,
        payload: dict[str, Any],
    ) -> None:
        event = self.event_log.new_event(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload,
        )
        self.event_log.append(event)

    def create_intent_draft(self, intent: dict[str, Any], *, event_id: str, timestamp: str, actor_type: str, actor_id: str) -> None:
        validate_intent(intent)
        if intent["status"] != "DRAFT" or intent["created_at"] != timestamp or intent["created_by"] != actor_id:
            raise IntentValidationError("draft must carry its creation timestamp and actor")
        if intent["source_event_id"] != event_id:
            raise IntentValidationError("source_event_id must identify the creation event")
        path = self._path("intent", intent["intent_id"], intent["version"])
        self._write_new(path, intent)
        self._append_transition(
            event_id=event_id, event_type="intent.draft.created", timestamp=timestamp,
            actor_type=actor_type, actor_id=actor_id, project_id=intent["project_id"], payload={"intent": intent}
        )
        # Reaching a draft intent creates a project-local HUMAN_ONLY review package.
        # The import is local to keep the Stage C model independent at module load.
        from control.human_decisions import HumanDecisionController, next_decision_id
        HumanDecisionController(self.project_root).create_intent(
            decision_id=next_decision_id(self.project_root), intent_id=intent["intent_id"],
            version=intent["version"], timestamp=timestamp,
        )

    def update_draft(self, intent: dict[str, Any], *, event_id: str, timestamp: str, actor_type: str, actor_id: str) -> None:
        validate_intent(intent)
        current = self.read_intent(intent["intent_id"], intent["version"])
        if current["status"] != "DRAFT":
            raise ImmutableIntentError("approved intent cannot be mutated")
        if intent["intent_id"] != current["intent_id"] or intent["version"] != current["version"]:
            raise ImmutableIntentError("intent identity cannot change")
        if intent["source_event_id"] != current["source_event_id"]:
            raise ImmutableIntentError("intent source identity cannot change")
        if intent["status"] != "DRAFT" or intent["created_by"] != current["created_by"]:
            raise IntentValidationError("draft update cannot change lifecycle authority")
        self._write_transition(self._path("intent", intent["intent_id"], intent["version"]), intent, "DRAFT")
        self._append_transition(
            event_id=event_id, event_type="intent.draft.updated", timestamp=timestamp,
            actor_type=actor_type, actor_id=actor_id, project_id=intent["project_id"], payload={"intent": intent}
        )

    def approve_intent(self, intent_id: str, version: int, *, event_id: str, timestamp: str, actor_type: str, actor_id: str) -> None:
        if actor_type != "human":
            raise AgentApprovalError("only a human actor may approve intent")
        path = self._path("intent", intent_id, version)
        intent = self.read_intent(intent_id, version)
        if intent["status"] != "DRAFT":
            raise ImmutableIntentError("only a draft intent may be approved")
        approved = deepcopy(intent)
        approved.update({"status": "APPROVED", "approved_by": actor_id, "approved_at": timestamp, "approval_event_id": event_id})
        validate_intent(approved)
        self._write_transition(path, approved, "DRAFT")
        self._append_transition(
            event_id=event_id, event_type="intent.approved", timestamp=timestamp,
            actor_type=actor_type, actor_id=actor_id, project_id=intent["project_id"], payload={"intent": approved}
        )

    def read_intent(self, intent_id: str, version: int) -> dict[str, Any]:
        path = self._path("intent", intent_id, version)
        if not path.exists():
            raise StageCError(f"intent does not exist: {intent_id} v{version}")
        intent = json.loads(path.read_text(encoding="utf-8"))
        validate_intent(intent)
        return intent

    def create_graph(self, graph: dict[str, Any], *, event_id: str, timestamp: str, actor_type: str, actor_id: str) -> None:
        intent = self.read_intent(graph["intent_id"], graph["intent_version"])
        if intent["status"] != "APPROVED":
            raise GraphValidationError("graph must bind to an approved intent")
        validate_graph(graph, intent)
        if graph["version"] != 1 or graph["created_at"] != timestamp or graph["created_by"] != actor_id:
            raise GraphValidationError("initial graph must carry version, timestamp, and actor")
        if graph["source_event_id"] != event_id:
            raise GraphValidationError("source_event_id must identify the graph event")
        self._write_new(self._path("graph", graph["graph_id"], graph["version"]), graph)
        self._append_transition(
            event_id=event_id, event_type="graph.created", timestamp=timestamp,
            actor_type=actor_type, actor_id=actor_id, project_id=graph["project_id"], payload={"graph": graph}
        )

    def revise_graph(self, graph: dict[str, Any], *, event_id: str, timestamp: str, actor_type: str, actor_id: str) -> None:
        previous = self.read_graph(graph["graph_id"], graph["version"] - 1)
        intent = self.read_intent(previous["intent_id"], previous["intent_version"])
        if intent["status"] != "APPROVED":
            raise GraphValidationError("graph must bind to an approved intent")
        validate_graph(graph, intent)
        if graph["project_id"] != previous["project_id"] or graph["intent_id"] != previous["intent_id"] or graph["intent_version"] != previous["intent_version"]:
            raise GraphValidationError("graph revision cannot change its intent binding")
        if graph["created_at"] != timestamp or graph["created_by"] != actor_id or graph["source_event_id"] != event_id:
            raise GraphValidationError("revision must carry its event timestamp, actor, and identity")
        self._write_new(self._path("graph", graph["graph_id"], graph["version"]), graph)
        self._append_transition(
            event_id=event_id, event_type="graph.revised", timestamp=timestamp,
            actor_type=actor_type, actor_id=actor_id, project_id=graph["project_id"],
            payload={"graph": graph, "previous_version": previous["version"]}
        )

    def read_graph(self, graph_id: str, version: int) -> dict[str, Any]:
        path = self._path("graph", graph_id, version)
        if not path.exists():
            raise StageCError(f"graph does not exist: {graph_id} v{version}")
        graph = json.loads(path.read_text(encoding="utf-8"))
        intent = self.read_intent(graph["intent_id"], graph["intent_version"])
        validate_graph(graph, intent)
        return graph

    def reconstruct(self) -> dict[str, Any]:
        records = self.event_log.verify()
        intents: dict[tuple[str, int], dict[str, Any]] = {}
        graphs: dict[tuple[str, int], dict[str, Any]] = {}
        active_graph_key: tuple[str, int] | None = None
        for record in records:
            payload = record["payload"]
            if record["event_type"] in {"intent.draft.created", "intent.draft.updated", "intent.approved"}:
                intent = payload["intent"]
                validate_intent(intent)
                if record["event_type"] == "intent.draft.created" and intent["source_event_id"] != record["event_id"]:
                    raise EventLogIntegrityError("intent creation source event mismatch")
                if record["event_type"] == "intent.approved":
                    if record["actor_type"] != "human":
                        raise EventLogIntegrityError("intent approval event is not human-authorized")
                    if intent.get("approval_event_id") != record["event_id"]:
                        raise EventLogIntegrityError("intent approval event identity mismatch")
                intents[(intent["intent_id"], intent["version"])] = intent
            elif record["event_type"] in {"graph.created", "graph.revised"}:
                graph = payload["graph"]
                if graph["source_event_id"] != record["event_id"]:
                    raise EventLogIntegrityError("graph source event mismatch")
                intent = intents.get((graph["intent_id"], graph["intent_version"]))
                if intent is None:
                    raise EventLogIntegrityError("graph references intent absent from event history")
                validate_graph(graph, intent)
                graphs[(graph["graph_id"], graph["version"])] = graph
                active_graph_key = (graph["graph_id"], graph["version"])
        approved = [intent for intent in intents.values() if intent["status"] == "APPROVED"]
        active = graphs.get(active_graph_key) if active_graph_key else None
        return {
            "intents": intents,
            "approved_intent": approved[-1] if approved else None,
            "graphs": graphs,
            "active_graph": active,
        }

    def verify_materialized_artifacts(self) -> None:
        state = self.reconstruct()
        for intent in state["intents"].values():
            actual = self.read_intent(intent["intent_id"], intent["version"])
            if actual != intent:
                raise EventLogIntegrityError("intent artifact diverges from event history")
        for graph in state["graphs"].values():
            actual = self.read_graph(graph["graph_id"], graph["version"])
            if actual != graph:
                raise EventLogIntegrityError("graph artifact diverges from event history")

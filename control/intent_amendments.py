"""Explicit, append-only Intent Amendments for genuinely new authority.

An amendment is separate from an approved intent version.  Creating one never
rewrites the approved intent, graph history, evidence, gates, or decisions.
The amendment becomes authoritative only after its own HUMAN_ONLY decision is
consumed by the controller.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_path, resolve_project_root
from control.events import EventLog
from control.events.format import canonical_json
from control.human_decisions import HumanDecisionController, next_decision_id
from control.models.store import StageCStore


class IntentAmendmentError(ValueError):
    pass


_AMENDMENT_ID = re.compile(r"^IA-[0-9]{3,}$")
_STATUSES = {"PENDING", "APPROVED", "REJECTED", "CHANGES_REQUESTED"}


def validate_amendment(amendment: dict[str, Any]) -> None:
    required = {
        "amendment_id", "schema_version", "status", "project_id", "source_intent",
        "amendment_version", "created_at", "created_by", "authority_change",
        "preserved_scope", "source_event_id",
    }
    if set(amendment) != required:
        raise IntentAmendmentError("intent amendment fields do not match schema")
    if not isinstance(amendment["amendment_id"], str) or not _AMENDMENT_ID.fullmatch(amendment["amendment_id"]):
        raise IntentAmendmentError("invalid amendment identity")
    if amendment["schema_version"] != 1 or amendment["status"] not in _STATUSES:
        raise IntentAmendmentError("invalid amendment state")
    if not isinstance(amendment["amendment_version"], int) or amendment["amendment_version"] < 1:
        raise IntentAmendmentError("invalid amendment version")
    for key in ("project_id", "created_at", "created_by", "source_event_id"):
        if not isinstance(amendment[key], str) or not amendment[key].strip():
            raise IntentAmendmentError(f"{key} must be non-empty")
    source = amendment["source_intent"]
    if set(source) != {"intent_id", "version"} or not isinstance(source["intent_id"], str) or not isinstance(source["version"], int):
        raise IntentAmendmentError("invalid source intent binding")
    change = amendment["authority_change"]
    if set(change) != {"removed_language", "replacement_language", "human_authority_after_approval"}:
        raise IntentAmendmentError("invalid authority change")
    if not all(isinstance(change[key], (str, list)) for key in change):
        raise IntentAmendmentError("authority change values must be text or lists")
    if not isinstance(amendment["preserved_scope"], dict):
        raise IntentAmendmentError("preserved scope must be an object")


class IntentAmendmentStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)

    def path(self, amendment_id: str, version: int) -> Path:
        if not _AMENDMENT_ID.fullmatch(amendment_id) or version < 1:
            raise IntentAmendmentError("invalid amendment identity")
        return resolve_project_path(self.project_root, f".idd/intent_amendments/{amendment_id}/v{version}.json")

    def read(self, amendment_id: str, version: int) -> dict[str, Any]:
        path = self.path(amendment_id, version)
        if not path.exists():
            raise IntentAmendmentError("intent amendment does not exist")
        value = json.loads(path.read_text(encoding="utf-8"))
        validate_amendment(value)
        return value

    def create(self, amendment: dict[str, Any]) -> Path:
        validate_amendment(amendment)
        path = self.path(amendment["amendment_id"], amendment["amendment_version"])
        if path.exists():
            raise IntentAmendmentError("amendment identity already exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(amendment) + "\n", encoding="utf-8")
        return path

    def update_status(self, amendment_id: str, version: int, status: str) -> dict[str, Any]:
        if status not in _STATUSES - {"PENDING"}:
            raise IntentAmendmentError("invalid amendment transition")
        current = self.read(amendment_id, version)
        if current["status"] != "PENDING":
            raise IntentAmendmentError("amendment is no longer pending")
        updated = deepcopy(current)
        updated["status"] = status
        self.path(amendment_id, version).write_text(canonical_json(updated) + "\n", encoding="utf-8")
        return updated


class IntentAmendmentController:
    """Create and, later, consume authority amendments without auto-approval."""

    REMOVED_LANGUAGE = [
        "HUMAN_ONLY verified-work approval is required for each eligible EU as applicable.",
        "HUMAN_ONLY integration approval is required before promoting the integrated result.",
        "The approved intent's routine lifecycle checkpoints treated graph activation, EU progression, verification, integration, and promotion as HUMAN_ONLY decisions.",
    ]
    REPLACEMENT_LANGUAGE = (
        "HUMAN DEVELOPS INTENT\n"
        "→ HUMAN APPROVES INTENT\n"
        "→ APPROVAL AUTHORIZES THE CONTROLLER TO RUN THE STACK AUTONOMOUSLY TO COMPLETION"
    )
    CONTROLLER_OWNED = [
        "graph activation", "EU scheduling and progression", "Builder completion",
        "controller-owned candidate creation", "Git attestation", "Spec Verifier execution/results",
        "Standards Reviewer execution/results", "EU verification/eligibility", "integration eligibility",
        "Integrator execution", "Integration Verifier execution/results", "successful integration",
        "promotion when already authorized by the approved intent", "completion", "bounded retry/recovery",
        "replanning that remains within the approved destination",
    ]
    HUMAN_AFTER_APPROVAL = [
        "an Intent Amendment that changes approved authority, destination, requirements, or constraints",
        "explicit control-plane maintenance authority", "break-glass authority",
        "another genuine unresolved authority question that cannot be resolved from the approved intent",
    ]

    # These are lifecycle authority claims, not project or gate identities.  An
    # approved amendment can retire a waiting gate only when it explicitly
    # removes the claim that created that gate.
    ROUTINE_GATE_AUTHORITY = {
        "VERIFIED_EU_REVIEW": "HUMAN_ONLY verified-work approval is required for each eligible EU as applicable.",
        "INTEGRATION_APPROVAL": "HUMAN_ONLY integration approval is required before promoting the integrated result.",
    }

    def __init__(self, project_root: str | Path, *, controller_execution_id: str = "EXEC-CONTROLLER-001") -> None:
        self.project_root = resolve_project_root(project_root)
        self.store = IntentAmendmentStore(self.project_root)
        self.events = EventLog(self.project_root)
        self.execution_id = controller_execution_id

    def create_authority_amendment(
        self, *, amendment_id: str, source_intent_id: str, source_intent_version: int,
        timestamp: str, decision_id: str | None = None, open_document: bool = False,
    ) -> tuple[Path, Path]:
        source = StageCStore(self.project_root).read_intent(source_intent_id, source_intent_version)
        if source["status"] != "APPROVED":
            raise IntentAmendmentError("only an approved intent may receive an amendment")
        amendment = {
            "amendment_id": amendment_id, "schema_version": 1, "status": "PENDING",
            "project_id": source["project_id"],
            "source_intent": {"intent_id": source_intent_id, "version": source_intent_version},
            "amendment_version": 1, "created_at": timestamp, "created_by": "controller",
            "authority_change": {
                "removed_language": self.REMOVED_LANGUAGE,
                "replacement_language": self.REPLACEMENT_LANGUAGE,
                "human_authority_after_approval": self.HUMAN_AFTER_APPROVAL,
            },
            "preserved_scope": {
                "destination": source["purpose"],
                "title": source["title"],
                "purpose": source["purpose"],
                "requirements": source["requirements"],
                "constraints": source["constraints"],
                "acceptance_summary": source["acceptance_summary"],
                "approved_intent": {"intent_id": source_intent_id, "version": source_intent_version},
                "completed_eu_work": ["EU-001", "EU-002"],
                "graph_history": [{"graph_id": "G-1001", "versions": [1, 2]}],
                "verified_integration": {
                    "integration_id": "IN-1001", "status": "VERIFIED",
                    "candidate_sha": "294ac19a13d6b09bd33f132edc3efea1020d444c",
                    "tree": "904354bc804787b03b7e2fe003bd80f4f1aa08a5",
                    "verifier_result": "VR-782653990",
                },
                "historical_records": ["HG-14001", "HD-007"],
            },
            "source_event_id": f"intent-amendment-{amendment_id}-created",
        }
        path = self.store.create(amendment)
        event = self.events.new_event(
            event_id=amendment["source_event_id"], event_type="intent.amendment.created",
            timestamp=timestamp, project_id=source["project_id"], actor_type="controller",
            actor_id="controller", execution_id=self.execution_id, payload={"amendment": amendment},
        )
        self.events.append(event)
        decision_id = decision_id or next_decision_id(self.project_root)
        decision = HumanDecisionController(self.project_root, controller_execution_id=self.execution_id).create_amendment(
            decision_id=decision_id, amendment=amendment, source_intent=source,
            timestamp=timestamp, open_document=open_document,
        )
        return path, decision

    def reconcile_obsolete_gates(self, amendment: dict[str, Any], *, timestamp: str) -> list[dict[str, Any]]:
        """Retire waiting gates whose authority basis was removed by *amendment*.

        The transition is an event, and the gate carries the exact amendment
        binding.  Human Decision documents are deliberately not read or
        consumed here: their historical response surface remains preserved.
        """
        validate_amendment(amendment)
        if amendment["status"] != "APPROVED":
            raise IntentAmendmentError("only an approved amendment can reconcile gates")
        from control.human import HumanGateStore

        removed = set(amendment["authority_change"]["removed_language"])
        binding = {"amendment_id": amendment["amendment_id"], "amendment_version": amendment["amendment_version"]}
        gates = HumanGateStore(self.project_root)
        retired = []
        for gate_id, gate in gates.reconstruct().items():
            if gate["status"] != "WAITING" or gate["project_id"] != amendment["project_id"]:
                continue
            if gate.get("related_intent") != amendment["source_intent"]:
                continue
            authority = self.ROUTINE_GATE_AUTHORITY.get(gate["gate_type"])
            if authority not in removed:
                continue
            if gate.get("superseded_by") == binding:
                retired.append(gate)
                continue
            retired.append(gates.supersede(
                gate, event_id=f"intent-amendment-{amendment['amendment_id']}-gate-{gate_id}-superseded",
                timestamp=timestamp, superseded_by=binding, reason="AUTHORITY_REMOVED_BY_APPROVED_INTENT_AMENDMENT",
            ))
        return retired

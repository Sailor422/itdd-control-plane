"""Project-local, controller-owned HUMAN_ONLY decision documents.

Only files in ``.idd/human_decisions`` with the signed metadata marker below
have response semantics.  The ordinary Markdown projection is deliberately
not parsed by this module.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_path, resolve_project_root
from control.events import EventLog
from control.events.format import canonical_json
from control.human import HumanGateController, HumanGateStore, HumanViewGenerator
from control.models.store import StageCStore


class HumanDecisionError(ValueError):
    pass


DECISIONS = {"PENDING", "APPROVE", "REJECT", "CHANGES_REQUESTED"}
SCHEMA_VERSION = 1
_MARKER = re.compile(r"^<!-- ITDD-HUMAN-DECISION (?P<meta>\{.*\}) -->$", re.MULTILINE)
_DECISION_ID = re.compile(r"^HD-[0-9]{3,}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _head(events: EventLog) -> tuple[str | None, str | None]:
    records = events.verify()
    return ((records[-1]["event_id"], records[-1]["event_hash"]) if records else (None, None))


def next_decision_id(project_root: str | Path) -> str:
    root = resolve_project_root(project_root) / ".idd/human_decisions"
    ids = [int(match.group(1)) for path in root.glob("**/HD-*.md") if (match := re.fullmatch(r"HD-(\d+)", path.stem))]
    return f"HD-{max(ids or [0]) + 1:03d}"


class HumanDecisionStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)
        self.events = EventLog(self.project_root)

    @property
    def root(self) -> Path:
        return resolve_project_path(self.project_root, ".idd/human_decisions")

    @property
    def registry(self) -> Path:
        return self.root / "registry"

    def path(self, decision_id: str, *, resolved: bool = False) -> Path:
        if not _DECISION_ID.fullmatch(decision_id):
            raise HumanDecisionError("invalid decision document identity")
        return self.root / ("resolved" if resolved else "pending") / f"{decision_id}.md"

    def superseded_path(self, decision_id: str) -> Path:
        return self.root / "superseded" / f"{decision_id}.json"

    def _locate(self, decision_id: str) -> Path:
        candidates = [self.path(decision_id), self.path(decision_id, resolved=True)]
        found = [path for path in candidates if path.exists()]
        if len(found) != 1:
            raise HumanDecisionError("decision document is missing or duplicated")
        return found[0]

    @staticmethod
    def _normalize_decision(value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in DECISIONS:
            raise HumanDecisionError("decision must be PENDING, APPROVE, REJECT, or CHANGES_REQUESTED")
        return normalized

    @classmethod
    def _parse_response(cls, text: str, *, allow_unclosed_resolved: bool = False) -> tuple[str, str]:
        # Prefer the last bounded editable area. This makes repaired documents
        # deterministic even when the damaged text contains old fragments.
        bounded = re.findall(r"EDIT ONLY BELOW THIS LINE\s*\n(?P<body>.*?)\nEDIT ONLY ABOVE THIS LINE", text, re.IGNORECASE | re.DOTALL)
        if bounded:
            section = bounded[-1]
        elif allow_unclosed_resolved and "EDIT ONLY BELOW THIS LINE" in text:
            # Older resolved packages may have lost their closing marker due
            # to the historical resolution rewrite bug.  This compatibility
            # path is limited to already-resolved documents; pending files
            # remain fail-closed and repairable.
            section = text[text.rfind("EDIT ONLY BELOW THIS LINE"):]
        else:
            section = text[text.rfind("# YOUR RESPONSE"):] if "# YOUR RESPONSE" in text else ""
        match = re.search(r"^\s*(?:[-*>]\s*)?Decision:\s*([^\r\n]+)\s*$", section, re.IGNORECASE | re.MULTILINE)
        if not match:
            raise HumanDecisionError("MALFORMED_RESPONSE: repair available")
        decision = cls._normalize_decision(match.group(1))
        comment_match = re.search(r"^\s*(?:[-*>]\s*)?Comment:\s*([^\r\n]*)", section, re.IGNORECASE | re.MULTILINE)
        comment = comment_match.group(1).strip() if comment_match else ""
        return decision, ("" if comment == "---" else comment)

    def read(self, decision_id: str) -> dict[str, Any]:
        path = self._locate(decision_id)
        text = path.read_text(encoding="utf-8")
        marker = _MARKER.search(text)
        if not marker:
            raise HumanDecisionError("file is not an ITDD human decision document")
        try:
            metadata = json.loads(marker.group("meta"))
        except json.JSONDecodeError as exc:
            raise HumanDecisionError("invalid decision metadata") from exc
        if metadata.get("schema_version") != SCHEMA_VERSION or metadata.get("decision_id") != decision_id:
            raise HumanDecisionError("decision metadata identity/schema mismatch")
        registry = self.registry / f"{decision_id}.json"
        registered = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else None
        # The registry binds creator-owned identity and subject fields.  A
        # resolved document legitimately adds controller-owned resolution
        # fields (status, event, decision, comment, timestamp) after the
        # human response is consumed; those fields must not invalidate the
        # original immutable binding.
        immutable_registry = {
            key: value for key, value in (registered or {}).items()
            if key != "status"
        }
        if not isinstance(registered, dict) or any(metadata.get(key) != value for key, value in immutable_registry.items()):
            raise HumanDecisionError("decision metadata does not match controller registry")
        decision, comment = self._parse_response(text, allow_unclosed_resolved=path.parent.name == "resolved")
        metadata["response_decision"] = decision
        metadata["response_comment"] = comment
        metadata["path"] = str(path)
        metadata["resolved"] = path.parent.name == "resolved"
        return metadata

    def create(self, metadata: dict[str, Any], *, review_body: str) -> Path:
        decision_id = metadata.get("decision_id")
        if not isinstance(decision_id, str) or not _DECISION_ID.fullmatch(decision_id):
            raise HumanDecisionError("invalid decision document identity")
        if metadata.get("schema_version") != SCHEMA_VERSION or metadata.get("status") != "PENDING":
            raise HumanDecisionError("invalid pending decision metadata")
        target = self.path(decision_id)
        # A registry entry is a tombstone for this identity.  Even if the
        # visible Markdown is deleted or replaced, a later controller pass
        # must fail closed rather than recreate a fresh PENDING package and
        # erase/obscure a human response.
        if target.exists() or self.path(decision_id, resolved=True).exists() or (self.registry / f"{decision_id}.json").exists():
            raise HumanDecisionError("decision identity already exists")
        target.parent.mkdir(parents=True, exist_ok=True)
        self.registry.mkdir(parents=True, exist_ok=True)
        registry = self.registry / f"{decision_id}.json"
        registry.write_text(canonical_json(metadata) + "\n", encoding="utf-8")
        body = (
            f"# ITDD HUMAN DECISION — {metadata['decision_type']}\n\n"
            f"<!-- ITDD-HUMAN-DECISION {canonical_json(metadata)} -->\n\n"
            f"{review_body.strip()}\n\n"
            "--------------------------------------------------\n"
            "EDIT ONLY BELOW THIS LINE\n\n"
            "Decision: PENDING\n"
            "Comment: \n\n"
            "EDIT ONLY ABOVE THIS LINE\n"
            "--------------------------------------------------\n"
            "This is the only authoritative response section. Save this file after editing.\n"
        )
        target.write_text(body, encoding="utf-8")
        return target

    def repair(self, decision_id: str, *, repaired_at: str) -> Path:
        """Preserve malformed input and append a safe, pending response area."""
        source = self.path(decision_id)
        if not source.exists() or self.path(decision_id, resolved=True).exists():
            raise HumanDecisionError("only an unconsumed pending decision can be repaired")
        text = source.read_text(encoding="utf-8")
        marker = _MARKER.search(text)
        if not marker:
            raise HumanDecisionError("decision metadata is missing")
        metadata = json.loads(marker.group("meta"))
        registered = self.registry / f"{decision_id}.json"
        if not registered.exists() or json.loads(registered.read_text(encoding="utf-8")) != metadata:
            raise HumanDecisionError("decision metadata does not match controller registry")
        evidence_root = self.root / "diagnostics"
        evidence_root.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        evidence = evidence_root / f"{decision_id}-{repaired_at.replace(':', '').replace('-', '')}.md"
        evidence.write_bytes(source.read_bytes())
        comment_matches = re.findall(r"^\s*(?:[-*>]\s*)?Comment:\s*([^\r\n]*)", text, re.IGNORECASE | re.MULTILINE)
        recovered_comment = next((item.strip() for item in reversed(comment_matches) if item.strip() and item.strip() != "---"), "")
        # Only an exact Decision field is eligible for recovery. Surrounding
        # prose such as `Gate: \"APPROVE\"` is intentionally ignored.
        exact_decisions = re.findall(r"^\s*(?:[-*>]\s*)?Decision:\s*([^\r\n]+)\s*$", text, re.IGNORECASE | re.MULTILINE)
        recovered = "PENDING"
        if exact_decisions:
            try:
                recovered = self._normalize_decision(exact_decisions[-1])
            except HumanDecisionError:
                recovered = "PENDING"
        addition = (
            "\n\n--------------------------------------------------\n"
            "EDIT ONLY BELOW THIS LINE\n\n"
            f"Decision: {recovered}\n"
            f"Comment: {recovered_comment}\n\n"
            "EDIT ONLY ABOVE THIS LINE\n"
            "--------------------------------------------------\n"
        )
        bounded = list(re.finditer(r"EDIT ONLY BELOW THIS LINE\s*\n(?P<body>.*?)\nEDIT ONLY ABOVE THIS LINE", text, re.IGNORECASE | re.DOTALL))
        if bounded:
            body = f"Decision: {recovered}\nComment: {recovered_comment}\n"
            text = text[:bounded[-1].start("body")] + body + text[bounded[-1].end("body"):]
            source.write_text(text, encoding="utf-8")
        else:
            source.write_text(text + addition, encoding="utf-8")
        evidence.with_suffix(".json").write_text(canonical_json({"decision_id": decision_id, "status": "REPAIRED", "repaired_at": repaired_at, "original_sha256": digest, "evidence_path": str(evidence), "recovered_decision": recovered, "recovered_comment": recovered_comment}) + "\n", encoding="utf-8")
        return source

    def invalidate(self, decision_id: str, *, reason: str, replacement_id: str, invalidated_at: str) -> Path:
        """Record creator-side invalidation without rewriting the original package."""
        source = self.path(decision_id)
        if not source.exists():
            raise HumanDecisionError("only a pending decision can be invalidated")
        document = self.read(decision_id)
        record = {
            "schema_version": SCHEMA_VERSION,
            "decision_id": decision_id,
            "status": "SUPERSEDED",
            "invalidated_at": invalidated_at,
            "reason": reason,
            "replacement_decision_id": replacement_id,
            "preserved_response_decision": document["response_decision"],
            "preserved_response_comment": document["response_comment"],
            "original_document_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "original_authoritative_event_head": document["authoritative_event_head"],
            "gate_id": document.get("gate_id"),
            "project_id": document["project_id"],
            "subject_id": document["subject_id"],
            "subject_version": document["subject_version"],
        }
        target = self.root / "superseded" / f"{decision_id}.json"
        if target.exists():
            raise HumanDecisionError("decision invalidation already exists")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(canonical_json(record) + "\n", encoding="utf-8")
        return target

    def mark_resolved(self, decision_id: str, *, decision: str, comment: str, event_id: str, resolved_at: str) -> Path:
        source = self.path(decision_id)
        if not source.exists():
            raise HumanDecisionError("decision is not pending or has already been resolved")
        text = source.read_text(encoding="utf-8")
        marker = _MARKER.search(text)
        if not marker:
            raise HumanDecisionError("invalid decision document")
        metadata = json.loads(marker.group("meta"))
        metadata.update({"status": "RESOLVED", "resolved_decision": decision, "resolved_comment": comment, "resolution_event_id": event_id, "resolved_at": resolved_at})
        updated = _MARKER.sub(f"<!-- ITDD-HUMAN-DECISION {canonical_json(metadata)} -->", text, count=1)
        bounded = list(re.finditer(
            r"EDIT ONLY BELOW THIS LINE\s*\n(?P<body>.*?)\nEDIT ONLY ABOVE THIS LINE",
            updated, re.IGNORECASE | re.DOTALL,
        ))
        if not bounded:
            raise HumanDecisionError("resolved response section is malformed")
        body = f"Decision: {decision}\nComment: {comment}\n"
        updated = updated[:bounded[-1].start("body")] + body + updated[bounded[-1].end("body"):]
        target = self.path(decision_id, resolved=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(updated, encoding="utf-8")
        source.unlink()
        # The registry is retained as immutable audit binding; it is not a response surface.
        return target


class HumanDecisionController:
    """Creates and consumes decision packages; the caller cannot select an agent actor."""
    def __init__(self, project_root: str | Path, *, controller_execution_id: str = "EXEC-CONTROLLER-001") -> None:
        self.project_root = resolve_project_root(project_root)
        self.store = HumanDecisionStore(self.project_root)
        self.events = EventLog(self.project_root)
        self.execution_id = controller_execution_id

    def _metadata(self, *, decision_id: str, decision_type: str, project_id: str, subject_id: str, subject_version: int, intent: dict[str, Any] | None, graph: dict[str, Any] | None, candidate: dict[str, Any] | None, gate_id: str | None, created_at: str) -> dict[str, Any]:
        event_id, event_hash = _head(self.events)
        return {"decision_id": decision_id, "schema_version": SCHEMA_VERSION, "status": "PENDING", "decision_type": decision_type, "project_id": project_id, "subject_id": subject_id, "subject_version": subject_version, "gate_id": gate_id, "intent": {"intent_id": intent["intent_id"], "version": intent["version"]} if intent else None, "graph": {"graph_id": graph["graph_id"], "version": graph["version"]} if graph else None, "candidate": candidate, "authoritative_event_head": {"event_id": event_id, "event_hash": event_hash}, "nonce": secrets.token_urlsafe(24), "created_at": created_at}

    def create_intent(self, *, decision_id: str, intent_id: str, version: int, timestamp: str, open_document: bool = False) -> Path:
        intent = StageCStore(self.project_root).read_intent(intent_id, version)
        if intent["status"] != "DRAFT": raise HumanDecisionError("only a draft intent may receive an approval decision")
        metadata = self._metadata(decision_id=decision_id, decision_type="INTENT_AUTHORITY", project_id=intent["project_id"], subject_id=intent_id, subject_version=version, intent=intent, graph=None, candidate=None, gate_id=None, created_at=timestamp)
        body = "\n".join([
            "## Project identity", f"- Project: `{intent['project_id']}`", f"- Intent: `{intent_id} v{version}`",
            "", "## Purpose", intent["purpose"],
            "", "## Full intent statement", "This milestone proves a multi-EU integration and recovery lifecycle from one human-approved intent through independent execution, controller-owned integration, exact-candidate promotion, and fresh-process reconstruction.",
            "", "## Requirements", *[f"- `{r['requirement_id']}` — {r['text']}" for r in intent["requirements"]],
            "", "## Constraints", *[f"- {c}" for c in intent["constraints"]],
            "", "## Success criteria", intent["acceptance_summary"],
            "", "## Recovery expectations",
            "- Interrupted Builders, Verifiers, Integrators, and Promoters must fail closed without manufacturing a candidate, approval, or promotion.",
            "- Failures, retries, superseded artifacts, stale evidence, and recovery transitions remain durably reconstructable.",
            "- A fresh process must reconstruct the complete lifecycle from project-local state without chat history.",
            "", "## Replanning boundaries",
            "- Controlled replanning may change how the approved intent is achieved while preserving its destination, requirements, and constraints.",
            "- A change to the approved destination requires a new versioned Intent Amendment and HUMAN_ONLY approval; replanning cannot silently amend intent.",
            "", "## Human gates",
            "- HUMAN_ONLY intent approval is required before Planner or Graph Evaluator execution.",
            "- HUMAN_ONLY verified-work approval is required for each eligible EU as applicable.",
            "- HUMAN_ONLY integration approval is required before promoting the integrated result.",
            "- Promotion remains controller-owned and must bind to the exact approved integration result.",
            "", "## What approval authorizes",
            "- APPROVE authorizes the controller to launch the bounded Planner and independent Graph Evaluator path for this exact intent.",
            "- Later machine work remains separately capability-bound, evidence-bound, and subject to its required HUMAN_ONLY gates.",
            "", "## What approval does NOT authorize",
            "- It does not authorize Planner, Graph Evaluator, Builder, Integrator, Verifier, or Promoter execution before the controller consumes this decision.",
            "- It does not approve any graph, EU, candidate, integration result, promotion, Intent Amendment, global Codex change, or unrelated project.",
            "", "## Exclusions and deferred scope",
            "- No parallel execution beyond the bounded multi-EU proof, no autonomous approval, no silent graph editing, and no unrelated project or production deployment.",
            "- Global Codex configuration, arbitrary OS-user process authentication, maintenance mode, and break-glass recovery remain deferred unless separately authorized.",
            "", "## Known limitations / open questions",
            "- ITDD does not authenticate against arbitrary malicious processes running with the human's unrestricted OS-user privileges.",
            "- Conflict classification and the exact controlled replan route will be exercised and recorded by the proof; unresolved ambiguity must stop safely for human clarification.",
            "", "## Decision meaning",
            "- REJECT leaves this intent unapproved and enables no downstream execution.",
            "- CHANGES_REQUESTED preserves your comment and routes the intent back for controlled reconsideration.",
        ])
        path = self.store.create(metadata, review_body=body)
        HumanViewGenerator(self.project_root).generate(project_id=intent["project_id"])
        if open_document and open_decision_document(path) is None:
            raise HumanDecisionError(f"VS CODE PRESENTATION FAILED: {path}")
        return path

    def create_gate(self, *, decision_id: str, gate_id: str, timestamp: str, open_document: bool = False) -> Path:
        gate = HumanGateStore(self.project_root).read(gate_id)
        if gate["status"] != "WAITING": raise HumanDecisionError("only a waiting gate may receive a decision document")
        metadata = self._metadata(decision_id=decision_id, decision_type=gate["gate_type"], project_id=gate["project_id"], subject_id=gate["subject_id"], subject_version=1, intent=gate.get("related_intent"), graph=gate.get("related_graph"), candidate=gate.get("related_candidate"), gate_id=gate_id, created_at=timestamp)
        body = "\n".join(["## Project identity", f"- Project: `{gate['project_id']}`", f"- Gate: `{gate_id}`", f"- Subject: `{gate['subject_id']}`", "", "## Exact review binding", f"- Candidate: `{gate['related_candidate']['candidate_sha']}`", f"- Required state: `{gate['required_state']}`", f"- Evidence: `{canonical_json(gate['evidence'])}`", "", "## Decision meaning", "- APPROVE permits the already-verified operation bound above.", "- REJECT denies this exact operation.", "- CHANGES_REQUESTED preserves your comment and routes controlled reconsideration.", "", "## Known limitations", "- This document cannot promote or alter intent, graph, candidate, or evidence.", "- ITDD does not authenticate against arbitrary malicious processes running with the human's unrestricted OS-user privileges."])
        path = self.store.create(metadata, review_body=body)
        HumanViewGenerator(self.project_root).generate(project_id=gate["project_id"])
        if open_document and open_decision_document(path) is None:
            raise HumanDecisionError(f"VS CODE PRESENTATION FAILED: {path}")
        return path

    def create_amendment(self, *, decision_id: str, amendment: dict[str, Any], source_intent: dict[str, Any], timestamp: str, open_document: bool = False) -> Path:
        if amendment.get("status") != "PENDING" or amendment.get("project_id") != source_intent.get("project_id"):
            raise HumanDecisionError("only a pending amendment bound to its source intent may receive a decision document")
        metadata = self._metadata(
            decision_id=decision_id, decision_type="INTENT_AMENDMENT",
            project_id=amendment["project_id"], subject_id=amendment["amendment_id"],
            subject_version=amendment["amendment_version"], intent=source_intent,
            graph=None, candidate=None, gate_id=None, created_at=timestamp,
        )
        change = amendment["authority_change"]
        preserved = amendment["preserved_scope"]
        body = "\n".join([
            "## Current approved intent and why amendment is required",
            f"- Project: `{source_intent['project_id']}`",
            f"- Approved intent: `{source_intent['intent_id']} v{source_intent['version']}`",
            f"- Destination: {source_intent['purpose']}",
            "- This amendment corrects erroneous routine HUMAN_ONLY lifecycle requirements embedded in the approved authority model. It does not rewrite or silently violate the approved intent.",
            "", "## Exact authority language being removed/replaced",
            *[f'- "{item}"' for item in change["removed_language"]],
            "", "## Exact replacement authority semantics", change["replacement_language"],
            "", "## Controller-owned lifecycle actions after initial intent approval",
            *[f"- {item}" for item in __import__("control.intent_amendments", fromlist=["IntentAmendmentController"]).IntentAmendmentController.CONTROLLER_OWNED],
            "", "## What remains unchanged",
            f"- Substantive destination, purpose, title, requirements, constraints, and acceptance summary remain those of `{source_intent['intent_id']} v{source_intent['version']}`.",
            f"- Completed EU work remains: {', '.join(preserved['completed_eu_work'])}.",
            f"- Graph history remains: {canonical_json(preserved['graph_history'])}.",
            f"- Verified integration remains `IN-1001`, candidate `{preserved['verified_integration']['candidate_sha']}`, tree `{preserved['verified_integration']['tree']}`, verifier result `{preserved['verified_integration']['verifier_result']}`.",
            "- Evidence, provenance, `HG-14001`, `HD-007`, and all historical events remain preserved. `HD-007` is not consumed by this amendment.",
            "", "## What approval authorizes",
            "- Approval authorizes the controller to continue the already-approved destination autonomously through eligible lifecycle work, including promotion when already authorized by the approved intent.",
            "- Approval authorizes the controller-owned authority model stated above, not a new destination or substantive requirement.",
            "", "## What approval does not authorize",
            "- It does not authorize a different destination, requirements, constraints, project, maintenance mode, break-glass action, or unrelated work.",
            "- It does not auto-approve, consume, or copy approval from `HG-14001` or `HD-007`.",
            "", "## Effect on already-verified `IN-1001`",
            "- `IN-1001` remains VERIFIED with its exact integrated candidate and evidence. Its obsolete routine approval gate remains historical and waiting; this amendment does not mutate the integration result or historical gate.",
            "", "## Human authority still required after initial intent approval",
            *[f"- {item}" for item in change["human_authority_after_approval"]],
            "", "## YOUR RESPONSE",
            "Approve this authority amendment only if it accurately restores the intended ITDD authority model while preserving all listed scope and history.",
        ])
        path = self.store.create(metadata, review_body=body)
        if open_document and open_decision_document(path) is None:
            raise HumanDecisionError(f"VS CODE PRESENTATION FAILED: {path}")
        return path

    def resolve(self, decision_id: str, *, timestamp: str, human_id: str = "local-human") -> dict[str, Any]:
        if self.store.superseded_path(decision_id).exists():
            raise HumanDecisionError("decision is SUPERSEDED and cannot be consumed")
        doc = self.store.read(decision_id)
        if doc.get("resolved") or doc.get("status") != "PENDING": raise HumanDecisionError("decision document is already resolved")
        if doc["response_decision"] == "PENDING": raise HumanDecisionError("decision remains PENDING")
        current_id, current_hash = _head(self.events)
        if doc["authoritative_event_head"] != {"event_id": current_id, "event_hash": current_hash}: raise HumanDecisionError("STALE_DECISION: authoritative event head changed")
        prefix = f"human-decision-{decision_id}"
        decision = doc["response_decision"]
        if doc["decision_type"] == "INTENT_AUTHORITY":
            if decision == "APPROVE":
                StageCStore(self.project_root).approve_intent(doc["subject_id"], doc["subject_version"], event_id=f"{prefix}-approved", timestamp=timestamp, actor_type="human", actor_id=human_id)
                event_id = f"{prefix}-approved"
            else:
                event_type = "human.decision.rejected" if decision == "REJECT" else "human.decision.changes_requested"
                event = self.events.new_event(event_id=f"{prefix}-{decision.lower()}", event_type=event_type, timestamp=timestamp, project_id=doc["project_id"], actor_type="human", actor_id=human_id, execution_id=self.execution_id, payload={"decision_id": decision_id, "subject_id": doc["subject_id"], "subject_version": doc["subject_version"], "decision": decision, "comment": doc["response_comment"]})
                self.events.append(event); event_id = event["event_id"]
        elif doc["decision_type"] == "INTENT_AMENDMENT":
            from control.intent_amendments import IntentAmendmentStore
            amendment = IntentAmendmentStore(self.project_root).read(doc["subject_id"], doc["subject_version"])
            if decision == "APPROVE":
                amendment = IntentAmendmentStore(self.project_root).update_status(doc["subject_id"], doc["subject_version"], "APPROVED")
                event_type = "intent.amendment.approved"
            else:
                status = "REJECTED" if decision == "REJECT" else "CHANGES_REQUESTED"
                amendment = IntentAmendmentStore(self.project_root).update_status(doc["subject_id"], doc["subject_version"], status)
                event_type = f"intent.amendment.{status.lower()}"
            event = self.events.new_event(event_id=f"{prefix}-{decision.lower()}", event_type=event_type, timestamp=timestamp, project_id=doc["project_id"], actor_type="human", actor_id=human_id, execution_id=self.execution_id, payload={"amendment": amendment, "decision_id": decision_id, "decision": decision, "comment": doc["response_comment"]})
            self.events.append(event)
            event_id = event["event_id"]
            # Approval changes effective lifecycle authority. Reconcile only
            # controller-owned gates made obsolete by that approved change;
            # this does not consume or mutate any gate decision document.
            if decision == "APPROVE":
                from control.intent_amendments import IntentAmendmentController
                IntentAmendmentController(self.project_root, controller_execution_id=self.execution_id).reconcile_obsolete_gates(amendment, timestamp=timestamp)
        else:
            if decision in {"APPROVE", "REJECT"}:
                gate = HumanGateStore(self.project_root).read(doc["gate_id"] or "")
                binding = {"project_id": gate["project_id"], "gate_id": gate["gate_id"], **gate["related_candidate"], "evidence": gate["evidence"]}
                result = HumanGateController(self.project_root, controller_execution_id=self.execution_id).decide(doc["gate_id"], decision="APPROVED" if decision == "APPROVE" else "REJECTED", actor_type="human", actor_id=human_id, binding=binding, event_prefix=prefix, timestamp=timestamp)
                event_id = result["decision_event_id"]
            else:
                event = self.events.new_event(event_id=f"{prefix}-changes-requested", event_type="human.decision.changes_requested", timestamp=timestamp, project_id=doc["project_id"], actor_type="human", actor_id=human_id, execution_id=self.execution_id, payload={"decision_id": decision_id, "gate_id": doc["gate_id"], "decision": decision, "comment": doc["response_comment"]})
                self.events.append(event); event_id = event["event_id"]
        path = self.store.mark_resolved(decision_id, decision=decision, comment=doc["response_comment"], event_id=event_id, resolved_at=timestamp)
        HumanViewGenerator(self.project_root).generate(project_id=doc["project_id"])
        return {"decision_id": decision_id, "decision": decision, "event_id": event_id, "path": str(path)}

    def scan(self, *, timestamp: str, human_id: str = "local-human") -> list[dict[str, Any]]:
        """Consume saved non-PENDING packages; a controller watcher can call this after a save."""
        results = []
        pending = self.store.root / "pending"
        for path in sorted(pending.glob("HD-*.md")) if pending.exists() else []:
            decision_id = path.stem
            if self.store.superseded_path(decision_id).exists():
                continue
            try:
                if self.store.read(decision_id)["response_decision"] != "PENDING":
                    results.append(self.resolve(decision_id, timestamp=timestamp, human_id=human_id))
            except HumanDecisionError:
                raise
        return results


def _window_has_target(process_names: list[str], filename: str) -> bool:
    if not shutil.which("osascript"):
        return False
    script = "tell application \"System Events\" to get {" + ",".join(
        f"name of every window of process \"{name}\"" for name in process_names
    ) + "}"
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
    return result.returncode == 0 and filename.lower() in result.stdout.lower()


def open_decision_document(path: str | Path, *, viewer: str | None = None) -> str | None:
    """Open and verify the exact package in VS Code only.

    Human decision documents are authority surfaces, not ordinary views.
    Failure to present the exact file fails closed; no alternate application
    is launched.
    """
    target = str(Path(path).resolve())
    filename = Path(target).name
    requested = (viewer or os.environ.get("ITDD_HUMAN_VIEWER") or "").lower()
    if requested not in {"", "code", "vscode", "visual studio code"} or not shutil.which("code"):
        return None
    command = ["code", "--reuse-window", "--goto", target]
    if subprocess.run(command, check=False).returncode == 0:
        time.sleep(0.7)
        if _window_has_target(["Code", "Visual Studio Code"], filename):
            return "VS Code"
    return None

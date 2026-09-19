"""Stage E6 controller-owned human gates and deterministic human views."""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_path, resolve_project_root
from control.authorization import CapabilityIssuer, ControllerAuthorizer
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json
from control.models.store import StageCStore
from control.verifier import VerifierOrchestrator


class HumanGateError(ValueError):
    pass


_GATE_ID = re.compile(r"^HG-[0-9]{3,}$")
_STATUSES = {"WAITING", "APPROVED", "REJECTED", "SUPERSEDED", "CANCELLED"}


def _binding(gate: dict[str, Any]) -> dict[str, Any]:
    return {"project_id": gate["project_id"], "gate_id": gate["gate_id"], **gate["related_candidate"], "evidence": gate["evidence"]}


def validate_gate(gate: dict[str, Any]) -> None:
    required = {"gate_id", "schema_version", "project_id", "gate_type", "subject_type", "subject_id", "required_state", "created_at", "status", "decision_event_id", "related_intent", "related_graph", "related_eu", "related_candidate", "evidence", "approval_capability_id"}
    if set(gate) != required: raise HumanGateError("human gate fields do not match schema")
    if not _GATE_ID.fullmatch(gate["gate_id"]): raise HumanGateError("invalid gate identity")
    if gate["schema_version"] != 1 or gate["status"] not in _STATUSES: raise HumanGateError("invalid gate state")
    if gate["gate_type"] != "VERIFIED_EU_REVIEW" or gate["required_state"] != "VERIFIED": raise HumanGateError("unsupported E6 gate")
    if gate["subject_type"] != "EU" or gate["subject_id"] != gate["related_eu"]["eu_id"]: raise HumanGateError("gate subject mismatch")
    if not re.fullmatch(r"[0-9a-f]{40,64}", gate["related_candidate"].get("candidate_sha", "")): raise HumanGateError("invalid candidate binding")
    if set(gate["evidence"]) != {"spec_execution_id", "standards_execution_id", "spec_result_id", "standards_result_id"}: raise HumanGateError("invalid evidence binding")


class HumanGateStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root); self.events = EventLog(self.project_root)

    def path(self, gate_id: str) -> Path: return resolve_project_path(self.project_root, f".idd/human_gates/{gate_id}.json")

    def read(self, gate_id: str) -> dict[str, Any]:
        path = self.path(gate_id)
        if not path.exists(): raise HumanGateError("human gate does not exist")
        gate = json.loads(path.read_text(encoding="utf-8")); validate_gate(gate); return gate

    def reconstruct(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for event in self.events.verify():
            if event["event_type"] == "human.gate.created":
                gate = event["payload"]["gate"]; validate_gate(gate)
                if gate["gate_id"] in result: raise EventLogIntegrityError("human gate reused")
                result[gate["gate_id"]] = gate
            elif event["event_type"] in {"human.gate.approved", "human.gate.rejected", "human.gate.superseded"}:
                gate_id = event["payload"]["gate_id"]
                if gate_id not in result: raise EventLogIntegrityError("decision references unknown gate")
                updated = deepcopy(result[gate_id]); updated["status"] = event["payload"]["status"]; updated["decision_event_id"] = event["event_id"]; result[gate_id] = updated
        return result

    def verify_materialized(self) -> None:
        for gate_id, gate in self.reconstruct().items():
            if self.read(gate_id) != gate: raise EventLogIntegrityError("human gate diverges from event history")

    def _append(self, *, event_id: str, event_type: str, timestamp: str, gate: dict[str, Any], actor_type: str, actor_id: str, payload: dict[str, Any]) -> None:
        event = self.events.new_event(event_id=event_id, event_type=event_type, timestamp=timestamp, project_id=gate["project_id"], actor_type=actor_type, actor_id=actor_id, execution_id=gate["evidence"]["spec_execution_id"], payload=payload); self.events.append(event)

    def create(self, gate: dict[str, Any], *, event_id: str, timestamp: str) -> dict[str, Any]:
        validate_gate(gate)
        if self.path(gate["gate_id"]).exists(): raise HumanGateError("gate identity already exists")
        self.path(gate["gate_id"]).parent.mkdir(parents=True, exist_ok=True); self.path(gate["gate_id"]).write_text(canonical_json(gate) + "\n", encoding="utf-8")
        self._append(event_id=event_id, event_type="human.gate.created", timestamp=timestamp, gate=gate, actor_type="controller", actor_id="controller", payload={"gate": gate}); return gate

    def transition(self, gate: dict[str, Any], *, status: str, event_id: str, timestamp: str, actor_type: str, actor_id: str, binding: dict[str, Any]) -> dict[str, Any]:
        if gate["status"] != "WAITING": raise HumanGateError("gate is no longer waiting")
        if binding != _binding(gate): raise HumanGateError("decision binding mismatch")
        updated = deepcopy(gate); updated["status"] = status; updated["decision_event_id"] = event_id
        self._append(event_id=event_id, event_type=f"human.gate.{status.lower()}", timestamp=timestamp, gate=updated, actor_type=actor_type, actor_id=actor_id, payload={"gate_id": gate["gate_id"], "status": status, "binding": binding})
        self.path(gate["gate_id"]).write_text(canonical_json(updated) + "\n", encoding="utf-8"); return updated

    def supersede(self, gate: dict[str, Any], *, event_id: str, timestamp: str) -> dict[str, Any]:
        if gate["status"] != "WAITING": raise HumanGateError("gate is no longer waiting")
        updated = deepcopy(gate); updated["status"] = "SUPERSEDED"; updated["decision_event_id"] = event_id
        self._append(event_id=event_id, event_type="human.gate.superseded", timestamp=timestamp, gate=updated, actor_type="controller", actor_id="controller", payload={"gate_id": gate["gate_id"], "status": "SUPERSEDED", "reason": "STALE_CANDIDATE"})
        self.path(gate["gate_id"]).write_text(canonical_json(updated) + "\n", encoding="utf-8"); return updated


class HumanGateController:
    def __init__(self, project_root: str | Path, *, controller_execution_id: str = "EXEC-CONTROLLER-001") -> None:
        self.project_root = resolve_project_root(project_root); self.store = HumanGateStore(self.project_root); self.execution_id = controller_execution_id
        self.capabilities = CapabilityIssuer(self.project_root); self.authorizer = ControllerAuthorizer(self.project_root); self.verifiers = VerifierOrchestrator(self.project_root, controller_execution_id=controller_execution_id)

    def create_verified_eu_review(self, *, gate_id: str, project_id: str, eu_id: str, candidate_sha: str, spec_execution_id: str, standards_execution_id: str, spec_result_id: str, standards_result_id: str, intent: dict[str, Any] | None = None, graph: dict[str, Any] | None = None, eu: dict[str, Any] | None = None, timestamp: str, event_prefix: str) -> dict[str, Any]:
        if self.verifiers.derive_candidate_status(candidate_sha) != "VERIFIED": raise HumanGateError("candidate is not VERIFIED")
        executions = self.verifiers.executions.reconstruct(); spec = executions.get(spec_execution_id, {}); standards = executions.get(standards_execution_id, {})
        if spec.get("role") != "SPEC_VERIFIER" or standards.get("role") != "STANDARDS_REVIEWER" or spec_execution_id == standards_execution_id: raise HumanGateError("evidence axes do not match gate")
        if spec.get("candidate_sha") != candidate_sha or standards.get("candidate_sha") != candidate_sha: raise HumanGateError("candidate binding mismatch")
        number = re.sub(r"\D", "", gate_id) or "1"; cap_id = f"CAP-{int(number):03d}"
        cap = self.capabilities.issue({"capability_id":cap_id,"schema_version":1,"project_id":project_id,"role":"CONTROLLER","execution_id":self.execution_id,"issued_at":timestamp,"baseline_sha":spec["baseline_sha"],"allowed_reads":[".idd"],"allowed_writes":[".idd/human_gates"],"allowed_executes":[],"allowed_operations":["HUMAN_GATE_APPROVAL"],"forbidden_operations":[],"allowed_request_types":[],"scope_bindings":{"eu_id":eu_id},"version":1,"issued_by":"controller"}, event_id=f"{event_prefix}-cap", timestamp=timestamp)
        gate = {"gate_id":gate_id,"schema_version":1,"project_id":project_id,"gate_type":"VERIFIED_EU_REVIEW","subject_type":"EU","subject_id":eu_id,"required_state":"VERIFIED","created_at":timestamp,"status":"WAITING","decision_event_id":None,"related_intent":intent,"related_graph":graph,"related_eu":eu or {"eu_id":eu_id},"related_candidate":{"candidate_sha":candidate_sha,"baseline_sha":spec["baseline_sha"]},"evidence":{"spec_execution_id":spec_execution_id,"standards_execution_id":standards_execution_id,"spec_result_id":spec_result_id,"standards_result_id":standards_result_id},"approval_capability_id":cap["capability_id"]}
        return self.store.create(gate, event_id=f"{event_prefix}-created", timestamp=timestamp)

    def decide(self, gate_id: str, *, decision: str, actor_type: str, actor_id: str, binding: dict[str, Any], event_prefix: str, timestamp: str) -> dict[str, Any]:
        if decision not in {"APPROVED", "REJECTED"}: raise HumanGateError("unsupported human decision")
        gate = self.store.read(gate_id); current = {"project_root":str(self.project_root),"project_id":gate["project_id"],"execution_id":self.execution_id,"baseline_sha":gate["related_candidate"]["baseline_sha"],"role":"CONTROLLER"}
        if binding.get("candidate_sha") != gate["related_candidate"]["candidate_sha"]:
            self.store.supersede(gate, event_id=f"{event_prefix}-superseded", timestamp=timestamp)
            raise HumanGateError("STALE_CANDIDATE: gate superseded; new review required")
        action = {"request_id":f"{event_prefix}-request","project_id":gate["project_id"],"execution_id":self.execution_id,"baseline_sha":current["baseline_sha"],"role":"CONTROLLER","actor_type":actor_type,"operation":"HUMAN_GATE_APPROVAL","intent_id":(gate["related_intent"] or {}).get("intent_id"),"intent_version":(gate["related_intent"] or {}).get("version"),"graph_id":(gate["related_graph"] or {}).get("graph_id"),"graph_version":(gate["related_graph"] or {}).get("version"),"eu_id":gate["subject_id"]}
        auth = self.authorizer.authorize(gate["approval_capability_id"], action, current, event_id=f"{event_prefix}-authorization", timestamp=timestamp)
        if auth.decision != "ALLOW": raise HumanGateError(auth.reason)
        if actor_type != "human": raise HumanGateError("DENY_HUMAN_ONLY")
        return self.store.transition(gate, status=decision, event_id=f"{event_prefix}-decision", timestamp=timestamp, actor_type=actor_type, actor_id=actor_id, binding=binding)


class HumanViewGenerator:
    VERSION = "e6-v1"
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root); self.gates = HumanGateStore(self.project_root); self.events = EventLog(self.project_root)
    @property
    def view_dir(self) -> Path: return resolve_project_path(self.project_root, ".idd/views")

    def is_stale(self, view: str | Path) -> bool:
        path = Path(view); path = path if path.is_absolute() else self.view_dir / path
        if not path.exists(): return True
        marker = re.search(r"source=([0-9a-f]{64})", path.read_text(encoding="utf-8"))
        gates = {key:value for key,value in sorted(self.gates.reconstruct().items())}
        records = self.events.verify(); head = records[-1]["event_hash"] if records else "EMPTY"
        expected = hashlib.sha256(canonical_json({"head":head,"gates":gates,"version":self.VERSION}).encode()).hexdigest()
        return marker is None or marker.group(1) != expected
    def generate(self, *, project_id: str) -> dict[str, str]:
        gates = {key:value for key,value in sorted(self.gates.reconstruct().items()) if value["project_id"] == project_id}; records = self.events.verify(); head = records[-1]["event_hash"] if records else "EMPTY"
        source = hashlib.sha256(canonical_json({"head":head,"gates":gates,"version":self.VERSION}).encode()).hexdigest(); now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        def page(title: str, body: str) -> str: return f"# {title}\n\n<!-- ITDD-DERIVED project={project_id} generated={now} source={source} generator={self.VERSION}; DO NOT EDIT FOR AUTHORITY -->\n\n{body.strip()}\n"
        waiting = [g for g in gates.values() if g["status"] == "WAITING"]; approved = [g for g in gates.values() if g["status"] == "APPROVED"]; rejected = [g for g in gates.values() if g["status"] == "REJECTED"]
        dashboard = page("Current Project Status", f"**Human review:** {len(waiting)} waiting, {len(approved)} approved, {len(rejected)} rejected.\n\n**Needs your decision:** {', '.join(g['gate_id'] for g in waiting) or 'none'}.\n\n**Authority:** controller event state.\n\n**Known limitation:** candidate SHA is an ITDD binding; independent Git/VCS attestation is deferred to E7.\n\n**Eligible after approval:** later controlled lifecycle work only; E6 launches no integration or promotion.")
        kanban = page("Kanban", "\n".join(["## HUMAN REVIEW", *[f"- {g['gate_id']} · {g['subject_id']} · WAITING" for g in waiting], "\n## APPROVED", *[f"- {g['gate_id']} · {g['subject_id']} · HUMAN APPROVED" for g in approved], "\n## REJECTED", *[f"- {g['gate_id']} · {g['subject_id']} · REJECTED" for g in rejected]]) or "- no supported state")
        human = page("Current Human Gates", "\n".join([f"- **{g['gate_id']}** · `{g['status']}` · subject `{g['subject_id']}` · candidate `{g['related_candidate']['candidate_sha']}`\n  - Evidence: Spec `{g['evidence']['spec_result_id']}`, Standards `{g['evidence']['standards_result_id']}`.\n  - Action: approve or reject this exact gate; Markdown is advisory." for g in gates.values()]) or "- no gates")
        verification = page("Verification Status", "\n".join([f"## {g['subject_id']} · `{g['related_candidate']['candidate_sha']}`\n- Spec Verification: PASS (`{g['evidence']['spec_result_id']}`)\n- Standards Review: PASS (`{g['evidence']['standards_result_id']}`)\n- Overall: VERIFIED\n- Human gate: {g['status']}" for g in gates.values()]) or "- no verified candidate gates")
        state = StageCStore(self.project_root).reconstruct(); intent = state.get("approved_intent"); graph = state.get("active_graph")
        outputs = {"dashboard.md":dashboard,"kanban.md":kanban,"human-gates.md":human,"verification.md":verification,"intent.md":page("Intent", f"- approved intent: `{intent['intent_id']} v{intent['version']}`" if intent else "- UNKNOWN"),"graph.md":page("Execution Graph", "\n".join(f"- `{n['eu_id']}` requirements: {', '.join(n['requirement_ids'])}" for n in (graph or {}).get("nodes", [])) or "- UNKNOWN"),"timeline.md":page("Timeline / Audit Summary", "\n".join(f"- {e['timestamp']} · `{e['event_type']}` · {e['actor_type']}:{e['actor_id']}" for e in records if e["event_type"].startswith(("intent.","graph.","verifier.execution.","human.gate."))) or "- no events")}
        self.view_dir.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items(): (self.view_dir / name).write_text(content, encoding="utf-8")
        return outputs

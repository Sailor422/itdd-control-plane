"""Stage E7 Git-attested candidate integration and fresh verification."""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_root
from control.authorization import CapabilityIssuer, ControllerAuthorizer
from control.context import ContextCompiler
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json
from control.git import CandidateAttestationStore, GitAdapter, GitError
from control.human import HumanGateStore
from control.verifier import VerifierOrchestrator, VerifierInterrupted


class IntegrationError(ValueError): pass


def _hash(item: dict[str, Any]) -> str:
    value = deepcopy(item); value.pop("result_hash", None); return hashlib.sha256(canonical_json(value).encode()).hexdigest()


class IntegrationStore:
    def __init__(self, root: str | Path) -> None: self.root = resolve_project_root(root); self.events = EventLog(self.root)
    def path(self, integration_id: str) -> Path: return self.root / ".idd/integrations" / f"{integration_id}.json"
    def read(self, integration_id: str) -> dict[str, Any]: return json.loads(self.path(integration_id).read_text(encoding="utf-8"))
    def reconstruct(self) -> dict[str, dict[str, Any]]:
        out = {}
        for event in self.events.verify():
            if event["event_type"] in {"integration.created", "integration.completed", "integration.failed", "integration.conflict", "integration.replan_required", "integration.interrupted", "integration.verified"}:
                item = event["payload"]["integration"]; out[item["integration_id"]] = item
        return out
    def write_event(self, item: dict[str, Any], *, event_id: str, event_type: str, timestamp: str, actor_type: str = "controller") -> None:
        item["result_hash"] = _hash(item); self.path(item["integration_id"]).parent.mkdir(parents=True, exist_ok=True); self.path(item["integration_id"]).write_text(canonical_json(item)+"\n", encoding="utf-8")
        event = self.events.new_event(event_id=event_id, event_type=event_type, timestamp=timestamp, project_id=item["project_id"], actor_type=actor_type, actor_id="controller", execution_id=item["execution_id"], payload={"integration":item}); self.events.append(event)
    def verify_materialized(self) -> None:
        for key, item in self.reconstruct().items():
            if self.read(key) != item or item.get("result_hash") != _hash(item): raise EventLogIntegrityError("integration result diverges from event history")


class IntegrationController:
    def __init__(self, root: str | Path, *, controller_execution_id: str = "EXEC-CONTROLLER-001") -> None:
        self.root = resolve_project_root(root); self.execution_id = controller_execution_id; self.git = GitAdapter(self.root); self.attestations = CandidateAttestationStore(self.root); self.store = IntegrationStore(self.root); self.gates = HumanGateStore(self.root); self.capabilities = CapabilityIssuer(self.root); self.authorizer = ControllerAuthorizer(self.root); self.verifiers = VerifierOrchestrator(self.root, controller_execution_id=controller_execution_id); self.compiler = ContextCompiler(self.root)

    def authorize_integrator_write(self, integration_id: str, path: str) -> str:
        item = self.store.read(integration_id)
        action = {"request_id":f"write-{integration_id}","project_id":item["project_id"],"execution_id":item["execution_id"],"baseline_sha":item["integration_baseline"],"role":"INTEGRATOR","operation":"WRITE","path":path,"intent_id":item["intent_id"],"intent_version":item["intent_version"],"graph_id":item["graph_id"],"graph_version":item["graph_version"],"eu_id":"EU-001"}
        state = {"project_root":str(self.root),"project_id":item["project_id"],"execution_id":item["execution_id"],"baseline_sha":item["integration_baseline"]}
        return self.authorizer.authorize(item["capability_id"], action, state).decision

    def _eligible(self, attestation_ids: list[str], *, project_id: str, require_human: bool) -> list[dict[str, Any]]:
        if len(attestation_ids) < 2: raise IntegrationError("at least two candidates are required")
        gates = self.gates.reconstruct(); eligible = []
        for aid in attestation_ids:
            att = self.attestations.verify(aid)
            if att["project_id"] != project_id: raise IntegrationError("candidate belongs to wrong project")
            if self.verifiers.derive_candidate_status(att["candidate_commit"]) != "VERIFIED": raise IntegrationError("candidate is not independently Spec and Standards verified")
            if require_human and not any(g["status"] == "APPROVED" and g["related_candidate"].get("candidate_sha") == att["candidate_commit"] for g in gates.values()): raise IntegrationError("candidate lacks required human approval")
            eligible.append(att)
        return eligible

    def create(self, *, integration_id: str, project_id: str, attestation_ids: list[str], intent_id: str, intent_version: int, graph_id: str, graph_version: int, timestamp: str, require_human: bool = True, event_prefix: str) -> dict[str, Any]:
        inputs = self._eligible(attestation_ids, project_id=project_id, require_human=require_human); baseline = inputs[0]["baseline_commit"]
        if any(item["baseline_commit"] != baseline for item in inputs): raise IntegrationError("integration baselines differ")
        branch = f"itdd/integration/{integration_id}"; workspace = self.root / ".idd/integration_workspaces" / integration_id
        if workspace.exists(): raise IntegrationError("integration workspace already exists")
        self.git.run("worktree", "add", "-b", branch, str(workspace), baseline)
        cap_number = int(re.sub(r"\D", "", integration_id) or "1") + 3000
        cap = self.capabilities.issue({"capability_id":f"CAP-{cap_number:03d}","schema_version":1,"project_id":project_id,"role":"INTEGRATOR","execution_id":f"EXEC-INTEGRATOR-{integration_id}","issued_at":timestamp,"baseline_sha":baseline,"allowed_reads":[".idd","."],"allowed_writes":[f".idd/integration_workspaces/{integration_id}"],"allowed_executes":["git"],"allowed_operations":["READ","WRITE","EXECUTE","CREATE_ARTIFACT"],"forbidden_operations":["PROMOTE","INTENT_APPROVAL","GRAPH_APPROVAL"],"allowed_request_types":[],"scope_bindings":{"intent_id":intent_id,"intent_version":intent_version,"graph_id":graph_id,"graph_version":graph_version,"eu_id":"EU-001"},"version":1,"issued_by":"controller"}, event_id=f"{event_prefix}-cap", timestamp=timestamp)
        packet = {"context_packet_id":f"CP-{cap_number:03d}","intent_binding":{"intent_id":intent_id,"intent_version":intent_version},"graph_binding":{"graph_id":graph_id,"graph_version":graph_version},"eu_binding":{"eu_id":"EU-001"},"authority_context":{"allowed_operations":["READ","WRITE","EXECUTE"],"acceptance_requirements":["combine only listed Git-attested candidates"]},"working_context":[{"resource_id":f"RES-{cap_number:03d}","path":f".idd/integration_workspaces/{integration_id}","purpose":"isolated integration workspace","authority":"WRITE","reason_included":"explicit integration scope","source":"controller","freshness_or_version":baseline}],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":100000}}
        compiled = self.compiler.compile(packet, capability_id=cap["capability_id"], state={"project_root":str(self.root),"project_id":project_id,"execution_id":cap["execution_id"],"baseline_sha":baseline,"role":"INTEGRATOR"}, event_id=f"{event_prefix}-packet", timestamp=timestamp)
        item = {"integration_id":integration_id,"schema_version":1,"project_id":project_id,"execution_id":cap["execution_id"],"capability_id":cap["capability_id"],"context_packet_id":compiled["context_packet_id"],"context_packet_hash":compiled["packet_hash"],"intent_id":intent_id,"intent_version":intent_version,"graph_id":graph_id,"graph_version":graph_version,"input_candidates":[x["candidate_commit"] for x in inputs],"input_attestations":attestation_ids,"integration_baseline":baseline,"integration_workspace":str(workspace),"branch":branch,"result_commit":None,"result_tree":None,"observed_changed_paths":[],"status":"CREATED","findings":[],"created_at":timestamp}
        self.store.write_event(item, event_id=f"{event_prefix}-created", event_type="integration.created", timestamp=timestamp); return item

    def run(self, integration_id: str, *, timestamp: str, event_prefix: str, semantic_conflict: bool = False, interrupted: bool = False) -> dict[str, Any]:
        item = self.store.read(integration_id)
        if interrupted: item["status"] = "INTERRUPTED"; item["findings"] = [{"classification":"INFRASTRUCTURE_ERROR","message":"integrator interrupted"}]; self.store.write_event(item, event_id=f"{event_prefix}-interrupted", event_type="integration.interrupted", timestamp=timestamp); return item
        if semantic_conflict: item["status"] = "REPLAN_REQUIRED"; item["findings"] = [{"classification":"SEMANTIC_CONFLICT","message":"integration requires redesign or replan"}]; self.store.write_event(item, event_id=f"{event_prefix}-replan", event_type="integration.replan_required", timestamp=timestamp); return item
        try:
            for candidate in item["input_candidates"]: self.git.run("-c", "user.name=ITDD Integrator", "-c", "user.email=itdd@example.invalid", "merge", "--no-edit", "--no-ff", candidate, cwd=Path(item["integration_workspace"]))
            item["result_commit"] = self.git.head(Path(item["integration_workspace"])); item["result_tree"] = self.git.tree(item["result_commit"]); item["observed_changed_paths"] = self.git.changed_paths(item["integration_baseline"], item["result_commit"]); item["status"] = "COMPLETED"; self.store.write_event(item, event_id=f"{event_prefix}-completed", event_type="integration.completed", timestamp=timestamp); return item
        except GitError as exc:
            try: self.git.run("merge", "--abort", cwd=Path(item["integration_workspace"]))
            except GitError: pass
            item["status"] = "CONFLICT"; item["findings"] = [{"classification":"MECHANICAL_CONFLICT","message":str(exc)}]; self.store.write_event(item, event_id=f"{event_prefix}-conflict", event_type="integration.conflict", timestamp=timestamp); return item

    def create_integration_verifier(self, integration_id: str, *, command: str, timestamp: str, event_prefix: str) -> dict[str, Any]:
        integration = self.store.read(integration_id)
        if integration["status"] != "COMPLETED" or not integration["result_commit"]: raise IntegrationError("integration candidate is not complete")
        number = int(re.sub(r"\D", "", integration_id) or "1") + 1000; execution_id = f"EXEC-INTEGRATION-VERIFIER-{number}"; cap_id = f"CAP-{number:03d}"; packet_id = f"CP-{number:03d}"; contract_id = f"VC-{number:03d}"
        cap = {"capability_id":cap_id,"schema_version":1,"project_id":integration["project_id"],"role":"INTEGRATION_VERIFIER","execution_id":execution_id,"issued_at":timestamp,"baseline_sha":integration["integration_baseline"],"allowed_reads":[integration["integration_workspace"]],"allowed_writes":[],"allowed_executes":["python3 -m pytest"],"allowed_operations":["READ","EXECUTE","CREATE_ARTIFACT"],"forbidden_operations":["WRITE","PROMOTE"],"allowed_request_types":[],"scope_bindings":{"intent_id":integration["intent_id"],"intent_version":integration["intent_version"],"graph_id":integration["graph_id"],"graph_version":integration["graph_version"],"eu_id":"EU-001"},"version":1,"issued_by":"controller"}
        packet = {"context_packet_id":packet_id,"intent_binding":{"intent_id":integration["intent_id"],"intent_version":integration["intent_version"]},"graph_binding":{"graph_id":integration["graph_id"],"graph_version":integration["graph_version"]},"eu_binding":{"eu_id":"EU-001"},"authority_context":{"allowed_operations":["READ","EXECUTE"],"acceptance_requirements":["integrated behavior and input regression checks"]},"working_context":[{"resource_id":f"RES-{number:03d}","path":integration["integration_workspace"],"purpose":"fresh integration verification","authority":"READ","reason_included":"exact integration candidate","source":"controller","freshness_or_version":integration["result_commit"]}],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":100000}}
        contract = {"verification_contract_id":contract_id,"project_id":integration["project_id"],"execution_id":execution_id,"role":"INTEGRATION_VERIFIER","intent_id":integration["intent_id"],"intent_version":integration["intent_version"],"graph_id":integration["graph_id"],"graph_version":integration["graph_version"],"eu_id":"EU-001","baseline_sha":integration["integration_baseline"],"candidate_sha":integration["result_commit"],"context_packet_id":packet_id,"context_packet_hash":"placeholder","required_checks":[{"check_id":f"REQCHECK-{number:03d}","kind":"INTEGRATION_TEST_COMMAND","command":command,"required_exit_code":0}],"required_artifacts":[],"allowed_changed_paths":integration["observed_changed_paths"],"created_at":timestamp,"created_by":"controller"}
        return self.verifiers.create_verifier(role="INTEGRATION_VERIFIER", execution_id=execution_id, capability=cap, packet=packet, contract=contract, event_prefix=event_prefix, timestamp=timestamp)

    def derive_integration_status(self, integration_id: str, verifier_execution_id: str, result_id: str) -> str:
        integration = self.store.read(integration_id); executions = self.verifiers.executions.reconstruct(); results = self.verifiers.verification.reconstruct()["results"]
        execution = executions.get(verifier_execution_id); result = results.get(result_id)
        if integration["status"] != "COMPLETED" or not execution or execution["role"] != "INTEGRATION_VERIFIER" or execution["candidate_sha"] != integration["result_commit"]: return "NOT_VERIFIED"
        return "INTEGRATION_VERIFIED" if execution["status"] == "COMPLETED" and result and result["status"] == "PASS" else "NOT_VERIFIED"

    def mark_verified(self, integration_id: str, *, verifier_execution_id: str, result_id: str, timestamp: str, event_prefix: str) -> dict[str, Any]:
        if self.derive_integration_status(integration_id, verifier_execution_id, result_id) != "INTEGRATION_VERIFIED": raise IntegrationError("integration verifier has not passed")
        item = self.store.read(integration_id); item["status"] = "INTEGRATION_VERIFIED"; item["integration_verifier_execution_id"] = verifier_execution_id; item["integration_verifier_result_id"] = result_id
        self.store.write_event(item, event_id=f"{event_prefix}-verified", event_type="integration.verified", timestamp=timestamp); return item

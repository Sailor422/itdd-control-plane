"""Stage E5 controller-owned live Spec/Standards verifier orchestration."""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Protocol

from control.authority.paths import AuthorityError, resolve_project_path, resolve_project_root
from control.authorization import CapabilityIssuer, ControllerAuthorizer
from control.context import ContextCompiler
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json
from control.verification import EvidenceEvaluator, VerificationStore


class VerifierOrchestrationError(ValueError):
    pass


class VerifierInterrupted(RuntimeError):
    pass


class VerifierAdapter(Protocol):
    def run(self, *, command: str, project_root: Path, execution_id: str, context_packet: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]: ...


class SubprocessVerifierAdapter:
    """Fresh-process adapter; it returns observations and cannot issue authority."""

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

    def run(self, *, command: str, project_root: Path, execution_id: str, context_packet: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
        try:
            completed = subprocess.run(shlex.split(command), cwd=project_root, capture_output=True, text=True, timeout=self.timeout_seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            raise VerifierInterrupted(f"verifier timed out: {execution_id}") from exc
        stdout = completed.stdout or ""; stderr = completed.stderr or ""
        count = _count(stdout); failed = _number(stdout, r"(\d+) failed") or (1 if completed.returncode else 0); skipped = _number(stdout, r"(\d+) skipped")
        check = {"check_id": contract["required_checks"][0]["check_id"], "command": command, "exit_code": completed.returncode, "observed_test_count": count, "passed": count if completed.returncode == 0 else max(count - failed, 0), "failed": failed, "skipped": skipped, "stdout_digest": hashlib.sha256((stdout + stderr).encode()).hexdigest(), "started_at": contract["created_at"], "finished_at": contract["created_at"]}
        return {"verifier_execution_id": execution_id, "verification_contract_id": contract["verification_contract_id"], "result": "PASS" if completed.returncode == 0 else "FAIL", "check_results": [check], "findings": [], "evidence_references": [], "candidate_sha": contract["candidate_sha"], "baseline_sha": contract["baseline_sha"], "context_packet_hash": context_packet["packet_hash"]}


def _number(text: str, pattern: str) -> int:
    match = re.search(pattern, text); return int(match.group(1)) if match else 0


def _count(text: str) -> int:
    return _number(text, r"(\d+) passed")


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{int(hashlib.sha256(value.encode()).hexdigest()[:10], 16) % 1000000000:09d}"


class VerifierExecutionStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root); self.event_log = EventLog(self.project_root)

    def _path(self, execution_id: str) -> Path:
        return resolve_project_path(self.project_root, f".idd/verifiers/executions/{execution_id}.json")

    def create(self, execution: dict[str, Any], *, event_id: str, timestamp: str) -> dict[str, Any]:
        if execution.get("status") != "CREATED": raise VerifierOrchestrationError("verifier execution must start CREATED")
        path = self._path(execution["execution_id"]); path.parent.mkdir(parents=True, exist_ok=True)
        encoded = canonical_json(execution) + "\n"
        if path.exists(): raise VerifierOrchestrationError("verifier execution already exists")
        path.write_text(encoded, encoding="utf-8")
        event = self.event_log.new_event(event_id=event_id, event_type="verifier.execution.created", timestamp=timestamp, project_id=execution["project_id"], actor_type="controller", actor_id="controller", execution_id=execution["execution_id"], payload={"execution": execution}); self.event_log.append(event); return execution

    def transition(self, execution_id: str, status: str, *, event_id: str, timestamp: str) -> dict[str, Any]:
        execution = self.read(execution_id); allowed = {"CREATED": {"LAUNCHED", "FAILED", "INTERRUPTED"}, "LAUNCHED": {"ACTIVE", "FAILED", "INTERRUPTED"}, "ACTIVE": {"COMPLETED", "FAILED", "INTERRUPTED"}}
        if status not in allowed.get(execution["status"], set()): raise VerifierOrchestrationError("invalid verifier execution transition")
        updated = deepcopy(execution); updated["status"] = status; updated["updated_at"] = timestamp
        if status == "LAUNCHED": updated["launched_at"] = timestamp
        if status in {"COMPLETED", "FAILED", "INTERRUPTED"}: updated["completed_at"] = timestamp
        self._path(execution_id).write_text(canonical_json(updated) + "\n", encoding="utf-8")
        event = self.event_log.new_event(event_id=event_id, event_type=f"verifier.execution.{status.lower()}", timestamp=timestamp, project_id=updated["project_id"], actor_type="controller", actor_id="controller", execution_id=execution_id, payload={"execution": updated}); self.event_log.append(event); return updated

    def read(self, execution_id: str) -> dict[str, Any]:
        path = self._path(execution_id)
        if not path.exists(): raise VerifierOrchestrationError("verifier execution does not exist")
        return json.loads(path.read_text(encoding="utf-8"))

    def reconstruct(self) -> dict[str, dict[str, Any]]:
        executions: dict[str, dict[str, Any]] = {}
        for event in self.event_log.verify():
            if event["event_type"].startswith("verifier.execution."):
                item = event["payload"]["execution"]; execution_id = item["execution_id"]
                if event["event_type"] == "verifier.execution.created" and execution_id in executions: raise EventLogIntegrityError("verifier execution reused")
                executions[execution_id] = item
        return executions

    def verify_materialized(self) -> None:
        for execution_id, item in self.reconstruct().items():
            if self.read(execution_id) != item: raise EventLogIntegrityError("verifier execution diverges from event history")


class VerifierOrchestrator:
    def __init__(self, project_root: str | Path, *, controller_execution_id: str = "EXEC-CONTROLLER-001") -> None:
        self.project_root = resolve_project_root(project_root); self.controller_execution_id = controller_execution_id
        self.executions = VerifierExecutionStore(self.project_root); self.capabilities = CapabilityIssuer(self.project_root); self.authorizer = ControllerAuthorizer(self.project_root); self.compiler = ContextCompiler(self.project_root); self.verification = VerificationStore(self.project_root)

    def create_verifier(self, *, role: str, execution_id: str, capability: dict[str, Any], packet: dict[str, Any], contract: dict[str, Any], event_prefix: str, timestamp: str) -> dict[str, Any]:
        if role not in {"SPEC_VERIFIER", "STANDARDS_REVIEWER", "INTEGRATION_VERIFIER"} or capability.get("role") != role or contract.get("role") != role: raise VerifierOrchestrationError("role axis mismatch")
        if execution_id == self.controller_execution_id or capability.get("execution_id") != execution_id: raise VerifierOrchestrationError("verifier must have distinct execution identity")
        if execution_id in self.executions.reconstruct() or self.executions._path(execution_id).exists(): raise VerifierOrchestrationError("verifier execution identity already exists")
        issued = self.capabilities.issue(capability, event_id=f"{event_prefix}-cap", timestamp=timestamp)
        state = {"project_root":str(self.project_root),"project_id":capability["project_id"],"execution_id":execution_id,"baseline_sha":capability["baseline_sha"],"role":role}
        compiled = self.compiler.compile(packet, capability_id=issued["capability_id"], state=state, event_id=f"{event_prefix}-packet", timestamp=timestamp)
        contract = deepcopy(contract); contract.update({"context_packet_id":compiled["context_packet_id"],"context_packet_hash":compiled["packet_hash"],"execution_id":execution_id,"role":role})
        created_contract = self.verification.create_contract(contract, event_id=f"{event_prefix}-contract", timestamp=timestamp)
        execution = {"execution_id":execution_id,"role":role,"parent_execution_id":self.controller_execution_id,"project_id":capability["project_id"],"baseline_sha":capability["baseline_sha"],"candidate_sha":created_contract["candidate_sha"],"capability_id":issued["capability_id"],"context_packet_id":compiled["context_packet_id"],"context_packet_hash":compiled["packet_hash"],"verification_contract_id":created_contract["verification_contract_id"],"verification_contract_hash":created_contract["contract_hash"],"status":"CREATED","created_at":timestamp,"updated_at":timestamp}
        self.executions.create(execution, event_id=f"{event_prefix}-execution", timestamp=timestamp); return execution

    def launch(self, execution_id: str, *, adapter: VerifierAdapter, event_prefix: str, timestamp: str) -> dict[str, Any]:
        execution = self.executions.read(execution_id); contract = self.verification.read_contract(execution["verification_contract_id"]); packet = self.compiler.store.read_packet(execution["context_packet_id"])
        command = contract["required_checks"][0].get("command") if contract["required_checks"] else None
        if not command: raise VerifierOrchestrationError("verification contract has no launchable check command")
        self.executions.transition(execution_id, "LAUNCHED", event_id=f"{event_prefix}-launched", timestamp=timestamp); self.executions.transition(execution_id, "ACTIVE", event_id=f"{event_prefix}-active", timestamp=timestamp)
        try:
            output = adapter.run(command=command, project_root=self.project_root, execution_id=execution_id, context_packet=packet, contract=contract)
            if output.get("verifier_execution_id") != execution_id or output.get("candidate_sha") != contract["candidate_sha"] or output.get("context_packet_hash") != packet["packet_hash"]: raise VerifierOrchestrationError("verifier output provenance mismatch")
            evidence = {"evidence_id":_stable_id("EV", execution_id),"verification_contract_id":contract["verification_contract_id"],"project_id":contract["project_id"],"execution_id":execution_id,"role":contract["role"],"intent_id":contract["intent_id"],"intent_version":contract["intent_version"],"graph_id":contract["graph_id"],"graph_version":contract["graph_version"],"eu_id":contract["eu_id"],"baseline_sha":contract["baseline_sha"],"candidate_sha":contract["candidate_sha"],"context_packet_id":packet["context_packet_id"],"context_packet_hash":packet["packet_hash"],"check_results":output["check_results"],"artifact_hashes":{},"observed_changed_paths":[],"created_at":timestamp,"created_by":execution_id}
            recorded = self.verification.record_evidence(evidence, event_id=f"{event_prefix}-evidence", timestamp=timestamp)
            result = EvidenceEvaluator(self.project_root).evaluate(contract["verification_contract_id"], recorded["evidence_id"], result_id=_stable_id("VR", execution_id), evaluator_execution_id=f"EXEC-EVALUATOR-{execution_id.split('-')[-1]}", event_id=f"{event_prefix}-result", timestamp=timestamp)
            self.executions.transition(execution_id, "COMPLETED", event_id=f"{event_prefix}-completed", timestamp=timestamp); return {"execution": self.executions.read(execution_id), "evidence": recorded, "result": result}
        except VerifierInterrupted:
            self.executions.transition(execution_id, "INTERRUPTED", event_id=f"{event_prefix}-interrupted", timestamp=timestamp); return {"execution": self.executions.read(execution_id), "evidence": None, "result": None}
        except Exception:
            self.executions.transition(execution_id, "FAILED", event_id=f"{event_prefix}-failed", timestamp=timestamp); raise

    def authorize_write(self, execution_id: str, path: str) -> str:
        execution = self.executions.read(execution_id); contract = self.verification.read_contract(execution["verification_contract_id"]); decision = self.authorizer.authorize(execution["capability_id"], {"request_id":f"write-{execution_id}","project_id":execution["project_id"],"execution_id":execution_id,"baseline_sha":execution["baseline_sha"],"role":execution["role"],"operation":"WRITE","path":path,"intent_id":contract["intent_id"],"intent_version":contract["intent_version"],"graph_id":contract["graph_id"],"graph_version":contract["graph_version"],"eu_id":contract["eu_id"]}, {"project_root":str(self.project_root),"project_id":execution["project_id"],"execution_id":execution_id,"baseline_sha":execution["baseline_sha"]})
        return decision.decision

    def derive_candidate_status(self, candidate_sha: str) -> str:
        state = self.executions.reconstruct(); results = self.verification.reconstruct()["results"]; axes: dict[str, bool] = {"SPEC_VERIFIER":False,"STANDARDS_REVIEWER":False}; executions: dict[str, str] = {}
        for execution in state.values():
            if execution["candidate_sha"] == candidate_sha and execution["role"] in axes and execution["status"] == "COMPLETED": executions[execution["execution_id"]] = execution["role"]
        for result in results.values():
            if result["status"] == "PASS" and result["evidence_id"]:
                evidence = self.verification.reconstruct()["evidence"].get(result["evidence_id"]); execution_id = evidence.get("execution_id") if evidence else None
                if execution_id in executions: axes[executions[execution_id]] = True
        return "VERIFIED" if all(axes.values()) and len({key for key, value in axes.items() if value}) == 2 else "NOT_VERIFIED"

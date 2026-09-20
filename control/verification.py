"""Stage E4 durable verification contracts, evidence, and mechanical evaluation."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from control.authority.paths import AuthorityError, resolve_project_path, resolve_project_root
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json
from control.models.store import StageCStore
from control.context.compiler import ContextStore, validate_context_packet


class VerificationError(ValueError):
    pass


CERTIFICATION_ROLES = frozenset({"SPEC_VERIFIER", "STANDARDS_REVIEWER", "INTEGRATION_VERIFIER"})


class VerificationStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = resolve_project_root(project_root)
        self.event_log = EventLog(self.project_root)

    def _path(self, kind: str, identity: str) -> Path:
        return resolve_project_path(self.project_root, f".idd/evidence/{kind}/{identity}.json")

    def _builder_path(self, identity: str) -> Path:
        return resolve_project_path(self.project_root, f".idd/evidence/build-records/{identity}.json")

    @staticmethod
    def _hash(document: dict[str, Any], field: str) -> str:
        value = deepcopy(document); value.pop(field, None)
        return hashlib.sha256(canonical_json(value).encode()).hexdigest()

    def _write_immutable(self, path: Path, document: dict[str, Any]) -> None:
        encoded = canonical_json(document) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != encoded: raise VerificationError("immutable verification artifact would be overwritten")
            raise VerificationError("verification artifact already exists")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(encoded, encoding="utf-8")

    def create_contract(self, contract: dict[str, Any], *, event_id: str, timestamp: str) -> dict[str, Any]:
        candidate = deepcopy(contract); candidate.setdefault("schema_version", 1); candidate.setdefault("version", 1); candidate["contract_hash"] = self._hash(candidate, "contract_hash")
        validate_contract(candidate)
        self._validate_authoritative_bindings(candidate)
        self._write_immutable(self._path("contracts", candidate["verification_contract_id"]), candidate)
        event = self.event_log.new_event(event_id=event_id, event_type="verification.contract.created", timestamp=timestamp, project_id=candidate["project_id"], actor_type="controller", actor_id=candidate["created_by"], execution_id=candidate["execution_id"], payload={"contract": candidate})
        self.event_log.append(event); return candidate

    def record_evidence(self, evidence: dict[str, Any], *, event_id: str, timestamp: str) -> dict[str, Any]:
        candidate = deepcopy(evidence); candidate.setdefault("schema_version", 1); candidate.setdefault("version", 1); candidate["evidence_hash"] = self._hash(candidate, "evidence_hash")
        validate_evidence(candidate)
        contract = self.read_contract(candidate["verification_contract_id"])
        _assert_binding(contract, candidate)
        self._validate_certification_provenance(contract, candidate)
        self._write_immutable(self._path("records", candidate["evidence_id"]), candidate)
        event = self.event_log.new_event(event_id=event_id, event_type="verification.evidence.recorded", timestamp=timestamp, project_id=candidate["project_id"], actor_type="verifier", actor_id=candidate["created_by"], execution_id=candidate["execution_id"], payload={"evidence": candidate})
        self.event_log.append(event); return candidate

    def record_builder_evidence(self, evidence: dict[str, Any], *, event_id: str, timestamp: str) -> dict[str, Any]:
        """Persist Builder-scoped observations without entering certification state."""
        candidate = deepcopy(evidence); candidate.setdefault("schema_version", 1); candidate.setdefault("version", 1)
        required = {"evidence_id", "schema_version", "version", "project_id", "execution_id", "role", "baseline_sha", "candidate_sha", "check_results", "artifact_hashes", "observed_changed_paths", "created_at", "created_by", "evidence_hash"}
        candidate["evidence_hash"] = self._hash(candidate, "evidence_hash")
        if set(candidate) != required or not re.fullmatch(r"BE-[0-9]+", candidate.get("evidence_id", "")):
            raise VerificationError("INVALID_BUILDER_EXECUTION_EVIDENCE")
        if candidate.get("role") != "BUILDER" or candidate.get("created_by") != candidate.get("execution_id"):
            raise VerificationError("DENY_BUILDER_PROVENANCE_MISMATCH")
        if not isinstance(candidate.get("check_results"), list) or not isinstance(candidate.get("artifact_hashes"), dict) or not isinstance(candidate.get("observed_changed_paths"), list):
            raise VerificationError("INVALID_BUILDER_EXECUTION_EVIDENCE")
        if not re.fullmatch(r"[0-9a-f]{40,64}", candidate["baseline_sha"]) or not re.fullmatch(r"[0-9a-f]{40,64}", candidate["candidate_sha"]):
            raise VerificationError("INVALID_BUILDER_EXECUTION_EVIDENCE")
        self._write_immutable(self._builder_path(candidate["evidence_id"]), candidate)
        event = self.event_log.new_event(event_id=event_id, event_type="builder.evidence.recorded", timestamp=timestamp, project_id=candidate["project_id"], actor_type="builder", actor_id=candidate["created_by"], execution_id=candidate["execution_id"], payload={"evidence": candidate})
        self.event_log.append(event); return candidate

    def _validate_certification_provenance(self, contract: dict[str, Any], evidence: dict[str, Any]) -> None:
        if contract.get("role") == "BUILDER":
            raise VerificationError("DENY_BUILDER_CERTIFICATION: Builder execution cannot record certification evidence")
        if contract.get("role") not in CERTIFICATION_ROLES:
            raise VerificationError("DENY_UNAUTHORIZED_CERTIFICATION_ROLE")
        if evidence.get("created_by") != evidence.get("execution_id"):
            raise VerificationError("DENY_CERTIFICATION_PROVENANCE_MISMATCH: creator is not the execution")
        execution = None
        for event in self.event_log.verify():
            if event["event_type"] != "verifier.execution.created":
                continue
            item = event["payload"].get("execution", {})
            if item.get("execution_id") == evidence.get("execution_id"):
                execution = item
                break
        if execution is None:
            raise VerificationError("DENY_UNAUTHORIZED_VERIFIER_EXECUTION: durable verifier execution is required")
        for key in ("execution_id", "role", "project_id", "baseline_sha", "candidate_sha", "verification_contract_id"):
            if execution.get(key) != evidence.get(key) and key != "verification_contract_id":
                raise VerificationError(f"DENY_CERTIFICATION_PROVENANCE_MISMATCH: {key}")
        if execution.get("verification_contract_id") != contract.get("verification_contract_id"):
            raise VerificationError("DENY_CERTIFICATION_PROVENANCE_MISMATCH: verification_contract_id")
        if execution.get("role") not in CERTIFICATION_ROLES:
            raise VerificationError("DENY_UNAUTHORIZED_CERTIFICATION_ROLE")

    def read_contract(self, contract_id: str) -> dict[str, Any]:
        path = self._path("contracts", contract_id)
        if not path.exists(): raise VerificationError("verification contract does not exist")
        try: document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc: raise VerificationError("verification contract is malformed") from exc
        validate_contract(document); return document

    def read_evidence(self, evidence_id: str) -> dict[str, Any]:
        path = self._path("records", evidence_id)
        if not path.exists(): raise VerificationError("verification evidence does not exist")
        try: document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc: raise VerificationError("verification evidence is malformed") from exc
        validate_evidence(document); return document

    def reconstruct(self) -> dict[str, dict[str, Any]]:
        contracts: dict[str, dict[str, Any]] = {}; evidence: dict[str, dict[str, Any]] = {}; results: dict[str, dict[str, Any]] = {}
        for event in self.event_log.verify():
            if event["event_type"] == "verification.contract.created":
                item = event["payload"]["contract"]; validate_contract(item)
                if item["contract_hash"] != self._hash(item, "contract_hash"): raise EventLogIntegrityError("contract hash mismatch")
                if item["verification_contract_id"] in contracts: raise EventLogIntegrityError("contract identity reused")
                contracts[item["verification_contract_id"]] = item
            elif event["event_type"] == "verification.evidence.recorded":
                item = event["payload"]["evidence"]; validate_evidence(item)
                if item["evidence_hash"] != self._hash(item, "evidence_hash"): raise EventLogIntegrityError("evidence hash mismatch")
                if item["evidence_id"] in evidence: raise EventLogIntegrityError("evidence identity reused")
                evidence[item["evidence_id"]] = item
            elif event["event_type"] == "verification.result.evaluated":
                item = event["payload"]["result"]; validate_result(item); results[item["result_id"]] = item
        return {"contracts": contracts, "evidence": evidence, "results": results}

    def verify_materialized(self) -> None:
        state = self.reconstruct()
        for item in state["contracts"].values():
            if self.read_contract(item["verification_contract_id"]) != item: raise EventLogIntegrityError("contract diverges from event history")
        for item in state["evidence"].values():
            if self.read_evidence(item["evidence_id"]) != item: raise EventLogIntegrityError("evidence diverges from event history")

    def _validate_authoritative_bindings(self, contract: dict[str, Any]) -> None:
        state = StageCStore(self.project_root).reconstruct(); intent = state["intents"].get((contract["intent_id"], contract["intent_version"]))
        graph = state["graphs"].get((contract["graph_id"], contract["graph_version"]))
        if intent is None or graph is None or graph["intent_id"] != intent["intent_id"] or graph["intent_version"] != intent["version"]: raise VerificationError("contract intent/graph binding is not durable")
        if not any(node["eu_id"] == contract["eu_id"] for node in graph["nodes"]): raise VerificationError("contract EU is not in graph")
        packet = ContextStore(self.project_root).read_packet(contract["context_packet_id"])
        if packet["project_id"] != contract["project_id"] or packet["execution_id"] != contract["execution_id"] or packet["baseline_sha"] != contract["baseline_sha"] or packet["packet_hash"] != contract["context_packet_hash"]: raise VerificationError("contract context binding is invalid")


def _bindings() -> tuple[str, ...]:
    return ("project_id", "execution_id", "role", "intent_id", "intent_version", "graph_id", "graph_version", "eu_id", "baseline_sha", "candidate_sha", "context_packet_id", "context_packet_hash", "verification_contract_id")


def _assert_binding(contract: dict[str, Any], evidence: dict[str, Any]) -> None:
    for key in _bindings():
        if evidence.get(key) != contract.get(key): raise VerificationError(f"evidence binding mismatch: {key}")


def _id(value: Any, pattern: str, name: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(pattern, value): raise VerificationError(f"invalid {name}")


def validate_contract(contract: dict[str, Any]) -> None:
    required = {"verification_contract_id", "schema_version", "version", "project_id", "execution_id", "role", "intent_id", "intent_version", "graph_id", "graph_version", "eu_id", "baseline_sha", "candidate_sha", "context_packet_id", "context_packet_hash", "required_checks", "required_artifacts", "allowed_changed_paths", "created_at", "created_by", "contract_hash"}
    if set(contract) != required: raise VerificationError("contract fields do not match schema")
    _id(contract["verification_contract_id"], r"VC-[0-9]{3,}", "verification_contract_id"); _id(contract["execution_id"], r"EXEC-[A-Za-z0-9._-]+", "execution_id"); _id(contract["intent_id"], r"I-[0-9]+", "intent_id"); _id(contract["graph_id"], r"G-[0-9]+", "graph_id"); _id(contract["eu_id"], r"EU-[0-9]+", "eu_id")
    for key in ("project_id", "role", "context_packet_id", "context_packet_hash", "created_at", "created_by"):
        if not isinstance(contract[key], str) or not contract[key]: raise VerificationError(f"{key} must be non-empty")
    for key in ("intent_version", "graph_version", "version"):
        if not isinstance(contract[key], int) or contract[key] < 1: raise VerificationError(f"{key} must be positive")
    if not re.fullmatch(r"[0-9a-f]{40,64}", contract["baseline_sha"]) or not re.fullmatch(r"[0-9a-f]{40,64}", contract["candidate_sha"]): raise VerificationError("invalid baseline or candidate SHA")
    for key in ("required_checks", "required_artifacts", "allowed_changed_paths"):
        if not isinstance(contract[key], list): raise VerificationError(f"{key} must be a list")
    if contract["contract_hash"] != _document_hash(contract, "contract_hash"): raise VerificationError("contract hash mismatch")


def validate_evidence(evidence: dict[str, Any]) -> None:
    required = {"evidence_id", "schema_version", "version", "verification_contract_id", "project_id", "execution_id", "role", "intent_id", "intent_version", "graph_id", "graph_version", "eu_id", "baseline_sha", "candidate_sha", "context_packet_id", "context_packet_hash", "check_results", "artifact_hashes", "observed_changed_paths", "created_at", "created_by", "evidence_hash"}
    if set(evidence) != required: raise VerificationError("evidence fields do not match schema")
    _id(evidence["evidence_id"], r"EV-[0-9]{3,}", "evidence_id"); _id(evidence["verification_contract_id"], r"VC-[0-9]{3,}", "verification_contract_id")
    if not isinstance(evidence["check_results"], list) or not isinstance(evidence["artifact_hashes"], dict) or not isinstance(evidence["observed_changed_paths"], list): raise VerificationError("invalid evidence collections")
    if evidence["evidence_hash"] != _document_hash(evidence, "evidence_hash"): raise VerificationError("evidence hash mismatch")


def _document_hash(document: dict[str, Any], field: str) -> str:
    value = deepcopy(document); value.pop(field, None); return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def validate_result(result: dict[str, Any]) -> None:
    required = {"result_id", "schema_version", "verification_contract_id", "evidence_id", "status", "reason_code", "evaluated_at", "evaluator_execution_id", "result_hash"}
    if set(result) != required: raise VerificationError("result fields do not match schema")
    _id(result["result_id"], r"VR-[0-9]{3,}", "result_id")
    if result["status"] not in {"PASS", "FAIL"}: raise VerificationError("invalid result status")
    if result["result_hash"] != _document_hash(result, "result_hash"): raise VerificationError("result hash mismatch")


class EvidenceEvaluator:
    def __init__(self, project_root: str | Path) -> None:
        self.store = VerificationStore(project_root); self.project_root = self.store.project_root

    def evaluate(self, contract_id: str, evidence_id: str | None, *, result_id: str, evaluator_execution_id: str, event_id: str, timestamp: str) -> dict[str, Any]:
        try: contract = self.store.read_contract(contract_id)
        except VerificationError: return self._result(result_id, contract_id, evidence_id or "", "FAIL", "FAIL_CONTRACT_INVALID", evaluator_execution_id, event_id, timestamp)
        if evidence_id is None: return self._result(result_id, contract_id, "", "FAIL", "FAIL_EVIDENCE_MISSING", evaluator_execution_id, event_id, timestamp)
        try: evidence = self.store.read_evidence(evidence_id)
        except VerificationError: return self._result(result_id, contract_id, evidence_id, "FAIL", "FAIL_EVIDENCE_TAMPERED", evaluator_execution_id, event_id, timestamp)
        try: _assert_binding(contract, evidence)
        except VerificationError as exc: return self._result(result_id, contract_id, evidence_id, "FAIL", "FAIL_CONTRACT_MISMATCH", evaluator_execution_id, event_id, timestamp, detail=str(exc))
        reason = self._check(contract, evidence)
        return self._result(result_id, contract_id, evidence_id, "PASS" if reason == "PASS" else "FAIL", reason, evaluator_execution_id, event_id, timestamp)

    def _check(self, contract: dict[str, Any], evidence: dict[str, Any]) -> str:
        if evidence["baseline_sha"] != contract["baseline_sha"]: return "FAIL_BASELINE_MISMATCH"
        if evidence["candidate_sha"] != contract["candidate_sha"]: return "FAIL_CANDIDATE_MISMATCH"
        try:
            packet = ContextStore(self.project_root).read_packet(contract["context_packet_id"])
        except Exception:
            return "FAIL_CONTEXT_MISMATCH"
        if packet["packet_hash"] != contract["context_packet_hash"]: return "FAIL_CONTEXT_MISMATCH"
        checks = {item.get("check_id"): item for item in evidence["check_results"]}
        for required in contract["required_checks"]:
            check_id = required.get("check_id")
            observed = checks.get(check_id)
            if observed is None: return "FAIL_REQUIRED_CHECK_MISSING"
            kind = required.get("kind")
            if kind == "TEST_COMMAND":
                if observed.get("command") != required.get("command"): return "FAIL_TEST_COMMAND_MISMATCH"
                if observed.get("exit_code") != required.get("required_exit_code", 0): return "FAIL_TEST_FAILURE"
                if required.get("expected_test_count") is not None and observed.get("observed_test_count") != required["expected_test_count"]: return "FAIL_TEST_COUNT_MISMATCH"
                if required.get("minimum_test_count") is not None and observed.get("observed_test_count", 0) < required["minimum_test_count"]: return "FAIL_TEST_COUNT_MISMATCH"
                if observed.get("failed", 0) or observed.get("skipped", 0): return "FAIL_TEST_FAILURE"
        allowed = [Path(path) for path in contract["allowed_changed_paths"]]
        for changed in evidence["observed_changed_paths"]:
            path = Path(changed)
            if path.is_absolute() or ".." in path.parts or not any(path == grant or grant in path.parents for grant in allowed): return "FAIL_UNAUTHORIZED_PATH_CHANGE"
        for artifact in contract["required_artifacts"]:
            path = artifact.get("path"); expected = artifact.get("sha256")
            if not isinstance(path, str) or not isinstance(expected, str): return "FAIL_REQUIRED_ARTIFACT_MISSING"
            try: actual_path = resolve_project_path(self.project_root, path)
            except AuthorityError: return "FAIL_REQUIRED_ARTIFACT_MISSING"
            if not actual_path.is_file(): return "FAIL_REQUIRED_ARTIFACT_MISSING"
            actual = hashlib.sha256(actual_path.read_bytes()).hexdigest()
            if actual != expected or evidence["artifact_hashes"].get(path) != actual: return "FAIL_ARTIFACT_HASH_MISMATCH"
        return "PASS"

    def _result(self, result_id: str, contract_id: str, evidence_id: str, status: str, reason: str, evaluator_execution_id: str, event_id: str, timestamp: str, detail: str = "") -> dict[str, Any]:
        result = {"result_id": result_id, "schema_version": 1, "verification_contract_id": contract_id, "evidence_id": evidence_id, "status": status, "reason_code": reason, "evaluated_at": timestamp, "evaluator_execution_id": evaluator_execution_id, "result_hash": ""}
        result["result_hash"] = _document_hash(result, "result_hash"); validate_result(result)
        event = self.store.event_log.new_event(event_id=event_id, event_type="verification.result.evaluated", timestamp=timestamp, project_id="verification", actor_type="evaluator", actor_id=evaluator_execution_id, execution_id=evaluator_execution_id, payload={"result": result, "detail": detail})
        self.store.event_log.append(event); return result

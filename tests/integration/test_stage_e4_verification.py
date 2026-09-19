import hashlib
import json
from pathlib import Path

import pytest

from control.authorization import CapabilityIssuer
from control.context import ContextCompiler
from control.events.format import canonical_json
from control.models.store import StageCStore
from control.verification import EvidenceEvaluator, VerificationError, VerificationStore


BASELINE = "d" * 40
CANDIDATE = "e" * 40


def setup(root: Path):
    (root / "src").mkdir(); (root / "src/a.py").write_text("class A: pass\n"); (root / "src/b.py").write_text("class B: pass\n")
    intent = {"intent_id":"I-001","version":1,"status":"DRAFT","created_at":"2026-09-20T00:00:00Z","created_by":"operator","project_id":"e4","title":"verification fixture","purpose":"prove evidence","requirements":[{"requirement_id":"REQ-001","text":"prove EU"}],"constraints":[],"acceptance_summary":"bound proof","source_event_id":"evt-intent","schema_version":1}
    graph = {"graph_id":"G-001","version":1,"project_id":"e4","intent_id":"I-001","intent_version":1,"status":"ACTIVE","created_at":"2026-09-20T00:00:02Z","created_by":"planner","nodes":[{"eu_id":"EU-001","requirement_ids":["REQ-001"]}],"edges":[],"reason":"fixture","source_event_id":"evt-graph","schema_version":1}
    stage_c = StageCStore(root); stage_c.create_intent_draft(intent, event_id="evt-intent", timestamp="2026-09-20T00:00:00Z", actor_type="agent", actor_id="operator"); stage_c.approve_intent("I-001", 1, event_id="evt-approve", timestamp="2026-09-20T00:00:01Z", actor_type="human", actor_id="operator"); stage_c.create_graph(graph, event_id="evt-graph", timestamp="2026-09-20T00:00:02Z", actor_type="agent", actor_id="planner")
    capability = {"capability_id":"CAP-904","schema_version":1,"project_id":"e4","role":"SPEC_VERIFIER","execution_id":"EXEC-VERIFIER-401","issued_at":"2026-09-20T00:00:03Z","baseline_sha":BASELINE,"allowed_reads":["src/a.py","src/b.py"],"allowed_writes":[],"allowed_executes":[],"allowed_operations":["READ","EXECUTE","CREATE_ARTIFACT"],"forbidden_operations":["WRITE","PROMOTE"],"allowed_request_types":[],"scope_bindings":{"intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001"},"version":1,"issued_by":"controller"}
    CapabilityIssuer(root).issue(capability, event_id="evt-cap", timestamp="2026-09-20T00:00:03Z")
    packet = {"context_packet_id":"CP-001","intent_binding":{"intent_id":"I-001","intent_version":1},"graph_binding":{"graph_id":"G-001","graph_version":1},"eu_binding":{"eu_id":"EU-001"},"authority_context":{"allowed_operations":["READ"],"acceptance_requirements":["3 tests"]},"working_context":[{"resource_id":"RES-001","path":"src/a.py","purpose":"fixture","authority":"READ","reason_included":"EU","source":"fixture","freshness_or_version":"HEAD"}],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":100000}}
    state = {"project_root":str(root),"project_id":"e4","execution_id":"EXEC-VERIFIER-401","baseline_sha":BASELINE,"role":"SPEC_VERIFIER"}
    created_packet = ContextCompiler(root).compile(packet, capability_id="CAP-904", state=state, event_id="evt-packet", timestamp="2026-09-20T00:00:04Z")
    artifact = root / "artifacts/report.txt"; artifact.parent.mkdir(); artifact.write_text("verification report\n")
    return created_packet, artifact


def contract(packet, artifact: Path):
    return {"verification_contract_id":"VC-001","project_id":"e4","execution_id":"EXEC-VERIFIER-401","role":"SPEC_VERIFIER","intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001","baseline_sha":BASELINE,"candidate_sha":CANDIDATE,"context_packet_id":"CP-001","context_packet_hash":packet["packet_hash"],"required_checks":[{"check_id":"REQCHECK-001","kind":"TEST_COMMAND","command":"python -m pytest tests/e4 -q","required_exit_code":0,"expected_test_count":3}],"required_artifacts":[{"artifact_id":"A-001","path":"artifacts/report.txt","sha256":hashlib.sha256(artifact.read_bytes()).hexdigest()}],"allowed_changed_paths":["artifacts/report.txt"],"created_at":"2026-09-20T00:00:05Z","created_by":"controller"}


def evidence(contract, artifact: Path, *, evidence_id="EV-001", **overrides):
    item = {"evidence_id":evidence_id,"verification_contract_id":contract["verification_contract_id"],"project_id":contract["project_id"],"execution_id":contract["execution_id"],"role":contract["role"],"intent_id":contract["intent_id"],"intent_version":contract["intent_version"],"graph_id":contract["graph_id"],"graph_version":contract["graph_version"],"eu_id":contract["eu_id"],"baseline_sha":contract["baseline_sha"],"candidate_sha":contract["candidate_sha"],"context_packet_id":contract["context_packet_id"],"context_packet_hash":contract["context_packet_hash"],"check_results":[{"check_id":"REQCHECK-001","command":"python -m pytest tests/e4 -q","exit_code":0,"observed_test_count":3,"passed":3,"failed":0,"skipped":0,"stdout_digest":"a"*64,"started_at":"2026-09-20T00:01:00Z","finished_at":"2026-09-20T00:01:01Z"}],"artifact_hashes":{"artifacts/report.txt":hashlib.sha256(artifact.read_bytes()).hexdigest()},"observed_changed_paths":["artifacts/report.txt"],"created_at":"2026-09-20T00:01:02Z","created_by":"verifier-execution-401"}
    item.update(overrides); return item


def test_valid_bound_evidence_passes_and_reconstructs(tmp_path: Path):
    packet, artifact = setup(tmp_path); store = VerificationStore(tmp_path); vc = store.create_contract(contract(packet, artifact), event_id="evt-contract", timestamp="2026-09-20T00:00:05Z")
    ev = store.record_evidence(evidence(vc, artifact), event_id="evt-evidence", timestamp="2026-09-20T00:01:02Z")
    result = EvidenceEvaluator(tmp_path).evaluate("VC-001", "EV-001", result_id="VR-001", evaluator_execution_id="EXEC-EVALUATOR-401", event_id="evt-result", timestamp="2026-09-20T00:02:00Z")
    assert result["status"] == "PASS" and result["reason_code"] == "PASS"
    fresh = EvidenceEvaluator(tmp_path); assert fresh.store.reconstruct()["contracts"]["VC-001"] == vc; assert fresh.store.reconstruct()["evidence"]["EV-001"] == ev
    assert fresh.evaluate("VC-001", "EV-001", result_id="VR-002", evaluator_execution_id="EXEC-EVALUATOR-402", event_id="evt-result-2", timestamp="2026-09-20T00:03:00Z")["status"] == "PASS"


@pytest.mark.parametrize(("field", "value", "reason"), [
    ("candidate_sha", "f" * 40, "FAIL_CANDIDATE_MISMATCH"),
    ("baseline_sha", "a" * 40, "FAIL_BASELINE_MISMATCH"),
    ("context_packet_id", "CP-999", "FAIL_CONTRACT_MISMATCH"),
])
def test_binding_mismatches_cannot_be_recorded_as_valid_evidence(tmp_path: Path, field, value, reason):
    packet, artifact = setup(tmp_path); store = VerificationStore(tmp_path); vc = store.create_contract(contract(packet, artifact), event_id="evt-contract", timestamp="2026-09-20T00:00:05Z")
    bad = evidence(vc, artifact, evidence_id="EV-002", **{field:value})
    # A mismatched record is rejected before it can become durable proof.
    with pytest.raises(VerificationError): store.record_evidence(bad, event_id="evt-bad", timestamp="2026-09-20T00:01:02Z")


@pytest.mark.parametrize(("change", "reason"), [
    ({"check_results":[{"check_id":"REQCHECK-001","command":"wrong command","exit_code":0,"observed_test_count":3,"passed":3,"failed":0,"skipped":0}],}, "FAIL_TEST_COMMAND_MISMATCH"),
    ({"check_results":[{"check_id":"REQCHECK-001","command":"python -m pytest tests/e4 -q","exit_code":0,"observed_test_count":1,"passed":1,"failed":0,"skipped":0}],}, "FAIL_TEST_COUNT_MISMATCH"),
    ({"check_results":[{"check_id":"REQCHECK-001","command":"python -m pytest tests/e4 -q","exit_code":0,"observed_test_count":3,"passed":3,"failed":0,"skipped":0}], "observed_changed_paths":["src/unauthorized.py"]}, "FAIL_UNAUTHORIZED_PATH_CHANGE"),
    ({"check_results":[],}, "FAIL_REQUIRED_CHECK_MISSING"),
])
def test_false_pass_inputs_fail_mechanically(tmp_path: Path, change, reason):
    packet, artifact = setup(tmp_path); store = VerificationStore(tmp_path); vc = store.create_contract(contract(packet, artifact), event_id="evt-contract", timestamp="2026-09-20T00:00:05Z")
    ev = evidence(vc, artifact, evidence_id="EV-003", **change); store.record_evidence(ev, event_id="evt-evidence", timestamp="2026-09-20T00:01:02Z")
    result = EvidenceEvaluator(tmp_path).evaluate("VC-001", "EV-003", result_id="VR-003", evaluator_execution_id="EXEC-EVALUATOR-401", event_id="evt-result", timestamp="2026-09-20T00:02:00Z")
    assert result["status"] == "FAIL" and result["reason_code"] == reason


def test_missing_artifact_claim_builder_claim_and_tamper_fail(tmp_path: Path):
    packet, artifact = setup(tmp_path); store = VerificationStore(tmp_path); vc = store.create_contract(contract(packet, artifact), event_id="evt-contract", timestamp="2026-09-20T00:00:05Z")
    store.record_evidence(evidence(vc, artifact, evidence_id="EV-004"), event_id="evt-evidence", timestamp="2026-09-20T00:01:02Z")
    artifact.unlink(); assert EvidenceEvaluator(tmp_path).evaluate("VC-001", None, result_id="VR-004", evaluator_execution_id="EXEC-EVALUATOR-401", event_id="evt-result-4", timestamp="2026-09-20T00:02:00Z")["reason_code"] == "FAIL_EVIDENCE_MISSING"
    assert EvidenceEvaluator(tmp_path).evaluate("VC-001", "EV-004", result_id="VR-006", evaluator_execution_id="EXEC-EVALUATOR-401", event_id="evt-result-4a", timestamp="2026-09-20T00:02:00Z")["reason_code"] == "FAIL_REQUIRED_ARTIFACT_MISSING"
    # A builder claim is not an evidence record and cannot be evaluated as PASS.
    assert EvidenceEvaluator(tmp_path).evaluate("VC-001", "EV-NONE", result_id="VR-005", evaluator_execution_id="EXEC-EVALUATOR-401", event_id="evt-result-5", timestamp="2026-09-20T00:02:01Z")["status"] == "FAIL"


def test_artifact_context_evidence_and_contract_tampering_fail(tmp_path: Path):
    packet, artifact = setup(tmp_path); store = VerificationStore(tmp_path); vc = store.create_contract(contract(packet, artifact), event_id="evt-contract", timestamp="2026-09-20T00:00:05Z")
    ev = store.record_evidence(evidence(vc, artifact, evidence_id="EV-006"), event_id="evt-evidence", timestamp="2026-09-20T00:01:02Z")
    artifact.write_text("tampered\n")
    assert EvidenceEvaluator(tmp_path).evaluate("VC-001", "EV-006", result_id="VR-006", evaluator_execution_id="EXEC-EVALUATOR-401", event_id="evt-result-6", timestamp="2026-09-20T00:02:00Z")["reason_code"] == "FAIL_ARTIFACT_HASH_MISMATCH"
    artifact.write_text("verification report\n")
    packet_path = ContextCompiler(tmp_path).store._packet_path("CP-001", 1); packet_data = json.loads(packet_path.read_text()); packet_data["authority_context"]["acceptance_requirements"] = ["tampered"]; packet_path.write_text(json.dumps(packet_data))
    assert EvidenceEvaluator(tmp_path).evaluate("VC-001", "EV-006", result_id="VR-007", evaluator_execution_id="EXEC-EVALUATOR-401", event_id="evt-result-7", timestamp="2026-09-20T00:02:01Z")["reason_code"] == "FAIL_CONTEXT_MISMATCH"
    evidence_path = store._path("records", "EV-006"); evidence_data = json.loads(evidence_path.read_text()); evidence_data["candidate_sha"] = "f" * 40; evidence_path.write_text(json.dumps(evidence_data))
    with pytest.raises(Exception): store.read_evidence("EV-006")
    contract_path = store._path("contracts", "VC-001"); contract_data = json.loads(contract_path.read_text()); contract_data["candidate_sha"] = "f" * 40; contract_path.write_text(json.dumps(contract_data))
    with pytest.raises(Exception): store.read_contract("VC-001")

import hashlib
from pathlib import Path

import pytest

from control.authorization import CapabilityIssuer
from control.context import ContextCompiler
from control.events.format import canonical_json
from control.verification import EvidenceEvaluator, VerificationError, VerificationStore
from control.verifier import VerifierExecutionStore, VerifierOrchestrator
from tests.integration.test_stage_e4_verification import CANDIDATE, BASELINE, setup
from tests.integration.test_stage_e5_verifiers import create_axes


def builder_contract_fixture(root: Path, role: str):
    setup(root)
    issuer = CapabilityIssuer(root)
    capability = {
        "capability_id": "CAP-905", "schema_version": 1, "project_id": "e4", "role": "BUILDER",
        "execution_id": "EXEC-BUILDER-405", "issued_at": "2026-09-20T02:00:00Z", "baseline_sha": BASELINE,
        "allowed_reads": ["src/a.py"], "allowed_writes": ["src/a.py"], "allowed_executes": ["python3"],
        "allowed_operations": ["READ", "WRITE", "EXECUTE", "CREATE_ARTIFACT"],
        "forbidden_operations": ["PROMOTE"], "allowed_request_types": [],
        "scope_bindings": {"intent_id": "I-001", "intent_version": 1, "graph_id": "G-001", "graph_version": 1, "eu_id": "EU-001"},
        "version": 1, "issued_by": "controller",
    }
    issued = issuer.issue(capability, event_id="builder-cap", timestamp="2026-09-20T02:00:00Z")
    packet = ContextCompiler(root).compile({
        "context_packet_id": "CP-905", "intent_binding": {"intent_id": "I-001", "intent_version": 1},
        "graph_binding": {"graph_id": "G-001", "graph_version": 1}, "eu_binding": {"eu_id": "EU-001"},
        "authority_context": {"allowed_operations": ["READ", "WRITE", "EXECUTE"], "acceptance_requirements": ["candidate output"]},
        "working_context": [{"resource_id": "RES-905", "path": "src/a.py", "purpose": "Builder implementation", "authority": "WRITE", "reason_included": "approved EU", "source": "approved graph", "freshness_or_version": BASELINE}],
        "knowledge_context": [], "evidence_context": [], "context_budget": {"max_bytes": 100000},
    }, capability_id=issued["capability_id"], state={"project_root": str(root), "project_id": "e4", "execution_id": "EXEC-BUILDER-405", "baseline_sha": BASELINE, "role": "BUILDER"}, event_id="builder-packet", timestamp="2026-09-20T02:00:01Z")
    contract = VerificationStore(root).create_contract({
        "verification_contract_id": "VC-905", "project_id": "e4", "execution_id": "EXEC-BUILDER-405", "role": role,
        "intent_id": "I-001", "intent_version": 1, "graph_id": "G-001", "graph_version": 1, "eu_id": "EU-001",
        "baseline_sha": BASELINE, "candidate_sha": CANDIDATE, "context_packet_id": packet["context_packet_id"],
        "context_packet_hash": packet["packet_hash"], "required_checks": [], "required_artifacts": [],
        "allowed_changed_paths": [], "created_at": "2026-09-20T02:00:02Z", "created_by": "controller",
    }, event_id="builder-contract", timestamp="2026-09-20T02:00:02Z")
    VerifierExecutionStore(root).create({
        "execution_id": "EXEC-BUILDER-405", "role": "BUILDER", "parent_execution_id": "EXEC-CONTROLLER-405",
        "project_id": "e4", "baseline_sha": BASELINE, "candidate_sha": CANDIDATE, "capability_id": issued["capability_id"],
        "context_packet_id": packet["context_packet_id"], "context_packet_hash": packet["packet_hash"],
        "verification_contract_id": contract["verification_contract_id"], "verification_contract_hash": contract["contract_hash"],
        "status": "CREATED", "created_at": "2026-09-20T02:00:03Z", "updated_at": "2026-09-20T02:00:03Z",
    }, event_id="builder-execution", timestamp="2026-09-20T02:00:03Z")
    return VerificationStore(root), contract, packet


def certification_evidence(contract, *, created_by="EXEC-BUILDER-405", role=None, evidence_id="EV-905"):
    item = {
        "evidence_id": evidence_id, "verification_contract_id": contract["verification_contract_id"], "project_id": contract["project_id"],
        "execution_id": contract["execution_id"], "role": role or contract["role"], "intent_id": contract["intent_id"], "intent_version": contract["intent_version"],
        "graph_id": contract["graph_id"], "graph_version": contract["graph_version"], "eu_id": contract["eu_id"], "baseline_sha": contract["baseline_sha"],
        "candidate_sha": contract["candidate_sha"], "context_packet_id": contract["context_packet_id"], "context_packet_hash": contract["context_packet_hash"],
        "check_results": [], "artifact_hashes": {}, "observed_changed_paths": [], "created_at": "2026-09-20T02:00:04Z", "created_by": created_by,
    }
    item["evidence_hash"] = hashlib.sha256(canonical_json(item).encode()).hexdigest()
    return item


def test_builder_can_record_scoped_execution_evidence_without_certifying(tmp_path: Path):
    store, contract, _ = builder_contract_fixture(tmp_path, "BUILDER")
    record = store.record_builder_evidence({
        "evidence_id": "BE-905", "project_id": "e4", "execution_id": "EXEC-BUILDER-405", "role": "BUILDER",
        "baseline_sha": BASELINE, "candidate_sha": CANDIDATE, "check_results": [{"command": "python3 -m pytest"}],
        "artifact_hashes": {}, "observed_changed_paths": ["src/a.py"], "created_at": "2026-09-20T02:00:04Z", "created_by": "EXEC-BUILDER-405",
    }, event_id="builder-observation", timestamp="2026-09-20T02:00:04Z")
    assert record["role"] == "BUILDER"
    assert (tmp_path / ".idd/evidence/build-records/BE-905.json").exists()
    assert store.reconstruct()["evidence"] == {}
    with pytest.raises(VerificationError, match="DENY_BUILDER_CERTIFICATION"):
        store.record_evidence(certification_evidence(contract), event_id="builder-cert", timestamp="2026-09-20T02:00:05Z")


@pytest.mark.parametrize("role", ["BUILDER", "SPEC_VERIFIER", "STANDARDS_REVIEWER"])
def test_builder_originated_certification_is_rejected_at_provenance_boundary(tmp_path: Path, role: str):
    store, contract, _ = builder_contract_fixture(tmp_path, role)
    before = store.reconstruct()
    with pytest.raises(VerificationError, match="DENY_") as exc:
        store.record_evidence(certification_evidence(contract, role=role), event_id=f"builder-cert-{role}", timestamp="2026-09-20T02:00:05Z")
    assert ("DENY_BUILDER_CERTIFICATION" in str(exc.value) or "DENY_CERTIFICATION_PROVENANCE_MISMATCH" in str(exc.value))
    after = VerificationStore(tmp_path).reconstruct()
    assert after == before and not list((tmp_path / ".idd/evidence/records").glob("EV-905.json"))


def test_builder_cannot_spoof_verifier_role_or_reclassify_observation(tmp_path: Path):
    store, contract, _ = builder_contract_fixture(tmp_path, "SPEC_VERIFIER")
    spoofed = certification_evidence(contract, role="SPEC_VERIFIER", created_by="EXEC-SPEC-405", evidence_id="EV-906")
    with pytest.raises(VerificationError, match="DENY_CERTIFICATION_PROVENANCE_MISMATCH"):
        store.record_evidence(spoofed, event_id="spoofed-cert", timestamp="2026-09-20T02:00:05Z")
    assert store.reconstruct()["evidence"] == {}


def test_fresh_spec_and_standards_evidence_remains_authorized_and_acceptance_is_fail_closed(tmp_path: Path):
    setup(tmp_path)
    orchestrator, spec, standards = create_axes(tmp_path)
    spec_result = orchestrator.launch(spec["execution_id"], adapter=__import__("control.verifier", fromlist=["SubprocessVerifierAdapter"]).SubprocessVerifierAdapter(), event_prefix="repair-spec", timestamp="2026-09-20T02:01:00Z")
    standards_result = orchestrator.launch(standards["execution_id"], adapter=__import__("control.verifier", fromlist=["SubprocessVerifierAdapter"]).SubprocessVerifierAdapter(), event_prefix="repair-standards", timestamp="2026-09-20T02:01:01Z")
    assert spec_result["result"]["status"] == "PASS" and standards_result["result"]["status"] == "PASS"
    assert orchestrator.derive_candidate_status(CANDIDATE) == "VERIFIED"
    fresh = VerifierOrchestrator(tmp_path, controller_execution_id="EXEC-CONTROLLER-501")
    assert fresh.derive_candidate_status(CANDIDATE) == "VERIFIED"


def test_rejected_builder_certification_cannot_resurrect_after_restart(tmp_path: Path):
    store, contract, _ = builder_contract_fixture(tmp_path, "STANDARDS_REVIEWER")
    with pytest.raises(VerificationError, match="DENY_CERTIFICATION_PROVENANCE_MISMATCH"):
        store.record_evidence(certification_evidence(contract, role="STANDARDS_REVIEWER"), event_id="restart-cert", timestamp="2026-09-20T02:02:00Z")
    fresh = VerificationStore(tmp_path)
    assert fresh.reconstruct()["evidence"] == {} and EvidenceEvaluator(tmp_path).evaluate("VC-905", "EV-905", result_id="VR-905", evaluator_execution_id="EXEC-EVALUATOR-905", event_id="restart-evaluate", timestamp="2026-09-20T02:02:01Z")["reason_code"] == "FAIL_EVIDENCE_TAMPERED"

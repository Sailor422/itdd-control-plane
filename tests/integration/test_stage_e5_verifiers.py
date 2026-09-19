from pathlib import Path

import pytest

from control.verifier import SubprocessVerifierAdapter, VerifierInterrupted, VerifierOrchestrationError, VerifierOrchestrator
from control.verification import VerificationStore
from tests.integration.test_stage_e4_verification import BASELINE, setup


CANDIDATE = "e" * 40


def cap(capability_id, role, execution_id, reads):
    return {"capability_id":capability_id,"schema_version":1,"project_id":"e4","role":role,"execution_id":execution_id,"issued_at":"2026-09-20T01:00:00Z","baseline_sha":BASELINE,"allowed_reads":reads,"allowed_writes":[".idd/evidence/spec"] if role == "SPEC_VERIFIER" else [".idd/evidence/standards"],"allowed_executes":["python3 -m pytest"],"allowed_operations":["READ","WRITE","EXECUTE","CREATE_ARTIFACT"],"forbidden_operations":["PROMOTE","INTENT_APPROVAL"],"allowed_request_types":[],"scope_bindings":{"intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001"},"version":1,"issued_by":"controller"}


def packet(packet_id, path, purpose):
    return {"context_packet_id":packet_id,"intent_binding":{"intent_id":"I-001","intent_version":1},"graph_binding":{"graph_id":"G-001","graph_version":1},"eu_binding":{"eu_id":"EU-001"},"authority_context":{"allowed_operations":["READ"],"acceptance_requirements":[purpose]},"working_context":[{"resource_id":f"RES-{packet_id[3:]}","path":path,"purpose":purpose,"authority":"READ","reason_included":"role-specific fixture context","source":"explicit fixture","freshness_or_version":"HEAD"}],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":100000}}


def contract(contract_id, role, command, count=None):
    check = {"check_id":f"REQCHECK-{contract_id[3:]}","kind":"TEST_COMMAND","command":command,"required_exit_code":0}
    if count is not None: check["expected_test_count"] = count
    return {"verification_contract_id":contract_id,"project_id":"e4","execution_id":"placeholder","role":role,"intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001","baseline_sha":BASELINE,"candidate_sha":CANDIDATE,"context_packet_id":"placeholder","context_packet_hash":"placeholder","required_checks":[check],"required_artifacts":[],"allowed_changed_paths":[],"created_at":"2026-09-20T01:00:10Z","created_by":"controller"}


def create_axes(root: Path):
    (root / "tests/fixtures").mkdir(parents=True); (root / "tests/fixtures/e5_candidate_test.py").write_text("def test_one():\n    assert True\n\ndef test_two():\n    assert 1 + 1 == 2\n\ndef test_three():\n    assert 'ITDD'.lower() == 'itdd'\n")
    (root / "standards").mkdir(); (root / "standards/STD-001.md").write_text("No implementation edits by reviewers.\n")
    (root / ".idd/evidence/spec").mkdir(parents=True); (root / ".idd/evidence/standards").mkdir(parents=True)
    orchestrator = VerifierOrchestrator(root, controller_execution_id="EXEC-CONTROLLER-501")
    spec = orchestrator.create_verifier(role="SPEC_VERIFIER", execution_id="EXEC-SPEC-501", capability=cap("CAP-951","SPEC_VERIFIER","EXEC-SPEC-501",["src/a.py","tests/fixtures/e5_candidate_test.py"]), packet=packet("CP-501","src/a.py","approved EU acceptance"), contract=contract("VC-501","SPEC_VERIFIER","python3 -m pytest -q tests/fixtures/e5_candidate_test.py",3), event_prefix="e5-spec", timestamp="2026-09-20T01:00:11Z")
    standards = orchestrator.create_verifier(role="STANDARDS_REVIEWER", execution_id="EXEC-STANDARDS-501", capability=cap("CAP-952","STANDARDS_REVIEWER","EXEC-STANDARDS-501",["src/a.py","standards/STD-001.md"]), packet=packet("CP-502","standards/STD-001.md","mandatory project standard"), contract=contract("VC-502","STANDARDS_REVIEWER","python3 -m pytest -q tests/fixtures/e5_candidate_test.py",3), event_prefix="e5-standards", timestamp="2026-09-20T01:00:12Z")
    return orchestrator, spec, standards


def test_controller_launches_fresh_separate_verifiers_and_derives_verified(tmp_path: Path):
    setup(tmp_path); orchestrator, spec, standards = create_axes(tmp_path); adapter = SubprocessVerifierAdapter()
    spec_result = orchestrator.launch(spec["execution_id"], adapter=adapter, event_prefix="e5-spec-run", timestamp="2026-09-20T01:00:20Z")
    standards_result = orchestrator.launch(standards["execution_id"], adapter=adapter, event_prefix="e5-standards-run", timestamp="2026-09-20T01:00:21Z")
    assert spec_result["result"]["status"] == "PASS" and standards_result["result"]["status"] == "PASS"
    assert orchestrator.derive_candidate_status(CANDIDATE) == "VERIFIED"
    assert spec["execution_id"] != standards["execution_id"] and spec["capability_id"] != standards["capability_id"] and spec["context_packet_id"] != standards["context_packet_id"]
    assert orchestrator.compiler.store.read_packet(spec["context_packet_id"])["working_context"][0]["path"].endswith("src/a.py")
    assert orchestrator.compiler.store.read_packet(standards["context_packet_id"])["working_context"][0]["path"].endswith("standards/STD-001.md")
    assert orchestrator.authorize_write(spec["execution_id"], "src/a.py") == "DENY" and orchestrator.authorize_write(spec["execution_id"], ".idd/evidence/spec/result.json") == "ALLOW"
    fresh = VerifierOrchestrator(tmp_path, controller_execution_id="EXEC-CONTROLLER-501")
    assert fresh.derive_candidate_status(CANDIDATE) == "VERIFIED"


def test_spec_failure_cannot_be_overridden_by_standards_pass(tmp_path: Path):
    setup(tmp_path); orchestrator, spec, standards = create_axes(tmp_path)
    failed = contract("VC-601","SPEC_VERIFIER","python3 -c 'import sys; sys.exit(1)'",0)
    # Create a separate failed Spec axis with its own execution; the existing positive contract remains unused.
    failed_spec = orchestrator.create_verifier(role="SPEC_VERIFIER", execution_id="EXEC-SPEC-601", capability=cap("CAP-961","SPEC_VERIFIER","EXEC-SPEC-601",["src/a.py"]), packet=packet("CP-601","src/a.py","failed EU acceptance"), contract=failed, event_prefix="e5-failed-spec", timestamp="2026-09-20T01:01:00Z")
    orchestrator.launch(failed_spec["execution_id"], adapter=SubprocessVerifierAdapter(), event_prefix="e5-failed-spec-run", timestamp="2026-09-20T01:01:01Z")
    orchestrator.launch(standards["execution_id"], adapter=SubprocessVerifierAdapter(), event_prefix="e5-standards-run", timestamp="2026-09-20T01:01:02Z")
    assert orchestrator.derive_candidate_status(CANDIDATE) == "NOT_VERIFIED"


def test_standards_failure_cannot_be_overridden_by_spec_pass(tmp_path: Path):
    setup(tmp_path); orchestrator, spec, standards = create_axes(tmp_path)
    orchestrator.launch(spec["execution_id"], adapter=SubprocessVerifierAdapter(), event_prefix="e5-spec-run", timestamp="2026-09-20T01:01:10Z")
    failed = contract("VC-602","STANDARDS_REVIEWER","python3 -c 'import sys; sys.exit(1)'",0)
    failed_standards = orchestrator.create_verifier(role="STANDARDS_REVIEWER", execution_id="EXEC-STANDARDS-602", capability=cap("CAP-962","STANDARDS_REVIEWER","EXEC-STANDARDS-602",["standards/STD-001.md"]), packet=packet("CP-602","standards/STD-001.md","failed mandatory standard"), contract=failed, event_prefix="e5-failed-standards", timestamp="2026-09-20T01:01:11Z")
    orchestrator.launch(failed_standards["execution_id"], adapter=SubprocessVerifierAdapter(), event_prefix="e5-failed-standards-run", timestamp="2026-09-20T01:01:12Z")
    assert orchestrator.derive_candidate_status(CANDIDATE) == "NOT_VERIFIED" and orchestrator.derive_candidate_status("f" * 40) == "NOT_VERIFIED"


def test_same_execution_wrong_role_builder_evidence_and_interruption_fail(tmp_path: Path):
    setup(tmp_path); orchestrator, spec, standards = create_axes(tmp_path)
    with pytest.raises(VerifierOrchestrationError):
        orchestrator.create_verifier(role="STANDARDS_REVIEWER", execution_id=spec["execution_id"], capability=cap("CAP-970","STANDARDS_REVIEWER",spec["execution_id"],["standards/STD-001.md"]), packet=packet("CP-701","standards/STD-001.md","wrong"), contract=contract("VC-701","STANDARDS_REVIEWER","python3 -m pytest -q tests/fixtures/e5_candidate_test.py",3), event_prefix="e5-same", timestamp="2026-09-20T01:02:00Z")
    assert orchestrator.authorize_write(spec["execution_id"], "src/a.py") == "DENY"
    class Interrupted:
        def run(self, **kwargs): raise VerifierInterrupted("synthetic interruption")
    result = orchestrator.launch(standards["execution_id"], adapter=Interrupted(), event_prefix="e5-interrupted", timestamp="2026-09-20T01:02:01Z")
    assert result["execution"]["status"] == "INTERRUPTED" and result["evidence"] is None and orchestrator.derive_candidate_status(CANDIDATE) == "NOT_VERIFIED"


def test_wrong_role_evidence_is_rejected_by_e4_binding(tmp_path: Path):
    setup(tmp_path); orchestrator, spec, _ = create_axes(tmp_path); store = VerificationStore(tmp_path); contract_record = store.read_contract(spec["verification_contract_id"])
    bad = {"evidence_id":"EV-799","verification_contract_id":contract_record["verification_contract_id"],"project_id":"e4","execution_id":spec["execution_id"],"role":"BUILDER","intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001","baseline_sha":BASELINE,"candidate_sha":CANDIDATE,"context_packet_id":spec["context_packet_id"],"context_packet_hash":spec["context_packet_hash"],"check_results":[],"artifact_hashes":{},"observed_changed_paths":[],"created_at":"2026-09-20T01:03:00Z","created_by":"builder"}
    import hashlib, json
    from control.events.format import canonical_json
    bad["evidence_hash"] = hashlib.sha256(canonical_json(bad).encode()).hexdigest()
    with pytest.raises(Exception): store.record_evidence(bad, event_id="e5-bad-evidence", timestamp="2026-09-20T01:03:01Z")

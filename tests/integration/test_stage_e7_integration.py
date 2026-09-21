import subprocess
from pathlib import Path

import pytest

from control.git import CandidateAttestationStore, GitError, GitAdapter
from control.human import HumanGateController, HumanGateError
from control.integration import IntegrationController, IntegrationError, IntegrationStore
from control.verifier import SubprocessVerifierAdapter, VerifierOrchestrator
from tests.integration.test_stage_e4_verification import setup


def run_git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True).stdout.strip()


def cap(cid, role, execution, baseline):
    return {"capability_id":cid,"schema_version":1,"project_id":"e4","role":role,"execution_id":execution,"issued_at":"2026-09-20T03:00:00Z","baseline_sha":baseline,"allowed_reads":["src","standards","tests"],"allowed_writes":[".idd/evidence/spec",".idd/evidence/standards"],"allowed_executes":["python3 -m pytest"],"allowed_operations":["READ","EXECUTE","CREATE_ARTIFACT"],"forbidden_operations":["WRITE","PROMOTE"],"allowed_request_types":[],"scope_bindings":{"intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001"},"version":1,"issued_by":"controller"}


def packet(pid, path):
    return {"context_packet_id":pid,"intent_binding":{"intent_id":"I-001","intent_version":1},"graph_binding":{"graph_id":"G-001","graph_version":1},"eu_binding":{"eu_id":"EU-001"},"authority_context":{"allowed_operations":["READ"],"acceptance_requirements":["fixture tests"]},"working_context":[{"resource_id":f"RES-{pid[3:]}","path":path,"purpose":"candidate verification","authority":"READ","reason_included":"exact fixture","source":"test","freshness_or_version":"HEAD"}],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":100000}}


def contract(cid, role, execution, baseline, candidate, pid):
    return {"verification_contract_id":cid,"project_id":"e4","execution_id":execution,"role":role,"intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001","baseline_sha":baseline,"candidate_sha":candidate,"context_packet_id":pid,"context_packet_hash":"placeholder","required_checks":[{"check_id":f"REQCHECK-{cid[3:]}","kind":"TEST_COMMAND","command":"python3 -m pytest -q tests/fixtures/e5_candidate_test.py","required_exit_code":0,"expected_test_count":3}],"required_artifacts":[],"allowed_changed_paths":[],"created_at":"2026-09-20T03:00:01Z","created_by":"controller"}


def prepare(root: Path):
    setup(root); (root / "tests/fixtures").mkdir(parents=True); (root / "tests/fixtures/e5_candidate_test.py").write_text("def test_one(): assert True\ndef test_two(): assert 1 + 1 == 2\ndef test_three(): assert 'ITDD'.lower() == 'itdd'\n")
    run_git(root, "init", "-b", "main"); run_git(root, "config", "user.name", "E7 Fixture"); run_git(root, "config", "user.email", "e7@example.invalid"); run_git(root, "add", "."); run_git(root, "commit", "-m", "baseline")
    baseline = run_git(root, "rev-parse", "HEAD")
    run_git(root, "checkout", "-b", "candidate-a"); (root / "src/a.py").write_text("class A: pass\n# candidate A\n"); run_git(root, "add", "src/a.py"); run_git(root, "commit", "-m", "candidate A"); candidate_a = run_git(root, "rev-parse", "HEAD")
    run_git(root, "checkout", "-b", "candidate-b", baseline); (root / "src/b.py").write_text("class B: pass\n# candidate B\n"); run_git(root, "add", "src/b.py"); run_git(root, "commit", "-m", "candidate B"); candidate_b = run_git(root, "rev-parse", "HEAD")
    orchestrator = VerifierOrchestrator(root, controller_execution_id="EXEC-CONTROLLER-701"); results = {}; executions = {}
    for index, candidate in enumerate((candidate_a, candidate_b), 1):
        for role, short in (("SPEC_VERIFIER", "SPEC"), ("STANDARDS_REVIEWER", "STD")):
            execution = f"EXEC-{short}-{700 + index}"; cid = f"CAP-{700 + index}{1 if short == 'SPEC' else 2}"; pid = f"CP-{700 + index}{1 if short == 'SPEC' else 2}"; vc = f"VC-{700 + index}{1 if short == 'SPEC' else 2}"
            item = contract(vc, role, execution, baseline, candidate, pid); item["candidate_sha"] = candidate
            created = orchestrator.create_verifier(role=role, execution_id=execution, capability=cap(cid, role, execution, baseline), packet=packet(pid, "src/a.py" if index == 1 else "src/b.py"), contract=item, event_prefix=f"e7-{index}-{short.lower()}", timestamp="2026-09-20T03:00:02Z")
            result = orchestrator.launch(execution, adapter=SubprocessVerifierAdapter(), event_prefix=f"e7-run-{index}-{short.lower()}", timestamp="2026-09-20T03:00:03Z")["result"]
            executions[(index, role)] = (created, result)
    return baseline, candidate_a, candidate_b, orchestrator, executions


def test_git_attestation_and_isolated_integration_with_fresh_verifier_and_gate(tmp_path: Path):
    baseline, candidate_a, candidate_b, orchestrator, executions = prepare(tmp_path); attest = CandidateAttestationStore(tmp_path)
    a = attest.attest(attestation_id="AT-701", project_id="e4", baseline_commit=baseline, candidate_commit=candidate_a, created_at="2026-09-20T03:01:00Z"); b = attest.attest(attestation_id="AT-702", project_id="e4", baseline_commit=baseline, candidate_commit=candidate_b, created_at="2026-09-20T03:01:01Z")
    assert a["observed_changed_paths"] == ["src/a.py"] and b["observed_changed_paths"] == ["src/b.py"]
    human = HumanGateController(tmp_path, controller_execution_id="EXEC-CONTROLLER-701")
    for gid, index, att in (("HG-701", 1, a), ("HG-702", 2, b)):
        spec, sr = executions[(index, "SPEC_VERIFIER")]; std, tr = executions[(index, "STANDARDS_REVIEWER")]
        gate = human.create_verified_eu_review(gate_id=gid, project_id="e4", eu_id="EU-001", candidate_sha=att["candidate_commit"], spec_execution_id=spec["execution_id"], standards_execution_id=std["execution_id"], spec_result_id=sr["result_id"], standards_result_id=tr["result_id"], timestamp="2026-09-20T03:01:02Z", event_prefix=f"e7-{gid}")
        human.decide(gid, decision="APPROVED", actor_type="human", actor_id="reviewer", binding={"project_id":"e4","gate_id":gid,**gate["related_candidate"],"evidence":gate["evidence"]}, event_prefix=f"e7-approve-{gid}", timestamp="2026-09-20T03:01:03Z")
    integration = IntegrationController(tmp_path, controller_execution_id="EXEC-CONTROLLER-701"); item = integration.create(integration_id="IN-701", project_id="e4", attestation_ids=["AT-701", "AT-702"], intent_id="I-001", intent_version=1, graph_id="G-001", graph_version=1, timestamp="2026-09-20T03:02:00Z", event_prefix="e7-integrator")
    assert item["integration_workspace"].endswith("IN-701") and item["integration_workspace"] != str(tmp_path)
    completed = integration.run("IN-701", timestamp="2026-09-20T03:02:01Z", event_prefix="e7-merge"); assert completed["status"] == "COMPLETED" and completed["result_commit"]
    assert integration.authorize_integrator_write("IN-701", ".idd/integration_workspaces/IN-701") == "ALLOW"
    assert integration.authorize_integrator_write("IN-701", ".idd/intent/I-001/v1.json") == "DENY"
    verifier = integration.create_integration_verifier("IN-701", command=f"python3 -m pytest -q {completed['integration_workspace']}/tests/fixtures/e5_candidate_test.py", timestamp="2026-09-20T03:02:02Z", event_prefix="e7-integration-verifier")
    assert integration.verifiers.authorize_write(verifier["execution_id"], "src/a.py") == "DENY"
    result = integration.verifiers.launch(verifier["execution_id"], adapter=SubprocessVerifierAdapter(), event_prefix="e7-integration-run", timestamp="2026-09-20T03:02:03Z")["result"]
    verified = integration.mark_verified("IN-701", verifier_execution_id=verifier["execution_id"], result_id=result["result_id"], timestamp="2026-09-20T03:02:04Z", event_prefix="e7-integrated"); assert verified["status"] == "INTEGRATION_VERIFIED"
    gate = human.create_integration_approval(gate_id="HG-703", integration=verified, verifier_execution_id=verifier["execution_id"], verifier_result_id=result["result_id"], timestamp="2026-09-20T03:02:05Z", event_prefix="e7-human-integration")
    binding = {"project_id":"e4","gate_id":"HG-703",**gate["related_candidate"],"evidence":gate["evidence"]}; assert human.decide("HG-703", decision="APPROVED", actor_type="human", actor_id="reviewer", binding=binding, event_prefix="e7-approve-integration", timestamp="2026-09-20T03:02:06Z")["status"] == "APPROVED"
    assert IntegrationStore(tmp_path).reconstruct()["IN-701"]["status"] == "INTEGRATION_VERIFIED"


def test_git_identity_conflict_and_missing_human_approval_fail_closed(tmp_path: Path):
    baseline, candidate_a, candidate_b, _, _ = prepare(tmp_path); attest = CandidateAttestationStore(tmp_path); attest.attest(attestation_id="AT-801", project_id="e4", baseline_commit=baseline, candidate_commit=candidate_a, created_at="2026-09-20T03:03:00Z")
    with pytest.raises(GitError): attest.attest(attestation_id="AT-802", project_id="e4", baseline_commit=baseline, candidate_commit="f" * 40, created_at="2026-09-20T03:03:01Z")
    item = IntegrationController(tmp_path, controller_execution_id="EXEC-CONTROLLER-701").create(integration_id="IN-801", project_id="e4", attestation_ids=["AT-801", "AT-801"], intent_id="I-001", intent_version=1, graph_id="G-001", graph_version=1, timestamp="2026-09-20T03:03:02Z", event_prefix="e7-no-human")
    assert item["status"] == "CREATED"
    with pytest.raises(IntegrationError, match="human approval"):
        IntegrationController(tmp_path, controller_execution_id="EXEC-CONTROLLER-701").create(integration_id="IN-802", project_id="e4", attestation_ids=["AT-801", "AT-801"], intent_id="I-001", intent_version=1, graph_id="G-001", graph_version=1, timestamp="2026-09-20T03:03:03Z", require_human=True, event_prefix="e7-explicit-human")


def test_semantic_and_interrupted_integration_never_produce_candidate(tmp_path: Path):
    baseline, candidate_a, candidate_b, _, _ = prepare(tmp_path); attest = CandidateAttestationStore(tmp_path); attest.attest(attestation_id="AT-901", project_id="e4", baseline_commit=baseline, candidate_commit=candidate_a, created_at="2026-09-20T03:04:00Z"); attest.attest(attestation_id="AT-902", project_id="e4", baseline_commit=baseline, candidate_commit=candidate_b, created_at="2026-09-20T03:04:01Z")
    controller = IntegrationController(tmp_path, controller_execution_id="EXEC-CONTROLLER-701"); item = controller.create(integration_id="IN-901", project_id="e4", attestation_ids=["AT-901", "AT-902"], intent_id="I-001", intent_version=1, graph_id="G-001", graph_version=1, timestamp="2026-09-20T03:04:02Z", require_human=False, event_prefix="e7-failure")
    assert controller.run("IN-901", timestamp="2026-09-20T03:04:03Z", event_prefix="e7-semantic", semantic_conflict=True)["status"] == "REPLAN_REQUIRED"
    interrupted = controller.create(integration_id="IN-902", project_id="e4", attestation_ids=["AT-901", "AT-902"], intent_id="I-001", intent_version=1, graph_id="G-001", graph_version=1, timestamp="2026-09-20T03:04:04Z", require_human=False, event_prefix="e7-interrupted")
    assert controller.run(interrupted["integration_id"], timestamp="2026-09-20T03:04:05Z", event_prefix="e7-interrupted-run", interrupted=True)["status"] == "INTERRUPTED"


def test_verified_evidence_cannot_be_reused_for_a_new_commit(tmp_path: Path):
    baseline, candidate_a, candidate_b, orchestrator, _ = prepare(tmp_path); attest = CandidateAttestationStore(tmp_path)
    original = attest.attest(attestation_id="AT-951", project_id="e4", baseline_commit=baseline, candidate_commit=candidate_a, created_at="2026-09-20T03:05:00Z")
    run_git(tmp_path, "checkout", "candidate-a"); (tmp_path / "src/a.py").write_text("class A: pass\n# changed after verification\n"); run_git(tmp_path, "add", "src/a.py"); run_git(tmp_path, "commit", "-m", "candidate A changed"); changed = run_git(tmp_path, "rev-parse", "HEAD")
    attest.attest(attestation_id="AT-952", project_id="e4", baseline_commit=baseline, candidate_commit=changed, created_at="2026-09-20T03:05:00Z")
    assert original["candidate_commit"] != changed and orchestrator.derive_candidate_status(changed) == "NOT_VERIFIED"
    with pytest.raises(IntegrationError, match="independently"):
        IntegrationController(tmp_path, controller_execution_id="EXEC-CONTROLLER-701").create(integration_id="IN-951", project_id="e4", attestation_ids=["AT-951", "AT-952"], intent_id="I-001", intent_version=1, graph_id="G-001", graph_version=1, timestamp="2026-09-20T03:05:01Z", require_human=False, event_prefix="e7-stale")

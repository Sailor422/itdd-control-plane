from pathlib import Path

from control.authorization import CapabilityIssuer, ControllerAuthorizer, AccessType


BASELINE = "a" * 40


def envelope(root: Path, role="BUILDER", execution="EXEC-A"):
    return {"capability_id":"CAP-001", "schema_version":1, "project_id":"p1", "role":role,
            "execution_id":execution, "issued_at":"2026-09-19T19:00:00Z", "baseline_sha":BASELINE,
            "allowed_reads":["tests/fixture.txt"], "allowed_writes":["tests/fixture.txt"], "allowed_executes":[],
            "allowed_operations":[AccessType.READ, AccessType.WRITE], "forbidden_operations":["PROMOTE"],
            "allowed_request_types":[], "scope_bindings":{}, "version":1, "issued_by":"controller"}


def state(root, execution="EXEC-A", project="p1", baseline=BASELINE):
    return {"project_root": str(root), "project_id": project, "execution_id": execution, "baseline_sha": baseline}


def action(path, operation=AccessType.WRITE, role="BUILDER", **extra):
    return {"request_id":"REQ-123", "project_id":"p1", "execution_id":"EXEC-A", "baseline_sha":BASELINE,
            "role":role, "operation":operation, "path":path, **extra}


def test_positive_builder_write_and_planner_artifact(tmp_path: Path):
    (tmp_path / "tests").mkdir(); (tmp_path / "tests/fixture.txt").write_text("x")
    issuer = CapabilityIssuer(tmp_path)
    issuer.issue(envelope(tmp_path), event_id="evt-cap", timestamp="2026-09-19T19:00:01Z")
    controller = ControllerAuthorizer(tmp_path)
    assert controller.authorize("CAP-001", action("tests/fixture.txt"), state(tmp_path)).decision == "ALLOW"


def test_planner_can_create_only_an_allowed_planning_artifact(tmp_path: Path):
    e = envelope(tmp_path, role="PLANNER"); e["capability_id"] = "CAP-003"; e["allowed_writes"] = ["work/plan.json"]; e["allowed_operations"] = ["CREATE_ARTIFACT"]
    CapabilityIssuer(tmp_path).issue(e, event_id="evt-plan-cap", timestamp="2026-09-19T19:00:01Z")
    c = ControllerAuthorizer(tmp_path)
    assert c.authorize("CAP-003", action("work/plan.json", "CREATE_ARTIFACT", "PLANNER"), state(tmp_path)).decision == "ALLOW"
    assert c.authorize("CAP-003", action("work/plan.json", "INTENT_APPROVAL", "PLANNER", actor_type="agent"), state(tmp_path)).reason == "DENY_HUMAN_ONLY"


def test_verifier_can_read_and_test_but_not_modify_implementation(tmp_path: Path):
    e = envelope(tmp_path, role="SPEC_VERIFIER"); e["capability_id"] = "CAP-004"; e["allowed_operations"] = ["READ", "EXECUTE"]; e["allowed_executes"] = ["tests/run.sh"]
    CapabilityIssuer(tmp_path).issue(e, event_id="evt-verifier-cap", timestamp="2026-09-19T19:00:01Z")
    c = ControllerAuthorizer(tmp_path)
    assert c.authorize("CAP-004", action("tests/fixture.txt", "READ", "SPEC_VERIFIER"), state(tmp_path)).decision == "ALLOW"
    assert c.authorize("CAP-004", action("tests/fixture.txt", "WRITE", "SPEC_VERIFIER"), state(tmp_path)).reason == "DENY_OPERATION_NOT_GRANTED"


def test_promoter_may_only_use_explicit_transition(tmp_path: Path):
    e = envelope(tmp_path, role="PROMOTER"); e["capability_id"]="CAP-002"; e["allowed_reads"]=[]; e["allowed_writes"]=[]; e["allowed_operations"]=["STATE_TRANSITION"]
    CapabilityIssuer(tmp_path).issue(e, event_id="evt-cap", timestamp="2026-09-19T19:00:01Z")
    c = ControllerAuthorizer(tmp_path)
    assert c.authorize("CAP-002", action(None, "STATE_TRANSITION", "PROMOTER", synthetic_operation="PROMOTE_CANDIDATE"), state(tmp_path)).decision == "ALLOW"
    assert c.authorize("CAP-002", action(None, "WRITE", "PROMOTER"), state(tmp_path)).decision == "DENY"


def test_restart_reconstructs_issued_capability(tmp_path: Path):
    CapabilityIssuer(tmp_path).issue(envelope(tmp_path), event_id="evt-cap", timestamp="2026-09-19T19:00:01Z")
    ControllerAuthorizer(tmp_path).store.verify_materialized()
    fresh = ControllerAuthorizer(tmp_path)
    assert fresh.authorize("CAP-001", action("tests/fixture.txt"), state(tmp_path)).decision == "ALLOW"

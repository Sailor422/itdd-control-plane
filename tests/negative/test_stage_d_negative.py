from pathlib import Path
import json
import pytest

from control.authorization import CapabilityIssuer, ControllerAuthorizer, AccessType
from control.authorization.capabilities import CapabilityError

from tests.integration.test_stage_d_authorization import BASELINE, envelope, state, action


def issued(tmp_path, role="BUILDER", execution="EXEC-A"):
    e = envelope(tmp_path, role, execution); e["capability_id"] = "CAP-001" if execution == "EXEC-A" else "CAP-002"
    CapabilityIssuer(tmp_path).issue(e, event_id="evt-cap-" + execution, timestamp="2026-09-19T19:00:01Z")
    return ControllerAuthorizer(tmp_path), e


def test_builder_cannot_modify_intent_or_graph_or_evidence(tmp_path: Path):
    c, _ = issued(tmp_path)
    for path in (".idd/intent/I-001/v1.json", ".idd/graph/G-001/v1.json", ".idd/evidence/x.md"):
        assert c.authorize("CAP-001", action(path), state(tmp_path)).reason == "DENY_PATH_NOT_GRANTED"


def test_path_traversal_and_symlink_escape_denied(tmp_path: Path):
    c, _ = issued(tmp_path); outside = tmp_path.parent / "outside"; outside.mkdir(); (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    assert c.authorize("CAP-001", action("tests/../.idd/intent/I-001/v1.json"), state(tmp_path)).reason == "DENY_SCOPE_ESCAPE"
    assert c.authorize("CAP-001", action("link/secret.txt"), state(tmp_path)).reason == "DENY_SCOPE_ESCAPE"


def test_role_operation_and_human_only_separation(tmp_path: Path):
    c, _ = issued(tmp_path)
    assert c.authorize("CAP-001", action("tests/fixture.txt", "INTENT_APPROVAL", "BUILDER", actor_type="agent"), state(tmp_path)).reason == "DENY_HUMAN_ONLY"
    assert c.authorize("CAP-001", action("tests/fixture.txt", "WRITE", "PLANNER"), state(tmp_path)).reason == "DENY_ROLE_MISMATCH"
    assert c.authorize("CAP-001", action("tests/fixture.txt", "PROMOTE_CANDIDATE", "BUILDER"), state(tmp_path)).reason == "DENY_OPERATION_NOT_GRANTED"


def test_wrong_execution_project_baseline_and_unlisted_operation_denied(tmp_path: Path):
    c, _ = issued(tmp_path)
    assert c.authorize("CAP-001", action("tests/fixture.txt", execution_id="EXEC-B"), state(tmp_path)).reason == "DENY_EXECUTION_MISMATCH"
    assert c.authorize("CAP-001", {**action("tests/fixture.txt"), "project_id":"p2"}, state(tmp_path)).reason == "DENY_PROJECT_MISMATCH"
    assert c.authorize("CAP-001", action("tests/fixture.txt", baseline_sha="b"*40), state(tmp_path)).reason == "DENY_BASELINE_MISMATCH"
    assert c.authorize("CAP-001", action("tests/fixture.txt", "APPEND_EVENT"), state(tmp_path)).reason == "DENY_OPERATION_NOT_GRANTED"
    assert c.authorize("CAP-404", action("tests/fixture.txt"), state(tmp_path)).reason == "DENY_NO_CAPABILITY"


def test_tamper_and_self_issuance_denied(tmp_path: Path):
    with pytest.raises(CapabilityError):
        CapabilityIssuer(tmp_path).issue({**envelope(tmp_path), "integrity_hash":"0"}, event_id="evt", timestamp="2026-09-19T19:00:01Z", issuer_role="BUILDER", actor_type="agent")
    issuer = CapabilityIssuer(tmp_path); issuer.issue(envelope(tmp_path), event_id="evt-cap", timestamp="2026-09-19T19:00:01Z")
    path = tmp_path / ".idd/capabilities/CAP-001/v1.json"; data = json.loads(path.read_text()); data["allowed_operations"]=["PROMOTE_CANDIDATE"]; path.write_text(json.dumps(data))
    assert ControllerAuthorizer(tmp_path).authorize("CAP-001", action("tests/fixture.txt"), state(tmp_path)).reason == "DENY_CAPABILITY_TAMPERED"

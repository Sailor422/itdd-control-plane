from pathlib import Path
import pytest

from control.authorization import CapabilityIssuer, ControllerAuthorizer
from control.context import ContextCompiler, ResolutionError, ScoutResolver
from tests.integration.test_stage_e2_resolver import BASELINE, builder_cap, scout_cap, setup


def test_ambiguity_not_found_and_budget_are_honest(tmp_path: Path):
    setup(tmp_path); (tmp_path / "src/payments/legacy.py").write_text("class PaymentProvider: pass\n")
    resolver = ScoutResolver(tmp_path); scout_state={"project_root":str(tmp_path),"project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":BASELINE}
    # No worker request is needed to prove search outcomes; intake is tested separately.
    compiler=ContextCompiler(tmp_path); worker={"project_root":str(tmp_path),"project_id":"e2","execution_id":"EXEC-201","baseline_sha":BASELINE,"role":"BUILDER"}; compiler.compile(__import__('tests.integration.test_stage_e1_context',fromlist=['packet']).packet(packet_id="CP-201"), capability_id="CAP-201", state=worker, event_id="evt-packet", timestamp="2026-09-19T22:00:03Z"); compiler.request_context({"context_request_id":"CR-201","context_packet_id":"CP-201","request_type":"MISSING_RESOURCE","requested_resource_or_question":"PaymentProvider","reason":"x","expected_use":"x"}, capability_id="CAP-201", state=worker, event_id="evt-request", timestamp="2026-09-19T22:00:04Z")
    assert resolver.resolve("CR-201", scout_capability_id="CAP-902", scout_state=scout_state, search_scope={"root":"src/payments"}, query_or_need="PaymentProvider", resolution_id="SR-201", event_id="evt-res", timestamp="2026-09-19T22:00:05Z")["status"] == "AMBIGUOUS"
    assert resolver.resolve("CR-201", scout_capability_id="CAP-902", scout_state=scout_state, search_scope={"root":"src/payments"}, query_or_need="NoSuchInterface", resolution_id="SR-202", event_id="evt-res-2", timestamp="2026-09-19T22:00:06Z")["status"] == "NOT_FOUND"
    assert resolver.resolve("CR-201", scout_capability_id="CAP-902", scout_state=scout_state, search_scope={"root":"src/payments"}, query_or_need="PaymentProvider", resolution_id="SR-203", event_id="evt-res-3", timestamp="2026-09-19T22:00:07Z", budget={"max_files_examined":1})["status"] == "PARTIALLY_RESOLVED"


def test_scope_isolation_stale_request_and_scout_role_boundaries(tmp_path: Path):
    worker=setup(tmp_path); compiler=ContextCompiler(tmp_path); compiler.compile(__import__('tests.integration.test_stage_e1_context',fromlist=['packet']).packet(packet_id="CP-201"), capability_id="CAP-201", state=worker, event_id="evt-packet", timestamp="2026-09-19T22:00:03Z"); compiler.request_context({"context_request_id":"CR-201","context_packet_id":"CP-201","request_type":"MISSING_RESOURCE","requested_resource_or_question":"x","reason":"x","expected_use":"x"}, capability_id="CAP-201", state=worker, event_id="evt-request", timestamp="2026-09-19T22:00:04Z")
    resolver=ScoutResolver(tmp_path); scout_state={"project_root":str(tmp_path),"project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":BASELINE}
    with pytest.raises(ResolutionError): resolver.resolve("CR-201", scout_capability_id="CAP-902", scout_state={**scout_state,"baseline_sha":"d"*40}, search_scope={"root":"src/payments"}, query_or_need="PaymentProvider", resolution_id="SR-301", event_id="evt-res", timestamp="2026-09-19T22:00:05Z")
    with pytest.raises(ResolutionError): resolver.resolve("CR-201", scout_capability_id="CAP-902", scout_state=scout_state, search_scope={"root":"../"}, query_or_need="PaymentProvider", resolution_id="SR-302", event_id="evt-res-2", timestamp="2026-09-19T22:00:05Z")
    c=ControllerAuthorizer(tmp_path)
    assert c.authorize("CAP-902", {"request_id":"x","project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":BASELINE,"role":"SCOUT","operation":"WRITE","path":"src/a.py"}, {**scout_state,"project_root":str(tmp_path)}).reason == "DENY_OPERATION_NOT_GRANTED"
    assert c.authorize("CAP-902", {"request_id":"x","project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":BASELINE,"role":"SCOUT","operation":"INTENT_APPROVAL","actor_type":"agent"}, {**scout_state,"project_root":str(tmp_path)}).reason == "DENY_HUMAN_ONLY"
    with pytest.raises(ResolutionError): resolver.resolve("CR-201", scout_capability_id="CAP-902", scout_state=scout_state, search_scope={"root":"/Users/herbertfields/.codex"}, query_or_need="x", resolution_id="SR-303", event_id="evt-res-3", timestamp="2026-09-19T22:00:05Z")


def test_wrong_project_and_execution_resolution_cannot_be_consumed(tmp_path: Path):
    worker=setup(tmp_path); compiler=ContextCompiler(tmp_path); from tests.integration.test_stage_e1_context import packet
    compiler.compile(packet(packet_id="CP-201"), capability_id="CAP-201", state=worker, event_id="evt-packet", timestamp="2026-09-19T22:00:03Z"); compiler.request_context({"context_request_id":"CR-201","context_packet_id":"CP-201","request_type":"MISSING_RESOURCE","requested_resource_or_question":"PaymentProvider","reason":"x","expected_use":"x"}, capability_id="CAP-201", state=worker, event_id="evt-request", timestamp="2026-09-19T22:00:04Z")
    ScoutResolver(tmp_path).resolve("CR-201", scout_capability_id="CAP-902", scout_state={"project_root":str(tmp_path),"project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":BASELINE}, search_scope={"root":"src/payments"}, query_or_need="PaymentProvider", resolution_id="SR-201", event_id="evt-res", timestamp="2026-09-19T22:00:05Z")
    with pytest.raises(Exception, match="binding"): compiler.compile_from_resolution(packet(packet_id="CP-202"), resolution_id="SR-201", capability_id="CAP-201", state={**worker,"execution_id":"EXEC-OTHER"}, event_id="evt-packet-2", timestamp="2026-09-19T22:00:06Z", grant_event_id="evt-grant")

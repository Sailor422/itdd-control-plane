from pathlib import Path

from control.authorization import CapabilityIssuer
from control.context import ContextCompiler, ScoutResolver
from tests.integration.test_stage_e1_context import BASELINE, packet, state


def builder_cap(root: Path, readable_provider=True):
    reads = ["src/a.py"] + (["src/payments"] if readable_provider else [])
    return {"capability_id":"CAP-201","schema_version":1,"project_id":"e2","role":"BUILDER","execution_id":"EXEC-201","issued_at":"2026-09-19T22:00:00Z","baseline_sha":BASELINE,"allowed_reads":reads,"allowed_writes":["src/b.py"],"allowed_executes":[],"allowed_operations":["READ","WRITE","REQUEST_CONTEXT"],"forbidden_operations":["RESOLVE_CONTEXT"],"allowed_request_types":[],"scope_bindings":{"intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001"},"version":1,"issued_by":"controller"}


def scout_cap(root: Path, scope="src/payments"):
    return {"capability_id":"CAP-902","schema_version":1,"project_id":"e2","role":"SCOUT","execution_id":"EXEC-SCOUT-201","issued_at":"2026-09-19T22:00:00Z","baseline_sha":BASELINE,"allowed_reads":[scope],"allowed_writes":[],"allowed_executes":[],"allowed_operations":["READ","RESOLVE_CONTEXT","CREATE_ARTIFACT"],"forbidden_operations":["WRITE","INTENT_APPROVAL"],"allowed_request_types":[],"scope_bindings":{},"version":1,"issued_by":"controller"}


def setup(root: Path, readable_provider=True):
    (root / "src/payments").mkdir(parents=True); (root / "src/a.py").write_text("# worker\n"); (root / "src/b.py").write_text("# output\n"); (root / "src/payments/provider.py").write_text("class PaymentProvider: pass\n")
    issuer = CapabilityIssuer(root)
    issuer.issue(builder_cap(root, readable_provider), event_id="evt-builder-201", timestamp="2026-09-19T22:00:01Z")
    issuer.issue(scout_cap(root), event_id="evt-scout-201", timestamp="2026-09-19T22:00:02Z")
    return {"project_root":str(root),"project_id":"e2","execution_id":"EXEC-201","baseline_sha":BASELINE,"role":"BUILDER"}


def test_request_scout_resolve_and_compiler_issue_new_packet(tmp_path: Path):
    worker = setup(tmp_path)
    compiler = ContextCompiler(tmp_path)
    compiler.compile(packet(packet_id="CP-201"), capability_id="CAP-201", state=worker, event_id="evt-packet-201", timestamp="2026-09-19T22:00:03Z")
    compiler.request_context({"context_request_id":"CR-201","context_packet_id":"CP-201","request_type":"MISSING_INTERFACE","requested_resource_or_question":"PaymentProvider","reason":"worker needs the provider contract","expected_use":"complete EU-001"}, capability_id="CAP-201", state=worker, event_id="evt-request-201", timestamp="2026-09-19T22:00:04Z")
    resolution = ScoutResolver(tmp_path).resolve("CR-201", scout_capability_id="CAP-902", scout_state={"project_root":str(tmp_path),"project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":BASELINE}, search_scope={"root":"src/payments"}, query_or_need="PaymentProvider", resolution_id="SR-201", event_id="evt-resolution-201", timestamp="2026-09-19T22:00:05Z")
    assert resolution["status"] == "RESOLVED"; assert resolution["selected_findings"][0]["path"] == str((tmp_path / "src/payments/provider.py").resolve())
    revised = packet(packet_id="CP-202"); revised["supersedes_packet_id"] = "CP-201"
    cp2 = compiler.compile_from_resolution(revised, resolution_id="SR-201", capability_id="CAP-201", state=worker, event_id="evt-packet-202", timestamp="2026-09-19T22:00:06Z", grant_event_id="evt-grant-201")
    assert cp2["resolution_binding"]["resolution_id"] == "SR-201"; assert any(item["path"].endswith("src/payments/provider.py") for item in cp2["working_context"])
    assert compiler.store.read_packet("CP-201") != cp2; assert compiler.store.reconstruct()["requests"]["CR-201"]["status"] == "GRANTED"


def test_scout_finds_but_compiler_rejects_unreadable_worker_resource(tmp_path: Path):
    worker = setup(tmp_path, readable_provider=False); compiler = ContextCompiler(tmp_path)
    compiler.compile(packet(packet_id="CP-201"), capability_id="CAP-201", state=worker, event_id="evt-packet-201", timestamp="2026-09-19T22:00:03Z")
    compiler.request_context({"context_request_id":"CR-201","context_packet_id":"CP-201","request_type":"MISSING_RESOURCE","requested_resource_or_question":"PaymentProvider","reason":"missing","expected_use":"contract"}, capability_id="CAP-201", state=worker, event_id="evt-request-201", timestamp="2026-09-19T22:00:04Z")
    ScoutResolver(tmp_path).resolve("CR-201", scout_capability_id="CAP-902", scout_state={"project_root":str(tmp_path),"project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":BASELINE}, search_scope={"root":"src/payments"}, query_or_need="PaymentProvider", resolution_id="SR-201", event_id="evt-resolution-201", timestamp="2026-09-19T22:00:05Z")
    import pytest
    with pytest.raises(Exception, match="resource rejected"): compiler.compile_from_resolution(packet(packet_id="CP-202"), resolution_id="SR-201", capability_id="CAP-201", state=worker, event_id="evt-packet-202", timestamp="2026-09-19T22:00:06Z", grant_event_id="evt-grant-201")

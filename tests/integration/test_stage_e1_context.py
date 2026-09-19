from pathlib import Path
import hashlib

from control.authorization import CapabilityIssuer
from control.context import ContextCompiler
from control.events.format import canonical_json


BASELINE = "c" * 40


def capability(root: Path, request=False):
    ops = ["READ", "WRITE"] + (["REQUEST_CONTEXT"] if request else [])
    return {"capability_id":"CAP-101", "schema_version":1, "project_id":"e1", "role":"BUILDER", "execution_id":"EXEC-101", "issued_at":"2026-09-19T21:00:00Z", "baseline_sha":BASELINE, "allowed_reads":["src/a.py"], "allowed_writes":["src/b.py"], "allowed_executes":[], "allowed_operations":ops, "forbidden_operations":["INTENT_APPROVAL"], "allowed_request_types":[], "scope_bindings":{"intent_id":"I-001","intent_version":1,"graph_id":"G-001","graph_version":1,"eu_id":"EU-001"}, "version":1, "issued_by":"controller"}


def state(root):
    return {"project_root":str(root), "project_id":"e1", "execution_id":"EXEC-101", "baseline_sha":BASELINE, "role":"BUILDER"}


def packet(max_bytes=10000, packet_id="CP-101"):
    resource = lambda rid, path, authority: {"resource_id":rid,"path":path,"purpose":"required task input","authority":authority,"reason_included":"EU-001 implementation contract","source":"explicit project input","freshness_or_version":"HEAD"}
    return {"context_packet_id":packet_id,"intent_binding":{"intent_id":"I-001","intent_version":1},"graph_binding":{"graph_id":"G-001","graph_version":1},"eu_binding":{"eu_id":"EU-001"},"authority_context":{"allowed_operations":["READ","WRITE"],"acceptance_requirements":["tests pass"]},"working_context":[resource("RES-001","src/a.py","READ"),resource("RES-002","src/b.py","WRITE")],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":max_bytes}}


def issue(root, request=False):
    (root / "src").mkdir(); (root / "src/a.py").write_text("class A: pass\n"); (root / "src/b.py").write_text("class B: pass\n")
    return CapabilityIssuer(root).issue(capability(root, request), event_id="evt-cap-101", timestamp="2026-09-19T21:00:01Z")


def test_compile_packet_is_explicit_provenance_bound_and_restartable(tmp_path: Path):
    issue(tmp_path)
    compiler = ContextCompiler(tmp_path)
    created = compiler.compile(packet(), capability_id="CAP-101", state=state(tmp_path), event_id="evt-packet-101", timestamp="2026-09-19T21:00:02Z")
    assert created["working_context"][0]["path"] == str((tmp_path / "src/a.py").resolve())
    assert created["working_context"][0]["reason_included"]
    expected = hashlib.sha256(canonical_json({k:v for k,v in created.items() if k != "packet_hash"}).encode()).hexdigest()
    assert created["packet_hash"] == expected
    fresh = ContextCompiler(tmp_path)
    assert fresh.load_for_execution("CP-101", state(tmp_path)) == created


def test_request_is_capability_gated_and_does_not_search(tmp_path: Path):
    issue(tmp_path, request=True)
    compiler = ContextCompiler(tmp_path)
    request = compiler.request_context({"context_request_id":"CR-101","context_packet_id":"CP-101","request_type":"MISSING_INTERFACE","requested_resource_or_question":"Need definition of PaymentProvider","reason":"src/a.py references the interface","expected_use":"complete the authorized EU"}, capability_id="CAP-101", state=state(tmp_path), event_id="evt-request-101", timestamp="2026-09-19T21:00:03Z")
    assert request["status"] == "REQUESTED"
    assert compiler.store.reconstruct()["requests"]["CR-101"] == request
    assert not (tmp_path / "legacy").exists()


def test_new_packet_preserves_previous_packet(tmp_path: Path):
    issue(tmp_path, request=True); compiler = ContextCompiler(tmp_path)
    first = compiler.compile(packet(packet_id="CP-101"), capability_id="CAP-101", state=state(tmp_path), event_id="evt-packet-101", timestamp="2026-09-19T21:00:02Z")
    second_input = packet(packet_id="CP-102"); second_input["supersedes_packet_id"] = first["context_packet_id"]
    second = compiler.compile(second_input, capability_id="CAP-101", state=state(tmp_path), event_id="evt-packet-102", timestamp="2026-09-19T21:00:04Z")
    assert compiler.store.read_packet("CP-101") == first
    assert second["supersedes_packet_id"] == "CP-101"

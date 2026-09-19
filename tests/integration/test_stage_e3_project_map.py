import json
import os
from pathlib import Path

import pytest

from control.authorization import CapabilityIssuer
from control.context import ContextCompiler, ProjectMapBuilder, ProjectMapStore, ScoutResolver
from control.models.store import StageCStore


BASELINE = "b" * 40


def intent(project="e3"):
    return {"intent_id":"I-001","version":1,"status":"DRAFT","created_at":"2026-09-19T23:00:00Z","created_by":"operator","project_id":project,"title":"map fixture","purpose":"prove map","requirements":[{"requirement_id":"REQ-001","text":"index payments"}],"constraints":[],"acceptance_summary":"map is derived","source_event_id":"evt-i","schema_version":1}


def graph(project="e3"):
    return {"graph_id":"G-001","version":1,"project_id":project,"intent_id":"I-001","intent_version":1,"status":"ACTIVE","created_at":"2026-09-19T23:00:02Z","created_by":"planner","nodes":[{"eu_id":"EU-001","requirement_ids":["REQ-001"]}],"edges":[],"reason":"fixture","source_event_id":"evt-g","schema_version":1}


def scout_capability():
    return {"capability_id":"CAP-903","schema_version":1,"project_id":"e3","role":"SCOUT","execution_id":"EXEC-SCOUT-301","issued_at":"2026-09-19T23:00:03Z","baseline_sha":BASELINE,"allowed_reads":["src/payments"],"allowed_writes":[],"allowed_executes":[],"allowed_operations":["READ","RESOLVE_CONTEXT","CREATE_ARTIFACT"],"forbidden_operations":["WRITE"],"allowed_request_types":[],"scope_bindings":{},"version":1,"issued_by":"controller"}


def fixture(root: Path):
    (root / "src/payments").mkdir(parents=True); (root / "tests").mkdir(); (root / "schemas").mkdir()
    (root / "src/payments/provider.py").write_text("class PaymentProvider:\n    pass\n")
    (root / "src/payments/service.py").write_text("from src.payments.provider import PaymentProvider\n")
    (root / "tests/test_payments.py").write_text("def test_provider():\n    assert True\n")
    (root / "schemas/payment.schema.json").write_text("{}\n")
    (root / "private/ignored.txt").parent.mkdir(); (root / "private/ignored.txt").write_text("secret")
    outside = root.parent / "outside.txt"; outside.write_text("outside")
    (root / "src/payments/outside-link").symlink_to(outside)
    (root / "nested-repo/.git").mkdir(parents=True); (root / "nested-repo/private.py").write_text("class ShouldNotAppear: pass\n")
    store = StageCStore(root); store.create_intent_draft(intent(), event_id="evt-i", timestamp="2026-09-19T23:00:00Z", actor_type="agent", actor_id="operator"); store.approve_intent("I-001", 1, event_id="evt-a", timestamp="2026-09-19T23:00:01Z", actor_type="human", actor_id="operator"); store.create_graph(graph(), event_id="evt-g", timestamp="2026-09-19T23:00:02Z", actor_type="agent", actor_id="planner")


def test_project_map_contains_deterministic_structure_and_rebuilds(tmp_path: Path):
    fixture(tmp_path); builder = ProjectMapBuilder(tmp_path)
    first = builder.build(project_map_id="PM-001", project_id="e3", baseline_sha=BASELINE, created_at="2026-09-19T23:01:00Z"); builder.write(first)
    assert any(item["relative_path"] == "src/payments/provider.py" for item in first["files"])
    assert any(item["name"] == "PaymentProvider" for item in first["symbols"])
    assert any(item["relative_path"] == "schemas/payment.schema.json" and item["classification"] == "schema" for item in first["files"])
    assert first["intent_bindings"] == [{"requirement_id":"REQ-001","eu_id":"EU-001","intent_id":"I-001","intent_version":1}]
    assert not any("outside" in item.get("relative_path", "") or "ShouldNotAppear" in json.dumps(item) or item.get("relative_path", "").startswith("private/") for item in first["files"] + first["symbols"])
    os.unlink(ProjectMapStore(tmp_path).path("PM-001")); second = ProjectMapBuilder(tmp_path).build(project_map_id="PM-001", project_id="e3", baseline_sha=BASELINE, created_at="2026-09-19T23:01:00Z")
    assert first == second


def test_map_tamper_and_stale_baseline_fail_closed(tmp_path: Path):
    fixture(tmp_path); document = ProjectMapBuilder(tmp_path).build(project_map_id="PM-001", project_id="e3", baseline_sha=BASELINE, created_at="2026-09-19T23:01:00Z"); ProjectMapBuilder(tmp_path).write(document)
    with pytest.raises(Exception, match="STALE_MAP"): ProjectMapStore(tmp_path).read("PM-001", expected_baseline_sha="c" * 40)
    path = ProjectMapStore(tmp_path).path("PM-001"); tampered = json.loads(path.read_text()); tampered["map_hash"] = "0" * 64; path.write_text(json.dumps(tampered))
    with pytest.raises(Exception, match="hash mismatch"): ProjectMapStore(tmp_path).read("PM-001")


def test_scout_prefers_map_and_falls_back_without_granting_worker_authority(tmp_path: Path):
    fixture(tmp_path); builder = ProjectMapBuilder(tmp_path); document = builder.build(project_map_id="PM-001", project_id="e3", baseline_sha=BASELINE, created_at="2026-09-19T23:01:00Z"); builder.write(document)
    CapabilityIssuer(tmp_path).issue(scout_capability(), event_id="evt-cap", timestamp="2026-09-19T23:00:03Z")
    compiler = ContextCompiler(tmp_path); packet = {"context_packet_id":"CP-301","intent_binding":{},"graph_binding":{},"eu_binding":{},"authority_context":{"allowed_operations":["READ"]},"working_context":[],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":100000}}
    worker = {"project_root":str(tmp_path),"project_id":"e3","execution_id":"EXEC-SCOUT-301","baseline_sha":BASELINE,"role":"SCOUT"}
    # A durable request is normally created by a worker capability; the map only supplies a finding.
    compiler.store.event_log.verify()
    request = {"context_request_id":"CR-301","context_packet_id":"CP-301","request_type":"MISSING_RESOURCE","requested_resource_or_question":"PaymentProvider","reason":"fixture","expected_use":"read provider"}
    # Exercise map lookup through a minimal durable E2 chain using the Scout capability itself.
    compiler.store._request_path("CR-301").parent.mkdir(parents=True, exist_ok=True)
    request.update({"schema_version":1,"project_id":"e3","execution_id":"EXEC-SCOUT-301","role":"SCOUT","created_at":"2026-09-19T23:00:04Z","status":"REQUESTED","capability_id":"CAP-903","baseline_sha":BASELINE,"source_event_id":"evt-request"})
    from control.context.compiler import validate_context_request
    validate_context_request(request); compiler.store._request_path("CR-301").write_text(json.dumps(request))
    # This synthetic request is not lifecycle authority; the event is still required for reconstruction.
    event = compiler.store.event_log.new_event(event_id="evt-request", event_type="context.request.created", timestamp="2026-09-19T23:00:04Z", project_id="e3", actor_type="controller", actor_id="context-compiler", execution_id="EXEC-SCOUT-301", payload={"request":request}); compiler.store.event_log.append(event)
    result = ScoutResolver(tmp_path).resolve("CR-301", scout_capability_id="CAP-903", scout_state=worker, search_scope={"root":"src/payments","project_map_id":"PM-001"}, query_or_need="PaymentProvider", resolution_id="SR-301", event_id="evt-resolution", timestamp="2026-09-19T23:00:05Z")
    assert result["resolution_source"] == "PROJECT_MAP" and result["search_trace"]["files_examined"] == 0
    assert "WRITE" not in result["selected_findings"][0]

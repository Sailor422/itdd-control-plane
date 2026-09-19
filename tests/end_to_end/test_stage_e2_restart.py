from pathlib import Path

from control.context import ContextCompiler, ScoutResolver
from tests.integration.test_stage_e2_resolver import setup
from tests.integration.test_stage_e1_context import packet


def test_fresh_process_reconstructs_request_resolution_and_packet_chain(tmp_path: Path):
    worker=setup(tmp_path); compiler=ContextCompiler(tmp_path); compiler.compile(packet(packet_id="CP-201"), capability_id="CAP-201", state=worker, event_id="evt-packet", timestamp="2026-09-19T22:00:03Z"); compiler.request_context({"context_request_id":"CR-201","context_packet_id":"CP-201","request_type":"MISSING_RESOURCE","requested_resource_or_question":"PaymentProvider","reason":"x","expected_use":"x"}, capability_id="CAP-201", state=worker, event_id="evt-request", timestamp="2026-09-19T22:00:04Z")
    ScoutResolver(tmp_path).resolve("CR-201", scout_capability_id="CAP-902", scout_state={"project_root":str(tmp_path),"project_id":"e2","execution_id":"EXEC-SCOUT-201","baseline_sha":"c"*40}, search_scope={"root":"src/payments"}, query_or_need="PaymentProvider", resolution_id="SR-201", event_id="evt-res", timestamp="2026-09-19T22:00:05Z")
    compiler.compile_from_resolution(packet(packet_id="CP-202"), resolution_id="SR-201", capability_id="CAP-201", state=worker, event_id="evt-packet-2", timestamp="2026-09-19T22:00:06Z", grant_event_id="evt-grant")
    fresh=ContextCompiler(tmp_path); reconstructed=fresh.store.reconstruct(); assert set(reconstructed["resolutions"]) == {"SR-201"}; assert set(reconstructed["packets"]) == {"CP-201","CP-202"}; assert reconstructed["requests"]["CR-201"]["status"] == "GRANTED"; fresh.store.verify_materialized()

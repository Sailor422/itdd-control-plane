from pathlib import Path

from control.context import ContextCompiler
from tests.integration.test_stage_e1_context import issue, packet, state


def test_fresh_process_reconstructs_packets_and_requests(tmp_path: Path):
    issue(tmp_path, request=True)
    compiler = ContextCompiler(tmp_path)
    compiler.compile(packet(), capability_id="CAP-101", state=state(tmp_path), event_id="evt-packet", timestamp="2026-09-19T21:00:02Z")
    compiler.request_context({"context_request_id":"CR-101","context_packet_id":"CP-101","request_type":"MISSING_RESOURCE","requested_resource_or_question":"X","reason":"required contract","expected_use":"verification"}, capability_id="CAP-101", state=state(tmp_path), event_id="evt-request", timestamp="2026-09-19T21:00:03Z")
    fresh = ContextCompiler(tmp_path)
    reconstructed = fresh.store.reconstruct()
    assert set(reconstructed["packets"]) == {"CP-101"}
    assert reconstructed["requests"]["CR-101"]["status"] == "REQUESTED"
    fresh.store.verify_materialized()

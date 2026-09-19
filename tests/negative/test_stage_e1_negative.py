from pathlib import Path
import json
import pytest

from control.authorization import CapabilityIssuer
from control.context import ContextCompilationError, ContextCompiler, ContextRequestError

from tests.integration.test_stage_e1_context import BASELINE, capability, issue, packet, state


def test_unauthorized_path_and_capability_expansion_rejected(tmp_path: Path):
    issue(tmp_path); compiler = ContextCompiler(tmp_path)
    bad = packet(); bad["working_context"][0]["path"] = "src/secret.py"
    with pytest.raises(ContextCompilationError, match="resource rejected"):
        compiler.compile(bad, capability_id="CAP-101", state=state(tmp_path), event_id="evt-bad-1", timestamp="2026-09-19T21:00:02Z")
    bad = packet(); bad["authority_context"]["allowed_operations"] = ["READ", "WRITE", "APPEND_EVENT"]
    with pytest.raises(ContextCompilationError, match="beyond capability"):
        compiler.compile(bad, capability_id="CAP-101", state=state(tmp_path), event_id="evt-bad-2", timestamp="2026-09-19T21:00:03Z")


def test_wrong_binding_budget_symlink_and_legacy_path_rejected(tmp_path: Path):
    issue(tmp_path); compiler = ContextCompiler(tmp_path)
    compiler.compile(packet(), capability_id="CAP-101", state=state(tmp_path), event_id="evt-packet", timestamp="2026-09-19T21:00:01Z")
    with pytest.raises(ContextCompilationError, match="binding"):
        compiler.load_for_execution("CP-101", {**state(tmp_path), "execution_id":"EXEC-OTHER"})
    with pytest.raises(ContextCompilationError, match="REQUIRED_CONTEXT_EXCEEDS_BUDGET"):
        compiler.compile(packet(max_bytes=50), capability_id="CAP-101", state=state(tmp_path), event_id="evt-budget", timestamp="2026-09-19T21:00:02Z")
    outside = tmp_path.parent / "outside-e1"; outside.mkdir(); (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    bad = packet(); bad["working_context"][0]["path"] = "link/secret.py"
    with pytest.raises(ContextCompilationError): compiler.compile(bad, capability_id="CAP-101", state=state(tmp_path), event_id="evt-link", timestamp="2026-09-19T21:00:03Z")
    bad = packet(); bad["working_context"][0]["path"] = "/Users/herbertfields/.codex/secret.md"
    with pytest.raises(ContextCompilationError): compiler.compile(bad, capability_id="CAP-101", state=state(tmp_path), event_id="evt-legacy", timestamp="2026-09-19T21:00:04Z")


def test_request_without_capability_and_packet_tamper_rejected(tmp_path: Path):
    issue(tmp_path); compiler = ContextCompiler(tmp_path)
    request = {"context_request_id":"CR-101","context_packet_id":"CP-101","request_type":"MISSING_RESOURCE","requested_resource_or_question":"x","reason":"x","expected_use":"x"}
    with pytest.raises(ContextRequestError): compiler.request_context(request, capability_id="CAP-404", state=state(tmp_path), event_id="evt-request", timestamp="2026-09-19T21:00:02Z")
    compiler.compile(packet(), capability_id="CAP-101", state=state(tmp_path), event_id="evt-packet", timestamp="2026-09-19T21:00:03Z")
    path = tmp_path / ".idd/context/packets/CP-101/v1.json"; data = json.loads(path.read_text()); data["working_context"][0]["path"] = str(tmp_path / "src/other.py"); path.write_text(json.dumps(data))
    with pytest.raises(Exception): compiler.load_for_execution("CP-101", state(tmp_path))

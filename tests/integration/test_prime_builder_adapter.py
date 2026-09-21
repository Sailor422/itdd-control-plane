import hashlib
import json
import sys
import textwrap
from pathlib import Path

import pytest

from control.operational import OperationalError, PrimeBuilderAdapter


def fake_prime(path: Path, *, mode: str = "ok") -> Path:
    path.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import json, pathlib, sys, time
        prompt = sys.argv[-1]
        if {mode!r} == "timeout":
            time.sleep(2)
        if {mode!r} == "fail":
            print("failed", file=sys.stderr)
            raise SystemExit(9)
        print(json.dumps({{"type": "result", "prompt_seen": prompt}}))
    """))
    path.chmod(0o755)
    return path


def inputs(tmp_path: Path):
    packet = {"context_packet_id": "CP-1", "working_context": ["REQ"]}
    capability = {"capability_id": "CAP-1", "allowed_writes": ["src/a.py"]}
    return packet, capability


def test_prime_adapter_is_fresh_bounded_and_provenance(tmp_path: Path):
    binary = fake_prime(tmp_path / "prime", mode="ok")
    # The fake gets its log path as its first argument; this does not enter the worker prompt.
    adapter = PrimeBuilderAdapter(prime_binary=str(binary))
    packet, capability = inputs(tmp_path)
    result = adapter.run(project_root=tmp_path, worktree=tmp_path, execution_id="EXEC-1",
                         context_packet=packet, capability=capability)
    command = result["runtime_provenance"]["command"]
    assert "--print" in command and "--mode" in command and "json" in command
    assert "--no-session" in command and "--no-context-files" in command
    assert "--no-skills" in command and "--no-extensions" in command
    assert "--no-prompt-templates" in command and "--no-themes" in command
    assert "<controller-supplied-prompt>" in command
    assert result["runtime_provenance"]["execution_id"] == "EXEC-1"
    assert result["runtime_provenance"]["stdout_sha256"] == hashlib.sha256(result["stdout"].encode()).hexdigest()
    assert result["runtime_provenance"]["prompt_sha256"]


def test_prime_prompt_contains_only_bounded_sections():
    prompt = PrimeBuilderAdapter._prompt({"context_packet_id": "CP", "x": "value"}, {"capability_id": "CAP"})
    assert "BEGIN CONTROLLER CONTEXT PACKET" in prompt
    assert "BEGIN CONTROLLER CAPABILITY ENVELOPE" in prompt
    assert "Do not create commits" in prompt


@pytest.mark.parametrize("mode, message", [("fail", "failed"), ("timeout", "timed out")])
def test_prime_adapter_fails_closed(tmp_path: Path, mode: str, message: str):
    binary = fake_prime(tmp_path / "prime", mode=mode)
    adapter = PrimeBuilderAdapter(prime_binary=str(binary), timeout_seconds=2 if mode == "fail" else 0.1)
    packet, capability = inputs(tmp_path)
    with pytest.raises(OperationalError, match=message):
        adapter.run(project_root=tmp_path, worktree=tmp_path, execution_id="EXEC-FAIL",
                    context_packet=packet, capability=capability)

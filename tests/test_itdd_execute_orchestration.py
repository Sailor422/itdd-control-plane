import json
import subprocess
import sys
from pathlib import Path

from tools.itdd_execute import (
    create_controller_candidate,
    controller_assign_execution,
    harmless_isolation_proof,
    invoke,
    reported_pass,
    verify_gate_decision,
)


def test_test_role_gets_writable_temp_without_candidate_write_access():
    result = harmless_isolation_proof()
    assert result["proof_passed"] is True
    assert result["candidate_unchanged"] is True
    assert result["sentinel"] == "immutable\n"
    assert result["scratch_files"]


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "controller"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "controller@example.invalid"], cwd=root, check=True)
    (root / "README.md").write_text("baseline\n")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
    return root, git(root, "rev-parse", "HEAD")


def test_controller_freezes_builder_result_as_git_commit_and_tree(tmp_path: Path):
    root, baseline = repo(tmp_path)
    (root / "tools").mkdir()
    (root / "tools/itdd_execute.py").write_text("candidate\n")
    candidate = create_controller_candidate(root, baseline, "ITDD-BUILD-test")
    assert candidate["provenance"] == "controller-owned-git-commit"
    assert candidate["baseline_sha"] == baseline
    assert candidate["build_execution_id"] == "ITDD-BUILD-test"
    assert candidate["changed_paths"] == ["tools/itdd_execute.py"]
    assert candidate["candidate_commit_sha"] == git(root, "rev-parse", "HEAD")
    assert candidate["candidate_tree_sha"] == git(root, "rev-parse", "HEAD^{tree}")
    assert git(root, "rev-parse", "HEAD^") == baseline


def test_controller_rejects_unscoped_builder_change_before_candidate_commit(tmp_path: Path):
    root, baseline = repo(tmp_path)
    (root / "outside.txt").write_text("unauthorized\n")
    try:
        create_controller_candidate(root, baseline, "ITDD-BUILD-test")
    except RuntimeError as exc:
        assert "unauthorized paths" in str(exc)
    else:
        raise AssertionError("unscoped builder change was accepted")
    assert git(root, "rev-parse", "HEAD") == baseline


def test_test_evidence_must_bind_exact_git_identity_not_digest(tmp_path: Path):
    identity = {
        "baseline_sha": "a" * 40,
        "candidate_commit_sha": "b" * 40,
        "candidate_tree_sha": "c" * 40,
    }
    output = tmp_path / "test.json"
    output.write_text(json.dumps({"status": "PASS", **identity, "candidate_digest": "not-authoritative"}))
    record = {"role": "TEST", "controller_assigned_role": "TEST", "output_exists": True, "output_file": str(output), "terminal_state": "PASS"}
    assert reported_pass(record, "TEST", identity)
    output.write_text(json.dumps({"status": "PASS", **{**identity, "candidate_tree_sha": "d" * 40}, "candidate_digest": "not-authoritative"}))
    assert not reported_pass(record, "TEST", identity)


def test_verify_evidence_requires_independent_observation_of_same_candidate(tmp_path: Path):
    identity = {"baseline_sha": "a" * 40, "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "c" * 40}
    output = tmp_path / "verify.json"
    output.write_text(json.dumps({"status": "PASS", "independently_observed_candidate": identity}))
    record = {"role": "VERIFY", "controller_assigned_role": "VERIFY", "output_exists": True, "output_file": str(output), "terminal_state": "PASS"}
    assert reported_pass(record, "VERIFY", identity)
    output.write_text(json.dumps({"status": "PASS", "independently_observed_candidate": {**identity, "candidate_commit_sha": "d" * 40}}))
    assert not reported_pass(record, "VERIFY", identity)


def command_fixture(tmp_path: Path) -> tuple[Path, Path]:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "sentinel.txt").write_text("immutable\n")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    return candidate, scratch


def python_process(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def test_normal_test_completion_captures_streams_and_heartbeat(tmp_path: Path):
    candidate, scratch = command_fixture(tmp_path)
    source = "import json, os, sys, time; print('stdout-line', flush=True); print('stderr-line', file=sys.stderr, flush=True); time.sleep(.05); open(os.environ['ITDD_OUTPUT'], 'w').write(json.dumps({'status':'PASS'}))"
    record = invoke(role="TEST", candidate=candidate, prompt="", scratch=scratch, writable=False, command_override=python_process(source), timeout_seconds=2, heartbeat_seconds=0.01)
    assert record["terminal_state"] == "PASS"
    assert "stdout-line" in Path(record["stdout_file"]).read_text()
    assert "stderr-line" in Path(record["stderr_file"]).read_text()
    assert Path(record["heartbeat_file"]).exists()
    assert record["candidate_unchanged"] is True


def test_failing_test_is_fail_and_missing_completion_cannot_pass(tmp_path: Path):
    candidate, scratch = command_fixture(tmp_path)
    source = "import json, os, sys; print('failed-output'); print('failed-error', file=sys.stderr); open(os.environ['ITDD_OUTPUT'], 'w').write(json.dumps({'status':'FAIL'})); raise SystemExit(3)"
    record = invoke(role="TEST", candidate=candidate, prompt="", scratch=scratch, writable=False, command_override=python_process(source), timeout_seconds=2, heartbeat_seconds=0.01)
    assert record["terminal_state"] == "FAIL"
    assert "failed-output" in Path(record["stdout_file"]).read_text()
    assert "failed-error" in Path(record["stderr_file"]).read_text()
    assert record["candidate_unchanged"] is True
    assert not reported_pass(record, "TEST", {"baseline_sha": "a", "candidate_commit_sha": "b", "candidate_tree_sha": "c"})


def test_hanging_test_times_out_and_blocks_verify(tmp_path: Path):
    candidate, scratch = command_fixture(tmp_path)
    record = invoke(role="TEST", candidate=candidate, prompt="", scratch=scratch, writable=False, command_override=python_process("import time; print('before-hang', flush=True); time.sleep(10)"), timeout_seconds=0.15, heartbeat_seconds=0.01)
    assert record["terminal_state"] == "TIMEOUT"
    assert "before-hang" in Path(record["stdout_file"]).read_text()
    assert "timeout" in str(record["terminal_reason"])
    assert record["candidate_unchanged"] is True
    assert not reported_pass(record, "TEST", {"baseline_sha": "a", "candidate_commit_sha": "b", "candidate_tree_sha": "c"})


def test_interrupted_test_is_terminal_and_candidate_unchanged(tmp_path: Path):
    candidate, scratch = command_fixture(tmp_path)
    record = invoke(role="TEST", candidate=candidate, prompt="", scratch=scratch, writable=False, command_override=python_process("import time; print('before-interrupt', flush=True); time.sleep(10)"), timeout_seconds=2, heartbeat_seconds=0.01, interrupt_after_seconds=0.15)
    assert record["terminal_state"] == "INTERRUPTED"
    assert "before-interrupt" in Path(record["stdout_file"]).read_text()
    assert record["candidate_unchanged"] is True


def test_successful_test_allows_verify_only_with_exact_identity(tmp_path: Path):
    identity = {"baseline_sha": "a" * 40, "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "c" * 40}
    output = tmp_path / "verify.json"
    output.write_text(json.dumps({"status": "PASS", "independently_observed_candidate": identity}))
    record = {"role": "VERIFY", "controller_assigned_role": "VERIFY", "output_exists": True, "output_file": str(output), "terminal_state": "PASS"}
    assert reported_pass(record, "VERIFY", identity)


def test_controller_verify_gate_rejects_role_spoof_and_preserves_reason(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ITDD_ROLE", "VERIFY")
    identity = {"baseline_sha": "a" * 40, "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "c" * 40}
    output = tmp_path / "test.json"
    output.write_text(json.dumps({"status": "PASS", **identity}))
    record = {"role": "BUILDER", "controller_assigned_role": "BUILDER", "execution_id": "ITDD-BUILD-spoof", "terminal_state": "PASS", "returncode": 0, "candidate_unchanged": True, "candidate_git_clean": True, "candidate_git_before": {**identity, "clean": True}, "candidate_git_after": {**identity, "clean": True}, "output_exists": True, "output_file": str(output), **identity}
    decision = verify_gate_decision(record, identity)
    assert decision["allowed"] is False
    assert decision["assigned_role"] == "TEST"
    assert decision["claimed_role"] == "BUILDER"
    assert decision["execution_id"] == "ITDD-BUILD-spoof"
    assert decision["reasons"]


def test_controller_verify_gate_rejects_dirty_candidate(tmp_path: Path):
    identity = {"baseline_sha": "a" * 40, "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "c" * 40}
    output = tmp_path / "test.json"
    output.write_text(json.dumps({"status": "PASS", **identity}))
    record = {"role": "TEST", "controller_assigned_role": "TEST", "execution_id": "ITDD-TEST-real", "terminal_state": "PASS", "returncode": 0, "candidate_unchanged": True, "candidate_git_clean": False, "candidate_git_before": {**identity, "clean": True}, "candidate_git_after": {**identity, "clean": False, "status_short": "M tracked.txt"}, "output_exists": True, "output_file": str(output), **identity}
    decision = verify_gate_decision(record, identity)
    assert decision["allowed"] is False
    assert any("dirty" in reason for reason in decision["reasons"])


def test_controller_verify_gate_rejects_fabricated_test_assignment(tmp_path: Path):
    identity = {"baseline_sha": "a" * 40, "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "c" * 40}
    output = tmp_path / "test.json"
    output.write_text(json.dumps({"status": "PASS", **identity}))
    fabricated = {"role": "TEST", "controller_assigned_role": "TEST", "execution_id": "ITDD-TEST-fabricated", "terminal_state": "PASS", "returncode": 0, "candidate_unchanged": True, "candidate_git_clean": True, "candidate_git_before": {**identity, "clean": True}, "candidate_git_after": {**identity, "clean": True}, "output_exists": True, "output_file": str(output), **identity}
    assert verify_gate_decision(fabricated, identity)["allowed"] is False


def test_controller_issued_test_assignment_is_required_for_verify(tmp_path: Path):
    identity = {"baseline_sha": "a" * 40, "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "c" * 40}
    output = tmp_path / "test.json"
    output.write_text(json.dumps({"status": "PASS", **identity}))
    execution_id = "ITDD-TEST-controller-issued"
    controller_assign_execution(execution_id=execution_id, role="TEST", identity=identity, scratch=tmp_path)
    record = {"role": "TEST", "controller_assigned_role": "TEST", "execution_id": execution_id, "terminal_state": "PASS", "returncode": 0, "candidate_unchanged": True, "candidate_git_clean": True, "candidate_git_before": {**identity, "clean": True}, "candidate_git_after": {**identity, "clean": True}, "output_exists": True, "output_file": str(output), **identity}
    assert verify_gate_decision(record, identity)["allowed"] is True
    assert (tmp_path / f"{execution_id}.assignment.json").exists()


def test_mutation_during_test_is_recorded_and_fails_closed(tmp_path: Path):
    candidate, identity = repo(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    identity = {"baseline_sha": identity, **{f: git(candidate, "rev-parse", f) for f in ("HEAD", "HEAD^{tree}")}}
    identity = {"baseline_sha": identity["baseline_sha"], "candidate_commit_sha": identity["HEAD"], "candidate_tree_sha": identity["HEAD^{tree}"]}
    source = "import json, os, pathlib; pathlib.Path('README.md').write_text('mutated\\n'); open(os.environ['ITDD_OUTPUT'], 'w').write(json.dumps({'status':'PASS', **{k: os.environ['ITDD_'+k.upper()] for k in []}}))"
    record = invoke(role="TEST", candidate=candidate, prompt="", scratch=scratch, writable=True, command_override=python_process(source), timeout_seconds=2, heartbeat_seconds=0.01, identity=identity)
    assert record["candidate_git_clean"] is False
    assert record["candidate_unchanged"] is False
    assert verify_gate_decision(record, identity)["allowed"] is False

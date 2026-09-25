import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.itdd_execute import (
    create_controller_candidate,
    controller_assign_execution,
    build_test_prompt,
    harmless_isolation_proof,
    invoke,
    reported_pass,
    allowed_test_command_for,
    validate_test_command,
    verify_gate_decision,
)


def test_test_command_allowlist_rejects_excluded_black_box_nodes(tmp_path: Path):
    candidate = tmp_path / "candidate"
    allowed = allowed_test_command_for(candidate)
    validate_test_command(allowed, candidate)
    with pytest.raises(ValueError, match="outside CODEX-RUNTIME-ROLES-V1 scope"):
        validate_test_command(f"{allowed}::test_full_single_eu_path_and_reconstruction", candidate)
    with pytest.raises(ValueError, match="outside CODEX-RUNTIME-ROLES-V1 scope"):
        validate_test_command("python3 scripts/verify_single_eu_operational_v1.py", candidate)


def test_test_prompt_forbids_excluded_black_box_scripts(tmp_path: Path):
    identity = {"baseline_sha": "a" * 40, "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "c" * 40}
    command = "cd /candidate && PYTHONPATH=/candidate pytest -q tests/test_itdd_execute_orchestration.py"
    prompt = build_test_prompt(test_dir=tmp_path / "candidate", scratch=tmp_path / "scratch", identity=identity, test_command=command)
    assert command in prompt
    assert "Do not run any other test command or verification script" in prompt
    assert "do NOT run scripts/verify_*.py" in prompt
    assert "black-box single-EU acceptance" in prompt


def test_test_role_gets_writable_temp_without_candidate_write_access():
    result = harmless_isolation_proof()
    assert result["proof_passed"] is True
    assert result["candidate_unchanged"] is True
    assert result["sentinel"] == "immutable\n"
    assert result["scratch_files"]


def test_live_read_only_role_uses_scratch_codex_home_and_read_only_sandbox(tmp_path: Path):
    candidate, scratch = command_fixture(tmp_path)
    source = "import json, os; open(os.environ['ITDD_OUTPUT'], 'w').write(json.dumps({'status':'PASS'}))"
    record = invoke(role="TEST", candidate=candidate, prompt="", scratch=scratch, writable=False, command_override=python_process(source), timeout_seconds=2)
    assert record["candidate_unchanged"] is True
    assert record["temp_env"]["TMPDIR"] == str(scratch)
    assert record["sandbox_mode"] == "workspace-write"
    assert str(candidate) not in record["argv"]
    assert record["candidate_access_mode"] == "read-only-outside-workspace"
    assert record["codex_home"] == str(scratch / "codex-home")


def test_live_read_only_role_seeds_auth_into_scratch_without_using_candidate(tmp_path: Path, monkeypatch):
    source_home = tmp_path / "source-codex-home"
    source_home.mkdir()
    (source_home / "auth.json").write_text('{"token":"secret"}\n')
    (source_home / "config.toml").write_text('model = "gpt-5.5"\n')
    monkeypatch.setenv("CODEX_HOME", str(source_home))
    candidate, scratch = command_fixture(tmp_path)
    source = "import json, os; open(os.environ['ITDD_OUTPUT'], 'w').write(json.dumps({'status':'PASS'}))"
    record = invoke(role="TEST", candidate=candidate, prompt="", scratch=scratch, writable=False, command_override=python_process(source), timeout_seconds=2)
    isolated = scratch / "codex-home"
    assert record["codex_auth_seeded"] is True
    assert (isolated / "auth.json").read_text() == '{"token":"secret"}\n'
    assert (isolated / "config.toml").exists()
    assert record["candidate_unchanged"] is True


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


def admission_fixture(tmp_path):
    from tools.itdd_execute import admit_task
    packet = {
        "objective": "Implement the #57 task-admission boundary: only a separately authorized, single-ticket request with the approved packet may reach the injected role runner.",
        "allowed_paths": ["tools/itdd_execute.py", "tests/test_itdd_execute_orchestration.py"],
        "forbidden_paths": ["all repository paths other than the two allowed paths", "BUILD→TEST→VERIFY sequencing", "candidate/evidence binding", "Prime-host integration or live-host proof", "model/provider/fallback selection or model-specific launcher", "issue-tracker changes, promotion, merge, or tagging"],
        "starting_commit": "12119dc10509684be8b7cfd444bcca8f6ab2b720",
        "acceptance_criteria": ["Missing request IDs, zero/multiple IDs, a mismatch with source_ticket_id, or invalid ticket identity fails before the injected runner is called.", "A modified objective, path, criterion, test list, invalid baseline, dirty checkout, or malformed packet fails before any role launches.", "A valid request and packet produce the exact six-field role packet; controller metadata stays separate.", "Tests prove every negative admission case results in zero runner calls, and the valid case accepts only the approved packet.", "No model/provider/fallback selector or model-specific launcher is introduced."],
        "relevant_tests": ["tests/test_itdd_execute_orchestration.py"],
    }
    import subprocess
    (tmp_path / "baseline.txt").write_text("baseline")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "baseline.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)
    packet["starting_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    return packet

def test_admit_task_rejects_bad_requests_before_runner(tmp_path):
    import subprocess
    from tools.itdd_execute import admit_task
    packet = admission_fixture(tmp_path)
    calls = []
    baseline = packet["starting_commit"]
    cases = [([], "57", packet, baseline), (["57", "58"], "57", packet, baseline), (["58"], "57", packet, baseline), (["abc"], "abc", packet, baseline), (["57"], "57", {**packet, "objective": "altered"}, baseline), (["57"], "57", {**packet, "allowed_paths": ["tools/itdd_execute.py"]}, baseline), (["57"], "57", {**packet, "acceptance_criteria": []}, baseline), (["57"], "57", {**packet, "relevant_tests": []}, baseline), (["57"], "57", packet, "bad-baseline"), (["57"], "57", {"objective": "malformed"}, baseline)]
    for ids, source, candidate, base in cases:
        with pytest.raises((ValueError, RuntimeError)):
            admit_task(request_ids=ids, source_ticket_id=source, packet=candidate, approved_packet=packet, baseline_sha=base, root=tmp_path, runner=lambda value: calls.append(value))
    assert calls == []

def test_admit_task_rejects_dirty_checkout_before_runner(tmp_path):
    from tools.itdd_execute import admit_task
    packet = admission_fixture(tmp_path)
    (tmp_path / "dirty").write_text("x")
    calls = []
    with pytest.raises((ValueError, RuntimeError)):
        admit_task(request_ids=["57"], source_ticket_id="57", packet=packet, approved_packet=packet, baseline_sha=packet["starting_commit"], root=tmp_path, runner=lambda value: calls.append(value))
    assert calls == []

def test_admit_task_dispatches_exact_six_fields_only(tmp_path):
    from tools.itdd_execute import admit_task
    packet = admission_fixture(tmp_path)
    calls = []
    result = admit_task(request_ids=["57"], source_ticket_id="57", packet=packet, approved_packet=packet, baseline_sha=packet["starting_commit"], root=tmp_path, runner=lambda value: calls.append(value))
    assert calls == [packet]
    assert result == packet

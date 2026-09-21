#!/usr/bin/env python3
"""Fail-fast BUILD -> TEST -> VERIFY orchestration with immutable Git binding.

Git commit and tree identities are the authoritative candidate identity. The
filesystem digest is retained only as secondary diagnostic evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PATHS = {"tools/itdd_execute.py", "tests/test_itdd_execute_orchestration.py"}
CONTROLLER_ASSIGNMENTS: dict[str, dict[str, object]] = {}


def execution_id(role: str) -> str:
    return f"ITDD-{role}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:10]}"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file() and ".git" not in p.parts):
        digest.update(str(item.relative_to(path)).encode())
        digest.update(item.read_bytes())
    return digest.hexdigest()


def changed_paths(root: Path, baseline: str) -> list[str]:
    tracked = git(root, "diff", "--name-only", "--diff-filter=ACDMRTUXB", baseline).splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked + untracked))


def candidate_identity(root: Path) -> dict[str, str]:
    return {"candidate_commit_sha": git(root, "rev-parse", "HEAD"), "candidate_tree_sha": git(root, "rev-parse", "HEAD^{tree}")}


def candidate_git_state(root: Path) -> dict[str, object]:
    identity = candidate_identity(root)
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    return {**identity, "status_short": status, "clean": status == ""}


def controller_assign_execution(*, execution_id: str, role: str, identity: dict[str, str], scratch: Path) -> dict[str, object]:
    """Create controller-owned authority before a worker is launched."""
    assignment = {"execution_id": execution_id, "assigned_role": role, **{key: identity[key] for key in ("baseline_sha", "candidate_commit_sha", "candidate_tree_sha")}, "authority": "controller-issued"}
    if execution_id in CONTROLLER_ASSIGNMENTS:
        raise RuntimeError(f"execution assignment already exists: {execution_id}")
    CONTROLLER_ASSIGNMENTS[execution_id] = assignment
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / f"{execution_id}.assignment.json").write_text(json.dumps(assignment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return assignment


def create_controller_candidate(build_dir: Path, baseline: str, build_execution_id: str) -> dict[str, object]:
    paths = changed_paths(build_dir, baseline)
    unauthorized = sorted(set(paths) - ALLOWED_PATHS)
    if unauthorized:
        raise RuntimeError(f"candidate changed unauthorized paths: {unauthorized}")
    if not paths:
        raise RuntimeError("Builder produced no candidate changes")
    git(build_dir, "add", "--all", "--", *paths)
    git(build_dir, "commit", "--no-verify", "-m", "itdd: freeze immutable candidate")
    identity = candidate_identity(build_dir)
    if git(build_dir, "rev-parse", "HEAD^") != git(build_dir, "rev-parse", baseline):
        raise RuntimeError("candidate parent does not match approved baseline")
    return {"baseline_sha": git(build_dir, "rev-parse", baseline), **identity, "build_execution_id": build_execution_id, "changed_paths": paths, "provenance": "controller-owned-git-commit"}


def _stop_process(process: subprocess.Popen[bytes]) -> str:
    """Terminate the role and report whether escalation to kill was needed."""
    def signal_group(number: int) -> None:
        try:
            os.killpg(process.pid, number)
        except ProcessLookupError:
            pass
        except OSError:
            process.send_signal(number)

    try:
        signal_group(signal.SIGTERM)
        process.wait(timeout=5)
        return "terminate"
    except subprocess.TimeoutExpired:
        signal_group(signal.SIGKILL)
        process.wait(timeout=5)
        return "kill"


def _prepare_isolated_codex_home(runtime_home: Path) -> bool:
    """Seed writable runtime state without putting credentials in evidence."""
    source_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    runtime_home.mkdir(parents=True, exist_ok=True)
    seeded = False
    for name in ("auth.json", "config.toml"):
        source = source_home / name
        if source.is_file():
            destination = runtime_home / name
            shutil.copy2(source, destination)
            if name == "auth.json":
                destination.chmod(0o600)
            seeded = True
    return seeded


def invoke(*, role: str, candidate: Path, prompt: str, scratch: Path, writable: bool, identity: dict[str, str] | None = None, required_test_command: str | None = None, primary: Path | None = None, additional: Path | None = None, command_override: list[str] | None = None, timeout_seconds: float | None = None, heartbeat_seconds: float = 5.0, interrupt_after_seconds: float | None = None) -> dict[str, object]:
    scratch.mkdir(parents=True, exist_ok=True)
    eid = execution_id(role)
    output = scratch / f"{eid}.last-message.json"
    events = scratch / f"{eid}.events.jsonl"
    env = os.environ.copy()
    runtime_home = scratch / "codex-home"
    auth_seeded = False
    if not writable:
        auth_seeded = _prepare_isolated_codex_home(runtime_home)
    env.update({"TMPDIR": str(scratch), "TMP": str(scratch), "TEMP": str(scratch), "ITDD_OUTPUT": str(output), "ITDD_EXECUTION_ID": eid})
    if not writable:
        env["CODEX_HOME"] = str(runtime_home)
    launch_root = primary or candidate
    if writable:
        extra = additional or scratch
        sandbox_mode = "workspace-write"
        candidate_access_mode = "writable-workspace"
    else:
        # Pytest and Python's tempfile need process-level writes. Keep those
        # writes in scratch, and leave the candidate outside Codex's writable
        # workspace; controller snapshots remain the authoritative mutation
        # guard.
        launch_root = primary or scratch
        extra = scratch
        sandbox_mode = "workspace-write"
        candidate_access_mode = "read-only-outside-workspace"
    command = command_override or ["codex", "exec", "--model", "gpt-5.5", "--json", "--sandbox", sandbox_mode, "--add-dir", str(extra), "-C", str(launch_root), "-o", str(output), "-"]
    if timeout_seconds is None and role == "TEST":
        timeout_seconds = float(os.environ.get("ITDD_TEST_TIMEOUT_SECONDS", "600"))
    before = tree_digest(candidate)
    git_before = candidate_git_state(candidate) if (candidate / ".git").exists() else None
    started = time.time()
    stdout_path = events
    stderr_path = scratch / f"{eid}.stderr.log"
    heartbeat_path = scratch / f"{eid}.heartbeat.jsonl"
    stdout_bytes = [0]
    stderr_bytes = [0]
    if identity:
        controller_assign_execution(execution_id=eid, role=role, identity=identity, scratch=scratch)

    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=launch_root, start_new_session=True)
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    process.stdin.write(prompt.encode())
    process.stdin.close()

    def drain(stream, destination: Path, counter: list[int]) -> None:
        with destination.open("wb") as handle:
            while True:
                chunk = stream.readline()
                if not chunk:
                    break
                handle.write(chunk)
                handle.flush()
                counter[0] += len(chunk)

    stdout_thread = threading.Thread(target=drain, args=(process.stdout, stdout_path, stdout_bytes), daemon=True)
    stderr_thread = threading.Thread(target=drain, args=(process.stderr, stderr_path, stderr_bytes), daemon=True)
    stdout_thread.start(); stderr_thread.start()
    terminal_state = "ACTIVE"
    stop_reason = None
    last_heartbeat = 0.0
    started_monotonic = time.monotonic()
    try:
        while process.poll() is None:
            elapsed = time.monotonic() - started_monotonic
            if elapsed - last_heartbeat >= heartbeat_seconds:
                with heartbeat_path.open("a", encoding="utf-8") as heartbeat:
                    heartbeat.write(json.dumps({"timestamp": time.time(), "execution_id": eid, "pid": process.pid, "state": "ACTIVE", "elapsed_seconds": elapsed, "stdout_bytes": stdout_bytes[0], "stderr_bytes": stderr_bytes[0]}) + "\n")
                last_heartbeat = elapsed
            if interrupt_after_seconds is not None and elapsed >= interrupt_after_seconds:
                stop_reason = "interrupt requested by harness"
                terminal_state = "INTERRUPTED"
                _stop_process(process)
                break
            if timeout_seconds is not None and elapsed >= timeout_seconds:
                stop_reason = f"timeout after {timeout_seconds:g} seconds"
                terminal_state = "TIMEOUT"
                _stop_process(process)
                break
            time.sleep(0.05)
    except KeyboardInterrupt:
        stop_reason = "operator interruption"
        terminal_state = "INTERRUPTED"
        _stop_process(process)
    stdout_thread.join(timeout=5); stderr_thread.join(timeout=5)
    if terminal_state == "ACTIVE":
        terminal_state = "PASS" if process.returncode == 0 and output.exists() else "FAIL"
    after = tree_digest(candidate)
    git_after = candidate_git_state(candidate) if (candidate / ".git").exists() else None
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    record: dict[str, object] = {"execution_id": eid, "role": role, "controller_assigned_role": role, "candidate_worktree": str(candidate), "candidate_digest_before": before, "candidate_digest_after": after, "candidate_unchanged": before == after, "candidate_git_before": git_before, "candidate_git_after": git_after, "candidate_git_clean": bool(git_after and git_after["clean"]), "scratch": str(scratch), "temp_env": {key: env[key] for key in ("TMPDIR", "TMP", "TEMP")}, "codex_home": env.get("CODEX_HOME"), "codex_auth_seeded": auth_seeded, "sandbox_mode": sandbox_mode, "candidate_access_mode": candidate_access_mode, "argv": command, "pid": process.pid, "returncode": process.returncode, "started_at": started, "finished_at": time.time(), "stdout_file": str(stdout_path), "stderr_file": str(stderr_path), "stderr": stderr_text, "heartbeat_file": str(heartbeat_path), "stdout_bytes": stdout_bytes[0], "stderr_bytes": stderr_bytes[0], "terminal_state": terminal_state, "terminal_reason": stop_reason, "timeout_seconds": timeout_seconds, "output_file": str(output), "output_exists": output.exists()}
    if identity:
        record.update(identity)
    if required_test_command:
        record["required_test_command"] = required_test_command
    (scratch / f"{eid}.record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def output_json(record: dict[str, object]) -> dict[str, object]:
    if not record["output_exists"]:
        return {}
    try:
        value = json.loads(Path(str(record["output_file"])).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def reported_pass(record: dict[str, object], role: str, identity: dict[str, str]) -> bool:
    if record.get("role") != role or record.get("controller_assigned_role") != role or record.get("terminal_state") != "PASS":
        return False
    result = output_json(record)
    status = str(result.get("status", result.get("verdict", ""))).upper()
    canonical = {key: identity[key] for key in ("baseline_sha", "candidate_commit_sha", "candidate_tree_sha")}
    if role == "TEST":
        return status == "PASS" and all(result.get(key) == value for key, value in canonical.items())
    if role == "VERIFY":
        observed = result.get("independently_observed_candidate", result)
        return status == "PASS" and isinstance(observed, dict) and all(observed.get(key) == value for key, value in canonical.items())
    return bool(record["output_exists"])


def verify_gate_decision(test_record: dict[str, object], identity: dict[str, str]) -> dict[str, object]:
    """Controller-owned TEST-to-VERIFY gate; worker claims grant no authority."""
    reasons: list[str] = []
    assignment = CONTROLLER_ASSIGNMENTS.get(str(test_record.get("execution_id", "")))
    if not assignment or assignment.get("assigned_role") != "TEST":
        reasons.append("no controller-issued TEST assignment")
    if test_record.get("role") != "TEST" or test_record.get("controller_assigned_role") != "TEST":
        reasons.append("assigned role is not TEST")
    if not str(test_record.get("execution_id", "")).startswith("ITDD-TEST-"):
        reasons.append("execution identity is not a controller TEST execution")
    if test_record.get("terminal_state") != "PASS" or test_record.get("returncode") != 0:
        reasons.append("TEST did not terminate successfully")
    if not test_record.get("candidate_unchanged") or not test_record.get("candidate_git_clean"):
        reasons.append("candidate was mutated or is not clean")
    for snapshot_name in ("candidate_git_before", "candidate_git_after"):
        snapshot = test_record.get(snapshot_name)
        if not isinstance(snapshot, dict) or not snapshot.get("clean"):
            reasons.append(f"{snapshot_name} is missing or dirty")
        elif any(snapshot.get(key) != identity[key] for key in ("candidate_commit_sha", "candidate_tree_sha")):
            reasons.append(f"{snapshot_name} does not match controller identity")
    for key, expected in identity.items():
        if key in {"baseline_sha", "candidate_commit_sha", "candidate_tree_sha"} and test_record.get(key) != expected:
            reasons.append(f"{key} does not match controller identity")
    if assignment and any(assignment.get(key) != identity[key] for key in ("baseline_sha", "candidate_commit_sha", "candidate_tree_sha")):
        reasons.append("controller assignment does not match controller identity")
    if not reported_pass(test_record, "TEST", identity):
        reasons.append("TEST evidence is not a controller-bound PASS")
    return {"allowed": not reasons, "assigned_role": "TEST", "claimed_role": test_record.get("role"), "execution_id": test_record.get("execution_id"), "candidate_commit_sha": identity["candidate_commit_sha"], "candidate_tree_sha": identity["candidate_tree_sha"], "reasons": reasons}


def make_candidate_read_only(candidate: Path) -> None:
    for item in sorted(candidate.rglob("*"), reverse=True):
        try:
            item.chmod(item.stat().st_mode & ~0o222)
        except OSError:
            pass
    candidate.chmod(candidate.stat().st_mode & ~0o222)


def clone_at(source: Path, destination: Path, revision: str) -> None:
    """Create an isolated clone without mutating the source repository metadata."""
    subprocess.run(["git", "clone", "--no-local", str(source), str(destination)], check=True, capture_output=True, text=True)
    git(destination, "checkout", "--detach", revision)


def harmless_isolation_proof() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="itdd-orchestration-proof-") as raw:
        root = Path(raw)
        candidate = root / "candidate"
        candidate.mkdir()
        (candidate / "sentinel.txt").write_text("immutable\n", encoding="utf-8")
        (candidate / "sentinel.txt").chmod(0o444)
        candidate.chmod(0o555)
        scratch = root / "test-tmp"
        scratch.mkdir()
        proof_code = ("import json, os, pathlib, tempfile; "
                      "p=pathlib.Path(os.environ['ITDD_CANDIDATE']) / 'sentinel.txt'; "
                      "created=tempfile.NamedTemporaryFile(dir=os.environ['TMPDIR'], delete=False); created.write(b'pytest-temp'); created.close(); "
                      "rejected=False; "
                      "\ntry: p.write_text('must-not-write'); "
                      "\nexcept OSError: rejected=True; "
                      "pathlib.Path(os.environ['ITDD_OUTPUT']).write_text(json.dumps({'temp_created': pathlib.Path(created.name).exists(), 'candidate_write_rejected': rejected}));")
        output = scratch / "proof.json"
        before = tree_digest(candidate)
        env = os.environ.copy()
        env.update({"ITDD_CANDIDATE": str(candidate), "ITDD_OUTPUT": str(output), "TMPDIR": str(scratch)})
        result = subprocess.run([sys.executable, "-c", proof_code], env=env, check=False)
        local_result = json.loads(output.read_text()) if output.exists() else {}
        unchanged = tree_digest(candidate) == before
        return {"returncode": result.returncode, "candidate_unchanged": unchanged, "sentinel": (candidate / "sentinel.txt").read_text(encoding="utf-8"), "scratch_files": sorted(p.name for p in scratch.iterdir()), "local_result": local_result, "proof_passed": result.returncode == 0 and unchanged and local_result == {"candidate_write_rejected": True, "temp_created": True}}


def accept() -> dict[str, object]:
    baseline = git(ROOT, "rev-parse", "HEAD")
    evidence = ROOT / "work" / "proofs" / f"itdd-runtime-roles-acceptance-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = evidence / "scratch"
    scratch.mkdir()
    (evidence / "previous-failure-preserved.md").write_text("# Preserved prior acceptance failure\n\nThe prior CODEX-RUNTIME-ROLES-V1 finalization remains FAIL and is immutable. Its execution records are preserved under the earlier acceptance directory; this repair never edits or reuses them.\n", encoding="utf-8")
    build_dir = evidence / "build-candidate"
    clone_at(ROOT, build_dir, baseline)
    build_prompt = f"""You are a fresh BUILD execution for the bounded repair: TEST execution hang handling in itdd-execute.
Work only in {build_dir}. Implement only tools/itdd_execute.py and tests/test_itdd_execute_orchestration.py.
Preserve the existing candidate commit/tree binding, candidate protection, and verification semantics. Repair only TEST process lifecycle: record launch timestamp, execution ID, PID, stdout/stderr, periodic heartbeat, configurable non-tiny timeout, and deterministic PASS/FAIL/INTERRUPTED/TIMEOUT terminal states. On timeout or interruption terminate cleanly, force-kill only if needed, preserve evidence, leave candidate unchanged, and prevent VERIFY. The positive test command must execute from the candidate checkout with PYTHONPATH set to that checkout while --basetemp points into writable scratch. Git commit/tree remain authoritative; any content digest remains secondary. Preserve the prior failed finalization; do not modify prior evidence, create a tag, or begin black-box work.
Run implementation-local checks. Do not commit, certify, promote, or act as TEST/VERIFY. Report exact changed paths and commands."""
    build = invoke(role="BUILD", candidate=build_dir, prompt=build_prompt, scratch=scratch / "build", writable=True)
    if build["returncode"] != 0 or not build["output_exists"]:
        result = {"status": "FAIL", "failed_at": "BUILD", "baseline_sha": baseline, "build": build, "evidence": str(evidence)}
        (evidence / "acceptance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    try:
        identity = create_controller_candidate(build_dir, baseline, str(build["execution_id"]))
    except Exception as exc:
        result = {"status": "FAIL", "failed_at": "CANDIDATE_CREATION", "baseline_sha": baseline, "build": build, "error": str(exc), "evidence": str(evidence)}
        (evidence / "acceptance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    (evidence / "candidate.json").write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    test_dir = evidence / "test-candidate"
    verify_dir = evidence / "verify-candidate"
    for checkout in (test_dir, verify_dir):
        clone_at(build_dir, checkout, identity["candidate_commit_sha"])
    test_command = f"cd {test_dir} && PYTHONPATH={test_dir} PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_itdd_execute_orchestration.py -p no:cacheprovider --basetemp=$TMPDIR/pytest"
    test_prompt = f"""You are a fresh TEST execution. Work read-only in exact candidate checkout {test_dir}; scratch is {scratch / 'test'}.
The controller-bound identity is baseline_sha={identity['baseline_sha']}, candidate_commit_sha={identity['candidate_commit_sha']}, candidate_tree_sha={identity['candidate_tree_sha']}. Resolve all three with Git yourself before testing. Run {test_command}. Execute real hostile probes for different candidate, tree mismatch, baseline mismatch, missing/ambiguous digest, stale evidence, candidate write/commit, and fake/placeholder acceptance evidence. Prove candidate SHA/tree before and after are unchanged, scratch remains writable, and rejected operations do not advance authoritative state. Return JSON status PASS/FAIL with fields baseline_sha, candidate_commit_sha, candidate_tree_sha, exact_test_command, hostile_probes, and candidate_immutability. Do not edit candidate, evidence, or act as VERIFY."""
    test = invoke(role="TEST", candidate=test_dir, prompt=test_prompt, scratch=scratch / "test", writable=False, identity=identity, required_test_command=test_command, primary=scratch / "test", additional=test_dir)
    test_gate = verify_gate_decision(test, identity)
    if test["returncode"] != 0 or not test["output_exists"] or not test_gate["allowed"]:
        result = {"status": "FAIL", "failed_at": "TEST", "baseline_sha": baseline, "candidate": identity, "build": build, "test": test, "test_gate": test_gate, "evidence": str(evidence)}
        (evidence / "acceptance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    verify_prompt = f"""You are the fresh independent VERIFY execution. Inspect read-only candidate checkout {verify_dir} and TEST raw evidence {test['output_file']}.
Independently resolve Git baseline_sha={identity['baseline_sha']}, candidate_commit_sha={identity['candidate_commit_sha']}, candidate_tree_sha={identity['candidate_tree_sha']}; do not trust acceptance JSON. Prove the commit exists, tree matches, TEST used that exact commit/tree, BUILD points to it, and SHA/tree are unchanged before/after VERIFY. Re-run critical positive and hostile checks with {test_command}. Challenge mismatched candidate/tree/baseline, ambiguous digest substitution, stale evidence, candidate mutation, and role spoofing. Return JSON status PASS/FAIL with an independently_observed_candidate object containing all three Git identities, hostile_probes, and candidate_immutability. Do not modify source or candidate state and do not repair."""
    verify = invoke(role="VERIFY", candidate=verify_dir, prompt=verify_prompt, scratch=scratch / "verify", writable=False, identity=identity, primary=scratch / "verify", additional=verify_dir)
    status = "PASS" if verify["returncode"] == 0 and verify["output_exists"] and verify["candidate_unchanged"] and verify["candidate_git_clean"] and reported_pass(verify, "VERIFY", identity) else "FAIL"
    result = {"status": status, "baseline_sha": baseline, "candidate": identity, "build": build, "test": test, "verify": verify, "evidence": str(evidence), "previous_failure_preserved": True}
    (evidence / "acceptance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", action="store_true")
    parser.add_argument("--accept", action="store_true")
    args = parser.parse_args()
    result = harmless_isolation_proof() if args.proof else accept() if args.accept else {"error": "choose --proof or --accept"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("proof_passed", result.get("status") == "PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

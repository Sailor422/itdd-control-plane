import subprocess
from pathlib import Path

import pytest

from control.operational import OperationalController, OperationalError
from tests.end_to_end.test_operational_single_eu import init_project


def prepared(root: Path):
    timestamp = init_project(root)
    controller = OperationalController(root)
    graph = {"graph_id":"G-001","version":1,"project_id":"demo","intent_id":"I-001","intent_version":1,"status":"ACTIVE","created_at":timestamp,"created_by":"planner","nodes":[{"eu_id":"EU-001","requirement_ids":["REQ-001"]}],"edges":[],"reason":"one vertical EU","source_event_id":"graph-created","schema_version":1}
    controller.propose_plan(operation_id="OP-001", project_id="demo", graph=graph, eu_paths={"EU-001":["src/feature.py"]}, timestamp=timestamp, event_prefix="op")
    baseline = controller.git.head(root)
    return controller, timestamp, baseline


def provenance(execution_id, packet, capability):
    return {"runtime":"test-builder", "execution_id":execution_id,
            "context_packet_id":packet["context_packet_id"], "capability_id":capability["capability_id"]}


class UnauthorizedBuilder:
    def run(self, *, project_root, worktree, execution_id, context_packet, capability):
        (worktree / "src").mkdir(exist_ok=True)
        (worktree / "src/feature.py").write_text("VALUE = 42\n")
        (worktree / "unauthorized.txt").write_text("no\n")
        return {"runtime_provenance": provenance(execution_id, context_packet, capability)}


class DirectCommitBuilder:
    def run(self, *, project_root, worktree, execution_id, context_packet, capability):
        (worktree / "src").mkdir(exist_ok=True)
        (worktree / "src/feature.py").write_text("VALUE = 42\n")
        subprocess.run(["git", "add", "src/feature.py"], cwd=worktree, check=True)
        subprocess.run(["git", "-c", "user.name=Builder", "-c", "user.email=builder@example.invalid", "commit", "-m", "builder-direct"], cwd=worktree, check=True, capture_output=True)
        return {"runtime_provenance": provenance(execution_id, context_packet, capability)}


class UnrelatedBuilder:
    def run(self, *, project_root, worktree, execution_id, context_packet, capability):
        (worktree / "src").mkdir(exist_ok=True)
        (worktree / "src/feature.py").write_text("VALUE = 42\n")
        (worktree / "README.unrelated").write_text("no\n")
        return {"runtime_provenance": provenance(execution_id, context_packet, capability)}


class EscapeBuilder:
    def run(self, *, project_root, worktree, execution_id, context_packet, capability):
        (worktree / "src").mkdir(exist_ok=True)
        (worktree / "src/feature.py").symlink_to(project_root / "outside.py")
        return {"runtime_provenance": provenance(execution_id, context_packet, capability)}


class InterruptedBuilder:
    def run(self, **kwargs):
        raise OperationalError("Codex Builder timed out")


@pytest.mark.parametrize("builder", [UnauthorizedBuilder(), DirectCommitBuilder(), UnrelatedBuilder(), EscapeBuilder()])
def test_invalid_builder_changes_never_create_candidate(tmp_path: Path, builder):
    controller, timestamp, baseline = prepared(tmp_path)
    (tmp_path / "outside.py").write_text("outside\n")
    with pytest.raises(OperationalError):
        controller.run_eu("OP-001", eu_id="EU-001", builder=builder,
                          spec_command="true", standards_command="true",
                          timestamp=timestamp, event_prefix="op")
    assert controller.git.head(tmp_path) == baseline
    item = controller.operations.read("OP-001")
    assert item["status"] == "BUILD_FAILED"
    assert not item.get("candidate_sha")


def test_interrupted_builder_has_no_candidate_commit(tmp_path: Path):
    controller, timestamp, baseline = prepared(tmp_path)
    result = controller.run_eu("OP-001", eu_id="EU-001", builder=InterruptedBuilder(),
                               spec_command="true", standards_command="true",
                               timestamp=timestamp, event_prefix="op")
    assert result["status"] == "BUILD_FAILED"
    assert controller.git.head(tmp_path) == baseline


def test_invalid_builder_provenance_has_no_candidate_commit(tmp_path: Path):
    controller, timestamp, baseline = prepared(tmp_path)

    class MissingProvenance:
        def run(self, *, worktree, **kwargs):
            (worktree / "src").mkdir(exist_ok=True)
            (worktree / "src/feature.py").write_text("VALUE = 42\n")
            return {}

    with pytest.raises(OperationalError, match="provenance"):
        controller.run_eu("OP-001", eu_id="EU-001", builder=MissingProvenance(),
                          spec_command="true", standards_command="true",
                          timestamp=timestamp, event_prefix="op")
    assert controller.git.head(tmp_path) == baseline

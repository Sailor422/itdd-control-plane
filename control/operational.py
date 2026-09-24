"""Controller-owned single-EU operational lifecycle.

This module is deliberately an orchestration layer over the accepted Stage B-E7
primitives.  It does not create a second authority model: every durable step is
recorded in the existing event log and every worker receives an existing
capability/context binding.
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import shlex
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Protocol

from control.authorization import CapabilityIssuer
from control.context import ContextCompiler
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json
from control.git import CandidateAttestationStore, GitAdapter, GitError
from control.human import HumanGateController
from control.models.store import StageCStore
from control.verifier import SubprocessVerifierAdapter, VerifierOrchestrator


class OperationalError(ValueError):
    """Raised when the controller cannot legally advance the lifecycle."""


class BuilderAdapter(Protocol):
    def run(
        self, *, project_root: Path, worktree: Path, execution_id: str,
        context_packet: dict[str, Any], capability: dict[str, Any]
    ) -> dict[str, Any]: ...


class SubprocessBuilderAdapter:
    """Run a real builder command in the controller-created worktree.

    The command must leave authorized filesystem changes in the worktree.  It may use the
    ITDD_* environment variables as a narrow, non-authoritative handoff.
    """

    def __init__(self, command: str, *, timeout_seconds: int = 900) -> None:
        self.command = command
        self.timeout_seconds = timeout_seconds

    def run(self, *, project_root: Path, worktree: Path, execution_id: str,
            context_packet: dict[str, Any], capability: dict[str, Any]) -> dict[str, Any]:
        env = os.environ.copy()
        env.update({
            "ITDD_PROJECT_ROOT": str(project_root),
            "ITDD_WORKTREE": str(worktree),
            "ITDD_EXECUTION_ID": execution_id,
            "ITDD_CONTEXT_PACKET_ID": context_packet["context_packet_id"],
            "ITDD_CAPABILITY_ID": capability["capability_id"],
        })
        try:
            result = subprocess.run(
                shlex.split(self.command), cwd=worktree, env=env,
                capture_output=True, text=True, timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise OperationalError(f"builder timed out: {execution_id}") from exc
        if result.returncode:
            raise OperationalError((result.stderr or result.stdout).strip() or "builder failed")
        return {"candidate_commit": None, "stdout": result.stdout, "stderr": result.stderr,
                "runtime_provenance": {"runtime": "subprocess", "execution_id": execution_id,
                                        "command": self.command, "exit_code": result.returncode}}


class CodexBuilderAdapter:
    """Launch one fresh, non-interactive Codex worker for a Builder execution.

    The controller supplies the only task context in the prompt.  The worker
    is started in the controller-created worktree and must only modify its changes;
    the controller still independently attests the resulting Git object.
    """

    def __init__(self, *, model: str | None = None, timeout_seconds: int = 1800,
                 codex_binary: str = "codex") -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.codex_binary = codex_binary

    @staticmethod
    def _prompt(context_packet: dict[str, Any], capability: dict[str, Any]) -> str:
        return (
            "You are an ITDD Builder worker. Perform only the software work described "
            "by this controller-supplied context. Work only in the current Git worktree. "
            "Read and write only the listed capability paths. Do not inspect parent "
            "directories, other repositories, Codex configuration, or hidden knowledge. "
            "Run the supplied checks when useful, then stop after leaving the implementation "
            "in the worktree. Do not create a Git commit. Do not change ITDD state, approve anything, promote, "
            "launch another role, or claim verification.\n\n"
            f"CONTEXT_PACKET_JSON:\n{json.dumps(context_packet, sort_keys=True)}\n\n"
            f"CAPABILITY_ENVELOPE_JSON:\n{json.dumps(capability, sort_keys=True)}\n"
        )

    def run(self, *, project_root: Path, worktree: Path, execution_id: str,
            context_packet: dict[str, Any], capability: dict[str, Any]) -> dict[str, Any]:
        command = [self.codex_binary, "exec", "--json", "--ephemeral",
                   "--ignore-user-config", "--sandbox", "workspace-write",
                   "--cd", str(worktree)]
        if self.model:
            command.extend(["--model", self.model])
        command.append(self._prompt(context_packet, capability))
        try:
            result = subprocess.run(command, cwd=worktree, stdin=subprocess.DEVNULL, capture_output=True,
                                    text=True, timeout=self.timeout_seconds,
                                    check=False)
        except subprocess.TimeoutExpired as exc:
            raise OperationalError(f"Codex Builder timed out: {execution_id}") from exc
        if result.returncode:
            raise OperationalError(
                f"Codex Builder failed ({execution_id}): "
                f"{(result.stderr or result.stdout).strip() or 'no diagnostic'}"
            )
        events: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                events.append(item)
        thread_id = next((item.get("thread_id") for item in events
                          if item.get("type") == "thread.started"), None)
        return {
            "candidate_commit": None,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "runtime_provenance": {
                "runtime": "codex",
                "execution_id": execution_id,
                "thread_id": thread_id,
                "command": command[:-1] + ["<controller-supplied-prompt>"],
                "exit_code": result.returncode,
                "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
                "event_count": len(events),
            },
        }


class PrimeBuilderAdapter:
    """Launch one fresh, non-interactive Prime Agent worker.

    Prime is treated as an untrusted implementation worker.  The controller
    owns the worktree and all lifecycle authority; the worker receives only
    the serialized context and capability envelope in its user prompt.
    """

    def __init__(self, *, model: str | None = None, timeout_seconds: int = 1800,
                 prime_binary: str = "prime-agent") -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.prime_binary = prime_binary

    @staticmethod
    def _prompt(context_packet: dict[str, Any], capability: dict[str, Any]) -> str:
        # Keep these delimiters unambiguous so a packet value cannot become an
        # instruction outside the controller-supplied data sections.
        return (
            "You are an ITDD Builder worker running under controller supervision. "
            "Perform only the software work in the controller-supplied context. "
            "Work only in the current Git worktree and only within capability paths. "
            "Do not inspect parent directories, other repositories, or ambient project "
            "configuration. Do not create commits or alter ITDD authority state. "
            "You have no authority to approve, promote, commit, launch roles, or claim "
            "verification. Leave implementation changes in the worktree and stop.\n\n"
            "--- BEGIN CONTROLLER CONTEXT PACKET (JSON) ---\n"
            f"{json.dumps(context_packet, sort_keys=True)}\n"
            "--- END CONTROLLER CONTEXT PACKET (JSON) ---\n\n"
            "--- BEGIN CONTROLLER CAPABILITY ENVELOPE (JSON) ---\n"
            f"{json.dumps(capability, sort_keys=True)}\n"
            "--- END CONTROLLER CAPABILITY ENVELOPE (JSON) ---\n"
        )

    def run(self, *, project_root: Path, worktree: Path, execution_id: str,
            context_packet: dict[str, Any], capability: dict[str, Any]) -> dict[str, Any]:
        prompt = self._prompt(context_packet, capability)
        command = [
            self.prime_binary, "--print", "--mode", "json", "--cwd", str(worktree),
            "--offline", "--no-session", "--no-context-files", "--no-skills",
            "--no-extensions", "--no-prompt-templates", "--no-themes",
        ]
        if self.model:
            command.extend(["--model", self.model])
        command.extend(["--", prompt])
        try:
            result = subprocess.run(
                command, cwd=worktree, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise OperationalError(f"Prime Builder timed out: {execution_id}") from exc
        except OSError as exc:
            raise OperationalError(f"Prime Builder could not start ({execution_id})") from exc
        if result.returncode:
            diagnostic = (result.stderr or result.stdout).strip() or "no diagnostic"
            raise OperationalError(f"Prime Builder failed ({execution_id}): {diagnostic}")
        return {
            "candidate_commit": None,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "runtime_provenance": {
                "runtime": "prime-agent",
                "execution_id": execution_id,
                "command": command[:-1] + ["<controller-supplied-prompt>"],
                "exit_code": result.returncode,
                "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            },
        }


class _WorktreeVerifierAdapter:
    def __init__(self, worktree: Path, *, timeout_seconds: int = 30) -> None:
        self.worktree = worktree
        self.adapter = SubprocessVerifierAdapter(timeout_seconds=timeout_seconds)

    def run(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["project_root"] = self.worktree
        return self.adapter.run(**kwargs)


class OperationalStore:
    """Materialized operational state reconstructed from append-only events."""

    EVENT_TYPES = {
        "plan.proposed", "graph.evaluated", "eu.building", "eu.built",
        "eu.verification_failed", "eu.build_failed", "eu.verified", "promotion.completed",
        "worker.execution.completed", "eu.abandoned", "eu.recovery_ready",
    }

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.events = EventLog(self.root)

    def path(self, operation_id: str) -> Path:
        return self.root / ".idd/operations" / f"{operation_id}.json"

    def read(self, operation_id: str) -> dict[str, Any]:
        path = self.path(operation_id)
        if not path.exists():
            raise OperationalError(f"operation does not exist: {operation_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def reconstruct(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for event in self.events.verify():
            if event["event_type"] in self.EVENT_TYPES:
                item = event["payload"]["operation"]
                result[item["operation_id"]] = item
        return result

    def write(self, item: dict[str, Any], *, event_id: str, event_type: str,
              timestamp: str, actor_type: str = "controller",
              actor_id: str = "controller") -> dict[str, Any]:
        if event_type not in self.EVENT_TYPES:
            raise OperationalError("unsupported operational event")
        path = self.path(item["operation_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(item) + "\n", encoding="utf-8")
        event = self.events.new_event(
            event_id=event_id, event_type=event_type, timestamp=timestamp,
            project_id=item["project_id"], actor_type=actor_type,
            actor_id=actor_id, execution_id=item.get("execution_id"),
            payload={"operation": item},
        )
        self.events.append(event)
        return item

    def verify_materialized(self) -> None:
        for operation_id, item in self.reconstruct().items():
            if self.read(operation_id) != item:
                raise EventLogIntegrityError("operational state diverges from event history")

    def write_recovery(self, item: dict[str, Any], *, event_id: str, event_type: str,
                       timestamp: str, actor_id: str) -> dict[str, Any]:
        """Append recovery authority before updating its materialized projection."""
        existing = next((event for event in self.events.verify()
                         if event["event_id"] == event_id), None)
        if existing is not None:
            if existing["event_type"] != event_type or existing["payload"].get("operation") != item:
                raise OperationalError("recovery event identity is bound to different state")
        else:
            event = self.events.new_event(
                event_id=event_id, event_type=event_type, timestamp=timestamp,
                project_id=item["project_id"], actor_type="human", actor_id=actor_id,
                execution_id=item.get("execution_id"), payload={"operation": item},
            )
            self.events.append(event)
        path = self.path(item["operation_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(item) + "\n", encoding="utf-8")
        return item


class OperationalController:
    """The minimum controller-owned path from approved intent to promotion."""

    def __init__(self, project_root: str | Path,
                 *, controller_execution_id: str = "EXEC-CONTROLLER-001") -> None:
        self.root = Path(project_root).resolve()
        self.execution_id = controller_execution_id
        self.git = GitAdapter(self.root)
        self.stage_c = StageCStore(self.root)
        self.operations = OperationalStore(self.root)
        self.capabilities = CapabilityIssuer(self.root)
        self.compiler = ContextCompiler(self.root)
        self.verifiers = VerifierOrchestrator(self.root, controller_execution_id=controller_execution_id)
        self.human = HumanGateController(self.root, controller_execution_id=controller_execution_id)
        self.attestations = CandidateAttestationStore(self.root)

    def recover_building_run(self, *, operation_id: str, eu_id: str, recovery_id: str,
                             old_execution_id: str, fresh_execution_id: str,
                             workspace: str | Path, confirm_worker_stopped: bool,
                             timestamp: str) -> dict[str, Any]:
        """Recover an explicitly confirmed stranded Builder execution."""
        if not confirm_worker_stopped:
            raise OperationalError("worker STOPPED confirmation is required")
        from getpass import getuser
        records = self.operations.events.verify()
        reconstructed = self.operations.reconstruct()
        item = self.operations.read(operation_id)
        durable = reconstructed.get(operation_id)
        if durable is not None and item != durable:
            if durable.get("recovery_id") != recovery_id or durable.get("status") not in {"ABANDONED", "READY"}:
                raise EventLogIntegrityError("operational state diverges from event history")
            path = self.operations.path(operation_id)
            path.write_text(canonical_json(durable) + "\n", encoding="utf-8")
            item = durable
        self.operations.verify_materialized()
        if not re.fullmatch(r"REC-[A-Za-z0-9._-]+", recovery_id):
            raise OperationalError("invalid recovery identity")
        if not re.fullmatch(r"EXEC-[A-Za-z0-9._-]+", old_execution_id) or not re.fullmatch(r"EXEC-[A-Za-z0-9._-]+", fresh_execution_id) or old_execution_id == fresh_execution_id:
            raise OperationalError("invalid recovery execution identities")
        binding_path = self.root / ".idd/recoveries" / f"{recovery_id}.json"
        known_event_ids = {event["event_id"] for event in records}
        expected_ids = {f"{recovery_id}-abandoned", f"{recovery_id}-ready"}
        stale_capability = item.get("builder_capability_id")
        if stale_capability and not any(e["event_type"] == "capability.revoked" and e["payload"].get("capability_id") == stale_capability for e in records):
            expected_ids.add(f"{recovery_id}-revoke")
        if not binding_path.exists() and known_event_ids.intersection(expected_ids):
            raise OperationalError("recovery event identity is already in use")
        path = Path(workspace)
        root = (self.root / ".idd/build_workspaces").resolve()
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise OperationalError("workspace is outside disposable root")
        binding = {"recovery_id": recovery_id, "operation_id": operation_id, "eu_id": eu_id,
                   "old_execution_id": old_execution_id, "fresh_execution_id": fresh_execution_id,
                   "workspace": str(path.resolve()), "actor": getuser()}
        if item.get("status") == "READY" and item.get("recovery_id") == recovery_id and item.get("recovered_from_execution_id") == old_execution_id and item.get("execution_id") == fresh_execution_id:
            if binding_path.exists() and json.loads(binding_path.read_text()) == binding:
                return item
            raise OperationalError("recovery ID binding mismatch")
        if item.get("status") not in {"BUILDING", "ABANDONED"}:
            raise OperationalError("only a BUILDING operation can be recovered")
        if item.get("status") == "BUILDING" and (item.get("execution_id") != old_execution_id or eu_id not in item.get("eu_paths", {})):
            raise OperationalError("recovery identity does not match BUILDING operation")
        if item.get("status") == "ABANDONED" and (
            item.get("recovery_id") != recovery_id
            or item.get("abandoned_execution_id") != old_execution_id
            or item.get("execution_id") != old_execution_id
        ):
            raise OperationalError("recovery identity does not match abandoned operation")
        quarantine_root = self.root / ".idd/quarantine"
        quarantined = quarantine_root / recovery_id
        if binding_path.exists():
            if json.loads(binding_path.read_text()) != binding:
                raise OperationalError("recovery ID is bound to a different request")
            if item.get("status") == "BUILDING" and path.exists() and quarantined.exists():
                raise OperationalError("both source workspace and quarantine exist; refusing uncertain data")
        else:
            if item.get("status") != "BUILDING" or not path.exists():
                raise OperationalError("recovery workspace is missing")
            if quarantined.exists():
                raise OperationalError("quarantine destination already exists; refusing uncertain data")
            binding_path.parent.mkdir(parents=True, exist_ok=True)
            binding_path.write_text(canonical_json(binding) + "\n", encoding="utf-8")
        quarantine_root.mkdir(parents=True, exist_ok=True)
        if item.get("status") == "BUILDING":
            if path.exists() and not quarantined.exists(): path.rename(quarantined)
            elif not quarantined.exists(): raise OperationalError("workspace and quarantine are missing")
        # Capability revocation is durable and consumed by the public authorizer.
        stale_capability = item.get("builder_capability_id")
        if stale_capability and not any(e["event_type"] == "capability.revoked" and e["payload"].get("capability_id") == stale_capability for e in records):
            revocation = self.operations.events.new_event(event_id=f"{recovery_id}-revoke", event_type="capability.revoked", timestamp=timestamp, project_id=item["project_id"], actor_type="human", actor_id=getuser(), execution_id=old_execution_id, payload={"capability_id":stale_capability, "recovery_id":recovery_id})
            self.operations.events.append(revocation)

        abandoned = deepcopy(item)
        if item.get("status") == "BUILDING":
            abandoned.update({"status":"ABANDONED", "abandoned_execution_id":old_execution_id,
                              "recovery_id":recovery_id, "worktree":str(quarantined)})
            self.operations.write_recovery(abandoned, event_id=f"{recovery_id}-abandoned",
                                           event_type="eu.abandoned", timestamp=timestamp,
                                           actor_id=getuser())
        ready = deepcopy(abandoned)
        ready.update({"status":"READY", "execution_id":fresh_execution_id,
                      "worktree":None, "recovered_from_execution_id":old_execution_id})
        return self.operations.write_recovery(ready, event_id=f"{recovery_id}-ready",
                                              event_type="eu.recovery_ready", timestamp=timestamp,
                                              actor_id=getuser())

    def propose_plan(self, *, operation_id: str, project_id: str, graph: dict[str, Any],
                     eu_paths: dict[str, list[str]], timestamp: str,
                     event_prefix: str) -> dict[str, Any]:
        state = self.stage_c.reconstruct()
        intent = state.get("approved_intent")
        if not intent or intent["project_id"] != project_id:
            raise OperationalError("an approved intent for this project is required")
        if graph["project_id"] != project_id or graph["intent_id"] != intent["intent_id"]:
            raise OperationalError("plan is bound to the wrong intent")
        if set(eu_paths) != {node["eu_id"] for node in graph["nodes"]}:
            raise OperationalError("every EU must have an explicit path scope")
        if any(not paths for paths in eu_paths.values()):
            raise OperationalError("an EU cannot have an empty path scope")
        if graph["version"] == 1:
            self.stage_c.create_graph(
                graph, event_id=graph["source_event_id"], timestamp=timestamp,
                actor_type="agent", actor_id="planner",
            )
        else:
            self.stage_c.revise_graph(
                graph, event_id=graph["source_event_id"], timestamp=timestamp,
                actor_type="agent", actor_id="planner",
            )
        item = {
            "operation_id": operation_id, "schema_version": 1,
            "project_id": project_id, "intent_id": intent["intent_id"],
            "intent_version": intent["version"], "graph_id": graph["graph_id"],
            "graph_version": graph["version"], "eu_paths": deepcopy(eu_paths),
            "status": "PLANNER_PROPOSED", "execution_id": self.execution_id,
            "candidate_sha": None, "gate_id": None, "branch": None,
            "worktree": None, "created_at": timestamp,
        }
        item = self.operations.write(item, event_id=f"{event_prefix}-proposed",
                                    event_type="plan.proposed", timestamp=timestamp)
        evaluator_number = self._number(operation_id) * 100 + 1
        evaluator_execution_id = f"EXEC-GRAPH-EVALUATOR-{evaluator_number:06d}"
        evaluator_capability = self.capabilities.issue({
            "capability_id":f"CAP-{evaluator_number:03d}", "schema_version":1,
            "project_id":project_id, "role":"GRAPH_EVALUATOR", "execution_id":evaluator_execution_id,
            "issued_at":timestamp, "baseline_sha":self.git.head(self.root),
            "allowed_reads":[f".idd/intent/{intent['intent_id']}/v{intent['version']}.json", f".idd/graph/{graph['graph_id']}/v{graph['version']}.json"],
            "allowed_writes":[], "allowed_executes":[], "allowed_operations":["READ", "CREATE_ARTIFACT"],
            "forbidden_operations":["WRITE", "PROMOTE", "HUMAN_GATE_APPROVAL"], "allowed_request_types":[],
            "scope_bindings":{"intent_id":intent["intent_id"], "intent_version":intent["version"], "graph_id":graph["graph_id"], "graph_version":graph["version"], "eu_id":"GRAPH"},
            "version":1, "issued_by":"controller",
        }, event_id=f"{event_prefix}-graph-evaluator-cap", timestamp=timestamp)
        packet = self.compiler.compile({
            "context_packet_id":f"CP-{evaluator_number:03d}",
            "intent_binding":{"intent_id":intent["intent_id"], "intent_version":intent["version"]},
            "graph_binding":{"graph_id":graph["graph_id"], "graph_version":graph["version"]},
            "eu_binding":{"eu_id":"GRAPH"},
            "authority_context":{"allowed_operations":["READ", "CREATE_ARTIFACT"], "acceptance_requirements":["valid graph bindings"]},
            "working_context":[], "knowledge_context":[], "evidence_context":[], "context_budget":{"max_bytes":100000},
        }, capability_id=evaluator_capability["capability_id"],
            state={"project_root":str(self.root), "project_id":project_id, "execution_id":evaluator_execution_id,
                   "baseline_sha":evaluator_capability["baseline_sha"], "role":"GRAPH_EVALUATOR"},
            event_id=f"{event_prefix}-graph-evaluator-packet", timestamp=timestamp)
        if graph["status"] != "ACTIVE" or not graph["nodes"] or any(not node["requirement_ids"] for node in graph["nodes"]):
            raise OperationalError("Graph Evaluator rejected invalid graph")
        item = deepcopy(item); item.update({"status":"ACTIVE", "planner_execution_id":f"EXEC-PLANNER-{self._number(operation_id):06d}",
                                            "graph_evaluator_execution_id":evaluator_execution_id,
                                            "graph_evaluator_capability_id":evaluator_capability["capability_id"],
                                            "graph_evaluator_context_packet_id":packet["context_packet_id"],
                                            "graph_evaluator_context_packet_hash":packet["packet_hash"],
                                            "graph_evaluator_result":"PASS"})
        return self.operations.write(item, event_id=f"{event_prefix}-graph-evaluated",
                                    event_type="graph.evaluated", timestamp=timestamp)

    @staticmethod
    def _number(value: str) -> int:
        return int(re.sub(r"\D", "", value) or "1")

    def _status_paths(self, worktree: Path) -> list[str]:
        raw = self.git.run("status", "--porcelain=v1", "-z", "--untracked-files=all", cwd=worktree)
        paths: list[str] = []
        for entry in raw.split("\0"):
            if not entry:
                continue
            if len(entry) < 4:
                raise OperationalError("invalid Builder Git status record")
            status, path = entry[:2], entry[3:]
            if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
                raise OperationalError("renames and copies are not valid Builder candidate changes")
            paths.append(path)
        return sorted(set(paths))

    def spawn_eu_operation(self, source_operation_id: str, *, operation_id: str,
                           eu_id: str, timestamp: str, event_prefix: str) -> dict[str, Any]:
        """Create a bounded EU execution record from one accepted multi-EU plan.

        The graph and its independent evaluator result are reused by identity;
        only the execution-unit operation record is split.  No graph artifact,
        approval, candidate, or human decision is created by this method.
        """
        source = self.operations.read(source_operation_id)
        if source.get("status") not in {"ACTIVE", "WAITING_HUMAN_REVIEW"}:
            raise OperationalError("source plan is not eligible for another EU execution")
        if operation_id == source_operation_id or self.operations.path(operation_id).exists():
            raise OperationalError("EU operation identity already exists")
        if eu_id not in source.get("eu_paths", {}):
            raise OperationalError("EU is not in the accepted plan")
        item = {
            "operation_id": operation_id, "schema_version": 1,
            "project_id": source["project_id"], "intent_id": source["intent_id"],
            "intent_version": source["intent_version"], "graph_id": source["graph_id"],
            "graph_version": source["graph_version"], "eu_paths": {eu_id: list(source["eu_paths"][eu_id])},
            "status": "ACTIVE", "execution_id": self.execution_id,
            "candidate_sha": None, "gate_id": None, "branch": None,
            "worktree": None, "created_at": timestamp,
            "planner_execution_id": source.get("planner_execution_id"),
            "graph_evaluator_execution_id": source.get("graph_evaluator_execution_id"),
            "graph_evaluator_capability_id": source.get("graph_evaluator_capability_id"),
            "graph_evaluator_context_packet_id": source.get("graph_evaluator_context_packet_id"),
            "graph_evaluator_context_packet_hash": source.get("graph_evaluator_context_packet_hash"),
            "graph_evaluator_result": source.get("graph_evaluator_result"),
        }
        proposed = self.operations.write(item, event_id=f"{event_prefix}-proposed",
                                         event_type="plan.proposed", timestamp=timestamp)
        return self.operations.write(proposed, event_id=f"{event_prefix}-graph-evaluated",
                                     event_type="graph.evaluated", timestamp=timestamp)

    @staticmethod
    def _validate_builder_provenance(provenance: Any, execution_id: str) -> dict[str, Any]:
        if not isinstance(provenance, dict) or provenance.get("execution_id") != execution_id:
            raise OperationalError("invalid Builder execution provenance")
        if not provenance.get("runtime"):
            raise OperationalError("Builder runtime provenance is missing")
        return deepcopy(provenance)

    def _validate_builder_diff(self, worktree: Path, paths: list[str], allowed: list[str], baseline: str) -> None:
        if self.git.head(worktree) != baseline:
            raise OperationalError("Builder changed the worktree Git commit; commit authority is controller-only")
        worktree_real = worktree.resolve()
        allowed_paths = {Path(item).as_posix() for item in allowed}
        for relative in paths:
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise OperationalError("Builder path escape detected")
            normalized = candidate.as_posix()
            if normalized == ".idd" or normalized.startswith(".idd/"):
                raise OperationalError("Builder cannot modify ITDD authority state")
            if normalized not in allowed_paths:
                raise OperationalError(f"Builder changed unauthorized path: {normalized}")
            target = worktree / candidate
            try:
                target.resolve(strict=False).relative_to(worktree_real)
            except ValueError as exc:
                raise OperationalError(f"Builder symlink/path escape detected: {normalized}") from exc
            if target.is_symlink():
                raise OperationalError(f"Builder symlink/path escape detected: {normalized}")
        if not paths:
            raise OperationalError("Builder produced no candidate filesystem changes")

    def _controller_commit(self, worktree: Path, paths: list[str], *, operation_id: str,
                           execution_id: str) -> dict[str, Any]:
        self.git.run("add", "--", *paths, cwd=worktree)
        self.git.run("-c", "user.name=ITDD Controller", "-c", "user.email=itdd-controller@example.invalid",
                     "commit", "--no-verify", "-m", f"ITDD candidate {operation_id} {execution_id}", cwd=worktree)
        candidate = self.git.head(worktree)
        return {"operation": "controller.git.commit", "execution_id": execution_id,
                "operation_id": operation_id, "paths": paths, "candidate_commit": candidate,
                "candidate_tree": self.git.tree(candidate)}

    def run_eu(self, operation_id: str, *, eu_id: str, builder: BuilderAdapter,
               spec_command: str, standards_command: str, timestamp: str,
               event_prefix: str) -> dict[str, Any]:
        item = self.operations.read(operation_id)
        if item["status"] != "ACTIVE":
            raise OperationalError("an evaluator-accepted graph is required before building")
        if eu_id not in item["eu_paths"]:
            raise OperationalError("EU is not in the approved plan")
        baseline = self.git.head(self.root)
        number = self._number(operation_id) * 10 + self._number(eu_id)
        execution_id = f"EXEC-BUILDER-{number:06d}"
        branch = f"itdd/build/{operation_id}/{eu_id}"
        worktree = self.root / ".idd/build_workspaces" / operation_id / eu_id
        if worktree.exists():
            raise OperationalError("builder worktree already exists")
        self.git.run("worktree", "add", "-b", branch, str(worktree), baseline)
        paths = item["eu_paths"][eu_id]
        intent = self.stage_c.read_intent(item["intent_id"], item["intent_version"])
        graph = self.stage_c.read_graph(item["graph_id"], item["graph_version"])
        requirement_ids = next(node["requirement_ids"] for node in graph["nodes"] if node["eu_id"] == eu_id)
        requirement_text = [req["text"] for req in intent["requirements"] if req["requirement_id"] in requirement_ids]
        capability = self.capabilities.issue({
            "capability_id": f"CAP-{number:03d}", "schema_version": 1,
            "project_id": item["project_id"], "role": "BUILDER",
            "execution_id": execution_id, "issued_at": timestamp,
            "baseline_sha": baseline, "allowed_reads": paths,
            "allowed_writes": paths, "allowed_executes":["git", "python3"],
            "allowed_operations":["READ", "WRITE", "EXECUTE", "CREATE_ARTIFACT"],
            "forbidden_operations":["PROMOTE", "INTENT_APPROVAL", "GRAPH_APPROVAL"],
            "allowed_request_types":["MISSING_RESOURCE", "CLARIFICATION"],
            "scope_bindings":{"intent_id":item["intent_id"], "intent_version":item["intent_version"],
                              "graph_id":item["graph_id"], "graph_version":item["graph_version"], "eu_id":eu_id},
            "version":1, "issued_by":"controller",
        }, event_id=f"{event_prefix}-cap", timestamp=timestamp)
        resources = [{
            "resource_id": f"RES-{number:03d}-{index:02d}", "path": path,
            "purpose": f"approved EU {eu_id} implementation context", "authority":"WRITE",
            "reason_included":"explicit path scope from approved plan", "source":"approved graph",
            "freshness_or_version":baseline,
        } for index, path in enumerate(paths, 1)]
        packet = self.compiler.compile({
            "context_packet_id":f"CP-{number:03d}",
            "intent_binding":{"intent_id":item["intent_id"], "intent_version":item["intent_version"]},
            "graph_binding":{"graph_id":item["graph_id"], "graph_version":item["graph_version"]},
            "eu_binding":{"eu_id":eu_id},
            "authority_context":{"allowed_operations":["READ", "WRITE", "EXECUTE"], "acceptance_requirements":requirement_text},
            "working_context":resources, "knowledge_context":[], "evidence_context":[],
            "context_budget":{"max_bytes":250000},
        }, capability_id=capability["capability_id"],
            state={"project_root":str(self.root), "project_id":item["project_id"],
                   "execution_id":execution_id, "baseline_sha":baseline, "role":"BUILDER"},
            event_id=f"{event_prefix}-packet", timestamp=timestamp)
        item = deepcopy(item); item.update({"status":"BUILDING", "execution_id":execution_id,
                                            "branch":branch, "worktree":str(worktree),
                                            "baseline_sha":baseline})
        self.operations.write(item, event_id=f"{event_prefix}-building",
                              event_type="eu.building", timestamp=timestamp)
        try:
            output = builder.run(project_root=self.root, worktree=worktree,
                                 execution_id=execution_id, context_packet=packet,
                                 capability=capability)
        except OperationalError as exc:
            item = deepcopy(item); item.update({"status":"BUILD_FAILED", "failure_class":"BUILDER_RUNTIME_FAILURE", "failure_detail":str(exc)})
            return self.operations.write(item, event_id=f"{event_prefix}-build-failed",
                                        event_type="eu.build_failed", timestamp=timestamp)
        try:
            provenance = self._validate_builder_provenance(output.get("runtime_provenance"), execution_id)
            changed_paths = self._status_paths(worktree)
            self._validate_builder_diff(worktree, changed_paths, capability["allowed_writes"], baseline)
            commit_operation = self._controller_commit(worktree, changed_paths,
                                                       operation_id=operation_id, execution_id=execution_id)
        except OperationalError as exc:
            failed = deepcopy(item); failed.update({"status":"BUILD_FAILED",
                                                    "failure_class":"BUILDER_CHANGE_REJECTED",
                                                    "failure_detail":str(exc)})
            self.operations.write(failed, event_id=f"{event_prefix}-build-failed",
                                  event_type="eu.build_failed", timestamp=timestamp)
            raise
        item = deepcopy(item); item.update({"builder_runtime_provenance": provenance,
                                            "builder_capability_id": capability["capability_id"],
                                            "builder_context_packet_id": packet["context_packet_id"],
                                            "builder_context_packet_hash": packet["packet_hash"],
                                            "observed_changed_paths": changed_paths,
                                            "controller_commit_operation": commit_operation})
        self.operations.write(item, event_id=f"{event_prefix}-worker-completed",
                              event_type="worker.execution.completed", timestamp=timestamp)
        candidate = commit_operation["candidate_commit"]
        if not self.git.exists(candidate) or not self.git.is_ancestor(baseline, candidate) or candidate == baseline:
            raise OperationalError("builder did not produce a new Git-attested candidate")
        attestation = self.attestations.attest(
            attestation_id=f"AT-{number:03d}", project_id=item["project_id"],
            baseline_commit=baseline, candidate_commit=candidate, created_at=timestamp,
        )
        item.update({"status":"BUILT", "candidate_sha":attestation["candidate_commit"],
                     "attestation_id":attestation["attestation_id"]})
        self.operations.write(item, event_id=f"{event_prefix}-built",
                              event_type="eu.built", timestamp=timestamp)
        verifier = self._verify_axes(item, eu_id, baseline, candidate, paths,
                                     spec_command, standards_command, worktree,
                                     number, timestamp, event_prefix)
        if verifier["status"] != "VERIFIED":
            item["status"] = "VERIFICATION_FAILED"
            self.operations.write(item, event_id=f"{event_prefix}-verification-failed",
                                  event_type="eu.verification_failed", timestamp=timestamp)
            return item
        # Verification is a deterministic lifecycle result.  Routine EU work
        # does not create a HUMAN_ONLY gate or decision document; explicit
        # human authority remains available for amendments, maintenance,
        # break-glass, or genuinely unresolved issues.
        item.update({"status":"VERIFIED", "gate_id":None,
                     "spec_execution_id":verifier["spec_execution_id"],
                     "standards_execution_id":verifier["standards_execution_id"]})
        result = self.operations.write(item, event_id=f"{event_prefix}-verified",
                                       event_type="eu.verified", timestamp=timestamp)
        return result

    def _verify_axes(self, item: dict[str, Any], eu_id: str, baseline: str, candidate: str,
                     paths: list[str], spec_command: str, standards_command: str,
                     worktree: Path, number: int, timestamp: str, prefix: str) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for index, (role, command) in enumerate((("SPEC_VERIFIER", spec_command),
                                                   ("STANDARDS_REVIEWER", standards_command)), 1):
            execution_id = f"EXEC-{role}-{number:06d}"
            cap = {"capability_id":f"CAP-{number + index + 100:03d}", "schema_version":1,
                   "project_id":item["project_id"], "role":role, "execution_id":execution_id,
                   "issued_at":timestamp, "baseline_sha":baseline, "allowed_reads":paths,
                   "allowed_writes":[], "allowed_executes":["python3"],
                   "allowed_operations":["READ", "EXECUTE", "CREATE_ARTIFACT"],
                   "forbidden_operations":["WRITE", "PROMOTE"], "allowed_request_types":[],
                   "scope_bindings":{"intent_id":item["intent_id"], "intent_version":item["intent_version"],
                                     "graph_id":item["graph_id"], "graph_version":item["graph_version"], "eu_id":eu_id},
                   "version":1, "issued_by":"controller"}
            packet = {"context_packet_id":f"CP-{number + index + 100:03d}",
                      "intent_binding":{"intent_id":item["intent_id"], "intent_version":item["intent_version"]},
                      "graph_binding":{"graph_id":item["graph_id"], "graph_version":item["graph_version"]},
                      "eu_binding":{"eu_id":eu_id},
                      "authority_context":{"allowed_operations":["READ", "EXECUTE"], "acceptance_requirements":[eu_id]},
                      "working_context":[{"resource_id":f"RES-{number + index + 100:03d}", "path":path,
                                           "purpose":f"fresh {role.lower()} context", "authority":"READ",
                                           "reason_included":"exact candidate path", "source":"approved graph",
                                           "freshness_or_version":candidate} for path in paths],
                      "knowledge_context":[], "evidence_context":[], "context_budget":{"max_bytes":250000}}
            contract = {"verification_contract_id":f"VC-{number + index + 100:03d}",
                        "project_id":item["project_id"], "role":role, "intent_id":item["intent_id"],
                        "intent_version":item["intent_version"], "graph_id":item["graph_id"],
                        "graph_version":item["graph_version"], "eu_id":eu_id,
                        "baseline_sha":baseline, "candidate_sha":candidate,
                        "context_packet_id":packet["context_packet_id"], "context_packet_hash":"placeholder",
                        "required_checks":[{"check_id":f"REQCHECK-{number + index + 100:03d}", "kind":"TEST_COMMAND",
                                             "command":command, "required_exit_code":0}],
                        "required_artifacts":[], "allowed_changed_paths":self.git.changed_paths(baseline, candidate),
                        "created_at":timestamp, "created_by":"controller"}
            execution = self.verifiers.create_verifier(role=role, execution_id=execution_id,
                                                       capability=cap, packet=packet, contract=contract,
                                                       event_prefix=f"{prefix}-{role.lower()}", timestamp=timestamp)
            result = self.verifiers.launch(execution["execution_id"], adapter=_WorktreeVerifierAdapter(worktree),
                                           event_prefix=f"{prefix}-{role.lower()}-run", timestamp=timestamp)
            if not result["result"] or result["result"]["status"] != "PASS":
                return {"status":"NOT_VERIFIED"}
            results[role] = {"execution_id":execution_id, "result_id":result["result"]["result_id"]}
        return {"status":"VERIFIED", "spec_execution_id":results["SPEC_VERIFIER"]["execution_id"],
                "standards_execution_id":results["STANDARDS_REVIEWER"]["execution_id"],
                "spec_result_id":results["SPEC_VERIFIER"]["result_id"],
                "standards_result_id":results["STANDARDS_REVIEWER"]["result_id"]}

    def promote(self, operation_id: str, *, actor_type: str, actor_id: str,
                timestamp: str, event_prefix: str) -> dict[str, Any]:
        if actor_type != "human":
            raise OperationalError("promotion is human-only")
        item = self.operations.read(operation_id)
        if item["status"] != "WAITING_HUMAN_REVIEW" or not item.get("gate_id"):
            raise OperationalError("only a human-approved verified EU may be promoted")
        gate = self.human.store.read(item["gate_id"])
        if gate["status"] != "APPROVED":
            raise OperationalError("the verified EU human gate is not approved")
        if self.git.head(self.root) != item.get("baseline_sha"):
            raise OperationalError("canonical branch changed; candidate is stale")
        # Durable controller records live in the ignored/project-local authority
        # domain and are expected to change during this lifecycle.  Only a
        # human/source change on the canonical branch makes the candidate stale.
        source_changes = [line for line in self.git.run("status", "--porcelain").splitlines()
                          if line and not line[3:].startswith(".idd/")]
        if source_changes:
            raise OperationalError("canonical project has uncommitted changes")
        self.git.run("merge", "--ff-only", item["candidate_sha"])
        item = deepcopy(item); item["status"] = "PROMOTED"; item["promoted_by"] = actor_id; item["promoted_at"] = timestamp
        return self.operations.write(item, event_id=f"{event_prefix}-promoted",
                                    event_type="promotion.completed", timestamp=timestamp,
                                    actor_type=actor_type, actor_id=actor_id)

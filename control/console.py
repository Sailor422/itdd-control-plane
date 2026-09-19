"""Small terminal human console; presentation delegates authority to controllers."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from control.authority.paths import AuthorityError, resolve_project_root
from control.events import EventLog
from control.human import HumanGateController, HumanGateStore, HumanGateError, HumanViewGenerator
from control.models.store import StageCStore


class ConsoleError(ValueError): pass


def discover_project(start: str | Path) -> Path:
    candidate = Path(start).expanduser().resolve()
    if candidate.is_file(): candidate = candidate.parent
    for root in (candidate, *candidate.parents):
        if (root / ".idd/state/events.jsonl").exists(): return root
    raise ConsoleError("No ITDD project found here; start inside a project with durable ITDD state.")


def _now() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class HumanConsole:
    def __init__(self, project_root: str | Path, *, input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print) -> None:
        self.root = resolve_project_root(project_root); self.input = input_fn; self.output = output_fn; self.stage_c = StageCStore(self.root); self.gates = HumanGateStore(self.root); self.controller = HumanGateController(self.root)

    def state(self) -> dict[str, Any]:
        stage = self.stage_c.reconstruct(); gates = self.gates.reconstruct(); graph = stage.get("active_graph"); intent = stage.get("approved_intent") or (list(stage.get("intents", {}).values())[-1] if stage.get("intents") else None)
        integrations = []
        for path in sorted((self.root / ".idd/integrations").glob("*.json")) if (self.root / ".idd/integrations").exists() else []:
            try: integrations.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError): pass
        waiting = [g for g in gates.values() if g["status"] == "WAITING"]
        graph_approved = any(g["gate_type"] == "GRAPH_APPROVAL" and g["status"] == "APPROVED" for g in gates.values())
        verifications = self._verifier_rows(); failed = [x for x in verifications if x["status"] == "FAIL"]
        actions: list[dict[str, str]] = []
        if intent and intent["status"] == "DRAFT": actions.append({"action":"APPROVE_INTENT","label":"Review and approve intent"})
        elif graph and not graph_approved: actions.append({"action":"REVIEW_GRAPH","label":"Review proposed execution graph"})
        elif failed: actions.append({"action":"VIEW_FAILURE","label":"Review failed verification evidence"})
        elif waiting: actions.append({"action":"REVIEW_GATE","label":f"Review {waiting[0]['gate_type']} {waiting[0]['gate_id']}"})
        return {"project_root":str(self.root),"project_id":intent["project_id"] if intent else None,"intent":intent,"graph":graph,"execution_units":(graph or {}).get("nodes",[]),"gates":gates,"integrations":integrations,"verifications":verifications,"failed_verifications":failed,"graph_approved":graph_approved,"actions":actions,"promotion":"NOT IMPLEMENTED"}

    def _verifier_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        try:
            from control.verifier import VerifierOrchestrator
            verifier = VerifierOrchestrator(self.root)
            executions = verifier.executions.reconstruct(); results = verifier.verification.reconstruct()["results"]
            by_execution = {e.get("execution_id"): e for e in results.values() for _ in [0] if e.get("evidence_id")}
            evidence = verifier.verification.reconstruct()["evidence"]
            for execution in executions.values():
                result = next((r for r in results.values() if evidence.get(r.get("evidence_id"), {}).get("execution_id") == execution["execution_id"]), None)
                if result: rows.append({"execution_id":execution["execution_id"],"role":execution["role"],"candidate_sha":execution["candidate_sha"],"status":result["status"],"result_id":result["result_id"],"reason_code":result["reason_code"]})
        except Exception: pass
        return sorted(rows, key=lambda row: row["execution_id"])

    def status_json(self) -> str: return json.dumps(self.state(), indent=2, sort_keys=True)

    def render(self) -> list[str]:
        state = self.state(); intent = state["intent"]; graph = state["graph"]; lines = ["ITDD — Human Console", "", f"PROJECT: {state['project_id'] or 'UNKNOWN'}", f"ROOT: {state['project_root']}", "", f"INTENT: {intent['status'] if intent else 'NOT CREATED'}" + (f" ({intent['intent_id']} v{intent['version']})" if intent else "")]
        if intent: lines += [f"REQUIREMENTS: {len(intent['requirements'])}"]
        lines += [f"EXECUTION GRAPH: {('PROPOSED — HUMAN REVIEW REQUIRED' if graph and not state['graph_approved'] else 'APPROVED' if graph else 'NOT CREATED')}", f"EXECUTION UNITS: {len(state['execution_units'])}"]
        if state["verifications"]:
            lines.append("VERIFICATION:")
            for row in state["verifications"]: lines.append(f"  {row['role']}: {row['status']} — {row['reason_code']}")
        if state["integrations"]: lines += ["INTEGRATION:", *[f"  {item['integration_id']}: {item['status']}" for item in state["integrations"]]]
        lines += ["PROMOTION: NOT IMPLEMENTED", "", "ACTION REQUIRED:"]
        if state["actions"]: lines += [f"  {index}. {item['label']}" for index, item in enumerate(state["actions"], 1)]
        elif state["failed_verifications"]: lines += ["  Verification failed. No human approval is legal."]
        else: lines += ["  NO HUMAN ACTION REQUIRED"]
        return lines

    def _confirm(self, prompt: str) -> bool:
        return self.input(f"{prompt}\nType APPROVE to confirm, or anything else to cancel: ").strip() == "APPROVE"

    def _ensure_graph_gate(self, state: dict[str, Any]) -> dict[str, Any]:
        graph = state["graph"]; existing = next((g for g in state["gates"].values() if g["gate_type"] == "GRAPH_APPROVAL" and g["related_graph"] == {"graph_id":graph["graph_id"],"version":graph["version"]}), None)
        if existing: return existing
        intent = state["intent"]; number = re.sub(r"\D", "", graph["graph_id"]) or "1"
        return self.controller.create_graph_approval(gate_id=f"HG-{int(number)+800:03d}", project_id=intent["project_id"], intent=intent, graph=graph, timestamp=_now(), event_prefix="console-graph")

    def approve_intent(self) -> None:
        state = self.state(); intent = state["intent"]
        if not intent or intent["status"] != "DRAFT": raise ConsoleError("No draft intent is awaiting approval.")
        self.output("REVIEW INTENT\n" + "\n".join(f"{req['requirement_id']}: {req['text']}" for req in intent["requirements"]))
        if not self._confirm(f"APPROVE INTENT {intent['intent_id']} v{intent['version']}?"): return
        self.stage_c.approve_intent(intent["intent_id"], intent["version"], event_id=f"console-intent-{intent['intent_id']}-approved", timestamp=_now(), actor_type="human", actor_id="console-human")
        approved = self.stage_c.reconstruct()["approved_intent"]; intent_number = re.sub(r"\D", "", intent["intent_id"]) or "001"; graph_id = f"G-{intent_number}"
        graph = {"graph_id":graph_id,"version":1,"project_id":intent["project_id"],"intent_id":intent["intent_id"],"intent_version":intent["version"],"status":"ACTIVE","created_at":_now(),"created_by":"console-planner","nodes":[{"eu_id":f"EU-{index:03d}","requirement_ids":[req["requirement_id"]]} for index, req in enumerate(intent["requirements"], 1)],"edges":[],"reason":"controller-proposed graph for human review","source_event_id":"console-graph-created","schema_version":1}
        self.stage_c.create_graph(graph, event_id="console-graph-created", timestamp=graph["created_at"], actor_type="agent", actor_id="console-planner"); self._ensure_graph_gate(self.state()); HumanViewGenerator(self.root).generate(project_id=intent["project_id"])
        self.output("Intent approved. A proposed graph now requires your review.")

    def review_graph(self) -> None:
        state = self.state(); graph = state["graph"]
        if not graph: raise ConsoleError("No execution graph exists.")
        self.output(f"REVIEW GRAPH {graph['graph_id']} v{graph['version']}\nIntent: {graph['intent_id']} v{graph['intent_version']}\n" + "\n".join(f"{node['eu_id']} -> {', '.join(node['requirement_ids'])}" for node in graph["nodes"]))
        gate = self._ensure_graph_gate(state)
        if self._confirm(f"APPROVE EXECUTION GRAPH {graph['graph_id']} v{graph['version']}?"): self.approve_gate(gate["gate_id"])

    def approve_gate(self, gate_id: str) -> None:
        gate = self.gates.read(gate_id); self.output(f"APPROVE {gate['gate_type']} {gate_id}?\nSubject: {gate['subject_id']}")
        if not self._confirm("Confirm this exact human decision?"): return
        binding = {"project_id":gate["project_id"],"gate_id":gate_id,**gate["related_candidate"],"evidence":gate["evidence"]}
        result = self.controller.decide(gate_id, decision="APPROVED", actor_type="human", actor_id="console-human", binding=binding, event_prefix=f"console-{gate_id}", timestamp=_now()); HumanViewGenerator(self.root).generate(project_id=result["project_id"])

    def assert_eu_eligible(self, eu_id: str) -> None:
        state = self.state()
        if not state["graph_approved"]: raise ConsoleError(f"EU execution blocked: graph approval is required before {eu_id} can start.")

    def show_failure(self) -> None:
        state = self.state()
        if not state["failed_verifications"]: self.output("No failed verification is recorded."); return
        for row in state["failed_verifications"]:
            self.output(f"VERIFICATION FAILED\nRole: {row['role']}\nCandidate: {row['candidate_sha']}\nResult: {row['result_id']}\nReason: {row['reason_code']}\nITDD stopped this execution. No human approval is available.")

    def run(self) -> None:
        while True:
            self.output("\n".join(self.render()) + "\n\n[1] Choose action   [R] Refresh   [Q] Exit")
            choice = self.input("Choice: ").strip().upper()
            if choice == "Q": return
            if choice == "R": continue
            state = self.state()
            try:
                if choice == "1" and state["actions"]:
                    action = state["actions"][0]["action"]
                    if action == "APPROVE_INTENT": self.approve_intent()
                    elif action == "REVIEW_GRAPH": self.review_graph()
                    elif action == "VIEW_FAILURE": self.show_failure()
                    elif action == "REVIEW_GATE": self.approve_gate(next(g["gate_id"] for g in state["gates"].values() if g["status"] == "WAITING"))
                else: self.output("No legal action selected.")
            except (ConsoleError, HumanGateError, AuthorityError) as exc: self.output(f"BLOCKED: {exc}")

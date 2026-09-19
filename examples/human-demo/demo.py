#!/usr/bin/env python3
"""Interactive Stage E7 demonstration driver.

Each command is controller-facing and project-local. Human-only commands are
deliberately never invoked by this driver without the human running them.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from control.authorization import CapabilityIssuer
from control.context import ContextCompiler
from control.human import HumanViewGenerator
from control.models.store import StageCStore
from control.verifier import SubprocessVerifierAdapter, VerifierOrchestrator


ROOT = Path(__file__).resolve().parent
BASELINE = ""  # populated from Git after init


def git(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(["git", "-C", str(cwd), *args], text=True, capture_output=True, check=True)
    return result.stdout.strip()


def timestamp() -> str:
    return "2026-09-20T04:00:00Z"


def init() -> None:
    (ROOT / ".idd").mkdir(exist_ok=True)
    if not (ROOT / ".git").exists():
        git("init", "-b", "main"); git("config", "user.name", "ITDD Human Demo"); git("config", "user.email", "itdd-demo@example.invalid")
        git("add", "temperature.py", "demo.py", "tests/test_temperature.py"); git("commit", "-m", "demo baseline")
    store = StageCStore(ROOT)
    intent = {"intent_id":"I-701","version":1,"status":"DRAFT","created_at":timestamp(),"created_by":"human-demo","project_id":"human-demo","title":"Temperature converter","purpose":"Demonstrate controlled delivery through E7","requirements":[{"requirement_id":"REQ-001","text":"The CLI shall accept a Fahrenheit temperature and output the equivalent Celsius temperature."},{"requirement_id":"REQ-002","text":"Invalid non-numeric input shall return a non-zero exit status and a clear error message."}],"constraints":["No promotion in this demonstration"],"acceptance_summary":"Valid conversion and graceful invalid-input handling","source_event_id":"demo-intent-created","schema_version":1}
    if not (ROOT / ".idd/intent/I-701/v1.json").exists(): store.create_intent_draft(intent, event_id="demo-intent-created", timestamp=timestamp(), actor_type="agent", actor_id="human-demo")
    HumanViewGenerator(ROOT).generate(project_id="human-demo")
    print("Intent is DRAFT. Human action required before graph/build:")
    print(f"  python3 {Path(__file__).name} approve-intent")
    print(f"Dashboard: {ROOT / '.idd/views/dashboard.md'}")


def approve_intent() -> None:
    StageCStore(ROOT).approve_intent("I-701", 1, event_id="demo-intent-approved", timestamp=timestamp(), actor_type="human", actor_id="local-human")
    graph = {"graph_id":"G-701","version":1,"project_id":"human-demo","intent_id":"I-701","intent_version":1,"status":"ACTIVE","created_at":timestamp(),"created_by":"human-demo","nodes":[{"eu_id":"EU-001","requirement_ids":["REQ-001"]},{"eu_id":"EU-002","requirement_ids":["REQ-002"]}],"edges":[],"reason":"small independent demo units","source_event_id":"demo-graph-created","schema_version":1}
    StageCStore(ROOT).create_graph(graph, event_id="demo-graph-created", timestamp=timestamp(), actor_type="agent", actor_id="human-demo")
    HumanViewGenerator(ROOT).generate(project_id="human-demo")
    print("Intent approved and graph created. Review views, then run:")
    print(f"  python3 {Path(__file__).name} run-bad-eu1")


def run_bad_eu1() -> None:
    if StageCStore(ROOT).reconstruct().get("approved_intent") is None: raise SystemExit("approve-intent must be performed by a human first")
    baseline = git("rev-parse", "HEAD")
    capability = {"capability_id":"CAP-770","schema_version":1,"project_id":"human-demo","role":"BUILDER","execution_id":"EXEC-BUILDER-DEMO-001","issued_at":timestamp(),"baseline_sha":baseline,"allowed_reads":["temperature.py"],"allowed_writes":["temperature.py"],"allowed_executes":["python3"],"allowed_operations":["READ","WRITE","EXECUTE","CREATE_ARTIFACT"],"forbidden_operations":["PROMOTE","INTENT_APPROVAL","GRAPH_APPROVAL"],"allowed_request_types":[],"scope_bindings":{"intent_id":"I-701","intent_version":1,"graph_id":"G-701","graph_version":1,"eu_id":"EU-001"},"version":1,"issued_by":"controller"}
    CapabilityIssuer(ROOT).issue(capability, event_id="demo-builder-cap", timestamp=timestamp())
    packet = {"context_packet_id":"CP-770","intent_binding":{"intent_id":"I-701","intent_version":1},"graph_binding":{"graph_id":"G-701","graph_version":1},"eu_binding":{"eu_id":"EU-001"},"authority_context":{"allowed_operations":["READ","WRITE"],"acceptance_requirements":["REQ-001"]},"working_context":[{"resource_id":"RES-770","path":"temperature.py","purpose":"EU-001 implementation","authority":"WRITE","reason_included":"exact candidate path","source":"approved graph","freshness_or_version":baseline}],"knowledge_context":[],"evidence_context":[],"context_budget":{"max_bytes":100000}}
    ContextCompiler(ROOT).compile(packet, capability_id="CAP-770", state={"project_root":str(ROOT),"project_id":"human-demo","execution_id":"EXEC-BUILDER-DEMO-001","baseline_sha":baseline,"role":"BUILDER"}, event_id="demo-builder-packet", timestamp=timestamp())
    # Deliberately bad candidate: 5/8 instead of 5/9. The source remains a
    # normal Builder-scoped write and its failed history is preserved.
    source = (ROOT / "temperature.py").read_text().replace("* 5 / 9", "* 5 / 8")
    (ROOT / "temperature.py").write_text(source); git("add", "temperature.py"); git("commit", "-m", "demo EU-001 bad candidate")
    candidate = git("rev-parse", "HEAD")
    verifier = VerifierOrchestrator(ROOT, controller_execution_id="EXEC-CONTROLLER-DEMO"); cap = {"capability_id":"CAP-771","schema_version":1,"project_id":"human-demo","role":"SPEC_VERIFIER","execution_id":"EXEC-SPEC-DEMO-001","issued_at":timestamp(),"baseline_sha":baseline,"allowed_reads":["temperature.py"],"allowed_writes":[],"allowed_executes":["python3 -m pytest"],"allowed_operations":["READ","EXECUTE","CREATE_ARTIFACT"],"forbidden_operations":["WRITE","PROMOTE"],"allowed_request_types":[],"scope_bindings":{"intent_id":"I-701","intent_version":1,"graph_id":"G-701","graph_version":1,"eu_id":"EU-001"},"version":1,"issued_by":"controller"}
    contract = {"verification_contract_id":"VC-771","project_id":"human-demo","execution_id":"EXEC-SPEC-DEMO-001","role":"SPEC_VERIFIER","intent_id":"I-701","intent_version":1,"graph_id":"G-701","graph_version":1,"eu_id":"EU-001","baseline_sha":baseline,"candidate_sha":candidate,"context_packet_id":"CP-771","context_packet_hash":"placeholder","required_checks":[{"check_id":"REQCHECK-771","kind":"TEST_COMMAND","command":"python3 -m pytest -q tests/test_temperature.py","required_exit_code":0}],"required_artifacts":[],"allowed_changed_paths":["temperature.py"],"created_at":timestamp(),"created_by":"controller"}
    verifier.create_verifier(role="SPEC_VERIFIER", execution_id="EXEC-SPEC-DEMO-001", capability=cap, packet={**packet,"context_packet_id":"CP-771","eu_binding":{"eu_id":"EU-001"}}, contract=contract, event_prefix="demo-spec-fail", timestamp=timestamp())
    result = verifier.launch("EXEC-SPEC-DEMO-001", adapter=SubprocessVerifierAdapter(), event_prefix="demo-spec-fail-run", timestamp=timestamp())
    HumanViewGenerator(ROOT).generate(project_id="human-demo")
    print(f"SPEC: {result['result']['status']}")
    print(f"Verification view: {ROOT / '.idd/views/verification.md'}")
    print("STOP: inspect the failed candidate and explicitly say 'continue' before any correction.")


COMMANDS = {"init":init,"approve-intent":approve_intent,"run-bad-eu1":run_bad_eu1}
if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS: raise SystemExit(f"usage: {Path(__file__).name} <{'|'.join(COMMANDS)}>")
    COMMANDS[sys.argv[1]]()

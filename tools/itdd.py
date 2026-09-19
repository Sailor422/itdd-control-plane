#!/usr/bin/env python3
"""ITDD human console entry point; Markdown is never authoritative."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from control.console import ConsoleError, HumanConsole, discover_project
from control.human import HumanGateController, HumanGateStore, HumanViewGenerator


def main() -> int:
    parser = argparse.ArgumentParser(prog="itdd", description="Human console for an ITDD project")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("console")
    sub.add_parser("status").add_argument("--json", action="store_true")
    show = sub.add_parser("review"); show.add_argument("gate_id")
    for name in ("approve", "reject"):
        command = sub.add_parser(name); command.add_argument("gate_id")
    args = parser.parse_args(); args.command = args.command or "console"
    try: root = discover_project(Path.cwd())
    except ConsoleError as exc: parser.error(str(exc))
    if args.command == "console": HumanConsole(root).run(); return 0
    if args.command == "status":
        console = HumanConsole(root); print(console.status_json() if args.json else "\n".join(console.render())); return 0
    store = HumanGateStore(root)
    if args.command == "review":
        print(store.read(args.gate_id)); return 0
    gate = store.read(args.gate_id)
    binding = {"project_id": gate["project_id"], "gate_id": gate["gate_id"], **gate["related_candidate"], "evidence": gate["evidence"]}
    controller = HumanGateController(root)
    result = controller.decide(args.gate_id, decision="APPROVED" if args.command == "approve" else "REJECTED", actor_type="human", actor_id="local-human", binding=binding, event_prefix=f"cli-{args.command}-{args.gate_id}", timestamp="2026-09-20T00:00:00Z")
    HumanViewGenerator(root).generate(project_id=result["project_id"]); print(result["status"]); return 0


if __name__ == "__main__":
    raise SystemExit(main())

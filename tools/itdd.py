#!/usr/bin/env python3
"""Small project-local human gate interface; Markdown is never authoritative."""
from __future__ import annotations

import argparse
from pathlib import Path

from control.human import HumanGateController, HumanGateStore, HumanViewGenerator


def main() -> int:
    parser = argparse.ArgumentParser(prog="itdd")
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("review"); show.add_argument("gate_id")
    for name in ("approve", "reject"):
        command = sub.add_parser(name); command.add_argument("gate_id")
    args = parser.parse_args(); root = Path.cwd(); store = HumanGateStore(root)
    if args.command == "review":
        print(store.read(args.gate_id)); return 0
    gate = store.read(args.gate_id)
    binding = {"project_id": gate["project_id"], "gate_id": gate["gate_id"], **gate["related_candidate"], "evidence": gate["evidence"]}
    controller = HumanGateController(root)
    result = controller.decide(args.gate_id, decision="APPROVED" if args.command == "approve" else "REJECTED", actor_type="human", actor_id="local-human", binding=binding, event_prefix=f"cli-{args.command}-{args.gate_id}", timestamp="2026-09-20T00:00:00Z")
    HumanViewGenerator(root).generate(project_id=result["project_id"]); print(result["status"]); return 0


if __name__ == "__main__":
    raise SystemExit(main())

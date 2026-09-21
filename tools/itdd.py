#!/usr/bin/env python3
"""Small project-local ITDD command line interface."""
from __future__ import annotations

import argparse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from control.view import ViewError, discover_project, open_visualization
from control.human import HumanGateStore
from control.human_decisions import HumanDecisionController
from control.intent_amendments import IntentAmendmentController


def main() -> int:
    parser = argparse.ArgumentParser(prog="itdd", description="Read-only ITDD project visualization and human gates")
    sub = parser.add_subparsers(dest="command", required=True)
    view = sub.add_parser("view", help="regenerate and open the read-only project visualization")
    view.add_argument("--no-open", action="store_true", help="regenerate views without launching Obsidian")
    show = sub.add_parser("review"); show.add_argument("gate_id")
    decisions = sub.add_parser("decision", help="create or consume a project-local HUMAN_ONLY decision document")
    decision_sub = decisions.add_subparsers(dest="decision_command", required=True)
    create_intent = decision_sub.add_parser("create-intent")
    create_intent.add_argument("intent_id"); create_intent.add_argument("version", type=int); create_intent.add_argument("--decision-id", required=True); create_intent.add_argument("--open", action="store_true")
    create_gate = decision_sub.add_parser("create-gate")
    create_gate.add_argument("gate_id"); create_gate.add_argument("--decision-id", required=True); create_gate.add_argument("--open", action="store_true")
    create_amendment = decision_sub.add_parser("create-amendment")
    create_amendment.add_argument("amendment_id"); create_amendment.add_argument("intent_id"); create_amendment.add_argument("version", type=int)
    create_amendment.add_argument("--decision-id"); create_amendment.add_argument("--open", action="store_true")
    resolve = decision_sub.add_parser("resolve", help="controller-side scan of a saved response")
    resolve.add_argument("decision_id")
    repair = decision_sub.add_parser("repair", help="preserve malformed input and restore a safe PENDING response area")
    repair.add_argument("decision_id")
    decision_sub.add_parser("scan", help="consume all saved non-PENDING decision responses")
    args = parser.parse_args()
    try: root = discover_project(Path.cwd())
    except ViewError as exc: parser.error(str(exc))
    if args.command == "view":
        dashboard, opened = open_visualization(root, launch=not args.no_open)
        print(f"Read-only ITDD visualization: {dashboard}")
        print("Obsidian opened." if opened else "Obsidian was not opened; the derived Markdown views are ready.")
        return 0
    store = HumanGateStore(root)
    if args.command == "review":
        print(store.read(args.gate_id)); return 0
    controller = HumanDecisionController(root)
    timestamp = "2026-09-20T00:00:00Z"
    if args.decision_command == "create-intent":
        print(controller.create_intent(decision_id=args.decision_id, intent_id=args.intent_id, version=args.version, timestamp=timestamp, open_document=args.open)); return 0
    if args.decision_command == "create-amendment":
        amendment = IntentAmendmentController(root).create_authority_amendment(amendment_id=args.amendment_id, source_intent_id=args.intent_id, source_intent_version=args.version, timestamp=timestamp, decision_id=args.decision_id, open_document=args.open)
        print(amendment); return 0
    if args.decision_command == "create-gate":
        print(controller.create_gate(decision_id=args.decision_id, gate_id=args.gate_id, timestamp=timestamp, open_document=args.open)); return 0
    if args.decision_command == "scan":
        print(controller.scan(timestamp=timestamp)); return 0
    if args.decision_command == "repair":
        print(controller.store.repair(args.decision_id, repaired_at=timestamp)); return 0
    print(controller.resolve(args.decision_id, timestamp=timestamp)); return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Operator command for explicit recovery of one stranded Builder run."""
import argparse
from getpass import getuser
from pathlib import Path

from control.operational import OperationalController, OperationalError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("operation_id")
    parser.add_argument("eu_id")
    parser.add_argument("recovery_id")
    parser.add_argument("old_execution_id")
    parser.add_argument("fresh_execution_id")
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args(argv)
    print(f"Operation/EU: {args.operation_id}/{args.eu_id}")
    print(f"Execution: {args.old_execution_id} -> {args.fresh_execution_id}")
    print(f"Workspace to quarantine: {args.workspace}")
    print(f"Actor: {getuser()}")
    answer = input("Confirm the worker is STOPPED? Type YES: ")
    if answer != "YES":
        print("Cancelled; no changes made.")
        return 1
    try:
        result = OperationalController(args.project).recover_building_run(
            operation_id=args.operation_id, eu_id=args.eu_id, recovery_id=args.recovery_id,
            old_execution_id=args.old_execution_id, fresh_execution_id=args.fresh_execution_id,
            workspace=args.workspace, confirm_worker_stopped=True,
            timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat())
    except OperationalError as exc:
        parser.error(str(exc))
    print(f"Recovery ready: {result['operation_id']} ({result['execution_id']}); builder not launched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only launcher for the derived ITDD project visualization."""
from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

from control.authority.paths import resolve_project_root
from control.human import HumanViewGenerator
from control.models.store import StageCStore


class ViewError(ValueError):
    pass


def discover_project(start: str | Path) -> Path:
    candidate = Path(start).expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for root in (candidate, *candidate.parents):
        if (root / ".idd/state/events.jsonl").exists():
            return resolve_project_root(root)
    raise ViewError("No ITDD project found here; start inside a project with durable ITDD state.")


def project_id(root: Path) -> str:
    state = StageCStore(root).reconstruct()
    intent = state.get("approved_intent") or (list(state.get("intents", {}).values())[-1] if state.get("intents") else None)
    if not intent:
        raise ViewError("ITDD project has no durable intent to visualize.")
    return intent["project_id"]


def open_visualization(root: str | Path, *, launch: bool = True) -> tuple[Path, bool]:
    """Regenerate derived views and optionally open the dashboard in Obsidian.

    This function reads authoritative state and writes only `.idd/views/*.md`.
    It never calls a controller or appends an event.
    """
    project_root = resolve_project_root(root)
    dashboard = project_root / ".idd/views/dashboard.md"
    HumanViewGenerator(project_root).generate(project_id=project_id(project_root))
    opened = False
    if launch and platform.system() == "Darwin" and shutil.which("open"):
        result = subprocess.run(["open", "-a", "Obsidian", str(dashboard)], check=False)
        opened = result.returncode == 0
    return dashboard, opened

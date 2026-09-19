"""Project-root authority checks independent of Codex trust settings."""

from __future__ import annotations

import os
from pathlib import Path


class AuthorityError(ValueError):
    """Raised when a path is outside the explicitly authorized project root."""


def resolve_project_root(root: str | os.PathLike[str]) -> Path:
    """Return an existing, canonical directory to serve as the ITDD root."""

    candidate = Path(root).expanduser()
    if not candidate.exists():
        raise AuthorityError(f"project root does not exist: {candidate}")
    if not candidate.is_dir():
        raise AuthorityError(f"project root is not a directory: {candidate}")
    return candidate.resolve()


def _reject_lexical_traversal(candidate: Path) -> None:
    if ".." in candidate.parts:
        raise AuthorityError(f"parent traversal is not authorized: {candidate}")


def resolve_project_path(
    project_root: str | os.PathLike[str],
    candidate: str | os.PathLike[str],
) -> Path:
    """Resolve *candidate* and require it to remain beneath *project_root*.

    Both lexical traversal and resolved symlink escapes are rejected. An absolute
    candidate is allowed only when its resolved path is still inside the root.
    """

    root = resolve_project_root(project_root)
    raw = Path(candidate).expanduser()
    _reject_lexical_traversal(raw)
    resolved = (raw if raw.is_absolute() else root / raw).resolve(strict=False)
    try:
        inside = os.path.commonpath((str(root), str(resolved))) == str(root)
    except ValueError as exc:
        raise AuthorityError(f"path has incompatible authority domain: {candidate}") from exc
    if not inside:
        raise AuthorityError(f"path escapes project root: {candidate}")
    return resolved


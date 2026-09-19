from pathlib import Path

import pytest

from control.authority.paths import AuthorityError, resolve_project_path, resolve_project_root


def test_root_and_nested_path_are_canonical(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    assert resolve_project_root(root) == root.resolve()
    assert resolve_project_path(root, "src/module.py") == (root / "src/module.py").resolve()


def test_parent_traversal_is_rejected(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    with pytest.raises(AuthorityError):
        resolve_project_path(root, "src/../outside.txt")


def test_symlink_escape_is_rejected(tmp_path: Path):
    root = tmp_path / "project"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(AuthorityError):
        resolve_project_path(root, "link/secret.txt")


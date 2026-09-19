from pathlib import Path

import pytest

from control.authority.paths import AuthorityError, resolve_project_path


def test_unrelated_repository_is_not_authorized(tmp_path: Path):
    root = tmp_path / "project"
    unrelated = tmp_path / "unrelated"
    root.mkdir()
    unrelated.mkdir()
    with pytest.raises(AuthorityError):
        resolve_project_path(root, unrelated)


@pytest.mark.parametrize("legacy", [".codex", ".claude", ".hermes"])
def test_legacy_vaults_are_not_auto_authorized(tmp_path: Path, legacy: str):
    root = tmp_path / "project"
    root.mkdir()
    legacy_path = tmp_path / legacy
    legacy_path.mkdir()
    with pytest.raises(AuthorityError):
        resolve_project_path(root, legacy_path)


def test_codex_global_trust_does_not_change_authority(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    with pytest.raises(AuthorityError):
        resolve_project_path(root, Path("/"))


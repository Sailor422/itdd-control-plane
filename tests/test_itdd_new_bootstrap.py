import json
import subprocess
from pathlib import Path

from skills import itdd_new

def project(tmp_path):
    (tmp_path / "AGENTS.md").write_text("## Agent skills\n### Issue tracker\n")
    docs = tmp_path / "docs" / "agents"; docs.mkdir(parents=True)
    for name in ("issue-tracker.md", "triage-labels.md", "domain.md"):
        (docs / name).write_text("ok")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)

def test_bootstrap_copies_runtime_and_populates_manifest(tmp_path):
    project(tmp_path)
    result = itdd_new.initialize_itdd_project(tmp_path)
    assert result["success"]
    assert (tmp_path / "control" / "__init__.py").exists()
    manifest = json.loads((tmp_path / "skills" / "manifest.json").read_text())
    assert manifest["skills"]
    assert manifest["skills"][0]["id"] == "itdd.grill-with-docs"
    assert (tmp_path / "skills" / manifest["skills"][0]["contract"]).exists()
    assert (tmp_path / "skills" / "itdd-prepare" / "SKILL.md").exists()

def test_bootstrap_fails_before_mutation_when_bundle_missing(tmp_path, monkeypatch):
    project(tmp_path)
    monkeypatch.setattr(itdd_new, "_bundle_root", lambda: tmp_path / "missing")
    result = itdd_new.initialize_itdd_project(tmp_path)
    assert not result["success"]
    assert "bundle is unavailable" in result["errors"][0]
    assert not (tmp_path / ".idd").exists()

def test_bootstrap_preserves_existing_runtime_file(tmp_path):
    project(tmp_path)
    (tmp_path / "control").mkdir()
    sentinel = tmp_path / "control" / "sentinel.py"; sentinel.write_text("custom")
    result = itdd_new.initialize_itdd_project(tmp_path)
    assert result["success"]
    assert sentinel.read_text() == "custom"


def test_bootstrap_runtime_discovers_contract(tmp_path):
    project(tmp_path)
    result = itdd_new.initialize_itdd_project(tmp_path)
    assert result["success"]
    from skills.runtime import SkillRuntime
    discovered = SkillRuntime(tmp_path).discover()
    assert "itdd.grill-with-docs" in discovered
    assert (tmp_path / "skills" / "runtime.py").exists()
    assert (tmp_path / "schemas").is_dir()
    assert (tmp_path / "skills" / "grill_with_docs" / "skill.json").exists()
    assert (tmp_path / "skills" / "grill-with-docs" / "SKILL.md").exists()


def test_invalid_existing_manifest_refuses_without_mutation(tmp_path):
    project(tmp_path)
    skills = tmp_path / "skills"; skills.mkdir()
    (skills / "manifest.json").write_text("{}")
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    result = itdd_new.initialize_itdd_project(tmp_path)
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert not result["success"]
    assert "invalid or empty" in result["errors"][0]
    assert before == after


def test_unrelated_existing_manifest_refuses_without_mutation(tmp_path):
    project(tmp_path)
    skills = tmp_path / "skills"; skills.mkdir()
    (skills / "manifest.json").write_text(json.dumps({"skills": [{"id": "other", "contract": "other/skill.json"}]}))
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    result = itdd_new.initialize_itdd_project(tmp_path)
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert not result["success"]
    assert "unrelated" in result["errors"][0]
    assert before == after


def test_bundle_symlink_refuses_without_mutation(tmp_path, monkeypatch):
    project(tmp_path)
    bundle = itdd_new._bundle_root()
    link = bundle / "skills" / "_test_escape_link"
    link.symlink_to(Path("/tmp"), target_is_directory=True)
    try:
        result = itdd_new.initialize_itdd_project(tmp_path)
    finally:
        link.unlink()
    assert not result["success"]
    assert "symlink" in result["errors"][0]
    assert not (tmp_path / ".idd").exists()


def test_bootstrap_skips_build_artifacts(tmp_path):
    project(tmp_path)
    result = itdd_new.initialize_itdd_project(tmp_path)
    assert result["success"]
    assert not list((tmp_path / "skills").rglob("__pycache__"))
    assert not list(tmp_path.rglob("*.pyc"))

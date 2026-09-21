"""Initialize a new ITDD-controlled project with Matt Pocock skills setup."""
import subprocess
import sys
import os
import json
import shutil
from pathlib import Path


def _bundle_root() -> Path:
    """Return the installed repository root containing the ITDD payload."""
    # In an editable checkout this is the repository root.  In a wheel, the
    # package-data configuration keeps ``control`` and ``skills`` beside this
    # module, so the same lookup works.
    return Path(__file__).resolve().parents[2]


def _validate_bundle(bundle: Path) -> tuple[bool, list[str]]:
    """Validate the payload before changing the destination project."""
    missing = [name for name in ("control", "skills")
               if not (bundle / name).is_dir()]
    for required in (
        "control/__init__.py",
        "schemas",
        "skills/runtime.py",
        "skills/grill_with_docs/skill.json",
        "skills/grill-with-docs/SKILL.md",
    ):
        path = bundle / required
        if not path.exists():
            missing.append(required)
    return not missing, missing


def _copy_missing(source: Path, destination: Path) -> list[str]:
    """Copy a bundle without replacing any user-owned file."""
    created = []
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            created.extend(_copy_missing(child, destination / child.name))
    elif not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        created.append(str(destination))
    return created


def install_itdd_bundle(root: Path, result: dict) -> bool:
    """Install the control-plane and skills payload into *root*."""
    bundle = _bundle_root()
    valid, missing = _validate_bundle(bundle)
    if not valid:
        result["errors"].append(
            "ITDD runtime/control-plane bundle is unavailable at "
            f"{bundle}: missing {', '.join(missing)}. Reinstall itdd-control-plane."
        )
        return False

    skill_root = root / "skills"
    manifest_path = skill_root / "manifest.json"
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            existing = None
        if not isinstance(existing, dict) or not existing.get("skills"):
            result["errors"].append("Existing skills/manifest.json is invalid or empty; refusing to overwrite it.")
            return False

    # The runtime is deliberately copied to the conventional import path.
    _copy_missing(bundle / "control", root / "control")
    # Do not copy the source repository's development manifest: the new
    # project's manifest is generated below from the actual skill documents.
    for child in (bundle / "skills").iterdir():
        if child.name not in {"manifest.json", "__pycache__"}:
            _copy_missing(child, skill_root / child.name)
    schemas_root = root / "schemas"
    if (bundle / "schemas").is_dir():
        _copy_missing(bundle / "schemas", schemas_root)
    # This is the canonical contract shipped by the control plane. Keep the
    # manifest shape aligned with SkillRuntime.discover().
    manifest = {
        "manifest_version": "1.0",
        "project_local_only": True,
        "skills": [{
            "id": "itdd.grill-with-docs",
            "contract": "grill_with_docs/skill.json",
            "disposition": "ADOPT",
            "source_rationale": "bundled ITDD contract",
        }],
    }
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        result["created"].append("skills/manifest.json")
    result["created"].append("ITDD runtime/control-plane and local skills bundle")
    return True


def check_pocock_setup(root: Path) -> tuple[bool, list[str]]:
    """Check if Matt Pocock skills setup has been run.
    
    Returns (success, errors) tuple.
    Validates minimum contract, not just file existence.
    """
    errors = []
    
    # Check for key Pocock setup files
    agents_md = root / 'AGENTS.md'
    claudemd = root / 'CLAUDE.md'
    docs_agents = root / 'docs' / 'agents'
    
    # Validate AGENTS.md or CLAUDE.md with required sections
    has_agent_skills = False
    has_issue_tracker = False
    for md_file in [agents_md, claudemd]:
        if md_file.exists():
            content = md_file.read_text()
            if '## Agent skills' in content or '### Agent skills' in content:
                has_agent_skills = True
            if '### Issue tracker' in content or '## Issue tracker' in content:
                has_issue_tracker = True
    
    if not has_agent_skills:
        errors.append("Missing '## Agent skills' section in AGENTS.md or CLAUDE.md")
    if not has_issue_tracker:
        errors.append("Missing '### Issue tracker' section in AGENTS.md or CLAUDE.md")
    
    # Validate docs/agents/ has minimum required files
    if not docs_agents.exists():
        errors.append("docs/agents/ directory missing")
    else:
        required_files = ['issue-tracker.md', 'triage-labels.md']
        for req_file in required_files:
            if not (docs_agents / req_file).exists():
                errors.append(f"docs/agents/{req_file} missing")
        
        # Check domain.md exists (required for domain modeling)
        if not (docs_agents / 'domain.md').exists():
            errors.append("docs/agents/domain.md missing")
    
    return (len(errors) == 0, errors)


def initialize_itdd_project(root: Path) -> dict:
    """Initialize ITDD infrastructure in the given directory.
    
    Returns a dict with status and any errors.
    """
    result = {"success": False, "created": [], "errors": [], "warnings": []}
    
    # CRITICAL: Check for Matt Pocock setup FIRST (stricter validation)
    pocock_ok, pocock_errors = check_pocock_setup(root)
    if not pocock_ok:
        error_msg = "Matt Pocock skills setup incomplete or invalid.\n\n"
        error_msg += "BEFORE running /itdd-new, you MUST run:\n"
        error_msg += "  /setup-matt-pocock-skills\n\n"
        error_msg += "Missing or invalid components:\n"
        for err in pocock_errors:
            error_msg += f"  - {err}\n"
        error_msg += "\nSee docs/GETTING-STARTED.md for the complete workflow."
        result["errors"].append(error_msg)
        return result
    
    # Check if .idd already exists
    if (root / '.idd').exists():
        result["errors"].append(".idd/ already exists. This project is already ITDD-initialized.")
        return result

    # Validate the installed payload before creating any project files.
    bundle_ok, bundle_missing = _validate_bundle(_bundle_root())
    if not bundle_ok:
        result["errors"].append(
            "ITDD runtime/control-plane bundle is unavailable at "
            f"{_bundle_root()}: missing {', '.join(bundle_missing)}. Reinstall itdd-control-plane."
        )
        return result
    
    # Initialize git if needed (use user's existing identity, don't set fake identity)
    git_check = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                               capture_output=True, text=True, cwd=root)
    if git_check.returncode != 0:
        try:
            subprocess.run(['git', 'init', '-b', 'main'], cwd=root, check=True, capture_output=True)
            # Don't set fake identity - user must configure git themselves
            # Check if user has global git config
            user_check = subprocess.run(['git', 'config', 'user.name'], 
                                        capture_output=True, text=True)
            if not user_check.stdout.strip():
                result["warnings"].append(
                    "Git user.name not configured. Run: git config --global user.name 'Your Name'"
                )
            result["created"].append("git repository")
        except subprocess.CalledProcessError as e:
            result["errors"].append(f"Failed to initialize git: {e}")
            return result
    
    # Create .idd structure
    idd_dirs = [
        'intent',
        'graph',
        'capabilities',
        'context/packets',
        'evidence/contracts',
        'evidence/records',
        'verifiers/executions',
        'human_decisions/registry',
        'human_decisions/pending',
        'operations',
        'attestations',
        'state',
        'views',
        'build_workspaces',
    ]
    for d in idd_dirs:
        full_path = root / '.idd' / d
        full_path.mkdir(parents=True, exist_ok=True)
        result["created"].append(f".idd/{d}")
    
    # Create project scaffolding
    (root / 'src').mkdir(exist_ok=True)
    result["created"].append("src/")
    
    (root / 'tests').mkdir(exist_ok=True)
    result["created"].append("tests/")
    
    # docs/adr already created by Pocock setup, but ensure it exists
    (root / 'docs' / 'adr').mkdir(parents=True, exist_ok=True)
    result["created"].append("docs/adr/")
    
    # Create CONTEXT.md
    context_md = root / 'CONTEXT.md'
    if not context_md.exists():
        context_md.write_text("""# Context

## Domain Glossary

*Terms and definitions specific to this project.*

## Project Identity

- **Project ID**: (assign unique identifier)
- **Description**: (project description)

## Authority Boundaries

- **Human decisions**: intent approval, graph approval, promotion
- **Agent authority**: clarification proposals, implementation within EU scope
""")
        result["created"].append("CONTEXT.md")
    
    # Install the self-contained runtime before writing the manifest.
    if not install_itdd_bundle(root, result):
        return result
    
    # Create .gitignore
    gitignore = root / '.gitignore'
    if not gitignore.exists():
        gitignore.write_text(""".idd/build_workspaces/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
""")
        result["created"].append(".gitignore")
    
    # Create initial commit
    commit_failed = False
    try:
        subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'ITDD infrastructure initialized'], 
                       cwd=root, check=True, capture_output=True)
        result["created"].append("git commit: 'ITDD infrastructure initialized'")
        result["success"] = True
    except subprocess.CalledProcessError as e:
        result["errors"].append(f"Failed to create commit: {e}")
        result["success"] = False  # Commit failure = initialization not complete
        result["warnings"].append("ITDD files created but not committed. Commit manually when ready.")
        commit_failed = True
    
    return result


if __name__ == '__main__':
    import os
    root = Path(os.getcwd())
    result = initialize_itdd_project(root)
    
    if result.get("errors"):
        print("\n❌ Cannot initialize ITDD infrastructure\n")
        for err in result["errors"]:
            print(f"ERROR: {err}\n")
        sys.exit(1)
    
    if result["success"]:
        print("\n✓ ITDD infrastructure initialized successfully")
        print("\nCreated:")
        for item in result["created"]:
            print(f"  - {item}")
        
        if result.get("warnings"):
            print("\nWarnings:")
            for warn in result["warnings"]:
                print(f"  ⚠ {warn}")
    else:
        print("\n✗ ITDD initialization partially failed")
        print("\nCreated (but commit failed):")
        for item in result["created"]:
            print(f"  - {item}")
        print("\nErrors:")
        for err in result["errors"]:
            print(f"  ERROR: {err}")
        if result.get("warnings"):
            print("\nWarnings:")
            for warn in result["warnings"]:
                print(f"  ⚠ {warn}")
        sys.exit(1)
    
    print("\nNext steps:")
    print("  1. Review CONTEXT.md and add your domain glossary")
    print("  2. Use /grill-with-docs to clarify requirements")
    print("  3. Create and approve an intent")
    print("  4. Propose an execution graph")

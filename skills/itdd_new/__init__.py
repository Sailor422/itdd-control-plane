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


def _copy_missing(source: Path, destination: Path, source_root: Path, destination_root: Path) -> list[str]:
    """Copy bundle content without replacing files or following symlinks."""
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    if source.is_symlink() or destination.is_symlink():
        raise ValueError(f"refusing symlink during bundle copy: {source} -> {destination}")
    try:
        source.resolve().relative_to(source_root)
        destination.resolve().relative_to(destination_root)
    except ValueError as exc:
        raise ValueError(f"bundle copy escapes its root: {source} -> {destination}") from exc

    created = []
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            if child.name == "__pycache__" or child.suffix == ".pyc":
                continue
            created.extend(_copy_missing(child, destination / child.name, source_root, destination_root))
    elif source.is_file() and not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        created.append(str(destination))
    return created


def _manifest_contracts(bundle: Path, manifest_path: Path) -> tuple[bool, str]:
    """Check an existing manifest without changing the destination."""
    if manifest_path.is_symlink():
        return False, "Existing skills/manifest.json is a symlink; refusing to follow it."
    try:
        existing = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        return False, "Existing skills/manifest.json is invalid or empty; refusing to overwrite it."
    entries = existing.get("skills") if isinstance(existing, dict) else None
    if not isinstance(entries, list) or not entries:
        return False, "Existing skills/manifest.json is invalid or empty; refusing to overwrite it."
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not isinstance(entry.get("contract"), str):
            return False, "Existing skills/manifest.json contains an invalid skill entry; refusing to overwrite it."
        contract = Path(entry["contract"])
        if contract.is_absolute() or ".." in contract.parts:
            return False, "Existing skills/manifest.json contains an unsafe contract path; refusing to overwrite it."
        bundled = bundle / "skills" / contract
        if not bundled.is_file() or bundled.is_symlink():
            return False, f"Existing skills/manifest.json references an unrelated or missing contract: {entry['contract']}"
    return True, ""


def _preflight_install(root: Path) -> tuple[bool, str]:
    """Validate every install refusal condition before any destination mutation."""
    bundle = _bundle_root()
    valid, missing = _validate_bundle(bundle)
    if not valid:
        return False, ("ITDD runtime/control-plane bundle is unavailable at "
                       f"{bundle}: missing {', '.join(missing)}. Reinstall itdd-control-plane.")
    manifest_path = root / "skills" / "manifest.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        ok, error = _manifest_contracts(bundle, manifest_path)
        if not ok:
            return False, error
    # Existing destination directories must not be symlinks, since copy_missing
    # intentionally never follows them.
    for name in ("control", "skills", "schemas"):
        path = root / name
        if path.is_symlink():
            return False, f"Refusing to copy through symlinked destination: {path}"
    for payload in (bundle / "control", bundle / "skills", bundle / "schemas"):
        for path in payload.rglob("*"):
            if path.is_symlink():
                return False, f"Refusing symlink in bundled payload: {path}"
    return True, ""


def install_itdd_bundle(root: Path, result: dict) -> bool:
    """Install the control-plane and skills payload into *root*."""
    bundle = _bundle_root()
    ok, error = _preflight_install(root)
    if not ok:
        result["errors"].append(error)
        return False

    _copy_missing(bundle / "control", root / "control", bundle, root)
    for child in (bundle / "skills").iterdir():
        if child.name not in {"manifest.json", "__pycache__"}:
            _copy_missing(child, root / "skills" / child.name, bundle / "skills", root / "skills")
    if (bundle / "schemas").is_dir():
        _copy_missing(bundle / "schemas", root / "schemas", bundle, root)
    manifest_path = root / "skills" / "manifest.json"
    manifest = {
        "manifest_version": "1.0",
        "project_local_only": True,
        "skills": [{
            "id": "itdd.grill-with-docs",
            "contract": "grill_with_docs/skill.json",
            "disposition": "ADOPT",
            "source_rationale": "bundled ITDD contract",
        }],
        "workflows": json.loads((bundle / "skills" / "manifest.json").read_text(encoding="utf-8")).get("workflows", {}),
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
        error_msg += "\nSee docs/GETTING-STARTED.md for the current planning path; /itdd-new is optional later-stage setup."
        result["errors"].append(error_msg)
        return result
    
    # Check if .idd already exists
    if (root / '.idd').exists():
        result["errors"].append(".idd/ already exists. This project is already ITDD-initialized.")
        return result

    # Preflight all bundle and manifest refusal conditions before git init or
    # any other destination mutation.
    install_ok, install_error = _preflight_install(root)
    if not install_ok:
        result["errors"].append(install_error)
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

"""Initialize a new ITDD-controlled project with Matt Pocock skills setup."""
import subprocess
import sys
import os
from pathlib import Path

def check_pocock_setup(root: Path) -> bool:
    """Check if Matt Pocock skills setup has been run.
    
    Returns True if setup is complete, False if missing.
    """
    # Check for key Pocock setup files
    agents_md = root / 'AGENTS.md'
    claudemd = root / 'CLAUDE.md'
    docs_agents = root / 'docs' / 'agents'
    
    # Has Agent skills section in AGENTS.md or CLAUDE.md?
    has_agent_skills = False
    for md_file in [agents_md, claudemd]:
        if md_file.exists():
            content = md_file.read_text()
            if '## Agent skills' in content or '### Issue tracker' in content:
                has_agent_skills = True
                break
    
    # Has docs/agents/ configuration?
    has_docs_agents = docs_agents.exists() and (docs_agents / 'issue-tracker.md').exists()
    
    return has_agent_skills and has_docs_agents


def initialize_itdd_project(root: Path) -> dict:
    """Initialize ITDD infrastructure in the given directory.
    
    Returns a dict with status and any errors.
    """
    result = {"success": False, "created": [], "errors": [], "warnings": []}
    
    # CRITICAL: Check for Matt Pocock setup FIRST
    if not check_pocock_setup(root):
        result["errors"].append(
            "Matt Pocock skills setup not detected.\n\n"
            "BEFORE running /itdd-new, you MUST run:\n"
            "  /setup-matt-pocock-skills\n\n"
            "This configures your issue tracker, triage labels, and domain docs layout.\n"
            "See docs/GETTING-STARTED.md for the complete workflow."
        )
        return result
    
    # Check if .idd already exists
    if (root / '.idd').exists():
        result["errors"].append(".idd/ already exists. This project is already ITDD-initialized.")
        return result
    
    # Initialize git if needed
    git_check = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                               capture_output=True, text=True, cwd=root)
    if git_check.returncode != 0:
        try:
            subprocess.run(['git', 'init', '-b', 'main'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'ITDD'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'itdd@local'], cwd=root, check=True, capture_output=True)
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
    
    # Create skills manifest
    skills_dir = root / 'skills'
    skills_dir.mkdir(exist_ok=True)
    import json
    manifest = {
        "manifest_version": "1.0",
        "project_local_only": True,
        "skills": []
    }
    (skills_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    result["created"].append("skills/manifest.json")
    
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
    try:
        subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'ITDD infrastructure initialized'], 
                       cwd=root, check=True, capture_output=True)
        result["created"].append("git commit: 'ITDD infrastructure initialized'")
        result["success"] = True
    except subprocess.CalledProcessError as e:
        result["errors"].append(f"Failed to create commit: {e}")
        result["success"] = True  # Still succeeded in creating files
    
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
    else:
        print("\n✗ Failed to initialize ITDD infrastructure")
        for err in result["errors"]:
            print(f"  ERROR: {err}")
        sys.exit(1)
    
    print("\nNext steps:")
    print("  1. Review CONTEXT.md and add your domain glossary")
    print("  2. Use /grill-with-docs to clarify requirements")
    print("  3. Create and approve an intent")
    print("  4. Propose an execution graph")

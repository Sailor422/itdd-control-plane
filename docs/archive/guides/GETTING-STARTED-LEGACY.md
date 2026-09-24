# Archived Getting Started Guide (superseded)

> Archived 2026-09-24. This is historical setup guidance, not a supported current workflow. It describes a former full execution-oriented path and contains obsolete release, install, and test claims. The project is in development, unreleased, and not in use. Use the current [planning-first Getting Started guide](../../GETTING-STARTED.md) instead.

---

# Getting Started with ITDD Control Plane

This guide walks you through setting up and using ITDD Control Plane for the first time.

## Prerequisites

### Required

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Git**: [Install Git](https://git-scm.com/downloads)
- **prime-agent v0.9.5+**: See installation below

### Recommended

- **VS Code** or similar editor with Python support
- **Obsidian** for viewing `.idd/` documents (optional)

## Installation

### Step 1: Install prime-agent

**macOS (Homebrew):**
```bash
brew install prime-agent
```

**From PyPI:**
```bash
pip install prime-agent
```

**From source:**
```bash
git clone https://github.com/prime-agent/prime-agent.git
cd prime-agent
pip install -e .
```

**Verify installation:**
```bash
prime-agent --version
# Expected: 0.9.5 or higher
which prime-agent
# Expected: /opt/homebrew/bin/prime-agent (macOS) or similar
```

### Step 2: Clone ITDD Control Plane

```bash
# For development/contributing
git clone https://github.com/YOUR_USERNAME/itdd-control-plane.git
cd itdd-control-plane
pip install -e ".[dev]"

# Or just use as a library
pip install itdd-control-plane
```

### Step 3: Verify Installation

```bash
# Run tests
cd itdd-control-plane
pytest -q
# Expected: 156 passed
```

## Your First ITDD Project

### Create a New Project

```bash
# Create project directory
cd ~/Projects
mkdir oak-harbor-marina
cd oak-harbor-marina

# Start Prime
prime-agent
```

### Step 1: Configure Matt Pocock Skills (REQUIRED)

**This step is mandatory.** The Matt Pocock engineering skills (`/triage`, `/to-spec`, `/to-tickets`, etc.) require per-repo configuration.

In the Prime prompt:
```
/setup-matt-pocock-skills
```

This interactive skill will:
1. **Explore** your repo (git remote, existing docs, etc.)
2. **Ask** about your issue tracker (GitHub/GitLab/local markdown)
3. **Ask** about triage label vocabulary (defaults recommended)
4. **Ask** about domain docs layout (single-context vs multi-context)
5. **Write** configuration files:
   - `docs/agents/issue-tracker.md`
   - `docs/agents/triage-labels.md`
   - `docs/agents/domain.md`
   - `AGENTS.md` or `CLAUDE.md` (agent skills block)

**Do not skip this step.** The engineering skills read these config files at runtime.

### Step 2: Initialize ITDD Infrastructure

After Pocock setup completes:
```
/itdd-new
```

**Note:** `/itdd-new` will fail if Pocock setup is not detected.

This creates:
- A self-contained local runtime and bundled contracts in `control/`, `schemas/`, and `skills/`
- `.idd/` directory structure (ITDD authoritative state)
- `CONTEXT.md` (domain glossary template)
- `src/` and `tests/` directories
- `docs/../../adr/` (architectural decisions)
- `skills/manifest.json` (project-local ITDD skills)
- `.gitignore`
- Initial git commit: "ITDD infrastructure initialized"

### Bootstrap safety

The bootstrap performs a read-only preflight before Git initialization or file creation. It refuses an invalid or empty existing `skills/manifest.json`, and refuses manifests that reference contracts not shipped in the local bundle. A valid manifest is retained after its contracts are verified against the bundle. Symlinked bundle content or destination roots is rejected to prevent path escape. Copied payloads omit `__pycache__` directories and `.pyc` files; wheel builds omit them too.

If preflight fails, the destination is unchanged. Fix or remove the existing manifest, then run `/itdd-new` again.

### Verify Setup

```bash
# Check structure
tree -L 2 -I '.git'
# Should show:
# .idd/
# docs/
#   agents/        (from Pocock setup)
#   ../../adr/
# src/
# tests/
# AGENTS.md        (from Pocock setup)
# CONTEXT.md
# skills/manifest.json
```

### Review Generated Configuration

Before proceeding, review what was created:

1. **`docs/agents/issue-tracker.md`** - Verify issue tracker is correct
2. **`docs/agents/triage-labels.md`** - Review triage label vocabulary
3. **`docs/agents/domain.md`** - Confirm single-context layout
4. **`AGENTS.md`** - Check agent skills block
5. **`CONTEXT.md`** - Edit with your domain glossary**

## Your First Execution Unit

### 1. Clarify Requirements

In Prime:
```
/grill-with-docs
```

This starts a clarification session to understand your requirements.

### 2. Prepare a bounded execution contract

Before implementation, run `/itdd-prepare`. It uses separate fresh agents for discovery, grilling, research, decomposition, contract drafting, and independent review. It records durable evidence and returns a contract containing the spec identity, full baseline SHA, exact allowed paths, acceptance criteria, positive and negative tests, artifacts, and exclusions.

Preparation never edits product code and never runs BUILD, TEST, or VERIFY. Review the exact contract and explicitly approve it before continuing.

### 3. Create Intent

```python
from control.models.store import StageCStore
from pathlib import Path

root = Path.cwd()
store = StageCStore(root)

# Create draft
store.create_intent_draft(
    {
        "intent_id": "I-001",
        "project_id": "oak-harbor-marina",
        "version": 1,
        "description": "Build a boat listing feature",
        "requirements": [
            "Display available boats",
            "Filter by boat type",
            "Show pricing"
        ]
    },
    event_id="intent-created",
    timestamp="2026-09-21T00:00:00Z",
    actor_type="human",
    actor_id="human"
)

# Human must approve (do this in Prime or manually)
store.approve_intent(
    "I-001", 1,
    event_id="intent-approved",
    timestamp="2026-09-21T00:01:00Z",
    actor_type="human",
    actor_id="human"
)
```

### 4. Propose Graph

```python
from control.operational import OperationalController

controller = OperationalController(root)

graph = {
    "graph_id": "G-001",
    "project_id": "oak-harbor-marina",
    "intent_id": "I-001",
    "version": 1,
    "nodes": [
        {
            "eu_id": "EU-001",
            "description": "Implement boat listing model",
            "dependencies": []
        }
    ],
    "edges": []
}

controller.propose_plan(
    operation_id="OP-001",
    project_id="oak-harbor-marina",
    graph=graph,
    eu_paths={"EU-001": ["src/listing.py", "tests/test_listing.py"]},
    timestamp="2026-09-21T00:02:00Z",
    event_prefix="op"
)
```

### 5. Execute EU

```python
from control.operational import PrimeBuilderAdapter

adapter = PrimeBuilderAdapter(
    model="openai-codex/gpt-5.6-luna",
    timeout_seconds=1800
)

result = controller.run_eu(
    "OP-001",
    eu_id="EU-001",
    builder=adapter,
    spec_command="python -m pytest tests/test_listing.py -q",
    standards_command="python -m pytest tests/test_listing.py -q",
    timestamp="2026-09-21T00:03:00Z",
    event_prefix="op"
)

print(f"Status: {result['status']}")
# Expected: VERIFIED
```

### 6. Review Evidence

```bash
# Check the proof
ls -la .idd/attestations/
cat .idd/state/events.head.json
```

## Troubleshooting

### prime-agent not found

```bash
# Check PATH
which prime-agent

# Reinstall
pip install --upgrade prime-agent
```

### /itdd-new not recognized

Ensure the skill is installed:
```bash
ls -la ~/.agents/skills/itdd-new/
# Should contain SKILL.md and __init__.py
```

### Tests fail

```bash
# Clean and reinstall
pip uninstall itdd-control-plane
pip install -e ".[dev]"
pytest -q --tb=short
```

### Git commit fails

```bash
# Configure git
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Next Steps

1. **Read the full [Usage Guide](../../agents/itdd-in-prime-usage.md)**
2. **Understand the [Operational Lifecycle](../../architecture/operational-lifecycle.md)**
3. **Review [Architectural Decisions](../../adr/)**
4. **Join the community** on GitHub Discussions

## Getting Help

- **Documentation**: Browse `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/itdd-control-plane/itdd-control-plane/issues)
- **Discussions**: [GitHub Discussions](https://github.com/itdd-control-plane/itdd-control-plane/discussions)

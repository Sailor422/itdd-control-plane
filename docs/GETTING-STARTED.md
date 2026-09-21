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

### Initialize with ITDD

In the Prime prompt:
```
/itdd-new
```

This creates:
- `.idd/` directory structure (ITDD state)
- `docs/agents/` (engineering skills config)
- `CONTEXT.md` (domain glossary template)
- `src/` and `tests/` directories
- `skills/manifest.json` (project-local skills)
- Initial git commit

### Verify Setup

```bash
# Check structure
tree -L 2 -I '.git'
# Should show:
# .idd/
# docs/
#   agents/
#   adr/
# src/
# tests/
# AGENTS.md
# CONTEXT.md
# skills/manifest.json
```

## Your First Execution Unit

### 1. Clarify Requirements

In Prime:
```
/grill-with-docs
```

This starts a clarification session to understand your requirements.

### 2. Create Intent

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

### 3. Propose Graph

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

### 4. Execute EU

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

### 5. Review Evidence

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

1. **Read the full [Usage Guide](agents/itdd-in-prime-usage.md)**
2. **Understand the [Operational Lifecycle](architecture/operational-lifecycle.md)**
3. **Review [Architectural Decisions](adr/)**
4. **Join the community** on GitHub Discussions

## Getting Help

- **Documentation**: Browse `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/itdd-control-plane/itdd-control-plane/issues)
- **Discussions**: [GitHub Discussions](https://github.com/itdd-control-plane/itdd-control-plane/discussions)

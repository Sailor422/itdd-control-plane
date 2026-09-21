# ITDD in Prime — Complete Usage Guide

**Date:** 2026-09-21  
**Status:** Validated by `prime-single-eu-20260921T034058Z-clean4` proof

## Architecture Summary

ITDD control plane supports **arbitrary external project roots**:

- `OperationalController` accepts any `Path` as `project_root` parameter
- No hardcoded paths — projects live in `~/Projects/`, not inside `itdd-control-plane`
- All `.idd/` state travels with the project
- Control plane is a library imported into your project

## New Project Initialization

### Two-Step Initialization

**Important:** Matt Pocock engineering skills require per-repo setup BEFORE ITDD initialization.

```bash
cd ~/Projects/oak-harbor-marina
prime-agent
/setup-matt-pocock-skills   # REQUIRED FIRST - configures issue tracker, labels, domain docs
/itdd-new                   # Creates ITDD infrastructure
```

**Why this order?**
- `/setup-matt-pocock-skills` is **user-invoked and interactive** (by design)
- It inspects your repo and asks about issue tracking, labels, and docs layout
- It writes repo-specific config under `docs/agents/` and `AGENTS.md`
- `/itdd-new` checks for this config and **will fail** if not found
- There is no global substitute - every repo needs its own setup

**What each does:**
1. `/setup-matt-pocock-skills`:
   - Configures issue tracker (GitHub/GitLab/local)
   - Sets triage label vocabulary
   - Defines domain docs layout
   - Creates `AGENTS.md` with agent skills block

2. `/itdd-new`:
   - Creates `.idd/` infrastructure
   - Adds project scaffolding (`src/`, `tests/`, `CONTEXT.md`)
   - Initializes git and creates initial commit

This single command creates:

1. **Matt Pocock engineering skills config:**
   - `docs/agents/issue-tracker.md` (GitHub Issues)
   - `docs/agents/triage-labels.md` (canonical labels)
   - `docs/agents/domain.md` (single-context layout)
   - `AGENTS.md` (agent instruction block)

2. **ITDD authoritative state:**
   - Complete `.idd/` directory structure
   - Intent, graph, capabilities, evidence, verifiers, human decisions, operations, attestations, state, views, build_workspaces

3. **Project scaffolding:**
   - `CONTEXT.md` (domain glossary template)
   - `docs/adr/` (architectural decisions)
   - `src/`, `tests/`
   - `skills/manifest.json` (project-local ITDD skills)
   - `.gitignore`

4. **Git repository:**
   - Initializes git if needed
   - Creates initial commit: "ITDD infrastructure initialized"

### Existing Projects

For projects that already exist (have `.idd/` or other content):

```bash
cd ~/Projects/existing-project
prime-agent
/setup-matt-pocock-skills
```

This adds the engineering skills configuration without recreating ITDD infrastructure.

## Post-Initialization Workflow

### Preparation to execution handoff

Preparation and execution are separate control-plane stages:

1. `/itdd-prepare` runs DISCOVERY and GRILLING first. If no immutable source exists, GRILLING forms a clarification frontier, asks the human, records the answers, and waits for the human to explicitly designate the immutable spec/ticket/intent. It stops when that designation is missing; it never self-approves intent.
2. After research, decomposition, drafting, and independent review, the human explicitly approves the exact execution contract. Preparation evidence is retained under `.idd/preparation/<preparation-id>/`.
3. Enter the approved contract through the `/idd` top-level directive. `/idd` starts the formal execution workflow; do not invoke BUILD, TEST, or VERIFY as an ordinary working-tree task.
4. `/idd` runs BUILD, TEST, and VERIFY in separate fresh executions in the project `.idd/build_workspaces/` boundary. Preparation evidence is read-only input, not an execution workspace. The ordinary working tree is never used for these roles.
5. Preserve role identities, commands, outputs, and acceptance evidence. Only the controlling workflow may advance lifecycle state after independent VERIFY passes.

See [itdd-preparation-execution-handoff.md](itdd-preparation-execution-handoff.md) for the compact handoff and evidence checklist.

### 1. Domain Clarification

```bash
/grill-with-docs
```

- Clarifies domain language, assumptions, and open questions
- Produces clarification proposals (not approvals)
- Runs in `human` role only

### 2. Intent Creation and Approval

```python
from control.models.store import StageCStore
from pathlib import Path

root = Path("/Users/herbertfields/Projects/oak-harbor-marina")
store = StageCStore(root)

# Create draft intent
store.create_intent_draft(
    {
        "intent_id": "I-001",
        "project_id": "oak-harbor-marina",
        "description": "Build marina booking system",
        # ... intent details
    },
    event_id="intent-created",
    timestamp="2026-09-21T00:00:00Z",
    actor_type="human",
    actor_id="human"
)

# Human must approve (cannot be automated)
store.approve_intent(
    "I-001", 1,
    event_id="intent-approved",
    timestamp="2026-09-21T00:01:00Z",
    actor_type="human",
    actor_id="human"
)
```

### 3. Graph Proposal and Evaluation

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
            "description": "Implement boat listing feature",
            "dependencies": []
        },
        # ... more EUs
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

### 4. EU Execution with Prime Builder

```python
from control.operational import PrimeBuilderAdapter

adapter = PrimeBuilderAdapter(
    model="openai-codex/gpt-5.6-luna",  # or your preferred model
    timeout_seconds=1800
)

result = controller.run_eu(
    "OP-001",
    eu_id="EU-001",
    builder=adapter,
    spec_command="python -m pytest tests/test_listing.py",
    standards_command="python -m pytest tests/test_listing.py",
    timestamp="2026-09-21T00:03:00Z",
    event_prefix="op"
)

assert result["status"] == "VERIFIED"
```

### 5. Evidence Preservation

After each EU, the controller preserves:

- `controller-result.json` — lifecycle state
- `candidate-identity.json` — frozen commit/tree
- `runtime-provenance.json` — Prime CLI, hashes, exit code
- `independent-verification.json` — spec/standards/event checks
- `events.json` — append-only audit trail
- `final-status.txt` — candidate cleanliness

On failure: `FAILURE.md` is created and the attempt is preserved immutably.

## Project Structure

```text
~/Projects/oak-harbor-marina/
├── .git/
├── .idd/                          # ITDD authoritative state
│   ├── intent/I-001/v1.json
│   ├── graph/G-001/v1.json
│   ├── capabilities/CAP-*/v1.json
│   ├── context/packets/CP-*/
│   ├── evidence/contracts/VC-*.json
│   ├── evidence/records/EV-*.json
│   ├── verifiers/executions/EXEC-*.json
│   ├── human_decisions/registry/HD-*.json
│   ├── human_decisions/pending/HD-*.md
│   ├── operations/OP-*.json
│   ├── attestations/AT-*.json
│   ├── state/events.head.json
│   ├── state/events.jsonl
│   ├── views/*.md
│   └── build_workspaces/          # isolated EU worktrees
├── docs/
│   ├── adr/                       # architectural decision records
│   └── agents/                    # engineering skills config
│       ├── issue-tracker.md
│       ├── triage-labels.md
│       └── domain.md
├── skills/
│   └── manifest.json              # project-local ITDD skills
├── src/                           # source code
├── tests/                         # tests
├── AGENTS.md                      # agent instructions
├── CONTEXT.md                     # domain glossary
└── .gitignore
```

## Critical Boundaries

### What Prime Can Do

- Implement code within EU scope
- Run tests and standards checks
- Leave filesystem changes only in the assigned isolated workspace (never the ordinary working tree or preparation evidence)
- Propose clarifications (via `/grill-with-docs`)

### What Controller Owns

- Worktree creation and isolation under the project `.idd/build_workspaces/` boundary
- Git diff validation
- Candidate commit creation
- State transitions (lifecycle)
- Promotion decisions
- Independent verification
- Evidence preservation

### What Prime Cannot Do

- Commit directly
- Promote to production
- Approve intents or graphs
- Modify `.idd/` state directly
- Escape project boundaries

## Usage Constraints

1. **No parallel EUs until proven** — Run single-EU proofs first for your project
2. **Fail-fast hygiene** — Preserve FAIL evidence immutably; new attempt for each retry
3. **No bytecode contamination** — Use `PYTHONDONTWRITEBYTECODE=1` for verification
4. **Prime flags required** — Always use `--no-session --no-skills --no-context-files`
5. **Independent verification mandatory** — Fresh spec/standards checks per EU

## Reference Evidence

Clean single-EU proof: `work/proofs/prime-single-eu-20260921T034058Z-clean4/`

Contains:
- `PASS.md` — all checks passed
- `candidate-identity.json` — controller-owned commit
- `controller-result.json` — status VERIFIED
- `independent-verification.json` — all probes exit 0
- `runtime-provenance.json` — Prime CLI with SHA-256 hashes
- `final-status.txt` — clean candidate (empty git status)

## Troubleshooting

### Skill not found: `/itdd-new`

Ensure the skill is installed:
```bash
ls -la ~/.agents/skills/itdd-new/
```

Should contain:
- `SKILL.md`
- `__init__.py`

### .idd already exists

The skill refuses to run if `.idd/` is present. For existing projects:
```bash
/setup-matt-pocock-skills
```

### Git commit fails

Ensure you have git configured:
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Prime binary not found

Install prime-agent:
```bash
brew install prime-agent  # or your installation method
which prime-agent
```

Expected: `/opt/homebrew/bin/prime-agent`

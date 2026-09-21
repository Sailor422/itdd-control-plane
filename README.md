# ITDD Control Plane

> **⚠️ Work in Progress — Research Prototype**
> 
> This is an active research implementation focused on Prime Agent integration.
> The architecture is stable for experimentation, but APIs and workflows may change.
> Use for learning, evaluation, and contribution — not for production systems.

**Intent-Driven Development with Independent Verification**

ITDD Control Plane implements an architecture for reliable AI-assisted software engineering. It enforces role separation between human authority, agent reasoning, and controller-owned lifecycle operations.

## Attribution

This project implements:

- **Prof Matt Pocock's AI-Assisted Engineering methodology** — Engineering skills, issue tracking workflow, and domain documentation patterns. See [`@total-typescript`](https://github.com/total-typescript) and his AI engineering talks.

- **Intent-Driven Development (IDD) research** — Human-intent-first development with AI execution, controller-owned lifecycle, and independent verification.

- **Prime Agent** — Current implementation is tightly integrated with Prime Agent as the execution harness. The architecture is designed to be harness-neutral, but Prime is the only supported backend at this time.

## Quick Start

### Prerequisites

- Python 3.10+
- [prime-agent](https://github.com/prime-agent/prime-agent) v0.9.5+ (or compatible harness)
- Git

### Initialize a New Project

**Important:** Matt Pocock engineering skills require per-repo setup. Run `/setup-matt-pocock-skills` **before** `/itdd-new`.

```bash
# Create your project directory
cd ~/Projects
mkdir oak-harbor-marina
cd oak-harbor-marina

# Start Prime
prime-agent

# Step 1: Configure Matt Pocock engineering skills (REQUIRED FIRST)
/setup-matt-pocock-skills

# Step 2: Initialize ITDD infrastructure
/itdd-new
```

The setup skill configures:
- Issue tracker (GitHub/GitLab/local markdown)
- Triage label vocabulary
- Domain docs layout
- `AGENTS.md` or `CLAUDE.md` with agent skills block

Then `/itdd-new` creates:
- Complete ITDD infrastructure (`.idd/`)
- Project scaffolding (`src/`, `tests/`, `CONTEXT.md`, `docs/adr/`)
- Initial git commit

This creates:
- Complete ITDD infrastructure (`.idd/`)
- Matt Pocock engineering skills configuration
- Project scaffolding (`src/`, `tests/`, `CONTEXT.md`, `docs/adr/`)
- Initial git commit

### Workflow

1. **Review generated config**: Check `docs/agents/*.md` and `AGENTS.md`
2. **Edit CONTEXT.md**: Add your domain glossary and project identity
3. **Clarify requirements**: `/grill-with-docs`
4. **Create and approve intent**: Human decision (immutable)
5. **Propose execution graph**: Planner agent
6. **Run EUs**: `PrimeBuilderAdapter` with independent verification
7. **Review and promote**: Human gate

See [Usage Guide](docs/agents/itdd-in-prime-usage.md) for complete workflow.

## Architecture

### Core Principles

1. **Human authority**: Humans approve intents (the authoritative starting point)
2. **Controller-owned lifecycle**: Agents reason; controller owns lifecycle operations
3. **Independent verification**: Fresh spec/standards checks per EU (not self-certification)
4. **Evidence-backed**: Every operation produces immutable, auditable records
5. **Framework-neutral**: Works with Prime today; other harnesses can implement the ITDD contract

**Note**: Once an intent is approved, the controller can execute graphs and EUs without requiring human approval for each step. Human gates are for intent approval and promotion decisions, not routine EU execution.

### Components

```
itdd-control-plane/
├── control/           # Controller implementation
│   ├── operational.py # OperationalController, PrimeBuilderAdapter
│   ├── models/        # Stage-C store, event log
│   ├── verifier.py    # Independent verification orchestrator
│   └── human.py       # Human gate controller
├── skills/            # ITDD skills (grill-with-docs, etc.)
├── schemas/           # JSON schemas for events and state
├── docs/
│   ├── agents/        # Usage guides (Prime integration)
│   ├── architecture/  # System design
│   ├── specs/         # Formal specifications
│   └── adr/           # Architectural decisions
├── tests/             # Integration and end-to-end tests
└── examples/          # Reference implementations
```

### Operational Lifecycle

```
Human Intent Discussion
         ↓
   /grill-with-docs (clarification proposal)
         ↓
   Human approves intent (immutable, I-001) [HUMAN GATE]
         ↓
   Planner proposes graph (G-001)
         ↓
   Graph Evaluator validates
         ↓
   Controller spawns EU with PrimeBuilderAdapter
         ↓
   Prime worker implements in isolated worktree
         ↓
   Controller validates diff, creates candidate commit
         ↓
   Fresh Spec Verifier + Standards Reviewer (independent)
         ↓
   Both PASS → status VERIFIED
         ↓
   [Optional: Human promotion gate if configured]
```

See [Operational Lifecycle](docs/architecture/operational-lifecycle.md) for details.

## Proof of Correctness

The single-EU lifecycle is **proven** with immutable evidence:

```bash
work/proofs/prime-single-eu-20260921T034058Z-clean4/
├── PASS.md                      # All checks passed
├── candidate-identity.json      # Controller-owned commit
├── controller-result.json       # Status: VERIFIED
├── independent-verification.json # All probes exit 0
├── runtime-provenance.json      # Prime CLI with SHA-256 hashes
└── final-status.txt             # Clean candidate (empty git status)
```

**Key invariants verified:**
- Real `prime-agent` binary via `PrimeBuilderAdapter`
- Controller-owned candidate commit (not Prime)
- Independent spec/standards checks (not self-certification)
- Clean worktree (no contamination)
- Immutable evidence preserved

## Harness Integration

### Prime Agent (Implemented)

```python
from control.operational import OperationalController, PrimeBuilderAdapter

controller = OperationalController("/path/to/project")
adapter = PrimeBuilderAdapter(model="openai-codex/gpt-5.6-luna", timeout_seconds=1800)

result = controller.run_eu(
    "OP-001",
    eu_id="EU-001",
    builder=adapter,
    spec_command="python -m pytest tests/test_feature.py",
    standards_command="python -m pytest tests/test_feature.py",
    timestamp="2026-09-21T00:00:00Z",
    event_prefix="op"
)
```

### Building Your Own Harness

ITDD is harness-neutral. To integrate a different agent runtime:

1. Implement the builder interface:
   ```python
   class MyBuilderAdapter:
       def run(self, *, project_root, worktree, execution_id, 
               context_packet, capability):
           # Launch your agent in worktree
           # Return: {candidate_commit, stdout, stderr, runtime_provenance}
           pass
   ```

2. Use with controller:
   ```python
   result = controller.run_eu("OP-001", "EU-001", MyBuilderAdapter(), ...)
   ```

See [Executable Skills Baseline V1](docs/specs/EXECUTABLE-SKILLS-BASELINE-V1.md) for the full contract.

## Installation

### From Source

```bash
git clone https://github.com/<your-org>/itdd-control-plane.git
cd itdd-control-plane
pip install -e .
```

### Dependencies

- Python 3.10+
- pytest (for verification)
- Git

### Prime Agent Installation

```bash
# macOS
brew install prime-agent

# Or from source
pip install prime-agent
```

Verify:
```bash
prime-agent --version
# Expected: 0.9.5+
```

## Testing

```bash
# Run all tests
pytest -q

# Integration tests only
pytest -q tests/integration/

# End-to-end tests
pytest -q tests/end_to_end/

# Specific test
pytest -q tests/integration/test_prime_builder_adapter.py
```

Current status: **156 tests passed**

## Documentation

- **[Usage Guide](docs/agents/itdd-in-prime-usage.md)** - Complete workflow for Prime users
- **[Operational Lifecycle](docs/architecture/operational-lifecycle.md)** - How EUs execute
- **[Control Plane Spec](docs/specs/CONTROL-PLANE-SPEC.md)** - Formal specification
- **[Bootstrap Handoff](docs/specs/CODEX-BOOTSTRAP-SPEC.md)** - Initial implementation plan
- **[Architectural Decisions](docs/adr/)** - Design rationale

## Repository Map

| Directory | Purpose |
|-----------|---------|
| `control/` | Controller implementation (operational, verifier, human gates) |
| `skills/` | ITDD skills (grill-with-docs, runtime execution) |
| `schemas/` | JSON schemas for events, state, and contracts |
| `tests/` | Unit, integration, and end-to-end tests |
| `examples/` | Reference implementations and demos |
| `docs/agents/` | Prime integration guides |
| `docs/architecture/` | System design documents |
| `docs/specs/` | Formal specifications |
| `docs/adr/` | Architectural decision records |
| `work/proofs/` | Immutable evidence from lifecycle executions |

## Safety Boundaries

- **No direct commits from agents**: Controller owns all git operations
- **No self-certification**: Independent verification required per EU
- **No lifecycle authority for agents**: Humans approve intents, graphs, promotions
- **No filesystem escape**: Work confined to project boundaries
- **Immutable evidence**: Failed attempts preserved with `FAILURE.md`

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest -q`
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Status

- ✅ Single-EU lifecycle (proven)
- ✅ Independent verification
- ✅ Human gate controller
- ✅ Evidence preservation
- ✅ Prime integration
- 🚧 Multi-EU parallel execution (planned)
- 🚧 Additional harness integrations (planned)

See [ROADMAP.md](ROADMAP.md) for upcoming work.

## Contact

- Issues: Use GitHub Issues (configured via `/setup-matt-pocock-skills`)
- Discussions: GitHub Discussions
- Security: See [SECURITY.md](SECURITY.md)

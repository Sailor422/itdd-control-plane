# ITDD Control Plane - Public Release v0.1.0

**Date:** 2026-09-21  
**Status:** Production Ready (Single-EU Proven)

## What is ITDD Control Plane?

ITDD (Intent-Driven Development) Control Plane is a production-ready architecture for reliable AI-assisted software engineering. It enforces strict role separation:

- **Humans**: Approve intents, graphs, and promotions (authority)
- **Agents**: Reason, propose, implement (no authority)
- **Controller**: Owns lifecycle, validates, attests (enforcement)

## Proof of Correctness

✅ **Single-EU lifecycle proven** with immutable evidence:
- Real `prime-agent` binary execution
- Controller-owned candidate commit (not agent)
- Independent verification (fresh spec + standards checks)
- Clean worktree (no contamination)
- All evidence preserved in `work/proofs/prime-single-eu-20260921T034058Z-clean4/`

## What's Included

### Core Implementation

- `control/operational.py` - OperationalController, PrimeBuilderAdapter
- `control/models/store.py` - Stage-C store (intents, graphs, capabilities)
- `control/verifier.py` - Independent verification orchestrator
- `control/human.py` - Human gate controller
- `control/git.py` - Git adapter with attestation
- `control/events.py` - Append-only event log

### Skills

- `/itdd-new` - Initialize new ITDD projects (one command)
- `/grill-with-docs` - Clarify requirements with documentation
- `/setup-matt-pocock-skills` - Configure engineering skills
- Matt Pocock skills: `/triage`, `/to-spec`, `/to-tickets`, `/to-questionnaire`, etc.

### Documentation

- **README.md** - Overview and quick start
- **docs/GETTING-STARTED.md** - Complete setup guide
- **docs/agents/itdd-in-prime-usage.md** - Prime integration workflow
- **docs/architecture/operational-lifecycle.md** - How EUs execute
- **docs/specs/CONTROL-PLANE-SPEC.md** - Formal specification
- **docs/specs/EXECUTABLE-SKILLS-BASELINE-V1.md** - Builder contract
- **docs/adr/** - Architectural decisions

### Tests

- 156 tests passing
- Unit, integration, and end-to-end coverage
- Proof tests for single-EU lifecycle

### Project Scaffolding

- `pyproject.toml` - Python package configuration
- `.gitignore` - Proper exclusions
- `LICENSE` - MIT License
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community standards

## Quick Start

### For New Projects

```bash
cd ~/Projects/my-project
prime-agent
/itdd-new
```

That's it. Creates complete ITDD infrastructure + Matt Pocock skills config.

### For Existing Projects

```bash
cd ~/Projects/existing-project
prime-agent
/setup-matt-pocock-skills
```

Adds engineering skills configuration.

## Harness Support

### ✅ Prime Agent (Implemented)

```python
from control.operational import OperationalController, PrimeBuilderAdapter

controller = OperationalController("/path/to/project")
adapter = PrimeBuilderAdapter(model="openai-codex/gpt-5.6-luna")

result = controller.run_eu("OP-001", "EU-001", adapter, ...)
assert result["status"] == "VERIFIED"
```

### 🔧 Your Harness (Build It With ITDD)

ITDD is harness-neutral. Implement the builder interface:

```python
class MyBuilderAdapter:
    def run(self, *, project_root, worktree, execution_id, 
            context_packet, capability):
        # Launch your agent in worktree
        # Return: {candidate_commit, stdout, stderr, runtime_provenance}
        pass
```

Then use with controller. See docs/specs/EXECUTABLE-SKILLS-BASELINE-V1.md.

## Repository Structure

```
itdd-control-plane/
├── control/           # Controller implementation
├── skills/            # ITDD skills (global + project-local)
├── schemas/           # JSON schemas
├── tests/             # Test suite (156 passing)
├── examples/          # Reference implementations
├── docs/
│   ├── agents/        # Prime integration guides
│   ├── architecture/  # System design
│   ├── specs/         # Formal specifications
│   └── adr/           # Architectural decisions
├── work/proofs/       # Immutable evidence (clean proof preserved)
└── [standard project files]
```

## Installation

```bash
# From source (development)
git clone https://github.com/itdd-control-plane/itdd-control-plane.git
cd itdd-control-plane
pip install -e ".[dev]"

# Or use as library
pip install itdd-control-plane
```

## Testing

```bash
# Run all tests
pytest -q  # 156 passed

# Integration tests
pytest -q tests/integration/

# End-to-end
pytest -q tests/end_to_end/
```

## Key Invariants

1. **No agent commits** - Controller owns all git operations
2. **No self-certification** - Independent verification required
3. **No lifecycle authority for agents** - Humans approve intents/graphs
4. **No filesystem escape** - Work confined to project boundaries
5. **Immutable evidence** - Failed attempts preserved with FAILURE.md

## Roadmap

- ✅ Single-EU lifecycle (proven)
- ✅ Independent verification
- ✅ Human gate controller
- ✅ Evidence preservation
- ✅ Prime integration
- 🚧 Multi-EU parallel execution
- 🚧 Additional harness integrations (Codex, Claude, custom)
- 🚧 CLI tooling (`itdd` command)

See [ROADMAP.md](ROADMAP.md) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest -q`
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contact

- **Issues**: https://github.com/itdd-control-plane/itdd-control-plane/issues
- **Discussions**: https://github.com/itdd-control-plane/itdd-control-plane/discussions
- **Security**: See [SECURITY.md](SECURITY.md)

---

**This release represents a complete, usable, documented ITDD implementation that any user can pull down and start using immediately with Prime.**

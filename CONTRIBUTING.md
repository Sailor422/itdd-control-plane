# Contributing to ITDD Control Plane

Thank you for contributing to ITDD Control Plane! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/itdd-control-plane.git`
3. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`
4. Install dependencies: `pip install -e ".[dev]"`
5. Create a branch: `git checkout -b feature/your-feature`

## Development Workflow

### ITDD Principles

This project uses ITDD itself:

- **Intents**: Major changes start with an approved intent (`.idd/intent/`)
- **Graphs**: Execution plans are explicit and approved
- **Independent verification**: All code must pass tests (not self-certification)
- **Evidence**: PRs should reference test results and proofs

### Testing

```bash
# Run all tests
pytest -q

# Run with coverage
pytest -q --cov=control --cov=skills

# Run specific test file
pytest -q tests/integration/test_prime_builder_adapter.py

# Run end-to-end tests
pytest -q tests/end_to_end/
```

### Code Style

```bash
# Format code
black .

# Lint
ruff check .

# Type checking (if using mypy)
mypy control/ skills/
```

## Pull Request Process

1. **Ensure tests pass**: `pytest -q` must show all green
2. **Update documentation**: If behavior changes, update relevant docs
3. **Add tests**: New features need test coverage
4. **Reference issues**: Link to related GitHub issues
5. **Describe changes**: Clear PR description with before/after

## Architecture Decisions

Major architectural changes require an ADR:

1. Copy `docs/adr/0000-template.md`
2. Fill in context, decision, consequences
3. Submit as part of your PR
4. Number sequentially (0001, 0002, etc.)

## Harness Integration

Adding support for a new agent harness:

1. Read [Executable Skills Baseline V1](docs/specs/EXECUTABLE-SKILLS-BASELINE-V1.md)
2. Implement the builder interface in `control/operational.py`
3. Add tests in `tests/integration/`
4. Document in `docs/agents/`
5. Create a proof in `work/proofs/`

## Questions?

- Open an issue for bugs or feature requests
- Use GitHub Discussions for questions
- Check existing [documentation](docs/)

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

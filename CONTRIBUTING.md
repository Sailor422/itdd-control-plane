# Contributing to ITDD Control Plane

Thank you for considering a contribution. This repository is public, but the product is in development, unreleased, and not currently in use. The active product direction is the planning-first handoff described in the [README](README.md); controller execution material is experimental research.

## First step: collect source data

Before proposing a change, inspect the relevant code, tests, documentation, issue-tracker decisions, and existing research/evidence. Record the baseline, source links, and unknowns. Do not infer current behavior from an old report or treat a historical PASS as product acceptance. The [archive source inventory](docs/archive/SOURCE-INVENTORY.md) describes known research, reports, logs, and review limits.

Preserve existing worktrees, evidence, failed attempts, and uncommitted user files. Do not bulk-add `.idd` runtime data, raw logs, or scratch outputs. The repository is public, so anything committed is public.

## Planning and changes

1. Read the [planning-first Getting Started guide](docs/GETTING-STARTED.md).
2. For uncertain or multi-step work, discuss the scope and publish a spec and human-agreed tickets through the configured tracker.
3. Keep planning separate from implementation. A ticket label or planning agreement is not execution authorization.
4. For a code change, add or update focused tests and preserve the exact test result. For documentation changes, check links and project-specific contract tests.
5. Clearly label research, drafts, local observations, and historical evidence. Do not claim a release, production use, or formal approval unless it has actually happened and is supported by evidence.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Pull requests

- Link the issue or decision that motivated the change.
- Summarize the source facts collected and any unresolved uncertainty.
- List changed paths and the checks actually run.
- Keep unrelated user changes, evidence, and worktrees untouched.

## Research and design

See the [contributor archive](docs/archive/README.md), [research notes](docs/research/README.md), [architecture notes](docs/architecture/README.md), and [ADRs](docs/adr/). These may describe broader prototype work and are not automatically current product behavior.

## Community

Open an issue for questions or proposed work. Read the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

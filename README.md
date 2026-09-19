# ITDD Control Plane

ITDD Control Plane is an experimental architecture for reliable AI-assisted software engineering. It combines Intent-Driven Development, Test-Driven Development, lean context and knowledge management, deterministic lifecycle control, independent verification, human decision gates, and evidence-backed promotion.

> **Agents reason. The controller decides what actions are legal.**

The project separates durable authority from disposable reasoning workers. Approved human intent is authoritative; execution plans may evolve through controlled, auditable replanning. Workers receive resolved, role-specific context and capabilities, and lifecycle state advances only through controller-authorized operations with bound evidence.

ITDD is intended to remain framework- and agent-runtime-neutral. Prime is one target runtime, not the definition of ITDD. Codex is currently the development agent being brought under control. The architecture is experimental: implemented behavior, research evidence, and proposed designs are labeled separately, and unfinished systems are not presented as proven.

## Repository map

- `thesis/` contains the supplied research/design thesis in DOCX, PDF, and Markdown form.
- `docs/specs/` contains the complete bootstrap handoff and the stable control-plane specification.
- `docs/architecture/` contains focused architecture documents.
- `control/`, `schemas/`, `tests/`, and `examples/` are reserved for staged implementation.
- `.idd/` is the future project-local authority domain; private runtime records are ignored until their schemas exist.

## Current status

This repository is at bootstrap / Stage A audit only. No control-plane implementation has started. See [ROADMAP.md](ROADMAP.md) and [docs/research/stage-a-codex-audit.md](docs/research/stage-a-codex-audit.md).

## Safety boundary

Legacy Codex, Claude, Hermes, and other knowledge stores are read-only source archives. Nothing from them is part of default project context, and no vault migration is authorized by this baseline.

## License

The repository is released under the MIT License. See [LICENSE](LICENSE).


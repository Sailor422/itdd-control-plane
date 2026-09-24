# ITDD Control Plane

> **In development · Unreleased · Not currently in use**
>
> This is a research prototype. It has not been released for use. APIs, skills, and workflows may change. Do not treat historical test evidence as proof that the product is production-ready.

ITDD Control Plane explores a small, human-invoked planning workflow: clarify a request, collect and verify relevant project data, publish a spec and human-agreed tickets through the configured issue tracker, then stop with links and a suggested next move.

## Current path

For a new or existing repository:

1. **Collect facts first.** Inspect the current code, docs, tracker, prior decisions, and relevant research or evidence. Record sources and unknowns. Do not turn unverified history into current requirements.
2. If the repository lacks project-specific Matt Pocock skill configuration, run `/setup-matt-pocock-skills` to configure the tracker, triage labels, and domain docs.
3. Run `/itdd-prepare` to clarify the request and prepare the planning handoff.
4. Agree on the spec and ticket breakdown. Publish them through the configured tracker.
5. Stop with the links, unresolved questions, and suggested next move. A `ready-for-agent` label or planning agreement does not authorize execution.

See [Getting Started](docs/GETTING-STARTED.md) and the [Prime planning guide](docs/agents/itdd-in-prime-usage.md).

`/itdd-new` is optional later-stage execution setup. It is not required for planning. The current planning path does not invoke BUILD, TEST, VERIFY, or the controller runtime.

## Project status and limits

- The product is in development, unreleased, and not in use.
- The planning-first workflow is the current product direction. The controller, schemas, broader skill manifest, and execution architecture are research/prototype material, not a supported production service.
- This repository contains historical reports, experiments, and evidence. Their status applies only to the specific dated work they describe; it does not establish a product release or current acceptance.
- No formal approval record should be claimed unless a supported controller interface actually records it.

## Development

This checkout is for contributors and research. It is not a published package installation guide.
The commands below install this source checkout for local development and tests; they do not indicate a published distribution or supported end-user installation.

```bash
git clone https://github.com/Sailor422/itdd-control-plane.git
cd itdd-control-plane
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
```

See [Contributing](CONTRIBUTING.md) for the development workflow. **Collect source data before proposing changes**; keep evidence and failed attempts intact, and clearly label drafts, historical reports, and unverified claims.

## Research and design

- [Contributor archive and source inventory](docs/archive/README.md) — curated research, historical guides, and evidence pointers.
- [Research notes](docs/research/README.md) — dated research, not normative policy.
- [Architecture notes](docs/architecture/README.md) and [ADRs](docs/adr/) — broader prototype design; not the current planning quick start.
- [Planning-first Wayfinder map](https://github.com/Sailor422/itdd-control-plane/issues/34) — product decisions and follow-up work.

## License

MIT. See [LICENSE](LICENSE).

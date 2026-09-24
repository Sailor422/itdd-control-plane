# Getting Started

> **In development · Unreleased · Not currently in use.** This guide describes the current planning-first product direction, not a released or production-ready system.

This project is being developed as a human-invoked, skill-first planning workflow. It clarifies a request, publishes a spec and human-agreed tickets through the configured issue tracker, and then stops. It does not start implementation.

## Before planning: collect the data

Data collection is the first job. Before proposing a solution or writing a spec, inspect the target repository and gather relevant facts from its code, documentation, issue tracker, existing decisions, research, and test/evidence records. Record where facts came from and mark unknown or unverified claims. Do not assume a historical report describes the current repository.

## Set up the planning skills

For a new or existing repository, first check whether its `AGENTS.md` (or `CLAUDE.md`) already configures:

- the issue tracker;
- the triage-label vocabulary; and
- the domain-documentation layout.

If any setup is missing, run the human-invoked `/setup-matt-pocock-skills` skill in the target repository. It asks about those project-specific choices and writes the required configuration. Do not change its defaults or skip needed setup by guessing.

If the configuration is already present, keep it and continue. Do not rerun setup just to use the planning workflow.

## Prepare and publish the handoff

In Prime, run `/itdd-prepare` in the target repository. It uses the configured skills to clarify the request, collect any remaining facts, and prepare a spec and ticket breakdown for human agreement.

The planning handoff is complete when the human has agreed to the spec and ticket breakdown and they are published to the configured tracker. Return the links, unresolved questions, and a suggested next move. Then stop.

A `ready-for-agent` label, ticket agreement, or planning handoff is not execution authorization. This workflow does not run BUILD, TEST, or VERIFY.

## Optional later-stage setup

`/itdd-new` initializes the broader ITDD runtime and execution scaffold. It is optional and separate from the planning-only path. Use it only when a later, explicit request calls for that execution setup and the applicable gates are understood.

## Contributing

The repository is public and under active development, but it has not been released or put into use. Start with the [contributor guide](../CONTRIBUTING.md) and [archive source inventory](archive/SOURCE-INVENTORY.md). Preserve existing evidence and worktrees; do not bulk-publish raw runtime, audit, or telemetry data.

For current Prime usage, see [ITDD in Prime](agents/itdd-in-prime-usage.md). For historical execution-era guidance, see the [archive index](archive/README.md).

# ITDD Planning in Prime

> **In development · Unreleased · Not currently in use.** This guide covers the current planning-first workflow. It is not a product release or production-use statement.

## Collect data first

Before framing a request, inspect the target repository, its issue tracker, setup/domain docs, relevant code, prior decisions, research, and evidence. Cite sources and separate verified facts from assumptions or unknowns. This source collection is the first job; do not infer current behavior from an old report alone.

## Planning path for new and existing repositories

1. Check the target repository's `AGENTS.md` or `CLAUDE.md` and its issue-tracker/domain documentation.
2. If project-specific Matt Pocock skill configuration is missing, run `/setup-matt-pocock-skills` and complete its human setup questions. If the configuration is already present, keep it.
3. Run `/itdd-prepare` to clarify the request and prepare the spec and proposed ticket breakdown using the gathered facts.
4. Review the proposed spec and ticket breakdown with the human. Publish only what they agree to through the configured tracker.
5. Return the spec and ticket links, open questions, and a suggested next move. Stop.

A `ready-for-agent` label or published ticket is not authorization to execute. The planning handoff does not run `/itdd-execute`, BUILD, TEST, or VERIFY. A separate explicit request and applicable gates are required before `/idd` can consider `/itdd-execute`.

## Separate later-stage work

`/itdd-new`, the controller, `.idd` execution state, and the broader execution skill manifest belong to separate experimental execution work. They are not prerequisites for planning. A separate explicit request and applicable execution gates are required before any execution work.

The architecture, specs, and historical execution examples remain available for research. See the [archive index](../archive/README.md). Historical milestone evidence is not a product release, current-use claim, or guarantee that the same result can be reproduced today.

## Contributor references

- [Getting Started](../GETTING-STARTED.md)
- [Contributing](../../CONTRIBUTING.md)
- [Source inventory](../archive/SOURCE-INVENTORY.md)
- [Research notes](../research/README.md)
- [Wayfinder product map](https://github.com/Sailor422/itdd-control-plane/issues/34)

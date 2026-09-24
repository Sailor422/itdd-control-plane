# Historical Codex bootstrap brief — curated summary

> **Status:** Historical design input, not current setup instructions or an approved execution plan.

## Purpose

The original brief proposed a shareable home for research into an intent- and test-driven control plane. It emphasized separating agent reasoning from durable authority, keeping the design runtime-neutral where practical, and developing capabilities in bounded stages.

## Reusable design principles

- Keep durable intent, lifecycle state, authorization, and verification outside the reasoning worker.
- Separate planning, building, verification, and integration responsibilities.
- Treat existing global instructions, skills, hooks, histories, and knowledge stores as external influences; do not import them wholesale into project context.
- Preserve legacy sources read-only until individual items are reviewed and deliberately selected.
- Record source provenance and validate each staged capability before extending the system.

These are historical proposals, not proof that the full architecture was implemented, released, or is currently in use. The active product direction is the planning-first handoff described in the [README](../../README.md).

## Curation note

The original bootstrap document included detailed host setup and local environment references. This summary does not reproduce those details. Git history was not rewritten, so older revisions may retain them.

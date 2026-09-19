# Proposed Stage B Plan

## Objective

Establish project isolation and the smallest durable state/audit foundation without implementing agent execution, role orchestration, context retrieval, or autonomy.

## Baseline and scope

Start from the accepted `bootstrap-0` tag. Create a written Stage B plan and commit it before implementation. Stage B is limited to schema-first project-local directories, append-only event records, validation, and tests proving isolation and tamper-evident recording.

## Proposed vertical slices

1. Define versioned schemas for project identity, event envelope, and human decision record.
2. Implement append-only event writing with deterministic serialization and hash chaining.
3. Implement read/rebuild checks that reconstruct state from events without treating derived state as authority.
4. Add negative tests for path escape, malformed events, hash-chain mismatch, unauthorized direct lifecycle mutation, and cross-project reads.
5. Produce a Stage B result report with commands, evidence hashes, independent review, and a known-good tag.

## Explicit non-goals

No Builder, Verifier, Planner, Context Compiler, Project Map, Obsidian view, parallel execution, legacy vault migration, controller self-modification, or break-glass implementation. Do not modify global Codex state or Prime.

## Human decisions required before Stage B

- Approve this scope and the event/schema format.
- Confirm the desired public repository visibility and license details if different from this baseline.
- Decide whether Stage B should use JSON Lines, SQLite, or another durable event representation after reviewing the trade-off.


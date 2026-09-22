# Human decisions for ticket-21-prepare-20260922T1952Z

Approval identity: originating conversation user (GitHub identity not independently verified).
Timestamp UTC: 2026-09-22T20:30:39.817404+00:00
Decision: “approve defaults”.

Approved preparation defaults:
- Source: GitHub issue Sailor422/itdd-control-plane#21 with parent spec #15; preserve both issue bodies/comments as immutable snapshots and record hashes.
- Baseline: current committed `main` SHA `80284553d571d5d92e2a8f66b7b8c312f9c283ef`, in a fresh isolated worktree; do not use or alter the dirty ordinary checkout. The earlier `bc2b53b...` baseline and failed candidates remain historical evidence only.
- Acceptance: include all preserved TEST and VERIFY gaps, with explicit tests/probes; failures remain historical and append-only.
- Scope: integration/promotion path only; exact path allowlist to be derived read-only and presented in the final contract. Exclude unrelated dirty files, worktrees, historical evidence, and unrelated tickets.
- Test policy: normal project-native test command must pass; any import shim must be documented and cannot conceal a failure of the normal command.
- Execution remains gated on human review and explicit approval of the exact contract (full source identity, baseline, paths, acceptance, tests, artifacts, exclusions).

This is approval of preparation defaults, not yet the exact execution contract.

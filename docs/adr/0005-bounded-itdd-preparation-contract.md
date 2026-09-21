# ADR-0005: Bounded preparation before ITDD execution

- **Status:** Accepted
- **Date:** 2026-09-21

## Context

`itdd-execute` requires an exact, bounded contract, but deciding scope and tests in the execution loop risks ambiguity and role collapse.

## Decision

Provide `/itdd-prepare` as a preparation-only skill. It runs six separate fresh agents for discovery, grilling, research, spec/ticket decomposition, contract drafting, and independent review. Each phase writes durable evidence. The output has fixed fields for source identity, full baseline SHA, allowed paths/scope, acceptance criteria, positive and negative tests, artifacts/evidence, and exclusions. Explicit human approval of the exact contract is required before `/itdd-execute`.

The skill cannot implement code or invoke BUILD, TEST, or VERIFY. The existing `itdd-new` bundle copies the complete `skills/` payload, so the skill is available in initialized projects without changing the project-local manifest authority boundary.

## Consequences

Preparation adds a deliberate gate and evidence overhead. In return, execution receives a reproducible scope and independent challenge before any mutation.

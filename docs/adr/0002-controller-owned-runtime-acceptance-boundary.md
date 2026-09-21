# Controller-Owned Runtime Acceptance Boundary

- Status: proposed
- Date: 2026-09-20
- Deciders: human reviewers

## Context

The claimed runtime-role PASS was invalid because candidate acceptance compared
only commit/tree identities and allowed role-like worker metadata to influence
lifecycle authority. These are trust-boundary failures, not merely missing
tests.

## Decision

The controller owns execution assignments and lifecycle transitions. It must
independently observe frozen candidate commit, tree, checkout, and clean Git
status before and after TEST and VERIFY. TEST-to-VERIFY requires an immutable
controller-issued TEST assignment, exact candidate identity, clean state, and
complete raw evidence. Worker output is observational and cannot grant role or
transition authority. Missing or ambiguous evidence fails closed.

## Consequences

Workers cannot self-authorize or make a mutated checkout acceptable. Scratch
state must remain outside the candidate checkout. Historical invalid PASS and
FAIL evidence remains immutable, and every repair requires a fresh acceptance
attempt.

## Evidence and reversibility

This decision is motivated by the preserved independent failure in
`work/proofs/itdd-runtime-roles-acceptance-20260920T202939Z/`. It can be
revisited only through a new independently verified trust-boundary design; the
historical evidence must remain unchanged.

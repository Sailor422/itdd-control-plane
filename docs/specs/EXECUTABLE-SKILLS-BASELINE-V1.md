# Executable Skills Baseline v1

## Problem Statement

The repository uses installed Pocock skills, including `grill-with-docs`, but
does not yet define and independently prove the boundary between skill
assistance and ITDD controller authority. Without that boundary, a skill's
proposal output could be mistaken for approved intent, lifecycle authority, or
acceptance evidence.

## Solution

Define and prove one project-local executable skill contract for
`grill-with-docs`, using the existing controller authority and append-only event
boundaries. A human-only invocation produces a versioned,
provenance-bound clarification proposal. The skill may clarify terminology,
assumptions, source inputs, and open questions, but it cannot approve intent,
grant capability, create human authority, mutate approved intent, advance
lifecycle state, or promote a candidate.

The installed user-facing skill is the behavioral source. The repository
contract records the ITDD boundary, source identity, artifact shape, and
acceptance evidence requirements.

## User Stories

1. As a human operator, I want to invoke `grill-with-docs` in a project so that
   decisions are sharpened in the repository where they will be used.
2. As a human operator, I want the skill to use the project's domain glossary
   so that terminology is consistent with existing decisions.
3. As a human operator, I want resolved terms and hard-to-reverse trade-offs
   recorded durably so that future sessions can reconstruct the reasoning.
4. As a human operator, I want the skill to produce a clarification proposal
   so that unresolved understanding is not confused with approved intent.
5. As a controller, I want every proposal bound to a project and execution so
   that evidence cannot be replayed in another context.
6. As a controller, I want every proposal bound to its intent or draft context
   so that its provenance is explicit.
7. As a controller, I want source inputs and the installed skill identity
   recorded so that the proposal's origin is auditable.
8. As a controller, I want capability and authority boundaries recorded so
   that a skill cannot silently acquire lifecycle powers.
9. As a controller, I want deterministic identity fields to reproduce
   byte-identically so that artifacts can be compared across processes.
10. As an independent verifier, I want to reconstruct the proposal from a
    fresh process so that acceptance does not depend on builder memory.
11. As an independent verifier, I want tampered artifacts and event history to
    fail closed so that false provenance cannot pass.
12. As a controller, I want unauthorized callers rejected so that agent or
    worker processes cannot impersonate human authority.
13. As a controller, I want wrong-project, wrong-execution, stale-baseline,
    path-escape, malformed-input, and capability-expansion attempts rejected.
14. As a controller, I want proposal creation to leave lifecycle state
    unchanged so that clarification cannot advance execution.
15. As a controller, I want the skill unable to approve intent or mutate
    approved intent so that authority remains outside the skill.
16. As a controller, I want the skill unable to create human authority,
    advance lifecycle state, or promote candidates so that controller-owned
    transitions remain controller-owned.
17. As a project maintainer, I want a clean candidate, preserved evidence, and
    a known-good tag so that the accepted contract is reproducible.
18. As a maintainer, I want installed-source identity and repository-contract
    version recorded so that source drift cannot be silently accepted.

## Implementation Decisions

- Add one project-local skill adapter at the existing controller authority and
  event boundary. Prefer this single seam over direct writes from the skill to
  intent, lifecycle, or promotion state.
- Keep the installed `grill-with-docs` definition as the user-facing
  behavioral source; record its source identity and an explicit repository
  contract version in proposal provenance.
- Represent the output as a versioned clarification proposal, not approved
  intent, a human decision, a lifecycle command, or a PASS record.
- Bind the proposal to project identity, execution identity, intent/draft
  context, baseline identity, source inputs, skill source identity, and
  capability grant.
- Separate deterministic identity/provenance fields from agent-reasoned
  clarification content. Deterministic fields must be byte-identical for the
  same inputs; reasoned content remains explicitly identified as such.
- Use the existing append-only event mechanism for proposal provenance and the
  existing authority path for any later human acceptance.
- Reject unauthorized roles and all missing, extra, mismatched, stale,
  escaped, malformed, or capability-expanding inputs.
- Keep `.idd` authority state and lifecycle state unchanged during proposal
  creation.
- Make all forbidden authority actions fail closed: approving intent, granting
  capability, creating human authority, mutating approved intent, advancing
  lifecycle state, and promoting a candidate.
- Do not add full lifecycle orchestration, single-EU acceptance, parallelism,
  replan, knowledge retrieval, maintenance mode, or break-glass behavior to
  this milestone.

## Testing Decisions

Tests must exercise observable contract behavior at the highest existing
controller/event seam, not internal helper implementation details.

Required coverage:

- valid human invocation creates the exact versioned proposal;
- project, execution, intent/draft, baseline, source, skill, and capability
  provenance are present and correct;
- deterministic fields reproduce byte-identically;
- a fresh process reconstructs the same proposal and event state;
- unauthorized agent invocation fails closed;
- missing and extra input fail closed;
- wrong project or execution fails closed;
- stale baseline fails closed;
- path escape fails closed;
- capability expansion fails closed;
- malformed output fails closed;
- approved-intent mutation, intent approval, human-authority creation,
  lifecycle advancement, and promotion attempts fail closed;
- tampered proposal and tampered event history are detected;
- lifecycle and authority state remain unchanged after proposal creation.

Prior art is the repository's existing authority, append-only event,
restart-reconstruction, isolation-negative, and evidence-binding test suites.
The milestone must also be accepted through separate fresh BUILD, TEST, and
independent VERIFY Codex executions against a clean candidate, with preserved
raw evidence and an exact diff inventory.

## Out of Scope

- Reinstalling or rewriting the installed Pocock skills.
- Implementing every skill in the installed skill set.
- Full single-EU lifecycle acceptance.
- Planner, graph evaluator, Builder, Spec Verifier, or Standards Reviewer
  orchestration.
- Candidate creation, promotion, integration, parallel EU execution, replan,
  intent amendment, knowledge retrieval, maintenance mode, or break-glass.
- Treating manual skill use or an installed `SKILL.md` as acceptance evidence.
- Reusing I-1001, the preserved runtime-role failure, or any dirty-worktree
  run as acceptance evidence.

## Further Notes

The current dirty worktree is forensic input, not an acceptance baseline. The
implementation must begin from a newly recorded clean checkout. At the first
failed invariant, preserve all evidence and stop that acceptance attempt; do
not repair the same attempt forward. A known-good tag may be created only
after independent verification passes.

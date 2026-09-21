---
name: idd
description: "Route intent-driven work to preparation or approved execution."
disable-model-invocation: true
---

# IDD Router

`/idd` is the top-level entry point for intent-driven work. This skill is a
router and authority gate. It does not implement code, run tests, create
lifecycle state, or approve its own work.

## Route first

1. **Unapproved or unbounded work** — route to `/itdd-prepare`. This includes
   missing, incomplete, or unclear scope, acceptance criteria, baseline,
   allowed paths, evidence obligations, or immutable spec/ticket/intent.
   Preparation must complete all six phases with a **fresh agent execution for
   each**: DISCOVERY, GRILLING, RESEARCH, SPEC/TICKET DECOMPOSITION,
   EXECUTION-CONTRACT DRAFTING, and INDEPENDENT REVIEW. Preparation is not
   approval and cannot invoke `/itdd-execute`.
2. **Approved, bounded work** — route to `/itdd-execute` only when a human has
   explicitly approved the exact execution contract (spec identity, baseline,
   scope/paths, criteria, tests, artifacts, exclusions, and evidence
   obligations). The approval identity, time, decision, and contract hash must
   be recorded. A preparation `READY FOR HUMAN APPROVAL` result is still
   unapproved.

If the contract, its immutable baseline, required fields, evidence, or explicit
human approval is missing, malformed, stale, or unverifiable, **fail closed**:
stop and route back to `/itdd-prepare` or request the missing human decision.
Never infer approval or expand scope.

## Approved execution handoff

When and only when the approval gate passes, hand the exact approved contract
to `/itdd-execute`. It must launch exactly three separate fresh agent
executions, in order:

1. **BUILD** — implement only the approved bounded change.
2. **TEST** — independently run all required positive and negative/hostile
   probes against the Builder output.
3. **VERIFY** — independently try to disprove the implementation and TEST
   evidence.

Distinct labels, callbacks, prompts, or subroutines in one session do not make
fresh executions. Stop at the first material failure, preserve that failed
attempt, and start any repair as a new BUILD/TEST/VERIFY cycle. Only the
controlling workflow may accept results or advance lifecycle state after
VERIFY passes.

## Workspace and evidence guardrails

All BUILD, TEST, and VERIFY work must run in isolated workspaces below
`.idd/build_workspaces/`. Never use the ordinary working tree or
`.idd/preparation/` as an execution workspace. Preserve prompts, outputs,
identities, baseline/candidate hashes, commands, results, artifacts, approval,
and failures as durable evidence. Do not replace failed evidence with a later
success.

## Completion rule

This router is complete only when it has selected the correct route and either
returned control to `/itdd-prepare` or handed an explicitly approved exact
contract to `/itdd-execute`. It must not write product code, self-approve, issue
an acceptance verdict, or perform promotion.

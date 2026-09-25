---
name: itdd-execute
description: "Orchestrate a bounded ITDD implementation milestone through three genuinely separate fresh agent executions: BUILD, TEST, then independent VERIFY. Use when a spec, ticket, or approved milestone is ready to implement and the user requires strict separation between implementation, testing, and verification, with preserved evidence, fail-fast behavior, and no self-certification."
---

# ITDD Execute

Use this skill only after the work is bounded by an approved spec, ticket, or milestone. Do not use it to invent scope or replace intent development. Every BUILD, TEST, and VERIFY invocation must be entered through the `/idd` top-level directive. The three roles run in an isolated workspace below the project `.idd/build_workspaces/` boundary; never run them in the ordinary working tree or in preparation evidence directories.

## Resume preflight

Before launching or replacing a role, inspect the live agent roster, exact assigned worktree HEAD and status, and latest role report. Match each report and evidence to the controlling contract, role, and candidate. Reconcile any conflict from durable evidence before acting; fail closed if identity or state remains ambiguous. Do not spawn a replacement for a completed phase. This preflight selects the next authorized action; it does not waive any required role execution, controller-owned approval, or controller authority.

## Core contract

Run exactly three acceptance roles in order:

1. **BUILD** — fresh agent execution implements the bounded change.
2. **TEST** — a different fresh agent execution tests the Builder output and executes required positive and negative probes.
3. **VERIFY** — a third fresh agent execution independently attempts to disprove both the implementation and the Tester's evidence.

Never collapse these roles into one execution. Different labels, subroutines, callbacks, or prompts inside one agent session do not satisfy separation.

The controlling system retains lifecycle authority. A skill invocation, agent worker, Builder, Tester, or Verifier never grants itself authority to advance state.

## Before BUILD

Require a bounded work contract containing at least:

- source spec/ticket/milestone identity
- exact baseline Git SHA/tag
- allowed scope and paths
- acceptance criteria
- required positive tests
- required negative/hostile tests
- expected artifacts
- evidence requirements
- explicit exclusions

If these are materially missing, stop and request clarification or return to the appropriate specification/decomposition workflow.

Preserve the exact baseline before any implementation begins.

## Phase 1 — BUILD

Launch a **fresh agent execution** dedicated only to BUILD.

Prefer the installed upstream implementation/TDD skills when they fit the work, such as the current `implement` and `tdd` skills. Discover their exact installed names rather than guessing.

Builder responsibilities:

- implement only the bounded work
- work only in the authorized isolated workspace under the project `.idd/build_workspaces/` boundary
- follow the accepted spec and acceptance contract
- run implementation-local checks needed to develop safely
- produce implementation artifacts and Builder-scoped evidence
- report exact changed paths and candidate state

Builder prohibitions:

- do not issue the acceptance verdict
- do not act as the TEST execution
- do not act as independent VERIFY
- do not promote
- do not rewrite the spec to fit the implementation
- do not fabricate probe results

Record durable BUILD provenance, including the actual agent invocation/session/process identity where available.

## Phase 2 — TEST

After BUILD completes, launch a **different fresh agent execution** dedicated only to TEST.

The Tester must not inherit the Builder's reasoning as proof. Give it the bounded contract, the exact candidate, and the tests/probes it must execute.

Tester responsibilities:

- run the required positive tests against the exact candidate
- execute every required negative/hostile operation for real
- verify changed-path and scope constraints
- record the actual enforcement boundary reached for negative probes
- compare expected vs actual rejection class/reason
- confirm rejected operations did not advance authoritative state
- produce TEST evidence bound to the exact baseline/candidate/execution

A negative test is invalid if:

- it is represented only by a placeholder or generated record
- it fails at an unrelated earlier guard
- the operation was never actually attempted
- the rejection reason/class is not the intended one

The Tester may report PASS or FAIL for TEST, but cannot provide final independent acceptance.

At the first material TEST failure, preserve evidence and stop this acceptance attempt. Do not let BUILD repair the same acceptance run in place.

## Phase 3 — VERIFY

Only after TEST passes, launch a **third fresh agent execution** dedicated only to independent VERIFY.

Prefer the installed upstream review/debugging skills when useful, such as the current code-review or diagnosing-bugs skills. Discover exact names rather than assuming them.

The Verifier must actively attempt to disprove both BUILD and TEST.

At minimum, verify:

- the Builder was a real separate agent execution
- the Tester was a real separate agent execution
- the Verifier itself is a distinct fresh agent execution
- baseline and candidate identities are exact
- required tests actually ran
- hostile probes actually executed
- hostile probes reached their intended enforcement boundaries
- no placeholder evidence substitutes for execution
- no Builder self-certification was accepted
- no Tester claim is accepted without reproducible evidence
- no unauthorized scope/path changes were accepted
- no hidden dependency on dirty/untrusted state exists
- reconstruction/restart requirements pass when included in the contract

The VERIFY execution owns the independent acceptance verdict for this bounded milestone. It may not repair the implementation it judges.

## Failure discipline

At the first failed invariant:

1. mark the acceptance attempt FAIL
2. preserve all evidence and artifacts
3. stop the attempt
4. diagnose separately
5. repair in a new BUILD cycle
6. launch a new TEST execution
7. launch a new VERIFY execution

Never nurse a failed acceptance run into PASS.

Historical FAIL remains FAIL.

## Evidence requirements

For each BUILD / TEST / VERIFY execution record at least:

- execution ID
- role
- actual agent runtime provenance
- baseline SHA
- candidate SHA where applicable
- context/spec/ticket identity
- commands/operations actually executed
- outputs/results
- artifact identities
- start/end status

For hostile probes record at least:

- requested operation
- expected enforcement boundary
- actual boundary reached
- expected rejection class
- actual rejection class/reason
- authoritative state before/after
- whether an unauthorized artifact was accepted

See `references/evidence-contract.md` for the compact evidence checklist.

## Completion rule

The milestone is accepted only when:

- BUILD completes from the approved baseline
- separate fresh TEST passes
- separate fresh VERIFY passes
- required evidence is durable and identity-bound
- no failed attempt was rewritten
- acceptance/tagging is performed only by the controlling workflow after VERIFY PASS

Report the final state concisely: BUILD identity/result, TEST identity/result, VERIFY identity/result, accepted SHA/tag if created, preserved failures, and next authorized milestone.

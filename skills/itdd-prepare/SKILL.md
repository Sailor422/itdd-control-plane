---
name: itdd-prepare
description: "Use the existing engineering skills to clarify work, publish an agreed spec and tickets, and hand planning back to the human without starting execution."
disable-model-invocation: true
---

# ITDD Prepare

Prepare the work with the existing engineering skills. The normal endpoint is a
published spec and agreed tickets, followed by a human handoff. Preparation
never launches `/itdd-execute`, BUILD, TEST, or VERIFY.

## Prepare and hand back

1. **Understand.** Read the request, `CONTEXT.md`, relevant ADRs, issue-tracker
   configuration, and existing issues. Identify what is known and what the
   human must decide. Use `wayfinder` for work too large or uncertain for a
   single spec; use `grill-with-docs` when the request needs an interview.
   Consult `research`, `codebase-design`, or `diagnosing-bugs` only when their
   specific question arises. Stop and ask rather than inventing requirements.
2. **Specify.** Once the relevant decisions are settled, use `to-spec` to
   synthesize and publish the spec through the configured tracker. Follow that
   skill's own seam check with the human. Do not bypass its process or create a
   second, competing spec format.
3. **Break down.** Use `to-tickets` on the spec. Present its proposed slices
   and blocking edges; iterate until the human agrees, then publish through
   the configured tracker. Agreement to a breakdown is an ordinary planning
   decision, not an `/approved` gate unless an active process explicitly
   requires formal approval.

   For this `/itdd-prepare` invocation, tell `to-tickets` this is planning only:
   publish the agreed tickets and stop. Apply `ready-for-human` to each ticket
   (use `Status: ready-for-human` in local ticket files); do not add
   `ready-for-agent`. Before publishing, verify that the configured tracker
   supports `ready-for-human`. If it does not, stop without creating tickets
   and ask the human how to proceed. After publishing, do not follow
   `/to-tickets`'s separate "Work the frontier" instruction. This override
   applies only through `/itdd-prepare`; direct `/to-tickets` invocations keep
   that skill's own instructions.
4. **Check and hand back.** Compare the published spec and tickets with the
   agreed scope and acceptance criteria. Report their links, unresolved
   questions, exclusions, and a suggested next move using
   [planning-handoff](references/execution-contract-template.md) and the
   [checklist](references/preparation-checklist.md). Stop here. A
   `ready-for-human` label is a tracker status, not formal approval or
   authorization to start execution.

Use `domain-modeling`, `tdd`, and `writing-for-agents` where their own triggers
apply. Leave the engineering skills unchanged and follow their instructions.
No helper grants authority or changes the execution lifecycle.

## Approval and execution boundary

Use the human-only `/approved` skill only when the active process requires a
formal human approval. Follow its artifact-match and trusted-invocation rules;
do not treat discussion, ticket agreement, or a label as formal approval. If
there is no supported controller interface to record a required approval,
report the blocker rather than claiming approval.

A separate human request is required to consider execution. At that time `/idd`
must check the exact bounded execution contract, baseline, scope, tests,
evidence, exclusions, and any required recorded approval. A planning handoff
alone is never an execution contract or permission to run work.

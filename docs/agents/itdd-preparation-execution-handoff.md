# ITDD Preparation-to-Execution Handoff

This guide defines the control-plane handoff for one bounded milestone.

## Prepare

- Enter preparation with `/itdd-prepare`; preparation does not execute code.
- DISCOVERY records the immutable spec/ticket/intent source. If none exists, GRILLING forms a clarification frontier, asks the human, records answers, and waits for explicit human designation of the immutable source. No designation means `BLOCKED`; the skill never self-approves intent.
- Preserve phase outputs, execution identities, source revisions, decisions, and failures under `.idd/preparation/<preparation-id>/`.
- A human approves the exact contract: source identity, baseline SHA, paths, criteria, tests, artifacts, and exclusions.

## Lazy helper-skill routing

`/itdd-prepare` is an explicit router, not an invitation to run every Pocock
skill. Consult a helper only when its trigger applies: use `grilling` for
ambiguity or a decision frontier; `research` for external or repository facts;
`domain-modeling` only for glossary or ADR decisions; `codebase-design` when a
public seam or module boundary is unclear; `tdd` for acceptance seams and
positive/negative tests; `writing-for-agents` for contract clarity;
`code-review` for independent standards/spec review; and
`diagnosing-bugs` only for a reproducible failure. Record the helper's output as
preparation evidence.

Lazy consultation does not relax the requirement for a fresh phase-agent
identity or ITDD role separation. No helper can approve intent, grant
authority, change lifecycle state, or execute BUILD, TEST, or VERIFY.

For a future Kanban/UI consumer, preserve grilling evidence with structured
`question`, `recommendation`, `human answer`, `blocker`, `phase`, and `execution identity` fields. This is future-facing only and out of current implementation scope; no UI is added by this handoff.

## Handoff and execute

- Enter the approved contract through the `/idd` top-level directive. `/idd` is the entry point for all BUILD/TEST/VERIFY work.
- The controller launches three fresh, separate executions in order: BUILD, TEST, VERIFY.
- Each role uses an isolated workspace under the project `.idd/build_workspaces/` boundary. Never use the ordinary working tree or `.idd/preparation/` as an execution workspace.
- Record each role's execution identity, baseline/candidate identity, commands, outputs, and status. Preserve hostile-probe evidence and failures without rewriting them.
- Only the controlling workflow may advance lifecycle state after independent VERIFY passes.

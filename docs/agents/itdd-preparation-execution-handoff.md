# ITDD Preparation-to-Execution Handoff

This guide defines the control-plane handoff for one bounded milestone.

## Prepare

- Enter preparation with `/itdd-prepare`; preparation does not execute code.
- DISCOVERY records the immutable spec/ticket/intent source. If none exists, GRILLING forms a clarification frontier, asks the human, records answers, and waits for explicit human designation of the immutable source. No designation means `BLOCKED`; the skill never self-approves intent.
- Preserve phase outputs, execution identities, source revisions, decisions, and failures under `.idd/preparation/<preparation-id>/`.
- A human approves the exact contract: source identity, baseline SHA, paths, criteria, tests, artifacts, and exclusions.

## Handoff and execute

- Enter the approved contract through the `/idd` top-level directive. `/idd` is the entry point for all BUILD/TEST/VERIFY work.
- The controller launches three fresh, separate executions in order: BUILD, TEST, VERIFY.
- Each role uses an isolated workspace under the project `.idd/build_workspaces/` boundary. Never use the ordinary working tree or `.idd/preparation/` as an execution workspace.
- Record each role's execution identity, baseline/candidate identity, commands, outputs, and status. Preserve hostile-probe evidence and failures without rewriting them.
- Only the controlling workflow may advance lifecycle state after independent VERIFY passes.

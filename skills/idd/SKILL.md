---
name: idd
description: "Route intent-driven planning to a spec-and-ticket handoff; gate a separately requested execution on an exact approved contract."
disable-model-invocation: true
---

# IDD Router

`/idd` routes work and checks authority. It does not implement code, run tests,
approve proposals, or advance lifecycle state.

## Resume before clarifying

When resuming, inspect the current conversation, approved source contract, project ledger when present, exact assigned worktree, and preserved BUILD/TEST/VERIFY evidence before declaring context missing or asking the human to repeat details. Reconstruct scope, baseline, last completed phase, and next authorized action from those records. For repair, use the failed candidate SHA as the new baseline and preserve prior reports. Ask only for genuinely missing facts or authority; never infer approval. A directive that covers the exact phase does not require repeated confirmation, but any controller-owned approval record required by the process remains mandatory.

## Route first

1. **Planning or unbounded work:** route to `/itdd-prepare`. Follow the
   engineering skills through a published spec and agreed tickets. Return the
   links and suggested next move to the human, then stop. Ticket publication,
   a `ready-for-agent` label, and a planning handoff do not trigger execution.
2. **Separately requested execution:** consider `/itdd-execute` only when the
   human explicitly asks to proceed with implementation and the exact bounded
   execution contract has a source identity, baseline SHA, allowed paths and
   operations, acceptance criteria, positive and negative tests, artifacts,
   evidence obligations, and exclusions. Check any formal approval required
   by the active process using the human-only `/approved` mechanism and its
   controller-confirmed record. Approval of planning does not grant execution
   authority. If the active process requires approval but no supported
   controller recording interface exists, stop.

If a required field, baseline, approval, or evidence is missing, malformed,
stale, or unverifiable, **fail closed**: stop and request the missing human
input or bounded contract. Never infer approval or enlarge scope.

## Execution boundary

Only after the separate request and all gates pass, hand the exact execution
contract to `/itdd-execute`. Its BUILD, TEST, and independent VERIFY roles must
run as three separate fresh agent executions in that order. Work belongs in
isolated `.idd/build_workspaces/`, not the ordinary working tree or preparation
artifacts. Preserve identities, hashes, commands, results, failures, and
approval evidence. Stop at the first material failure; any repair is a new
attempt. Only the controlling workflow may accept or promote verified work.

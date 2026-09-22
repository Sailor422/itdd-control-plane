# ITDD preparation manifest — ticket-28-prepare-20260922T213125Z

Status: DISCOVERY in progress. Preparation only; no tests, implementation, or lifecycle operations.

## Source identity

- ITDD issue: https://github.com/Sailor422/itdd-control-plane/issues/28
- Parent spec: https://github.com/Sailor422/itdd-control-plane/issues/27
- Related: ITDD #21, #24, #25, #26; Prime `prime-agent-config` #1, #3, #5.
- Repo baseline: `80284553d571d5d92e2a8f66b7b8c312f9c283ef`
- This checkout already contains user-owned dirty/untracked files and worktrees. Preserve them unchanged.

## Initial dirty-state snapshot

```text
M CONTEXT.md
?? .idd/preparation/
?? .worktrees/
?? Pocock-skills-reference.md
?? docs/adr/0006-prime-workbench-itdd-authority-contract.md
?? evidence/ticket-16-test-current/
?? evidence/ticket-16-test-final/
?? evidence/ticket-16-test-new/
?? evidence/ticket-16-test-repair/
?? evidence/ticket-16-test/
?? evidence/ticket-16-verify-current/
?? evidence/ticket-16-verify-final/
?? evidence/ticket-16-verify/
?? evidence/ticket-18-verify-new/
?? evidence/ticket-2-test-combined/
?? evidence/ticket-2-test-controller-path/
?? evidence/ticket-2-test-repair/
?? evidence/ticket-2-test/
?? evidence/ticket-2-verify-combined/
?? evidence/ticket-20-test-20260922T1830Z/
?? evidence/ticket-21-test-20260922T1917Z/
?? full-itdd-stack.md
?? test1.md
```

## Approved constraints carried forward

- Prime-native RLM only; no Codex runtime/tool/model or fallback.
- ITDD owns execution assignments, candidate/scope identity, evidence custody, lifecycle transitions, and recovery.
- Human-directed, auditable bootstrap only; no claim of normal ITDD acceptance.
- Bootstrap route may admit only #21 after a fresh independent review and explicit approval of its exact contract hash; #24/#26 remain gates for other work.
- No tests, execution, source edits, worktree changes, commits, or lifecycle changes during preparation.

## Fresh phase executions

- DISCOVERY attempt 1: `sub-276701ac` — exited with empty reply; failure preserved.
- DISCOVERY attempt 2: `sub-6b2937dd` — cancelled after user correction because it overrode the Prime session model; no report accepted.
- DISCOVERY retry: `sub-a0579751` — fresh child inheriting the Prime session model; in progress.
- GRILLING: pending fresh execution.
- RESEARCH: pending fresh execution.
- SPEC/TICKET DECOMPOSITION: pending fresh execution.
- EXECUTION-CONTRACT DRAFTING: pending fresh execution.
- INDEPENDENT REVIEW: pending fresh execution.

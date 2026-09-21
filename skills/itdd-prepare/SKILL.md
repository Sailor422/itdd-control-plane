---
name: itdd-prepare
description: "Prepare a bounded ITDD execution contract through isolated discovery, grilling, research, decomposition, drafting, and independent review before itdd-execute."
disable-model-invocation: true
---

# ITDD Prepare

Prepare, but do not execute, one bounded ITDD milestone. This skill ends with a reviewable execution contract for `/itdd-execute`; it never implements code and never invokes BUILD, TEST, or VERIFY.

## Non-negotiable boundaries

- Use a **new, fresh sub-agent execution for each phase**. Do not reuse a conversation, callback, or role-labelled subroutine. Record each execution identity and provenance.
- Run the phases in order: **DISCOVERY**, **GRILLING**, **RESEARCH**, **SPEC/TICKET DECOMPOSITION**, **EXECUTION-CONTRACT DRAFTING**, and **INDEPENDENT REVIEW**.
- Agents may inspect files, issues, history, and documentation and may write preparation artifacts only. They must not modify product/source/test code, commit, merge, promote, or change authoritative lifecycle state.
- Do not call `/itdd-execute`, BUILD, TEST, or VERIFY. Preparation is not approval and does not grant execution authority.
- Preserve prompts, outputs, source identities, decisions, and failures as durable evidence under a preparation directory (for example `.idd/preparation/<preparation-id>/`). Never replace a failed attempt with a later success.
- Stop if a required input, baseline SHA, path boundary, acceptance criterion, or evidence obligation is unknown. Ask the human instead of guessing.

## Phase protocol

1. **DISCOVERY** — map the request to its source spec/ticket/intent, repository state, current baseline SHA, relevant paths, constraints, and open questions. No solution design or edits.
2. **GRILLING** — a fresh agent challenges ambiguity, assumptions, edge cases, success/failure meaning, and exclusions. Capture answered questions and unresolved blockers.
3. **RESEARCH** — a fresh agent gathers only evidence needed to resolve the questions, citing authoritative repository or external sources and recording source revisions/URLs. Research does not change code.
4. **SPEC/TICKET DECOMPOSITION** — a fresh agent turns the approved source material into one bounded milestone: behavior, dependencies, allowed paths, acceptance criteria, positive tests, negative/hostile tests, artifacts, and exclusions. Do not invent requirements.
5. **EXECUTION-CONTRACT DRAFTING** — a fresh agent fills `references/execution-contract-template.md`, binds the exact baseline SHA, and links all preparation evidence. The result must be executable by `itdd-execute` without expanding scope.
6. **INDEPENDENT REVIEW** — a fresh agent, not involved in drafting, tries to disprove completeness, scope safety, testability, identity binding, and role separation. It must issue PASS only when every required field is concrete; otherwise issue FAIL with blockers.

A human must review the independent-review result and explicitly approve the exact contract (identity, baseline, paths, criteria, tests, artifacts, and exclusions). Record the approval identity, timestamp, contract hash, and decision. Without approval, stop and return `READY FOR HUMAN APPROVAL`, never `READY FOR EXECUTION`.

## Required final output

Return exactly these headings, in this order. Values must be concrete; use `UNKNOWN` only to report a blocker and then stop:

```text
PREPARATION: <preparation-id>
STATUS: READY FOR HUMAN APPROVAL | BLOCKED
SPEC IDENTITY: <issue/spec/intent ID, version, and immutable source location>
BASELINE SHA: <full Git SHA>
ALLOWED PATHS/SCOPE: <exact paths and bounded operations>
ACCEPTANCE CRITERIA:
- <observable criterion>
POSITIVE TESTS:
- <command/probe and expected result>
NEGATIVE/HOSTILE TESTS:
- <operation, enforcement boundary, expected rejection, and no-state-change assertion>
ARTIFACTS/EVIDENCE:
- <artifact path or identity, owner, and hash/provenance>
EXCLUSIONS:
- <explicitly out-of-scope item>
PHASE EVIDENCE: <durable directory and six fresh execution identities>
INDEPENDENT REVIEW: <PASS/FAIL, execution identity, evidence path>
HUMAN APPROVAL: <PENDING or approver, timestamp, contract hash>
NEXT AUTHORIZED ACTION: <itdd-execute only after explicit approval, or STOP>
```

Do not append an execution verdict. A `READY FOR HUMAN APPROVAL` contract is still unapproved; only the controlling workflow may hand an approved contract to `/itdd-execute`.

See [execution-contract-template.md](references/execution-contract-template.md) and [preparation-checklist.md](references/preparation-checklist.md).

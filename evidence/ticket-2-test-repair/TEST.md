# TEST Evidence — Issue #2 repaired candidate

- Result: **TEST FAIL** (stopped at first material failure)
- Candidate: `2945d0d69d1762d5c3cd34fed619079b95bf73d2`
- Baseline: `db09daa966a14099ef18cba548b6f608cea5a18b7`
- Worktree: `/Users/herbertfields/itdd-control-plane/.worktrees/build-ticket-2-repair`
- Fresh execution: this tester process, distinct from BUILD attempts
- Raw evidence: `evidence/ticket-2-test-repair/probe-output.txt`

## Preserved inputs

Read Issue #2, repaired BUILD evidence at `work/proofs/ticket-2-build/BUILD.md`, and prior failed TEST evidence at `evidence/ticket-2-test/TEST.md` before testing. The prior failure was wrong-project acceptance; the repair added `CapabilityGrant.project_id` validation.

## Scope and identity

`git rev-parse HEAD` returned the candidate hash above. Worktree status was clean before testing (`(empty)`). Exact diff against the recorded BUILD baseline `db09daa966a14099ef18cba548b6f608cea5a18b` (the user-supplied baseline string has an extra trailing `7` and is not a Git object):

```text
M	skills/runtime.py
M	tests/integration/test_grill_with_docs_contract.py
A	work/proofs/ticket-2-build/BUILD.md
```

No candidate files were modified. No VERIFY was run.

## Automated ticket-local contract

```text
PYTHONPATH=. pytest -q tests/integration/test_grill_with_docs_contract.py
16 passed in 0.16s
```

## Fresh-process contract probe

The raw probe was executed as a new Python process with `PYTHONPATH` set to the candidate. It exercised positive proposal creation, fresh-process reconstruction, and hostile cases in order. For each hostile case it recorded the intended enforcement boundary, actual reason/class, and before/after `.idd` state file snapshot.

Passed before stop:

- positive proposal creation: accepted; proposal was `PROPOSED`, `authority_effect: NONE`;
- fresh-process reconstruction: exact proposal/event reconstruction passed;
- unauthorized role: rejected as `SkillContractError: grill-with-docs requires a human actor`; state unchanged;
- wrong project: rejected as `SkillContractError: DENY_PROJECT_MISMATCH`; state unchanged;
- wrong execution: rejected as `SkillContractError: DENY_EXECUTION_MISMATCH`; state unchanged;
- stale baseline: rejected as `SkillContractError: DENY_BASELINE_MISMATCH`; state unchanged.

## First material failure

Probe: **path escape**. Intended boundary: reject escaped source input. Actual result: accepted a request with `source_inputs: ["../outside-secret"]`, returned a clarification proposal, and created new `.idd` state (`before_files: 3`, `after_files: 4`). The authoritative controller seam therefore does not reject path-escape source inputs. Testing stopped immediately. Malformed/missing/extra input, capability expansion, forbidden authority actions, tampered proposal/event history, lifecycle/authority invariants, exact hostile reason coverage after this point, and runtime-specific probes were not run after the required fail-fast stop.

Raw JSON records (including actual reason/class and state snapshots) are in `probe-output.txt`.

## Status

**FAIL.** Candidate does not satisfy the full ticket contract. Do not promote or accept this candidate from this TEST execution.

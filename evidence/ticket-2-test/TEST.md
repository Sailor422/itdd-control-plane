# TEST Evidence — Issue #2 (STOPPED AT FIRST MATERIAL FAILURE)

- Result: **TEST FAIL**
- Candidate: `ae425c70442be09788dd26e1b09985e80d1faac1`
- Baseline: `db09daa966a14099ef18cba548b6f608cea5a18b`
- Worktree: `/Users/herbertfields/itdd-control-plane/.worktrees/build-ticket-2`
- Recorded: 2026-09-22T13:46:49.922766+00:00
- Candidate worktree status before/after: clean (`git status --porcelain=v1` empty)

## Scope / identity checks

Command:
```
git rev-parse HEAD
git status --porcelain=v1
git diff --stat db09daa966a14099ef18cba548b6f608cea5a18b --
```

Output:
```
HEAD ae425c70442be09788dd26e1b09985e80d1faac1
status: (empty)
 skills/runtime.py                                  | 25 ++++++++++++++++++++++
 tests/integration/test_grill_with_docs_contract.py | 11 +++++++++-
 work/proofs/ticket-2-build/BUILD.md                | 25 ++++++++++++++++++++++
 3 files changed, 60 insertions(+), 1 deletion(-)
```

## Positive baseline test

Command:
```
PYTHONPATH=. pytest -q tests/integration/test_grill_with_docs_contract.py
```

Output:
```
...............                                                          [100%]
15 passed in 0.14s
```

This is insufficient for acceptance because the required hostile probes below are independent of the existing tests.

## Fresh-process hostile probe and first failure

The probe copied the candidate `skills/` contract into an isolated temporary project, then used `SkillRuntime` with a valid human invocation, an unauthorized `agent` invocation, and a wrong-project invocation. Capability grant and project root remained bound to the isolated project. Full raw output is in `probe-output.txt`.

Command shape:
```
PYTHONPATH=. python -c '<fresh-process probe>'
```

Observed:
```
POS ACCEPT
UNAUTH REJECT SkillRuntimeError: role is not authorized for skill
WRONG_PROJECT ACCEPT (proposal project_id=project-2, execution_id=EXEC-1)
```

Expected wrong-project behavior: reject closed. Actual behavior: proposal accepted and persisted for `project-2` while the grant remained bound to the same project root. This is the first material failure, so testing stopped as required. No repair, VERIFY, or further probes were run.

## Enforcement boundary demonstrated

- Unauthorized role was rejected.
- Project-root binding and execution binding alone did not enforce project identity.
- `SkillRuntime._validate_invocation` checks only `grant.project_root == self.project_root`; it has no controller/project identity binding.
- The wrong-project proposal was non-authoritative in shape (`PROPOSAL_ONLY`, `authority_effect=NONE`) but still violated the required wrong-project rejection boundary.

## Authoritative state / mutation observation

The candidate worktree `.idd` authority/lifecycle state was not used or modified. The probe used an isolated temporary root (path recorded in `probe-output.txt`) and observed only skill artifact, evidence, and telemetry outputs there. Candidate worktree remained clean.

## Status

**FAIL.** Required contract is not satisfied. Evidence is preserved. Do not promote or accept this candidate from this TEST execution.

# TEST Evidence — Issue #2 controller-path candidate

- Result: **TEST FAIL** (stopped at first material hostile failure)
- Candidate: `4aee6766d88e8cb9a3d5abb07a3a8ada9585385d`
- Baseline: `db09daa966a14099ef18cba548b6f608cea5a18b`
- Worktree: `/Users/herbertfields/itdd-control-plane/.worktrees/build-ticket-2-controller-path`
- Raw evidence: `evidence/ticket-2-test-controller-path/probe-output.txt`

## Inputs reviewed

Issue #2, latest BUILD evidence `work/proofs/ticket-2-build/BUILD.md`, prior failed TEST evidence `evidence/ticket-2-test/TEST.md` and `evidence/ticket-2-test-repair/TEST.md`, and diagnosis comments/artifacts were reviewed before execution.

## Scope and identity

Candidate HEAD was `4aee6766d88e8cb9a3d5abb07a3a8ada9585385d`. Candidate status before/after remained clean: `(empty)`. Exact diff against baseline:

```text
 control/skills.py                                  |  7 ++-
 tests/integration/test_grill_with_docs_contract.py | 19 ++++++
 work/proofs/ticket-2-build/BUILD.md                | 68 ++++++++++++++++++++++
 3 files changed, 93 insertions(+), 1 deletion(-)
```

No candidate files were modified. No VERIFY was run.

## Automated candidate tests

`PYTHONPATH=. pytest -q tests/integration/test_grill_with_docs_contract.py` -> **16 passed**.

## Fresh-process hostile probe

The probe ran as a separate Python process and recorded actual exception/reason, before/after `.idd` file snapshots, and raw results. Direct controller seam passed positive creation, fresh-process reconstruction, unauthorized role, project/execution/intent/version/baseline mismatches, source path traversal and absolute path escape, malformed/missing/extra input, capability expansion, forbidden-authority capability, and proposal tamper detection. Direct rejections left state unchanged.

Runtime seam passed positive creation and unauthorized role. **First material failure:** runtime wrong-project invocation was accepted and wrote runtime artifacts (`state_unchanged: false`). Invocation used `project_id: project-2` and matching input binding while the grant remained `CapabilityGrant(execution_id='EXEC-1', project_root=<same runtime root>, capabilities=project.artifact.write)`. Actual runtime output was `ACCEPT`; expected closed rejection. This shows runtime grant binding enforces execution and root, but not project identity.

Testing stopped immediately at this first material failure. Runtime path traversal, malformed/extra inputs after this point, capability expansion, forbidden authority operations, tamper detection, and runtime fresh-process reconstruction were not run after the stop.

## Status

**FAIL.** Candidate does not satisfy the full Issue #2 contract. Do not promote or accept it.

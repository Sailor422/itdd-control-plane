# Ticket #16 TEST evidence

## Verdict: FAIL

- Candidate: `80284553d571d5d92e2a8f66b7b8c312f9c283ef`
- Baseline: `ticket-2-grill-with-docs-pass` / `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Scope: TEST only. No repair, candidate modification, or VERIFY was performed.

## Targeted tests

`env PYTHONPATH=. .venv/bin/pytest -q tests/integration/test_workflow_runtime_registration.py tests/test_itdd_new_bootstrap.py tests/integration/test_grill_with_docs_contract.py` — **25 passed**.

## Hostile and contract probes

Raw output: `probe-output.txt`; probe source: `probe.py`.

Passed probes covered workflow order and registration, controller-only acceptance, non-mutating acceptance result, malformed/missing/extra registration, stale identity, forbidden worker role, stale execution binding, extra inputs, malformed source ID, fresh-process reconstruction, and valid proposal invocation.

### First material failure

`wrong_project` invocation was accepted. A `CapabilityGrant` bound to the isolated project root was used with a `SkillInvocation` whose `project_id` was `other`; `SkillRuntime.invoke()` persisted/accepted the proposal instead of rejecting the project identity mismatch. The output records `wrong_project: UNEXPECTED_PASS`. This violates project-aware controller/runtime binding and the contract's stale/mismatched rejection boundary. No repair was attempted.

## Full suite

`env PYTHONPATH=. .venv/bin/pytest -q` stopped at collection with 156 errors caused by pre-existing `.worktrees/` duplicate modules/import-path failures (raw: `full-suite.txt`). The targeted candidate tests were run separately and passed. This collection condition is distinguished from the candidate hostile failure above.

## Changed-path observation

Candidate-vs-baseline diff was recorded during TEST. It includes paths beyond the BUILD-declared scope (`control/skills.py`, `tests/integration/test_grill_with_docs_contract.py`, and deletion/change of `work/proofs/ticket-2-build/BUILD.md`), so exact changed-path scope was not cleanly satisfied either. Command output is preserved in session command history; no files were changed by TEST.

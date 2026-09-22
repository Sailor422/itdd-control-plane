# Ticket #16 TEST evidence (fresh execution)

## Verdict: FAIL

- Candidate: `4406448321ccf4cd4fa89c5f273eec228ffdd42b`
- Baseline: `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Worktree: `/Users/herbertfields/itdd-control-plane/.worktrees/build-ticket-16-new`
- Scope: TEST only. Candidate was not modified. VERIFY was not run.

## Targeted tests

`env PYTHONPATH=. /Users/herbertfields/itdd-control-plane/.venv/bin/pytest -q tests/integration/test_workflow_runtime_registration.py tests/test_itdd_new_bootstrap.py tests/integration/test_grill_with_docs_contract.py` — **29 passed**.

## Full suite

`env PYTHONPATH=. /Users/herbertfields/itdd-control-plane/.venv/bin/pytest -q` — **195 passed** in the clean candidate worktree. Raw output: `full-suite.txt`.

## Hostile contract probe

Raw output: `probe-output.txt`; source: `probe.py`. Registration/order, controller-only acceptance, malformed/missing/extra registration, wrong project/execution, stale root, worker role, extra inputs, malformed source ID, and unchanged-state rejection all passed.

### First material failure

`capability_expand` was an **UNEXPECTED_PASS**. A grant containing `project.artifact.write` plus forbidden extra `lifecycle.advance` was accepted and persisted the proposal. The runtime only checks that required capabilities are present; it does not reject extra granted capabilities. This violates the capability-expansion hostile contract and stop-first rule. No repair was attempted.

## Candidate integrity

Candidate status was clean before and after testing. Candidate and baseline identities above are exact. Candidate-vs-baseline paths were `evidence/ticket-16-build/BUILD.md`, `skills/itdd_new/__init__.py`, `skills/manifest.json`, `skills/runtime.py`, and `tests/integration/test_workflow_runtime_registration.py`, matching the BUILD declaration plus its evidence.

# Ticket #16 TEST evidence (fresh execution)

## Verdict: PASS

- Candidate: `dd66558f3bec01119f9d497c653b38997cbd7e37`
- Baseline: `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Worktree: `/tmp/ticket-16-build-final`
- TEST only; candidate was not modified. VERIFY was not run.

## Evidence

- Targeted suite: `31 passed` (`targeted.txt`), including installer propagation and accepted ticket-2 grill contract regression.
- Full suite: `197 passed` (`full-suite.txt`).
- Hostile/positive probe: `probe.py`, `probe-output.txt`. It passed exact workflow registration/order and identity, tamper/malformed/missing/extra registration, controller-only acceptance, four-field project/execution/root/baseline binding rejection, exact capability-set equality with forbidden extra and unchanged state, forbidden worker role, extra inputs, malformed source IDs, fresh reconstruction, and clean proposal invocation.
- Direct controller relative/absolute path rejection with unchanged state: `supplemental.py`, `supplemental-output.txt`.
- Exact changed-path allowlist: `skills/runtime.py`, `skills/manifest.json`, `skills/itdd_new/__init__.py`, `tests/integration/test_workflow_runtime_registration.py`, `evidence/ticket-16-build/BUILD.md`; candidate status clean after testing.

All required phases completed without material failure. Acceptance returned `OBSERVED`, `authority=controller`, `lifecycle_effect=none`, `promotion_effect=none`; invocation returned `PROPOSAL_ONLY`, `authority=none`.

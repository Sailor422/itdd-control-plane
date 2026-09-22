# GRILLING clarification frontier

Execution identity: fresh sub-agent `itdd21-grilling`, RLM child id `sub-e38ec296`; session artifacts `/Users/herbertfields/.prime/agent/session-artifacts/01a0c9a1-c6cf-7659-a446-ada53a2f1aee/sub-e38ec296`.

1. Choose the immutable source and baseline: issue #21 plus parent #15; choose exact commit. Options: current `main` HEAD `80284553d571d5d92e2a8f66b7b8c312f9c283ef` (use a fresh isolated workspace, not the dirty checkout) or historical failed-run baseline `bc2b53b6b989cac8ad9ad5948385fe2a65799669`.
2. Confirm bounded scope: recommend integration/promotion behavior only, with exact file paths derived during read-only research and then listed in the final contract. Exclude unrelated dirty files, worktrees, historical evidence, and unrelated tickets; append new evidence without replacing old.
3. Confirm prior TEST/VERIFY gaps are acceptance obligations: recommend yes, each with discrete probes; otherwise identify deferred gaps.
4. Confirm evidence obligations: exact baseline/candidate/tree, commands/environment/results, raw outputs, non-mutation assertions, actual conflict/abort/no-commit/tree probes, schema/order/chronology, fresh reconstruction, role provenance, reviews. Clarify acceptable pytest import-shim policy and whether independent Standards/Spec evidence remains required.
5. Entry point: issue says `/implement`; current repo handoff says `/idd`; `itdd-prepare` says `/itdd-execute`. Select the supported sequence. User's prior request names `/idd`; recommendation is `/itdd-prepare` then `/idd` as the public entry, with `implement` only as its isolated BUILD role.
6. Exact-contract approval is still required by `itdd-prepare`. Prior request authorizes moving toward execution after preparation, but not approval of an unseen baseline/path/acceptance contract.

No code or execution authorized by this report.

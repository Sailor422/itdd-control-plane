# TEST Evidence — Issue #2 combined candidate

- Result: **TEST PASS**
- Candidate: `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Baseline: `db09daa966a14099ef18cba548b6f608cea5a18b`
- Worktree: `/Users/herbertfields/itdd-control-plane/.worktrees/build-ticket-2-combined`
- Raw evidence: `evidence/ticket-2-test-combined/probe-output.txt`
- VERIFY: not run

## Scope / identity

Candidate status was clean before and after testing. Exact diff against baseline:

```text
 control/skills.py                                  |  7 ++-
 skills/runtime.py                                  |  3 ++
 tests/integration/test_grill_with_docs_contract.py | 29 +++++++++-
 work/proofs/ticket-2-build/BUILD.md                | 62 ++++++++++++++++++++++
 4 files changed, 98 insertions(+), 3 deletions(-)
```

No candidate files were modified. Issue #2, BUILD evidence, all prior failed TEST evidence, and diagnoses were read before execution.

## Automated suite

`PYTHONPATH=. pytest -q tests/integration/test_grill_with_docs_contract.py` -> **17 passed in 0.16s**.

## Contract and hostile probes

A fresh-process probe exercised direct controller and runtime seams. Positive creation and fresh-process reconstruction passed. Every rejection preserved an unchanged `.idd` snapshot. Passed cases included unauthorized role, wrong project, wrong execution, stale baseline, relative and absolute path traversal, malformed/missing/extra data, capability expansion, forbidden authority boundaries, tampered proposal history, and tampered event history. Runtime probes also passed wrong-project binding with matching root/execution, path-bearing source IDs, malformed data, missing/extra data, missing capability, and contract-forbidden authority actions.

Observed direct malformed source type rejection was `TypeError` from path resolution before authorization/write; it still left authoritative state unchanged. All other rejection reasons were contract-specific errors. No acceptance boundary was violated, so testing completed rather than stopping early.

## Status

**PASS.** Candidate satisfies the exercised Issue #2 contract. Independent VERIFY remains required before promotion.

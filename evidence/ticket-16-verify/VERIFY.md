# Ticket #16 independent VERIFY evidence

## Verdict: FAIL (2026-09-22)

Execution: fresh verifier process (this agent), PID/process commands run in a clean `git archive` checkout at `/tmp/ticket-16-verify-clean`; no implementation or candidate files were modified. Candidate `9eeae77ed77c5de41d02651ce75294ac6528dcd3`; implementation parent `c7ed6b87ca906d96c885ab98ce0f48b796e8f40a`; exact baseline `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`. The candidate worktree was clean before verification (`git status --porcelain=v1` empty).

## Identity and scope

`git rev-parse HEAD` => `9eeae77ed77c5de41d02651ce75294ac6528dcd3`.
`git diff --name-status ecf530dd2f8318c0cc258509bc8dbb5d86d697ee..HEAD` => exactly:

- `A evidence/ticket-16-build/BUILD.md`
- `M skills/itdd_new/__init__.py`
- `M skills/manifest.json`
- `M skills/runtime.py`
- `A tests/integration/test_workflow_runtime_registration.py`

This matches the BUILD allowlist plus BUILD evidence. No unauthorized path was observed. Historical failed evidence remains preserved in the main checkout. No candidate repair or promotion occurred.

## Independent commands/results

1. `git archive 9eeae77ed77c5de41d02651ce75294ac6528dcd3 | tar -x -C /tmp/ticket-16-verify-clean` — PASS; clean archive used.
2. `pytest -q tests/integration/test_workflow_runtime_registration.py tests/test_itdd_new_bootstrap.py tests/integration/test_grill_with_docs_contract.py` in archive — **FAIL: 5 failed, 25 passed**. Failures include all new runtime wrong-project/capability tests calling `CapabilityGrant` with four fields while the imported runtime constructor rejects the call (`TypeError: CapabilityGrant.__init__() takes 4 positional arguments but 5 were given`), and the direct controller escaped-source test failing to raise `SkillContractError`. Thus the claimed 29-pass TEST result is not reproducible in a clean fresh archive.
3. Independent hostile probe (`verify_probe.py`, adapted only by copying preserved TEST probe) — registration/order, controller-only acceptance, wrong project/execution, worker role, extra input, malformed source ID, stale root, capability expansion, and unchanged-state checks passed. The probe then **FAILED** at `tamper_contract`: changing the contract name to `tampered` was accepted by `SkillRuntime.discover()` (`UNEXPECTED_PASS`). The runtime has no pinned contract identity/hash and accepts this tampered contract. No unauthorized artifact was accepted by the probes before this stop.
4. `pytest -q` in clean archive — **FAIL collection: 16 errors**, including `ModuleNotFoundError: tests` / `tools`; raw terminal output is preserved in the verifier session and reflects clean-archive import-path failure. This is not treated as acceptance evidence.

## Boundary review

`discover_workflow()` verifies ordered names, controller-routed mode, controller authority, local skill files, and BUILD/TEST/VERIFY isolation flags. `validate_workflow_acceptance()` is controller-only and returns `lifecycle_effect: none`, `promotion_effect: none`. `invoke()` validates exact capability set and project/execution/root bindings before writes; hostile rejection snapshots showed unchanged state. However, clean archive targeted tests fail, and contract tampering is accepted. Therefore workflow registration/provenance and acceptance cannot be independently accepted.

## Disposition

FAIL at first material independent invariant. Do not repair this acceptance attempt, rewrite BUILD/TEST evidence, tag, or promote. Preserve this evidence and start a new BUILD → TEST → VERIFY cycle after diagnosis.

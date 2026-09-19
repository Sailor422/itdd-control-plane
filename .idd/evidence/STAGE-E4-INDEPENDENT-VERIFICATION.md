# Stage E4 independent verification

- Stage: E4 Verification Contracts, Evidence Binding, and False-Pass Resistance
- Baseline: `23eba98`
- Candidate implementation: `03eb1a190ba8ed19659c6e8dbef4ab745def1c20`
- Verifier execution: `stage-e4-verifier-20260920T001500Z-clean-checkout`
- Verification checkout: fresh clone of the candidate, with no local modifications

## Commands and results

1. `python3 -m pytest -q tests` — PASS, `66 passed in 0.65s`.
2. JSON parsing of `schemas/verification-contract.schema.json`, `schemas/verification-evidence.schema.json`, and `schemas/verification-result.schema.json` — PASS.
3. `git diff --check` — PASS.
4. `git status --short --branch` in the verifier checkout — clean.

## Acceptance evidence

- Durable VC-001 binds project, execution, verifier role, approved intent/graph/EU, exact baseline/candidate, context packet/hash, checks, artifacts, and allowed paths.
- Contract and evidence artifacts are immutable and SHA-256 protected; event reconstruction verifies materialized records and evaluation results survive restart.
- A valid synthetic EV-001 with exact command, three observed tests, required artifact hash, and authorized changed path evaluates to PASS; a fresh evaluator recomputes PASS.
- Wrong command, wrong count, missing required check, partial suite, missing evidence, missing artifact, artifact tampering, context tampering, evidence tampering, contract tampering, wrong candidate/baseline/context, and unauthorized changed paths fail closed.
- A builder claim without a durable evidence record returns `FAIL_EVIDENCE_MISSING`; no natural-language claim can reach PASS.
- Test evidence records command, exit code, observed count, pass/fail/skip counts, output digest, and timing fields; the evaluator enforces command identity and count.
- Required artifact paths are re-hashed from the project root. Changed paths are checked for lexical traversal and contract allowance.
- Stage B through E3 regressions remain green: all 66 tests passed.

## Limitations

E4 prepares role provenance for future verifier executions but does not launch live Verifiers, Standards Reviewers, repair loops, or orchestration. Changed-path evidence is supplied by the future verifier record rather than independently attested by a VCS integration. It does not defend against a malicious OS-user process, compromised test tooling/runtime, unverifiable external services, or deliberate human modification outside ITDD.

# Stage E5 independent verification

- Stage: E5 Live Spec Verifier and Standards Reviewer Orchestration
- Baseline: `f1fa59ab95deab9cf62c4a6704362a9f7219f9fb`
- Candidate implementation: `34f58b76c678e3f8091b803e4ef9ade018fb04fa`
- Verifier execution: `stage-e5-verifier-20260920T011500Z-clean-checkout`
- Verification checkout: fresh clone of the candidate, with no local modifications

## Commands and results

1. `python3 -m pytest -q tests` — PASS, `74 passed in 1.89s`.
2. JSON parsing of all three E4 verification schemas — PASS.
3. `git diff --check` — PASS.
4. `git status --short --branch` in the verifier checkout — clean.

## Acceptance evidence

- Controller-owned `VerifierOrchestrator` creates lifecycle records, issues distinct Stage D capabilities, compiles distinct role packets, creates E4 contracts, launches the adapter, records evidence, evaluates evidence, and derives candidate status.
- `SubprocessVerifierAdapter` runs Spec and Standards commands in separate fresh subprocesses and returns structured output; it has no authority to issue capabilities, alter candidates, or promote state.
- Positive fixture proves distinct Spec and Standards execution IDs, capability IDs, context packet IDs, roles, and contracts. Both E4 PASS results derive `VERIFIED`; a fresh orchestrator reconstructs the same result.
- Spec failure cannot be overridden by Standards PASS. Standards failure cannot be overridden by Spec PASS. A candidate with only one axis, an interrupted execution, or a different candidate SHA remains `NOT_VERIFIED`.
- Verifier implementation writes are denied by Stage D; evidence-area writes are allowed only within the explicit role envelope.
- Builder-role evidence is rejected against a verifier contract. Reusing one execution for both roles is rejected before launch. E4 remains the only evidence evaluator.
- Spec and Standards packets contain different role-specific resources. The Standards fixture is explicit and project-local; no global skills, vaults, or retrieval sources are used.
- Stage B through E4 regressions remain green: all 74 tests passed.

## Limitations

The current adapter proves fresh subprocess separation, not OS-level containment. Changed candidate content is represented by exact candidate SHA bindings; there is no VCS attestation layer yet. Test tooling/runtime compromise, unrestricted same-user processes, human views, repair loops, integration orchestration, parallelism, knowledge retrieval, promotion, and later lifecycle stages remain out of scope.

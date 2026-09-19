# Stage E5 implementation plan

Baseline: `f1fa59ab95deab9cf62c4a6704362a9f7219f9fb`

| Requirement | Acceptance | Implementation | Evidence |
|---|---|---|---|
| Controller-owned launch | Builder/verifier cannot self-launch; controller creates durable verifier executions and capabilities | `VerifierOrchestrator` and `VerifierExecutionStore` | E5 integration tests |
| Runtime boundary | Fresh process returns structured observations without embedding runtime policy in models | `SubprocessVerifierAdapter` | fresh-process positive proof |
| Separate axes/context | Spec and Standards use distinct executions, capabilities, packets, contracts, and roles | role-specific packet/contract creation | provenance/isolation tests |
| No repair | Verifier capabilities allow reads/execute and evidence-area writes only; implementation write is denied | Stage D authorization check at write boundary | negative test |
| E4 evidence path | Both live results become E4 evidence and are mechanically evaluated | adapter output -> evidence -> `EvidenceEvaluator` | positive/failure tests |
| Derived verification | Candidate is VERIFIED only from independent Spec PASS and Standards PASS | `derive_candidate_status` | two-axis tests/restart |
| Failure/recovery | Candidate failure, missing context, wrong role/candidate, and interruption never become VERIFIED | explicit execution states and fail-closed derivation | negative tests |

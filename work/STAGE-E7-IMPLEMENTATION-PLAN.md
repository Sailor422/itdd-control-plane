# Stage E7 Implementation Plan

| Requirement | Acceptance | Implementation | Evidence |
|---|---|---|---|
| Git-attested candidates | Real baseline/candidate/tree/repository and Git-derived paths | `control/git.py` | `test_git_attestation...` |
| Evidence binding | E5 Spec + Standards results must match attested commit | `IntegrationController._eligible` | positive and missing-approval tests |
| Controlled Integrator | Controller-created capability, packet, branch/worktree, result | `control/integration.py` | isolated integration test |
| Conflict routing | Mechanical conflict vs semantic replan are durable states | `IntegrationController.run` | semantic failure test |
| Fresh integration verification | Distinct `INTEGRATION_VERIFIER` through E4 evaluator | `create_integration_verifier` | positive test |
| Integration human gate | Exact result commit/verifier result binding, append-only decision | E6 `HumanGateController` extension | positive test |
| Projection/restart | E6 generator reads durable integration state | `HumanViewGenerator` | full regression and clean-checkout evidence |

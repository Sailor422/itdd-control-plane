# Stage D Implementation Plan

Baseline: `2e8f00246349494a2fc3b6f2607415be0551969e` (`stage-c-intent-graph-pass`)

| Requirement | Planned change | Verification |
|---|---|---|
| Roles and deny-by-default capabilities | `control/authorization/roles.py`, capability model, schemas | role/schema tests |
| Exact project/execution/baseline/scope binding | controller decision function | binding negative tests |
| Path-bound authority | reuse `resolve_project_path` for exact grants | traversal/symlink tests |
| Operation-bound authority and human-only actions | explicit operation allow list and human-only policy | role/operation tests |
| Trusted issuance and immutable history | project-local capability artifacts plus Stage B events | issuance/tamper/restart tests |
| Independent evidence | Stage D evidence and clean-checkout verifier | full regression |

Decisions: allow-first authorization; an envelope is immutable and integrity-bound; exact file grants are used for this stage; no OS-user sandbox claim is made; denied decisions are auditable when the caller supplies an event identity.

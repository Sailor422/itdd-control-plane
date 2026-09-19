# Stage D: roles and capability authorization

Stage D makes the controller—not agent reasoning—the authority boundary. A role definition describes potential operations only. A durable capability envelope grants a specific role, execution, project, baseline, optional artifact scope, and explicit allow-list. Nothing is permitted merely because it is absent from `forbidden_operations`.

The controller checks, in order, capability integrity, project/execution/baseline identity, role identity, human-only policy, explicit operation grant, path grant through the Stage B `resolve_project_path()` boundary, and optional intent/graph/EU bindings. It returns a structured `ALLOW` or `DENY` with deterministic reason codes such as `DENY_PATH_NOT_GRANTED`, `DENY_SCOPE_ESCAPE`, and `DENY_OPERATION_NOT_GRANTED`.

Capability artifacts live under `.idd/capabilities/` and are issued only through the controller/human issuance path. Issuance is recorded in the Stage B event chain; authorization decisions can also be recorded with an event identity. Materialized artifacts are checked against event reconstruction before a decision, so tampering fails closed. Capability files are immutable by version.

Role separation is policy, not trust in a role name: builders cannot approve intent, alter graphs, write verifier evidence, or promote; verifiers have read/test/evidence potential but no implementation write grant; promoters receive only a specifically granted transition; and controllers do not receive general implementation authority.

Threat model: this protects against accidental overreach, agent desire exceeding authority, path expansion, cross-execution/project/baseline reuse, lifecycle misuse, and self-escalation. It does not prevent a malicious process with the OS user's unrestricted permissions, direct manual edits outside ITDD, kernel/root compromise, or full sandbox escape. The Stage A Codex trust finding remains unchanged.

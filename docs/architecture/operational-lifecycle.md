# Operational single-EU lifecycle

`control.operational.OperationalController` composes the accepted Stage B-E7
controls into the first usable ITDD path. It is intentionally a thin
controller-owned orchestration layer; it does not replace intent, graph,
capability, context, verification, Git-attestation, or human-gate stores.

The supported path is:

1. An approved intent is required before a plan can be proposed.
2. The planner creates a versioned graph and explicit per-EU path scopes.
3. A fresh Graph Evaluator validates the Planner proposal; a valid graph becomes
   active without a new human lifecycle gate.
4. The controller creates a builder worktree, capability, and compiled context.
5. A builder adapter performs work and leaves only authorized filesystem
   changes; it has no candidate-commit authority.
6. The controller independently validates the worktree diff, stages only the
   authorized paths, creates the candidate commit, and attests that commit
   before launching fresh Spec and Standards verifier executions against the
   builder worktree.
7. Two passing, independently evaluated axes make the EU eligible for the
   controller-owned integration path; routine EU completion does not create a
   HUMAN_ONLY gate.
8. The controller determines integration eligibility, runs the Integrator and
   Integration Verifier, and promotes when the approved intent authorizes that
   transition. HUMAN_ONLY documents are reserved for new authority such as an
   intent amendment, maintenance, break-glass, or unresolved ambiguity.

`CodexBuilderAdapter` launches one fresh non-interactive Codex worker with the
compiled packet and capability envelope. The worker receives path-scoped
capability and context metadata and cannot commit, advance lifecycle state, or
issue evidence. The controller records the worker provenance, validates the
resulting worktree diff, and owns the Git commit. `SubprocessBuilderAdapter`
remains runtime-neutral for controlled non-Codex adapters and tests.

The implementation currently targets one EU in `OperationalController`; the
accepted Stage E7 `IntegrationController` provides the controller-owned
multi-EU integration primitive. Neither path inserts routine human approvals
between deterministic lifecycle stages.

# Git-Attested Candidates and Controlled Integration

Stage E7 makes a candidate identity meaningful by resolving it to an actual
commit in the project repository. The controller records the baseline commit,
candidate commit, candidate tree, repository identity, and paths produced by a
Git comparison. A verifier-supplied path list cannot replace that observation.

Only candidates with independent E5 Spec and Standards PASS results and the
required E6 human approvals enter integration. The controller creates an
Integrator capability and capability-bound context packet, then creates a
dedicated `.idd/integration_workspaces/<id>` Git worktree. Integrator output is
an integration candidate, never canonical promotion.

Integration verification uses a distinct `INTEGRATION_VERIFIER` execution and
the existing E4 contract/evidence/evaluator path. A passing result becomes
`INTEGRATION_VERIFIED`, after which E6 gate machinery creates an exact
`INTEGRATION_APPROVAL` gate. Semantic conflicts route to `REPLAN_REQUIRED` and
no repair or promotion is attempted.

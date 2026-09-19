# Stage E5: live verifier orchestration

Stage E5 adds the smallest controller-owned execution boundary for two independent verification axes. `SPEC_VERIFIER` answers whether the candidate satisfies the approved EU contract and required checks. `STANDARDS_REVIEWER` answers whether it meets explicitly supplied project standards. Each receives a distinct capability, execution identity, context packet, and E4 verification contract. Neither role inherits Builder context or can launch itself.

The runtime-neutral `VerifierAdapter` returns structured observations from a fresh process. The current `SubprocessVerifierAdapter` is intentionally small and isolated at the adapter boundary; it does not issue capabilities, write candidate files, promote state, or decide PASS. The controller records execution lifecycle, converts adapter output to E4 evidence, and invokes the existing mechanical evaluator.

Verifier capabilities allow exact reads, authorized verification commands, and evidence-area writes only. Implementation writes are denied by the Stage D controller. A verifier defect is reported through failed evidence or an interrupted execution; there is no repair loop. Candidate `VERIFIED` is derived only when distinct completed Spec and Standards executions each have valid E4 PASS results for the same candidate.

Fresh subprocess execution is proven for the fixture. This is not OS-level containment: an unrestricted process running as the same user could still bypass the controller, and test tooling/runtime integrity is not independently attested. Human views, Obsidian, integration orchestration, parallelism, retrieval, promotion, and later lifecycle stages remain out of scope.

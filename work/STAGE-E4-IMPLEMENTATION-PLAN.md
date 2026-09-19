# Stage E4 implementation plan

Baseline: `23eba98`

| Requirement | Acceptance | Implementation | Evidence |
|---|---|---|---|
| Durable verification contract | Success criteria are versioned, bound, and immutable before evaluation | `VerificationStore.create_contract` and contract schema | E4 integration tests |
| Execution-bound evidence | Evidence exactly matches project, execution, role, intent/graph/EU, baseline, candidate, packet/hash, and contract | `VerificationStore.record_evidence` and semantic validator | Binding negative tests |
| Mechanical evaluation | PASS requires valid contract, evidence, checks, artifacts, paths, hashes, and no failures | `EvidenceEvaluator.evaluate` with stable reason codes | Positive/negative tests |
| Test false-pass resistance | Wrong command/count/partial suite/exit code cannot pass | Explicit TEST_COMMAND check vocabulary and check identity/count validation | E4 negative tests |
| Provenance/tamper resistance | Claims, missing artifacts, tampered records/contracts, stale candidates fail | SHA-256 integrity and durable event reconstruction | Tamper/restart tests |
| Earlier-stage compatibility | Stage B–E3 controls remain green | No changes to authority, context packet, or map authority | Full regression suite and clean checkout |

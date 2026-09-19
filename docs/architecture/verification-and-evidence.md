# Stage E4: verification contracts and evidence

Stage E4 separates a success claim from accepted proof. A durable verification contract is created before evidence evaluation and binds the project, execution, role, approved intent and graph, EU, exact baseline and candidate, context packet/hash, required checks, required artifacts, and allowed changed paths. The contract is immutable; changing acceptance criteria requires a new contract identity.

Evidence is a durable, hash-protected record produced by a future verifier execution. It must exactly match every contract binding. Test evidence records the command, exit code, observed count, pass/fail/skip counts, and result digest fields needed by the contract. Required artifact paths are re-hashed from the project root, and observed changed paths must remain within the contract envelope. A builder statement or missing evidence cannot produce PASS.

The evaluator is deterministic and returns `PASS` only when the contract, evidence, context packet, required checks, test counts, artifacts, hashes, and changed paths all satisfy their bindings. Otherwise it returns `FAIL` with a reason code. Evaluation results are durable and reconstructable, but are derived from the contract and evidence rather than an unaudited Boolean.

This layer protects against stale or reused proof, wrong candidate/baseline/context, wrong command, partial test suites, unauthorized files, missing or tampered artifacts, tampered contracts/evidence, and self-certification. It does not yet protect against a malicious OS-user process, compromised test tooling/runtime, unverifiable external services, or deliberate human modification outside ITDD.

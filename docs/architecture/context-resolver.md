# Stage E2: Scout and controlled resolution

Workers submit durable E1 Context Requests. A separately issued `SCOUT` capability permits a Scout/Resolver to search one explicit project-local scope using deterministic filename/text matching. The search is bounded by files, bytes, and result count, and records its scope and counters. It never searches home directories, legacy vaults, unrelated projects, or symlink escapes.

The result is a structured immutable resolution artifact containing exact canonical paths, optional symbols, match type, source, content hash, candidates, selected findings, exclusions, status, and search trace. `AMBIGUOUS`, `NOT_FOUND`, and `PARTIALLY_RESOLVED` are honest outcomes; only a unique `RESOLVED` result is eligible for compiler acceptance.

The compiler validates request and resolution provenance, project/execution/baseline bindings, exact paths, and the worker’s current capability before creating a new packet. Scout cannot write implementation files, modify intent/graph/capabilities, or mutate an existing packet. A discovered path outside the worker’s grant remains excluded.

Scout discovers. Compiler selects. Controller authorizes. Worker acts.

Project Map, semantic retrieval, and orchestration remain future work.

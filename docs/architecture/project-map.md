# Stage E3: derived Project Map

The Project Map is a versioned, project-local structural index of files, deterministic Python symbols/imports, tests, schemas, durable intent requirements, graph execution-unit edges, and evidence references. **Project Map describes project reality; it does not define project authority.** Intent, graph, capability, event, context-packet, and verification artifacts remain authoritative in their existing stores.

Generation is a full rebuild from the canonical project root and reconstructed Stage C state. Traversal is sorted and excludes Git metadata, caches, build output, virtual environments, explicit private directories, external legacy stores, symlinks, and the derived map directory. Each map binds to an exact baseline SHA and contains a SHA-256 hash of canonical JSON excluding the hash field. Deleting the derived artifact and rebuilding from the same baseline and durable state must reproduce the same map and hash.

Scout may use a valid current map for exact structural matches before Stage E2 bounded deterministic search. A stale or tampered map is rejected; an absent map falls back safely. Map findings remain untrusted context candidates and pass through the existing Context Compiler and capability gate before a worker packet is revised. The map never grants worker authority.

Stage E3 deliberately does not provide semantic retrieval, orchestration, Obsidian rendering, or incremental indexing. A future incremental strategy may reuse content hashes and per-directory manifests, but full rebuild remains the correctness reference. Future traceability is `Intent Requirement -> Execution Unit -> File/Symbol -> Test -> Verification Evidence -> Integration Result`.

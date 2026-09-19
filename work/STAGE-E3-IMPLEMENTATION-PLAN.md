# Stage E3 implementation plan

Baseline: `a3b1fa1e19dcf7155c3f51d2653e689382b0d7e1`

| Requirement | Acceptance | Implementation | Evidence |
|---|---|---|---|
| Derived structural map | Project-local files, symbols, imports, tests, schemas, intent and graph bindings | `control/project_map.py` | E3 positive tests |
| Deterministic rebuild/hash | Same baseline/state yields identical canonical map | Sorted walk, canonical JSON, SHA-256 | Restart test |
| Isolation and staleness | Escapes/private/legacy paths excluded; mismatched baseline rejected | Root path checks, explicit exclusions, baseline validation | Negative tests |
| Map-first Scout | Valid exact symbol hit uses map; misses retain E2 search | Scout integration | Integration/negative tests |
| Authority separation | Map remains derived and Compiler-gated | Read-only map store and existing compiler path | Regression tests |

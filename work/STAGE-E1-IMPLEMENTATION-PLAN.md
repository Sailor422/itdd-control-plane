# Stage E1 Implementation Plan

Baseline: `777a0f6019bbe49258ca0c639212277d3bc8ff05` (`stage-d-capability-authorization-pass`)

| Requirement | Planned change | Verification |
|---|---|---|
| Explicit packet and resource models | `control/context/compiler.py`, packet/resource schemas | model and schema tests |
| Capability intersection and path authority | compiler delegates exact checks to Stage D controller and Stage B resolver | unauthorized, traversal, symlink tests |
| Provenance, bindings, immutable hashing, budget | canonical packet artifacts with SHA-256 and deterministic byte budget | hash/budget/binding tests |
| Controlled requests | capability-gated durable request artifacts; no resolver/search | request and legacy-path tests |
| Event reconstruction | packet/request events and fresh-process reducer | restart test |
| Traceable evidence | architecture/result/evidence artifacts | clean-checkout verification |

Decisions: only explicitly supplied resources are considered; required resources fail closed at the budget boundary; knowledge remains empty or explicitly supplied; packet compilation never searches project or user directories; a request is not authority.

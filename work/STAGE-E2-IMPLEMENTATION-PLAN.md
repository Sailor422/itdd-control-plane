# Stage E2 Implementation Plan

Baseline: `a2efa4b454e2b99ed88192fe4248162e276532c7` (`stage-e1-context-compiler-pass`)

| Requirement | Planned change | Verification |
|---|---|---|
| Narrow Scout authority | `RESOLVE_CONTEXT` capability and directory-scoped Stage D checks | role/authority negatives |
| Durable request intake and resolution result | `ScoutResolver`, resolution model/schema, event-backed artifacts | lifecycle/reconstruction tests |
| Deterministic bounded search | exact project-local filename/text scan with file/byte/result limits | positive, ambiguity, not-found, budget tests |
| Compiler gatekeeper and packet revision | resolution-bound compiler method creates new packet only after worker capability checks | authorized/unauthorized result tests |
| Isolation and provenance | canonical paths, trace, project/execution/baseline bindings, no external stores | traversal/legacy/unrelated tests |
| Traceable evidence | E2 plan, architecture/result/evidence artifacts | fresh-checkout verification |

Decisions: deterministic project-local search only; no semantic retrieval or Project Map; ambiguous results are never silently selected; a resolution is discovery evidence, not worker authority; CP-001, CR-001, SR-001, and CP-002 are immutable and separately reconstructable.

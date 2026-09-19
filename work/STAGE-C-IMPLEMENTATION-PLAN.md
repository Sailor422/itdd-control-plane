# Stage C Implementation Plan

Status: authorized for implementation  
Baseline: `4e69db26b0d9c7b54035f5bb3dbfc7a372cf0fae`  
Scope: durable intent authority, versioned execution graphs, event integration, and reconstruction

## Traceability

| Requirement | Acceptance | Planned change | Verification |
|---|---|---|---|
| Intent model | Versioned draft/approved/superseded intent with stable requirements | `control/models/intent.py`, `schemas/intent.schema.json` | Model and schema tests |
| Human approval | Only a human actor can approve; approved version rejects normal mutation | `control/models/store.py` | Approval and mutation-negative tests |
| Graph model | Explicit intent binding, stable EUs, dependency edges, DAG validation | `control/models/graph.py`, `schemas/graph.schema.json` | Graph semantic negative tests |
| Graph versioning | Revisions create new immutable version files and preserve prior versions | `control/models/store.py` | Revision/history tests |
| Event integration | Draft, approval, creation, and revision transitions append events | `control/models/store.py` | Event-chain and reconstruction tests |
| Restart proof | Fresh process reconstructs approved intent, active graph, and prior graph | `control/models/store.py` | End-to-end subprocess test |
| Documentation | Intent/graph authority distinction and limits are explicit | `docs/architecture/intent-and-graph.md` | Independent documentation inspection |

## Decisions

- Intent requirements are objects with stable `requirement_id` values and text.
- Graph edges use `from` prerequisite -> `to` dependent orientation.
- Execution graphs are DAGs; cycles are rejected because scheduling needs an acyclic dependency relation.
- Artifacts are stored under `.idd/intent/<intent-id>/v<version>.json` and `.idd/graph/<graph-id>/v<version>.json`.
- Event payloads carry the complete transition artifact so durable event replay does not depend on chat or process memory.
- Graph revisions preserve previous graph files and bind every version explicitly to `intent_id` and `intent_version`.
- Normal APIs reject approved-intent changes and agent-originated approval. OS users can still edit files outside the API; verification detects divergence where possible.

## Out of scope

Intent grilling, amendments, replans, Context Compiler, Scout, Project Map, Builder, Verifier, Integrator, Promoter, UI, parallel execution, vault migration, global Codex settings, Prime, maintenance, and break-glass.


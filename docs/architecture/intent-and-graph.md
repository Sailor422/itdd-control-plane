# Durable Intent and Mutable Execution Graph

## Core distinction

Intent is durable human authority: it records the approved destination and stable requirement identities. The execution graph is versioned strategy: it records how the system currently proposes to reach that destination. A graph revision may change decomposition and dependencies without changing the approved intent.

Every graph version explicitly binds `intent_id` and `intent_version`. The graph cannot rely on a directory's “current intent.” Graph edges use `from` prerequisite -> `to` dependent orientation. Graphs are DAGs; cycles are rejected because controller scheduling requires acyclic dependencies.

## Intent lifecycle and human authority

Stage C supports `DRAFT`, `APPROVED`, and `SUPERSEDED` intent statuses. A draft may be proposed by an agent, but `intent.approved` requires `actor_type=human`. Once approved, normal APIs reject mutation of that version. A future Intent Amendment mechanism may create a new intent version; it is not implemented here.

Approval is recorded in the Stage B append-only event history with the complete approved artifact, approval actor, timestamp, and event identity. Replaying the history reconstructs the approved intent without chat context.

## Graph versioning

Graph `G-001 v1` and `G-001 v2` are separate immutable artifact files. A revision records `previous_version`, reason, source event, and the exact intent binding. The latest graph transition is the active graph; prior versions remain reconstructable. A future Replan Request mechanism may govern how revisions are proposed and reviewed.

## Threat model and limits

Normal Stage C APIs prevent silent approved-intent mutation, agent approval, wrong intent binding, invalid requirements, duplicate execution-unit identities, invalid edges, self-dependencies, and cycles. Materialized artifacts can be checked against event history.

This is not OS-level immutability. A user or malicious process with filesystem permissions can rewrite artifacts and event files outside the API. Stage B integrity checks and Stage C artifact verification detect ordinary divergence where the event history remains intact; they cannot defeat a hostile administrator who rewrites every source of evidence.

## Future extension points

Intent Amendment, Replan Request, richer Execution Units, Project Map traceability, and controller eligibility checks build on these durable bindings. Builder, Verifier, Integrator, Promoter, Context Compiler, Scout, UI, and parallel execution remain outside Stage C.


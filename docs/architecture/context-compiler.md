# Stage E1: bounded context compiler

The Context Compiler converts already-resolved inputs into the smallest sufficient packet for one role, execution, project, baseline, capability, and optional intent/graph/EU scope. Workers receive exact canonical resources with purpose, authority, inclusion reason, source, and freshness/version. They do not receive a vague task and permission to discover context.

The compiler consumes a Stage D capability; it never grants authority. Each resource is checked by the existing controller and `resolve_project_path()` boundary. A `WRITE` grant for one file cannot make another file appear in the packet. A packet compiled for another execution, project, baseline, or capability is rejected.

Packets are immutable versioned artifacts with deterministic canonical SHA-256 hashes and an explicit byte budget. Required content that cannot fit produces `CONTEXT_COMPILATION_FAILED: REQUIRED_CONTEXT_EXCEEDS_BUDGET`; there is no deceptive partial packet. Knowledge and evidence are explicit lists, not retrieval channels.

A worker with `REQUEST_CONTEXT` may create a durable Context Request containing the missing resource or question, reason, and expected use. The request does not grant search authority and Stage E1 does not resolve it. Scout/resolver behavior is deferred to Stage E2. No `.codex`, `.claude`, `.hermes`, legacy vault, or chat history is queried.

The system may know a great deal. The worker receives only the subset required and authorized for its current task.

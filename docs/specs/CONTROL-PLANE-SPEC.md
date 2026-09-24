# ITDD Control Plane Specification

## Status and scope

This is the proposed architecture derived from a historical bootstrap handoff, summarized in `CODEX-BOOTSTRAP-SPEC.md`. It is not a claim that the repository already implements it. The initial authorized scope ends at bootstrap, Stage A audit, research analysis, and a proposed Stage B plan.

## 1. Authority model

The core invariant is: **agents reason; the controller decides what actions are legal**. Human-approved intent is durable authority. The execution graph and plan are versioned mutable state. Replanning changes the route; an intent amendment changes the authorized destination. Approved intent versions are immutable and changes must be explicit, reviewed, and append-only.

The controller validates, authorizes, launches, stops, transitions, and records. It does not invent requirements, design the application, write normal implementation code, or alter human intent. No worker may launch or promote another role. Skills provide procedure, never authority.

## 2. Project authority domain

Each controlled project is self-contained under its repository root: intent, graph, state, evidence, telemetry, knowledge, context packets, project map, approvals, tests, implementation, documentation, and recovery state. External material enters only through explicit, recorded import or retrieval. Legacy vaults remain untrusted source archives and are never default context.

The canonical repository is durable authority. Worker branches/worktrees are disposable. Failed attempts remain represented in evidence even when they do not reach the canonical branch.

## 3. Lifecycle and roles

The authoritative flow is `PROPOSED -> APPROVED -> READY -> BUILDING -> VERIFYING -> HUMAN REVIEW -> INTEGRATING -> INTEGRATION VERIFY -> PROMOTED -> DONE`, with `BLOCKED`, `NEEDS CLARIFICATION`, `REPLAN REQUIRED`, `INTENT AMENDMENT REQUIRED`, `FAILED`, `INTERRUPTED`, and `ABANDONED` as explicit states.

Roles are conceptually separate: Conversational Agent/Prime, Planner, Graph Evaluator, Scout/Context Resolver, Context Compiler, Builder, Spec Verifier, Standards Reviewer, Integrator, Integration Verifier, Promoter, and Controller. Initially, humans approve intent, the initial graph, independently verified EU work, material integration, final promotion, significant replans, amendments, and controller changes.

## 4. Intent, graph, and execution units

Intent development may begin in conversation, but `/idd` starts formal intent work. Intent work clarifies terminology, assumptions, ambiguity, and decisions; it performs no implementation. The Planner proposes behavior-oriented vertical tracer-bullet execution units and dependencies. The Graph Evaluator independently checks meaning, verticality, provability, size, interfaces, parallelism, architecture coverage, and intent alignment. Initially, graph approval is human-only.

Each EU defines behavior, acceptance criteria, blockers, dependencies, allowed files, tests/evidence, integration assumptions, and human-review requirements. Its size is an empirical question measured through telemetry, not a universal constant.

## 5. Capability and context boundaries

Workers receive capability-based authority enforced through filesystem, sandbox, Git, and controller mechanisms where practical. A Builder packet binds role, execution ID, EU, baseline SHA, exact read/write/execute scope, and forbidden operations. Builders and Verifiers do not casually hunt the filesystem.

The Context Compiler supplies resolved context, not open-ended discovery. Packets separate Authority, Working, Knowledge, and Evidence Context and record source, reason, authority, freshness, related EU, and token cost where measurable. Priority is authority, EU contract, acceptance, dependency contracts, working files, relevant knowledge, then history. Additional material requires a structured context request resolved by Scout and Compiler.

## 6. Project map and knowledge

The Project Map is derived, rebuildable state covering files, symbols, imports, dependencies, APIs, contracts, architecture, tests, EUs, findings, requirements, knowledge relationships, and history. Desired traceability is `Intent Requirement -> EU -> File/Symbol -> Test -> Verification Evidence -> Integration Result`.

Knowledge is separate from context and is classified as Project Truth, Historical Evidence, Learned Operational Knowledge, or External Reference Knowledge. Authority is ordered: authoritative state, verified project knowledge, validated operational knowledge, historical observation, external reference. Observations become policy only through `Observation -> Pattern -> Candidate Rule -> Validated Rule -> Policy` with human approval.

## 7. Evidence and verification

Acceptance is defined before implementation wherever practical. Evidence binds `intent_version`, `graph_version`, `eu_id`, `execution_id`, `role`, `baseline_sha`, `candidate_sha`, `context_packet_hash`, test command, observed result, artifact hashes, and timestamp. Absence of proof is never success.

The design explicitly resists wrong or partial tests, stale or pre-change evidence, wrong branches, Builder self-certification, provenance mismatch, unauthorized writes, and missing artifacts. Spec Verification asks whether the EU contract is satisfied. Standards Review independently asks whether implementation and architecture standards are satisfied. Neither substitutes for the other.

## 8. Integration, recovery, maintenance

Verified EUs are not automatically globally correct. Integrators may combine approved work and perform narrow mechanics; substantive redesign stops for replan and fresh Integration Verification. Worker death without completion evidence yields `INTERRUPTED`; a dead Verifier never yields PASS.

Maintenance Mode freezes normal execution, snapshots state, preserves the known-good controller, uses a dedicated repair branch/worktree, runs control regression tests, and requires human activation approval. A human-only break-glass path freezes execution, snapshots state, records controller SHA, creates a unique nonce, obtains confirmation, records reason, creates repair environment, and preserves the prior controller. Exit requires regression and recovery proof, a new SHA, explicit approval, and an append-only activation record; old approvals are not reusable.

## 9. Telemetry and visualization

Telemetry records context size and misses, sources, tokens, retries, verifier/standards failures, integration conflicts, test effectiveness, human corrections, graph revisions, EU size, interruptions, duration, failure class, retrieval, and promotion outcomes. Telemetry informs policy but does not become policy automatically. Obsidian is a human visualization layer, never authority, with operational and teaching views over controller/project state.

## 10. Failure routing and rollout gate

Implementation defects return to Builder; missing context to Scout/Compiler; bad decomposition to Replan; ambiguity to human clarification; destination change to Intent Amendment; integration conflict to Replan; control failure freezes execution for maintenance. Graph revisions preserve prior versions, reasons, affected EUs/dependencies, evidence validity, and intent relationship.

Parallel EU execution is prohibited until a reliable single-EU path exists. The rollout sequence is isolation and durable state, intent/graph, roles/capabilities, context compiler, Scout, Project Map, human views, independent review, evidence/false-pass resistance, single-EU proof, recovery, integration, parallelism, replanning, project-local knowledge, legacy curation, maintenance, and break-glass.


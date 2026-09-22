# Intent Proposal: Complete the ITDD Control Plane Architectural Vision

**Intent ID:** PROPOSAL-FULL-VISION-001  
**Status:** CLARIFICATION PROPOSAL — NOT APPROVED  
**Created:** 2026-09-22  
**Owner:** Human authority required  
**Source:** User request in the originating conversation: “create a plan to complete the full architectural vision and save it as a new intent doc per the itdd control plane procedure so it can follow the full idd tdd enforced cycle”

## Authority and procedure boundary

This document is a durable planning artifact, not an approved ITDD intent, execution contract, graph, capability, or lifecycle command. It grants no implementation authority.

The approved route for every implementation milestone is:

1. `/idd` routes unbounded work to `/itdd-prepare`.
2. Preparation runs six fresh phases: DISCOVERY, GRILLING, RESEARCH, SPEC/TICKET DECOMPOSITION, EXECUTION-CONTRACT DRAFTING, and INDEPENDENT REVIEW.
3. A human explicitly approves the exact contract, including source, baseline, paths, criteria, tests, artifacts, exclusions, and evidence obligations.
4. `/idd` hands the approved contract to `/itdd-execute`.
5. `/itdd-execute` runs separate fresh BUILD, TEST, and VERIFY executions in isolated controller workspaces.
6. The controller alone accepts evidence and advances lifecycle state.

No phase agent, skill, Prime session, Builder, Tester, or Verifier may approve this proposal, create authority, promote a candidate, or broaden scope.

## Problem

The repository has a strong single-EU and evidence-oriented foundation, but the complete architectural vision described in `full-itdd-stack.md`, `docs/specs/CONTROL-PLANE-SPEC.md`, and `ROADMAP.md` is not yet complete. The remaining work must add recovery, controller-owned execution admission, integration and promotion, operational telemetry, advisory knowledge, real-system proof, and earned autonomy without weakening authority boundaries.

The current repository also has an explicit prerequisite gap: issue #27 defines the Prime-native RLM execution handoff and issue #28 defines durable ITDD execution assignments and evidence custody. Existing preparation evidence for ticket 21 records that manually spawning workers and copying results would bypass the controller boundary. Therefore #28 must establish the supported route before later governed implementation work is admitted.

## Desired outcome

A human-authorized, Prime-orchestrated, ITDD-controlled engineering system in which:

- Prime plans, converses, observes, and recommends but does not directly mutate project code.
- Pocock skills provide procedure but never authority.
- ITDD creates execution assignments before launch, binds role/runtime/model/scope/candidate identity, and owns lifecycle transitions.
- BUILD, TEST, and VERIFY are fresh, separate, isolated, evidence-producing executions.
- Failed attempts remain immutable historical evidence; retries receive fresh identities.
- Integration, promotion, recovery, maintenance, and break-glass actions fail closed unless their exact authority exists.
- Required proof exercises the real deliverable through its public interface where automated checks are insufficient.
- Telemetry supports measured process improvement without becoming authority automatically.
- QMD or an equivalent retrieval layer remains advisory; ITDD remains the authority layer.
- Parallelism and autonomy are earned only after reliable single-EU and integration behavior is proven.

## Scope model

This is a multi-milestone architectural program, not one executable ticket. Each milestone below must become its own bounded specification and execution contract. No milestone inherits approval from another milestone. The plan is dependency-ordered and deliberately stops at each human approval gate.

### Milestone 0 — Establish governed execution admission

**Primary sources:** GitHub issues #27 and #28; `skills/idd/SKILL.md`; `skills/itdd-execute/SKILL.md`; `CONTEXT.md`.  
**Purpose:** Create the supported ITDD-owned controller interface and Prime-native RLM adapter.

Required outcomes:

- Exact approved-contract validation fails closed on missing, stale, altered, or mismatched approval.
- Durable BUILD, TEST, and VERIFY assignments exist before launch.
- Assignments bind execution ID, role, project, contract hash, baseline/candidate, workspace/scope, runtime, and explicitly selected model.
- Observable raw runtime evidence is controller-custodied and identity-bound.
- State and evidence reconstruct in a fresh process.
- Failures and interruptions stop advancement and require fresh assignments for retry.
- No Codex runtime, fallback, worker self-certification, or Prime-owned acceptance.

**Gate:** Independent review and explicit human approval of the exact #28 bootstrap contract. This milestone must not admit #21 until its route is accepted.

### Milestone 1 — Complete Git-attested integration and promotion

**Primary source:** fresh contract derived from issue #21 and parent #15 after Milestone 0. Historical #21 failures remain immutable evidence and are not reused as passes.

Required outcomes:

- Fresh integration verification is bound to exact candidate commit and tree.
- Actual overlapping Git branches exercise mechanical conflict detection and clean abort.
- Conflict produces durable evidence and no result commit/tree or canonical HEAD change.
- Approval precedes promotion; independent VERIFY PASS precedes approval/promotion.
- Rejected admission, approval, chronology, identity, and tamper attempts prove byte-identical authoritative state before and after rejection.
- Fresh-process reconstruction works for successful and conflict states.
- Native documented test execution works without import shims.

**Gate:** Independent BUILD/TEST/VERIFY and separate Standards/Spec review bound to the exact candidate.

### Milestone 2 — Recovery, interruption, retry, and replanning

**Purpose:** Make authorized recovery a first-class lifecycle operation without weakening denial behavior.

Required outcomes:

- Human-authorized abandonment preserves intent, history, evidence, and telemetry.
- Old execution authority is invalidated; new attempts receive new identities.
- Disposable workspaces can be safely discarded and reconstructed.
- BUILD, TEST, VERIFY, integration, and human-proof failures route to fresh diagnosis or repair cycles.
- Replanning changes execution strategy without mutating approved intent.
- Intent amendments are explicit, versioned, append-only, and human-authorized.
- Recovery state reconstructs after restart and never converts historical failure into success.

**Gate:** Recovery proofs include interrupted workers, verifier death, stale authority, duplicate recovery, and restart reconstruction.

### Milestone 3 — Human validation and real-system proof

**Purpose:** Enforce project-specific proof requirements that automation cannot establish alone.

Required outcomes:

- Intent/contracts declare whether human validation is required and why.
- Human checkpoints exercise the actual deliverable, not an agent report.
- PASS/FAIL, instructions, observed result, identity, timestamps, and artifacts are durable.
- Human FAIL routes back through diagnosis/build/test/verify with fresh identities.
- UI, CLI, service, game, and visualization proof strategies are represented without a universal mandatory gate.
- Human views remain derived and advisory, never authority.

**Gate:** At least one disposable real-system proof for a project type that requires it, plus hostile tests for forged, stale, mismatched, and duplicate human decisions.

### Milestone 4 — Telemetry and operational learning

**Purpose:** Make execution history measurable and useful for controlled process improvement.

Required outcomes:

- Telemetry records project, intent, EU, execution, role, skill sequence, model/runtime, context cost, duration, files, retries, failures, diagnosis, recovery, human proof, verification, integration, and promotion outcomes.
- Raw observations, derived patterns, and validated operational knowledge are separate classes.
- Telemetry is append-only, identity-bound, privacy-safe, and reconstructable.
- Recommendations are advisory and cannot grant capability or alter policy.
- Process changes follow Observation → Pattern → Proposed Change → Human Review → Controlled Experiment → Adopt/Reject.

**Gate:** A controlled before/after experiment demonstrates a recommendation without allowing telemetry to change authority automatically.

### Milestone 5 — Project-local knowledge and QMD advisory integration

**Purpose:** Add retrieval over specifications, evidence, history, skills, and validated operational knowledge.

Required outcomes:

- QMD or an equivalent local retrieval adapter indexes project-local evidence and skill documentation.
- Retrieval distinguishes Project Truth, Historical Evidence, Learned Operational Knowledge, and External Reference Knowledge.
- Retrieval results include provenance, freshness, authority class, and source identity.
- Prime may ask for procedure recommendations and historical comparisons.
- Retrieval cannot approve intent, issue capability, select an unauthorized model, or advance lifecycle state.
- Obsidian remains a human-readable view, not an authority store.

**Gate:** Tamper, stale-index, wrong-project, authority-confusion, and retrieval-unavailable tests fail closed or degrade to explicit advisory absence.

### Milestone 6 — Maintenance mode and break-glass recovery

**Purpose:** Repair the controller itself under explicit human authority while preserving the prior known-good controller.

Required outcomes:

- Normal execution freezes before maintenance.
- State, controller SHA, nonce, reason, and activation approval are recorded.
- Repair occurs in a dedicated branch/worktree.
- Control regression, recovery, and restart proofs run before exit.
- Old approvals are never reused after controller changes.
- Break-glass is human-only, auditable, time-bounded, and cannot silently promote product work.

**Gate:** Independent hostile tests for unauthorized maintenance, stale approval, nonce reuse, interrupted repair, and failed rollback.

### Milestone 7 — Earned parallel execution and autonomy

**Purpose:** Add concurrency only after the single-EU, integration, recovery, and evidence paths are reliable.

Required outcomes:

- Graph dependencies and disjoint scopes are enforced by controller assignments.
- Parallel workers cannot overlap unauthorized files or authority state.
- Join/integration verification is independent and identity-bound.
- One failed EU does not erase or falsely invalidate unrelated historical evidence.
- Scheduling, cancellation, retry, and resource limits are durable and reconstructable.
- Autonomy level is a validated project policy, never inferred from one successful run.

**Gate:** Stress, conflict, interruption, resource-limit, restart, and cross-EU contamination proofs pass before any default parallel mode is enabled.

## Cross-cutting acceptance invariants

Every milestone must preserve these invariants:

1. Agents reason; the controller decides what actions are legal.
2. Human-approved intent is durable authority; approved intent versions are immutable.
3. Every execution has a controller-created assignment before launch.
4. Every accepted artifact binds project, intent/graph/EU, execution, role, baseline, candidate, scope, context, command, result, hashes, and time.
5. Absence of proof is never success.
6. Builder, Tester, Verifier, Integrator, Promoter, skill, Prime, and QMD cannot self-grant authority.
7. Historical PASS-shaped records that fail trust-boundary checks remain invalid and are never rewritten.
8. A failed or interrupted attempt is preserved; retry means new identity, not mutation of history.
9. No ordinary working tree or preparation directory is used as an execution workspace.
10. No milestone may broaden its own paths, criteria, dependencies, or exclusions during BUILD.
11. Each acceptance attempt stops at the first material failure and preserves raw evidence.
12. Promotion is impossible before controller-owned independent verification and any declared human proof.

## Required lifecycle for each milestone

For each milestone, the human and Prime must:

1. Run the preparation phases with fresh identities and preserve evidence under `.idd/preparation/<preparation-id>/`.
2. Resolve the clarification frontier and explicitly designate the immutable source.
3. Produce a bounded vertical-slice specification and ticket graph.
4. Draft an exact execution contract with baseline SHA, path allowlist, criteria, tests, hostile probes, artifacts, and exclusions.
5. Obtain independent preparation review.
6. Obtain explicit human approval of the exact contract hash.
7. Enter the contract through `/idd`, then `/itdd-execute`.
8. Run fresh BUILD → TEST → VERIFY roles in isolated workspaces.
9. Run independent Standards and Spec review where required.
10. Preserve all raw role evidence, failures, hashes, and lifecycle records.
11. Accept or reject only through the controller after VERIFY.
12. Prepare the next milestone only after the dependency gate is satisfied.

## Human decisions recorded during grilling

The originating human accepted the recommended definitions and ordering:

- The first milestone is **Milestone 0**, establishing the controller-owned Prime-native RLM execution route in issues #27/#28.
- The first immutable milestone source should be **issue #28 with parent #27**, captured as frozen snapshots by `/itdd-prepare`.
- “Full architectural vision complete” means every approved milestone passes its own independent governed BUILD → TEST → VERIFY cycle and dependency gates; it does not mean optional capabilities are enabled by default.
- “Promotion” means a controller-owned fast-forward into the canonical branch with exact commit/tree attestation.
- “Earned autonomy” means an explicit versioned project policy enabled only after required evidence gates pass; it is never inferred.

These decisions narrow the route but do not constitute approval of an execution contract.

## Remaining clarification frontier

The proposal remains blocked for execution until the human resolves at least:

- Is Prime-native RLM the only supported runtime for the whole program, or only the initial adapter milestone?
- What is the required first real-system proof target: this control plane’s CLI/API, a disposable example project, or another project?
- What local QMD interface and storage boundary are acceptable, and what data must never be indexed?
- Which telemetry fields may contain model prompts/responses, and what redaction/retention policy applies?
- What evidence threshold earns permission to enable parallel execution and higher autonomy?
- Which milestones must be delivered first if the full program is split across multiple human-approved intents?
- What exact issue/spec snapshot should be the immutable source if issue #28 changes before preparation begins?

## Additional human decisions recorded during grilling

The human approved the remaining recommendations with one telemetry/QMD change:

- Prime-native RLM is the only supported runtime for Milestone 0. Other runtimes require separate future adapter decisions.
- The first real-system proof targets the control plane’s controller/adapter boundary using a disposable bounded contract.
- QMD is project-local and advisory. It receives curated lessons and best practices, not raw sessions.
- All telemetry and session data, including complete session records, are retained for audit, replay, and later analysis. Retention and access controls must be specified by the execution contract.
- Analysis may inspect the complete retained telemetry/session dataset, but raw sessions are not exposed to agents through QMD.
- QMD lessons must be provenance-linked, curated from the complete dataset, and human-validated before becoming operational guidance or policy.
- Telemetry must preserve complete raw evidence while separately supporting redacted or access-controlled operational views.
- Parallelism and increased autonomy remain disabled until Milestones 0–4 pass fresh independent proof and have no unresolved critical findings.
- The milestone order remains: #28/#27, #21, recovery/replanning, serial multi-EU, telemetry/knowledge, then parallelism/autonomy.

## Final clarification decisions recorded during grilling

The human approved the security, access, and source-freezing recommendations:

- Complete agent sessions and telemetry may be retained for audit, replay, and analysis, but credentials, tokens, and unrelated secrets must not be intentionally placed in prompts or captured artifacts.
- If a secret is accidentally captured, it is handled as an access-controlled incident and is never exposed through QMD.
- Raw evidence is available to the controller and authorized human reviewers. Ordinary agents receive only bounded evidence or curated QMD lessons.
- Human review is required before a QMD lesson class can guide agents. QMD remains advisory and cannot grant authority.
- At Milestone 0 preparation start, freeze GitHub issues #28 and #27 plus this proposal into hashed snapshots. A source change requires a new preparation cycle.

These decisions complete the clarification pass for this proposal. They do not approve an execution contract or authorize implementation.

These decisions narrow the route but do not approve an execution contract.

## Exclusions

This proposal does not authorize:

- implementation, tests, commits, merges, promotion, or lifecycle transitions;
- deletion or rewriting of dirty checkout content, historical evidence, or existing worktrees;
- treating prior test or verification artifacts as fresh acceptance;
- manual parent orchestration as a substitute for controller-owned execution;
- Codex runtime/tool/model use or silent model substitution;
- automatic QMD policy changes;
- parallel execution before the single-EU and integration gates pass;
- broad changes outside the exact allowlist of a future approved milestone.

## Evidence references

- `CONTEXT.md`
- `ROADMAP.md`
- `full-itdd-stack.md`
- `docs/specs/CONTROL-PLANE-SPEC.md`
- `docs/specs/EXECUTABLE-SKILLS-BASELINE-V1.md`
- `docs/architecture/operational-lifecycle.md`
- `docs/architecture/verification-and-evidence.md`
- `docs/architecture/isolation-and-events.md`
- `docs/architecture/git-attested-integration.md`
- `skills/idd/SKILL.md`
- `skills/itdd-prepare/SKILL.md`
- `skills/itdd-execute/SKILL.md`
- `.idd/preparation/ticket-21-prepare-20260922T1952Z/14-preparation-outcome.md`
- `.idd/preparation/ticket-21-prepare-20260922T1952Z/15-resumed-research.md`
- `.idd/preparation/ticket-28-prepare-20260922T213125Z/00-manifest.md`
- GitHub issues #15, #21, #27, and #28

## Current disposition

**STATUS: BLOCKED FOR EXECUTION / READY FOR HUMAN CLARIFICATION**

This document is a planning and clarification artifact. It must not be entered as an approved intent until the human answers the clarification frontier and the `/itdd-prepare` six-phase process produces an independently reviewed, exact execution contract for the first bounded milestone.

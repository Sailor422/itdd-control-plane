# Context Budget and Session Handoff — Discussion Draft

- Status: planning discussion only; not approved for implementation
- Date: 2026-09-23
- Authority: records the human-confirmed design direction; grants no intent, capability, or execution authority
- Related research: [curated research catalog](../archive/RESEARCH-CATALOG.md)

## Problem Statement

Long-running agent sessions accumulate current context from system instructions, shared LPVM/lean-prompt material, project context, conversation, tool results, and retrieved sources. Large context costs tokens and may reduce the quality of work. A transcript's total size or lifetime token use does not show what a model receives on its next request.

The ITDD Control Plane should plan a harness-agnostic way to keep each session's actual current context lean, hand work to a fresh session before it grows beyond the user's limit, and preserve enough information to continue safely. Prime Agent is the current research environment, not the architectural boundary or only supported harness.

## Solution

Define a shared ITDD context-renewal policy and controller-to-harness adapter contract. The controller measures each session's assembled model input and reports value, source, uncertainty, model/harness limit, and response reserve. It selects only useful context and checks the projected request before dispatch.

The objective is **the best work for the least tokens**, not minimum token count regardless of quality. Each session, including each child session, is budgeted independently. The shared policy sets a hard ceiling of 100,000 current-context tokens. Start renewal near 95,000 when the model/harness supports it. If a model or harness has less usable context, renew earlier; never wait for it to reach 100,000. The ±5,000 margin is safety headroom, not permission to exceed the ceiling.

The compaction process is the primary place to pass working context forward. ITDD should record decisions, authority, current work state, outcomes, and evidence references as work happens. At compaction, reconstruct authority from durable ITDD state and combine it with the compacted span to create a concise, intelligent continuation brief. The brief carries only what is needed to resume: objective, progress, unresolved work, decisions/failures, artifact references, and the exact next permitted action. It instructs the agent to continue without pausing unless an existing ITDD human gate or safety blocker applies. The brief is continuity context, not authority.

Prefer Prime's native same-session compaction so the visible session can continue indefinitely. Reuse the existing Prime compaction and extension lifecycle, not a second compaction engine. Shared LPVM/system directives remain in the normal system-prompt path; the compaction summary carries the task-specific continuation brief. If a harness cannot safely compact in place, use the validated replacement-session flow as a fallback: create an `itdd`-named session, reconstruct authority from durable state, load the minimal continuation package, verify readiness, then park the source and continue.

**Continuation invariant:** Context exhaustion is an ordinary controller-managed renewal event, not a human-intervention event. A renewed session continues automatically until the work completes, an existing ITDD human gate is reached, or safe continuation is impossible.

## User Stories

1. As a project using ITDD, I want context budgeting to work across harnesses so that the policy is not tied to Prime Agent.
2. As an operator, I want each session measured independently so that an oversized child session is not hidden by a smaller parent session.
3. As an agent, I want only the applicable shared LPVM and project context loaded so that startup does not waste the context budget.
4. As a controller, I want durable ITDD state to capture authority, decisions, current work state, outcomes, and evidence as work proceeds so that compaction does not depend on conversational memory alone.
5. As an operator, I want context reports to distinguish direct measurements from estimates and identify source and uncertainty so that the controller can make a safe decision.
6. As an operator, I want measurement to describe the assembled input for the next model request, not lifetime token usage or transcript size.
7. As a controller, I want the effective limit to be no greater than 100,000 tokens and no greater than the model/harness usable limit so that no request is intentionally sent above either bound.
8. As an agent, I want budgeting during startup, retrieval, tool-result handling, child creation, and before model dispatch so that context stays lean throughout the workflow.
9. As a controller, I want same-session compaction to begin near 95,000 tokens where supported, and earlier for smaller model windows, so that there is room to renew context safely.
10. As a controller, I want compaction to build a concise continuation brief from durable ITDD state and the span being compacted so that the next request has enough information to continue well.
11. As a controller, I want the brief to identify the exact next permitted action and direct automatic continuation so that no routine human prompt is needed after compaction.
12. As a controller, I want authority reconstructed from durable ITDD state rather than outgoing agent text so that summaries cannot grant or enlarge authority.
13. As a project owner, I want shared LPVM/system directives to remain in their normal system-prompt path so that a task-specific summary cannot replace them.
14. As a human, I want same-session compaction to preserve the visible session identity so that I can monitor the continuing work in one place.
15. As a controller, I want repeated compactions to chain safely so that the logical session can continue indefinitely while current context stays bounded.
16. As an operator, I want a validated `itdd`-named replacement session only when the harness cannot compact safely in place so that there is a portable fallback.
17. As a controller, I want replacement readiness verified before parking the source so that fallback session creation alone cannot interrupt valid work.
18. As a controller, I want unknown measurements, unsafe requests, invalid authority, or unsupported renewal operations treated as unsafe so that missing support cannot bypass the limit.
19. As a project owner, I want quality measured alongside token efficiency so that minimizing tokens does not harm correct work.
20. As a human, I want context exhaustion handled as an ordinary controller event so that I am contacted only for an existing human gate or a genuine safety blocker.
## Implementation Decisions (planning commitments only)

- Define context renewal as a harness-neutral controller operation. Each adapter reports context value, source, uncertainty, model/harness limits, and supported renewal operations.
- Use the controller-to-adapter boundary as the primary behavioral seam. The controller consumes a context report and adapter capabilities, then chooses to continue, compact in place, or stop safely. Replacement-session renewal is a fallback only when safe in-place compaction is unavailable.
- Make the compaction skill/process the canonical place to construct and pass the lean continuation brief. For smaller model windows, this same process renews context earlier; do not create a separate context-transfer mechanism. If replacement is required, it consumes the same validated brief.
- Measure the assembled input expected for the next model request. Include system/LPVM instructions, tools, retrieved material, conversation, and prior tool results as applicable.
- Optimize for task quality per token. Prefer relevant context selection, bounded retrieval/tool results, durable references to bulky evidence, and minimal child-session packets before renewing context.
- Treat 100,000 as a hard upper bound, not a target to fill. Begin renewal near 95,000 where supported, and earlier when the model/harness usable limit is lower. The lower effective limit controls; never wait for a smaller-context model to reach 100,000. Do not use the ±5,000 margin to permit exceeding either limit.
- For Prime, reuse the native compactor and `session_before_compact` extension seam. The compaction callback should provide or steer an intelligent continuation brief using the compacted span and durable ITDD state; the brief must direct immediate continuation of the exact next permitted action unless a gate applies. This is the primary context-transfer path, including when the model window is below 100,000.
- The brief is continuity context, not authority. Reconstruct intent/EU, lifecycle state, capability/scope, and current permitted action from durable ITDD state. Treat outgoing summaries as untrusted working information; validate critical state and references before continuation.
- Keep LPVM/system directives in their verified system-prompt path. A compaction summary is not a substitute for system-prompt injection. Prime's documented `before_agent_start` system prompt/message hook and `session_before_compact` summary hook have different roles.
- Reuse the existing local LPVM context-pressure configuration and continuity extension as the Prime starting point. Do not introduce a second compaction engine. Existing configured limits and code are not yet a hard 100,000-token guard; threshold ordering, same-turn continuation, headless behavior, and failure cases must be validated before relying on it.
- Continue through repeated same-session compactions without routine human intervention. If in-place renewal is unsupported or unsafe, use the existing planned fallback: create an `itdd`-named replacement, load durable authority and continuity context, validate readiness, park the source, then continue.
- Fail closed on unknown context, an unsafe projected request, invalid/mismatched authority, unresolved artifacts, failed compaction/readiness, or unsupported adapter operations: preserve evidence, do not send an over-budget request, and do not report renewal as complete.
- Keep this capability planning-only until separately authorized. This draft does not approve an intent, create a ticket, or authorize implementation.
## Testing Decisions

The agreed primary seam is the ITDD controller ↔ harness-adapter boundary. Tests should exercise observable decisions from a context report and advertised adapter capabilities, not private implementation details.

For Prime, test the existing compaction integration before adding a mechanism. Use a fake adapter/controller test for context below threshold, threshold crossing, hard limit, lower model limit, uncertain/missing measurement, and an oversized tool/retrieval result. Test that the built-in compaction completes, produces a bounded continuation brief, preserves the session identity, reloads the verified LPVM/system baseline, and continues the same authorized task without waiting for a new user prompt. Repeat compaction to prove continuation chains. Include negative controls where a key decision or next action is absent from the brief, stale authority is referenced, or the callback fails.

Prove that the authority package comes from durable controller state, mismatched or stale continuity data cannot enlarge authority, and a model-authored next action is checked against current permission. For the fallback adapter, cover successful replacement readiness, wrong project/work/role/scope, missing/changed artifacts, an over-budget replacement context, and failure while creating, loading, or parking; the old session must not be parked until readiness passes, and both sessions must never execute concurrently.

Adapter conformance tests should verify context and model-limit reporting, compaction/resume semantics, support for immediate continuation, and safe replacement fallback. Quality and token efficiency should be measured together. Exact calibration and quality measures remain open. Existing Prime compaction, LPVM context-pressure, continuity-ledger, context-packet, and runtime-adapter tests are prior art; the final buildable spec should map these behaviors to exact test seams after implementation scope is authorized.
## Out of Scope

- Implementing or changing Prime Agent's current configuration in this planning step.
- Treating this capability as exclusive to Prime Agent or to one model provider.
- Copying the full source transcript into a compaction summary or replacement session.
- Allowing a project or adapter to silently raise the shared 100,000-token maximum.
- Treating a compaction summary as durable authority or as a replacement for raw session evidence.
- Creating an approved intent, GitHub issue, execution ticket, or implementation assignment.

## Open Questions for later specification

- Can Prime's documented `session_before_compact` seam reliably supply the requested custom continuation summary for both native automatic and explicit compaction, and does the same agent turn resume without a new user prompt in every supported mode?
- Can the native summarizer be steered dynamically on auto-compaction, or must the extension return a full custom summary? The installed docs demonstrate custom summaries and manual `ctx.compact({customInstructions})`, but do not establish a dynamic instruction override for every automatic compaction path.
- How should Prime headless sessions renew context when the current LPVM extension only requests `ctx.compact()` when `ctx.hasUI`?
- What normalized context-report fields and estimator confidence levels can be required across harnesses and providers?
- How should the controller validate that a report reflects all material input sent to the model, and what safe limit applies when a model's usable window is below 100,000?
- What exact quality and token-efficiency measures should be used to ensure that less context does not harm work quality?
- Which readiness observations can each harness provide independently of the replacement model's own claims, and what transaction/lease protocol prevents two active workers if fallback replacement fails partway through?
- What privacy and retention rules govern authority references, continuity briefs, and linked raw session evidence?

These questions do not change the agreed direction. They must be resolved before a buildable spec or implementation is authorized.

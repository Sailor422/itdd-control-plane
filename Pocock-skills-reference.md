Pocock Skills Reference for Prime + ITDD

Purpose

This document defines how Matt Pocock’s engineering skills should be used inside the Prime + ITDD architecture.

The skills provide methodology and procedure.

They do not provide lifecycle authority.

The intended architecture is:

Human
  ↕
Prime — conversational architect/orchestrator
  │
  │ launches fresh skill-guided subagents
  ↓
Planning / Research / Design Subagents
  │
  │ produce bounded durable artifacts
  ↓
ITDD Controller Subagent
  │
  │ owns execution authority
  ↓
BUILD → TEST → VERIFY → REVIEW → INTEGRATE
  │       │       │
  └ fresh skill-guided agents ─┘

Prime and the human can continue discussing the project while execution proceeds.

Prime should not become the Builder, Tester, Verifier, or Integrator.

⸻

1. Authority Model

Top-level Prime

Prime is the human-facing project brain.

Prime may:

* read the complete project
* read ITDD state
* read source documents
* read specifications
* read tickets
* read evidence
* read telemetry
* read previous failures
* reason with the human
* discuss architecture
* help decide what should happen next
* launch an appropriate skill-guided subagent
* launch the ITDD controller for approved execution

Prime should normally have read-only project access.

Prime does NOT:

* directly implement production code
* directly modify tests
* self-certify work
* directly promote a candidate
* bypass ITDD
* repair implementation while acting as orchestrator
* silently change approved intent

Prime orchestrates.

⸻

2. Skill-Guided Subagents

A skill invocation should normally create or guide a fresh agent execution.

The skill tells that agent how to reason about its task.

Examples:

Prime
  ↓
fresh /research agent
Prime
  ↓
fresh /diagnosing-bugs agent
Prime
  ↓
fresh /to-spec agent
Prime
  ↓
fresh /code-review agent

The important principle is:

The Prime conversation should not accumulate implementation responsibility merely because it knows the project.

The worker gets the skill.

Prime keeps the overview.

⸻

3. ITDD’s Role

Once work has been sufficiently defined, Prime hands the bounded execution contract to ITDD.

From that point:

Prime
  ↓
ITDD Controller
  ↓
fresh BUILD agent
  ↓
fresh TEST agent
  ↓
fresh VERIFY agent
  ↓
integration / review / promotion

ITDD controls:

* identities
* authority
* allowed paths
* baselines
* candidate identity
* context
* execution order
* evidence
* failure handling
* retries
* interruption
* abandonment
* verification
* integration
* promotion

Pocock skills control how the agent approaches the job inside that envelope.

⸻

4. The Main Pocock Flow

The canonical Pocock flow is:

idea
 ↓
/grill-with-docs
 ↓
optional prototype/research
 ↓
/to-spec
 ↓
/to-tickets
 ↓
/implement
 ↓
/tdd
 ↓
/code-review
 ↓
ship

This is a reasoning workflow.

ITDD should adapt this into an enforced execution workflow.

⸻

5. /ask-matt

Purpose

Router for the Pocock skill system.

Use when Prime is unsure which skill applies.

Good use cases

* “We have a bug. Which workflow fits?”
* “This idea is still vague.”
* “We have a finished spec. What comes next?”
* “This architectural problem is enormous.”
* “Should we research this or prototype it?”

Do not use when

The correct skill is already obvious.

Prime/ITDD position

Primarily useful to Prime, not BUILD workers.

Think:

uncertain routing
    ↓
/ask-matt
    ↓
correct skill

⸻

6. /grill-with-docs

Purpose

Turn a fuzzy idea into a precise shared understanding through aggressive questioning.

It combines:

* grilling
* domain modeling
* durable documentation

It updates project knowledge such as:

* CONTEXT.md
* ADRs where justified

Use when

You know roughly what you want, but requirements, terminology, boundaries, behavior, or decisions remain unclear.

Example

“We need ITDD recovery.”

That is too vague.

/grill-with-docs might force questions such as:

* What exactly survives recovery?
* What does abandonment mean?
* Is candidate code disposable?
* Which state is authoritative?
* What constitutes a safe restart?

Do not use when

A complete specification already exists.

Prime/ITDD position

Usually a Prime-launched design subagent before ITDD execution.

⸻

7. /grill-me

Purpose

Same interrogation discipline as grilling, but without the repository documentation behavior.

Use when

There is no project workspace or durable repository context.

Prefer

/grill-with-docs whenever operating inside a real project.

⸻

8. /grilling

Purpose

Underlying interview primitive.

It relentlessly exposes unanswered decisions, assumptions, contradictions, and ambiguity.

Use directly when

You specifically need the interview process without another wrapper.

Usually other skills should invoke it.

⸻

9. /domain-modeling

Purpose

Create and maintain precise project vocabulary.

This is much more important than it looks.

It prevents terms such as:

run
execution
operation
candidate
worker
session
recovery
reset
restart

from quietly acquiring several incompatible meanings.

Outputs

Primarily:

CONTEXT.md
docs/adr/*

Use when

* terminology is ambiguous
* two concepts are being conflated
* the human and code use different words
* a major architectural term needs a canonical definition

ITDD importance

Very high.

ITDD is state-machine-heavy. Ambiguous vocabulary creates control-plane bugs.

⸻

10. /research

Purpose

Delegate factual investigation to a fresh agent.

The research agent should favor primary sources and leave durable cited findings.

Use when

A design decision requires information rather than judgment.

Examples:

* investigate Git worktree behavior
* investigate Prime runtime capabilities
* investigate Codex sandbox behavior
* investigate event-sourcing recovery models
* investigate testing strategies

Output

Research artifact.

Research does NOT decide architecture.

It informs later design.

Flow

question
 ↓
/research
 ↓
research artifact
 ↓
/grill-with-docs or /to-spec

⸻

11. /prototype

Purpose

Answer a design question with runnable code.

Prototype code is not automatically production code.

Use when

Discussion cannot answer a question reliably.

Examples:

* Does this state-machine design actually work?
* Can Prime launch nested workers this way?
* Can this Git recovery sequence reconstruct the workspace?
* Does this UI interaction make sense?

Output

Evidence for a decision.

Not necessarily a deliverable.

Important distinction

Research answers:

What is true?

Prototype answers:

Will this design work?

⸻

12. /handoff

Purpose

Carry durable context across a real boundary.

Examples:

* another harness
* another repository/directory
* another person
* another long-running session

Do not use

Just because an agent finished a normal subtask.

ITDD evidence and contracts should normally provide the execution handoff.

⸻

13. /wayfinder

Purpose

Resolve large-scale uncertainty when the path itself is unknown.

This is not a generic planner.

It creates decision tickets to progressively eliminate uncertainty.

Appropriate example

“We want to build an entirely new distributed autonomous engineering platform, but we don’t know the major architecture yet.”

Bad example

“We know ITDD needs an abandon/restart operation.”

That does NOT require Wayfinder.

Outputs

Decisions.

Not implementation tickets.

Exit

Once the route is known:

/wayfinder
 ↓
/to-spec

Rule

Use Wayfinder rarely.

It is for fog, not size alone.

⸻

14. /to-spec

Purpose

Convert already-understood requirements and decisions into a durable implementation specification.

It should synthesize rather than start another interrogation.

Typical contents

* problem
* solution
* user stories
* implementation decisions
* testing decisions
* out-of-scope behavior
* important notes

Major TDD connection

The spec identifies testing seams before implementation.

That is important because /tdd expects testing at agreed public seams.

Prime/ITDD position

One of the principal handoff artifacts between planning and ITDD.

discussion/research/design
        ↓
     /to-spec
        ↓
authoritative specification

⸻

15. /to-tickets

Purpose

Break a specification into executable vertical tracer bullets.

Not horizontal engineering tasks.

Bad tickets:

write database layer
write API
write tests
write UI

Good ticket:

A user can abandon an interrupted execution and restart it
while preserving previous evidence.

That ticket may touch:

* event state
* controller API
* CLI
* tests
* evidence

but it produces one observable end-to-end behavior.

Blocking relationships

Every ticket declares what blocks it.

This produces an execution graph.

ITDD relationship

This maps naturally to Execution Units.

A Pocock ticket can become or generate an ITDD EU.

⸻

16. /implement

Purpose

Implement one bounded piece of work.

/implement is not merely “write code.”

It internally uses:

/tdd

and concludes with:

/code-review

Normal internal flow

ticket/spec
   ↓
/implement
   ↓
/tdd
   ↓
red → green
   ↓
repeat vertical slices
   ↓
full tests
   ↓
/code-review

ITDD modification

Inside ITDD, /implement must NOT own authority that belongs to the controller.

For example, the upstream skill says to commit its work.

Under ITDD:

the worker does not decide candidate acceptance or promotion.

ITDD owns Git candidate identity and lifecycle transitions.

Therefore Pocock process should be retained while authority-changing actions remain controller-owned.

⸻

17. /tdd

Purpose

Test-driven implementation.

This is one of the most important worker skills.

Core rule

RED
 ↓
GREEN
 ↓
next vertical slice

A failing test comes first.

Then the smallest implementation that makes it pass.

Tests should

* exercise public behavior
* survive refactoring
* use independently known expected results
* test agreed seams
* behave like executable specifications

Tests should NOT

* directly test private implementation
* reproduce the implementation algorithm in the assertion
* excessively mock internals
* write hundreds of imagined tests before implementation begins

Pocock’s critical concept: seams

A seam is the public interface where behavior can be observed.

Example ITDD seams might include:

Controller.abandon_execution()
Controller.recover_project()
CLI /itdd-recover
Event replay → reconstructed state

The seam should be agreed in the specification before execution.

ITDD role

BUILD workers use /tdd.

TEST and VERIFY remain separate independent roles.

This gives us:

BUILD
  /tdd
TEST
  independent acceptance tests
VERIFY
  adversarial independent verification

TDD does not replace independent verification.

⸻

18. /code-review

Purpose

Independent two-axis review.

The two axes are deliberately separate.

Standards

Does this code meet the repository’s engineering standards?

Spec

Does this code actually implement what was requested?

These run through separate subagents.

Why this matters

Code can be:

beautiful but wrong

or:

correct but terrible

The two reviews detect different failures.

ITDD relationship

This concept maps almost perfectly onto ITDD’s independent verification architecture.

Possible mapping:

Pocock Standards Review
        ↕
ITDD Standards Reviewer
Pocock Spec Review
        ↕
ITDD Spec Verifier

The Pocock method provides the review procedure.

ITDD provides identity, independence, evidence binding, and authority.

⸻

19. /diagnosing-bugs

Purpose

Debug difficult failures scientifically rather than by guessing.

Golden rule

Do not form elaborate theories until there is a tight feedback loop.

First create a command that reliably demonstrates the bug.

Typical order:

reproduce
 ↓
make reproduction deterministic
 ↓
minimize
 ↓
investigate
 ↓
regression test
 ↓
fix

Use when

* test suddenly fails
* behavior is intermittent
* recovery logic breaks
* integration regresses
* previous fix didn’t solve the real problem

ITDD importance

Very high.

A failed EU should be able to spawn a diagnosis subagent rather than letting the Builder thrash around experimentally.

⸻

20. /triage

Purpose

Turn incoming bugs/features/PRs into agent-ready work.

It categorizes, verifies and sharpens incoming requests.

Use for

Work arriving from outside the controlled planning process.

Do NOT use for

Tickets generated by /to-tickets.

Those tickets are already agent-ready.

⸻

21. /resolving-merge-conflicts

Purpose

Resolve an existing Git merge or rebase conflict based on intent, rather than mechanically choosing one side.

ITDD use

Potentially useful to a narrowly authorized Integration subagent.

It should not grant authority to change behavior beyond the integration contract.

⸻

22. /improve-codebase-architecture

Purpose

Proactively identify structural weaknesses that make the codebase difficult for humans or agents to work in.

This is not feature implementation.

Output

Architectural improvement opportunities.

Those opportunities normally become new ideas entering:

/grill-with-docs

⸻

23. /codebase-design

Purpose

Vocabulary/reference for designing deep modules and good interfaces.

Concepts include:

* module
* interface
* depth
* seam
* adapter
* leverage
* locality

Use

When deciding where a behavior belongs or where a public testing seam should be.

Usually consumed underneath /tdd or architecture work.

⸻

24. /to-questionnaire

Purpose

Extract missing knowledge from another human asynchronously.

Use when the required information is held by someone else.

Example:

ITDD project
needs production deployment constraints
        ↓
/to-questionnaire
        ↓
questionnaire for infrastructure owner

The returned answers feed planning.

⸻

25. /wizard

Purpose

Handle actions only a human can perform.

Examples:

* create credentials
* configure external dashboards
* provision accounts
* enter secrets
* approve cloud configuration

It should make the human step structured and repeatable.

ITDD position

Escape hatch for genuine external HUMAN_ONLY operations.

Do not use it merely because an automated operation is inconvenient.

⸻

26. /wait-what

Purpose

Explain something again when the previous explanation did not land.

It is a communication repair skill.

It should not alter lifecycle state.

⸻

27. /teach

Purpose

Longer-term structured learning.

Not part of normal software execution.

⸻

28. /writing-for-agents

Purpose

Create instructions and documents intended to be consumed by agents.

Very useful for:

* ITDD skills
* AGENTS.md
* execution contracts
* durable agent instructions
* context documents

Use it when designing the documents that drive the agent system itself.

⸻

29. /setup-matt-pocock-skills

Purpose

Bootstrap the Pocock environment in a repository.

It configures things the other skills assume exist, including:

* issue tracker
* labels
* documentation conventions
* agent configuration

Run it once during project setup.

It is infrastructure, not part of every execution.

⸻

30. Fully Autonomous ITDD Lifecycle

The target should be:

                   HUMAN
                     ↕
              ┌──────────────┐
              │    PRIME     │
              │ conversational│
              │ orchestrator │
              └──────┬───────┘
                     │
          read-only project access
                     │
         launches skill subagents
                     │
       ┌─────────────┴─────────────┐
       │                           │
 /grill-with-docs              /research
       │                           │
       ├──────── design ───────────┤
       │
    /to-spec
       │
    /to-tickets
       │
       ▼
 ┌────────────────┐
 │ ITDD CONTROLLER│
 └───────┬────────┘
         │
         ├──── BUILD
         │       │
         │   /implement
         │       │
         │     /tdd
         │
         ├──── TEST
         │       │
         │ independent tests
         │
         ├──── VERIFY
         │       │
         │ spec verification
         │ standards review
         │
         ├──── INTEGRATE
         │       │
         │ optional
         │ /resolving-merge-conflicts
         │
         └──── PROMOTE

⸻

31. No-Human Execution After Authorization

The desired lifecycle is not literally “no human anywhere.”

It is:

Human authority is established before autonomous execution, then routine execution requires no human intervention.

Prime and the human determine:

* intent
* boundaries
* major architecture
* constraints
* acceptable testing seams
* autonomy envelope

Once handed to ITDD:

BUILD
TEST
VERIFY
repair cycles
integration
reverification

should proceed autonomously wherever the existing authority already answers the question.

A worker should stop only when it encounters a decision that truly changes authority, such as:

* changing approved intent
* materially expanding scope
* changing an irreversible architecture decision outside authorization
* using break-glass
* changing the control plane itself beyond its authorized maintenance contract

Routine failures are not human decisions.

They are workflow events.

⸻

32. Autonomous Failure Routing

ITDD should eventually route failures automatically.

BUILD implementation failure
        ↓
fresh /diagnosing-bugs agent
        ↓
new BUILD cycle
missing knowledge
        ↓
/research
        ↓
recompile context
        ↓
retry
bad decomposition
        ↓
replanning agent
        ↓
new graph
test failure
        ↓
new BUILD
        ↓
new TEST
verification failure
        ↓
new BUILD
        ↓
new TEST
        ↓
new VERIFY
merge conflict
        ↓
/resolving-merge-conflicts
        ↓
integration verification

Every retry receives a new identity.

No failed evidence disappears.

⸻

33. Pocock Skills vs ITDD Authority

This boundary must remain explicit.

Pocock skill provides	ITDD provides
reasoning procedure	authority
TDD method	execution identity
debugging method	state machine
review method	independent role enforcement
specification method	immutable intent binding
ticket decomposition	execution graph
research procedure	context authorization
implementation procedure	allowed paths
code review	evidence binding
workflow advice	promotion authority
engineering quality	auditability

Neither system replaces the other.

Together they are significantly stronger.

⸻

34. Prime’s Central Rule

Prime should follow this rule:

If an action will materially change the project, launch the appropriate skill-guided subagent rather than doing the work yourself.

Prime may read everything and discuss everything.

But action is delegated.

This keeps the top-level conversation useful throughout a long build.

The human can ask:

* What is BUILD doing?
* Why did VERIFY reject it?
* What decisions remain?
* What did we learn?
* What is blocked?
* What does the telemetry show?
* Should we change the design?

without forcing Prime itself to become the implementation agent.

⸻

35. ITDD’s Central Rule

ITDD should follow this rule:

Choose the procedure with a skill; enforce the authority with the controller.

Examples:

Need implementation?
→ fresh agent + /implement + /tdd
→ ITDD constrains it
Need debugging?
→ fresh agent + /diagnosing-bugs
→ ITDD constrains it
Need review?
→ fresh agents + /code-review
→ ITDD binds them to exact candidate
Need merge repair?
→ fresh agent + /resolving-merge-conflicts
→ ITDD limits integration scope

⸻

36. The Target System

The finished architecture should allow this interaction:

Human: Prime, add recovery to ITDD.
Prime:
I understand the request.
I have read the current project state.
This needs design clarification.
Prime launches:
fresh /grill-with-docs subagent
Subagent returns durable design.
Prime:
Here is the resulting design.
We discuss it.
Prime launches:
/to-spec
Prime launches:
/to-tickets
Prime:
The work is now bounded.
I'm handing execution to ITDD.
ITDD launches:
BUILD + /implement + /tdd
ITDD launches:
TEST
ITDD launches:
VERIFY + independent Spec/Standards review
Failure?
ITDD automatically routes the failure through the appropriate fresh skill-guided agent and repeats the cycle.
Meanwhile:
Human ↔ Prime
continues normally.

That is the intended operating model.
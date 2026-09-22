Prime + ITDD + Pocock Skills + QMD

Architecture and Operational Learning Report

Date: September 22, 2026
Status: Design direction established through discussion
Purpose: Capture the architectural conclusions, operating model, skill strategy, human-validation philosophy, telemetry strategy, and proposed role for QMD developed during this discussion.

⸻

1. Executive Summary

The emerging system consists of four complementary layers:

1. Prime — conversational architect, orchestrator, and operational analyst.
2. Pocock Skills — reusable engineering procedures that tell specialized agents how to perform particular kinds of work.
3. ITDD Control Plane — deterministic authority, isolation, lifecycle, evidence, and verification enforcement.
4. QMD + Knowledge Vault — historical operational memory used to learn which procedures work best and advise Prime.

The fundamental separation is:

Prime decides and orchestrates. Pocock skills define how specialized work should be performed. ITDD controls what execution agents are authorized to do and proves what actually happened. QMD learns from the resulting history.

Prime should have broad read-only visibility into the project, ITDD state, telemetry, evidence, specifications, source material, history, and operational knowledge.

Prime should not normally perform implementation work itself.

Instead, Prime launches specialized subagents with the appropriate Pocock skill.

Once work reaches implementation, the ITDD control plane takes ownership of the BUILD → TEST → VERIFY → integration/promotion lifecycle.

The human and Prime remain able to converse throughout execution.

Human checkpoints are not generic approval gates. Prime and the human decide, project by project, where human observation is genuinely necessary to prove that the real product works.

All execution produces telemetry. QMD indexes the resulting operational history so Prime can learn which skills, workflows, decomposition strategies, test seams, recovery procedures, and human-validation strategies actually produce good results.

The desired long-term feedback loop is:

Human ↔ Prime
          │
          ├── planning / architecture / orchestration
          │
          ▼
    Skill-guided agents
          │
          ▼
         ITDD
          │
    BUILD → TEST → VERIFY
          │
          ▼
    Real-system proof
          │
          ▼
       Telemetry
          │
          ▼
         QMD
          │
          ▼
        Prime
          │
          ▼
Human discussion
          │
          ▼
Process improvement

The objective is not merely autonomous coding.

The objective is a controlled engineering system that learns from its own real performance.

⸻

2. Origin of the Current Discussion

A real-world test project exposed an important weakness in the ITDD control plane.

The test workload itself is disposable.

The valuable result is the information generated around the failure:

* controller behavior
* execution history
* evidence
* telemetry
* state transitions
* failures
* recovery difficulty
* security behavior
* worker behavior
* testing results
* verification results

This led to an important distinction:

Recovering the product and recovering the control plane are separate operations.

For the current experiment, preserving the game or test application is secondary.

Preserving what ITDD learned while building it is critical.

⸻

3. Recovery Problem Discovered

The existing ITDD architecture is deliberately strict.

It successfully prevents many unauthorized continuation paths.

However, the real-world experiment demonstrated that the system can reach a state where it correctly refuses unsafe continuation but does not provide an equally strong authorized recovery path.

In other words:

DENY unsafe continuation

exists more completely than:

ALLOW authorized abandonment and recovery

This can leave a human operator unable to restart cleanly without manually manipulating ITDD state.

That is unacceptable for a practical long-running development system.

The desired recovery behavior is:

failed/interrupted execution
        ↓
human-authorized recovery
        ↓
preserve execution history
        ↓
mark attempt abandoned/interrupted
        ↓
invalidate old authority
        ↓
dispose of disposable workspaces
        ↓
reconstruct durable project authority
        ↓
issue fresh execution identities
        ↓
restart BUILD → TEST → VERIFY

The .idd/ history should not need to be deleted.

Failures are valuable evidence.

⸻

4. Recovery Principle

The correct response to recovery problems is not globally weakening ITDD security.

Instead:

Execution should remain strict while recovery should become an explicit, first-class, human-authorized lifecycle operation.

Recovery should preserve:

* previous executions
* failed attempts
* evidence
* telemetry
* intent
* specifications
* verification results
* provenance
* event history

Disposable execution environments may be discarded.

Historical truth may not.

A failed execution must never silently transform into a successful execution.

A new attempt receives a new identity.

⸻

5. Discovery About the Pocock Skill System

The discussion initially considered using /wayfinder broadly.

Inspection of the actual Pocock skill routing documentation showed that this was too broad.

/wayfinder is specifically intended for large, foggy efforts where the route itself is unknown.

It is not the default project-planning mechanism.

The normal Pocock engineering flow is approximately:

idea
 ↓
/grill-with-docs
 ↓
optional research/prototype
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

This discovery led to a larger architectural insight:

ITDD should not invent a competing engineering methodology when the Pocock skills already provide a disciplined engineering methodology.

Instead, ITDD should enforce that methodology.

⸻

6. Core Architectural Separation

The system should separate three concepts that are easy to confuse.

Prime

Prime provides:

* conversation
* reasoning
* orchestration
* architecture discussion
* project-level awareness
* operational analysis
* skill selection
* telemetry analysis
* recommendations

Pocock Skills

Pocock skills provide:

* engineering procedures
* TDD discipline
* debugging discipline
* specification methodology
* decomposition methodology
* code review methodology
* research methodology
* architectural vocabulary
* domain modeling

ITDD

ITDD provides:

* authority
* execution identities
* capability boundaries
* state transitions
* lifecycle enforcement
* candidate identity
* immutable evidence
* isolation
* independent verification
* recovery
* integration control
* promotion authority

A concise formulation is:

Choose the procedure with a skill. Enforce the authority with ITDD.

⸻

7. Prime’s Intended Role

Prime should become the persistent human-facing intelligence above the execution system.

Prime should have broad read-only access to:

* source code
* specifications
* approved intent
* execution graphs
* tickets
* ITDD state
* test results
* verification results
* telemetry
* previous failures
* operational evidence
* QMD knowledge
* project documentation

Prime should be able to reason across the complete project history.

Prime should normally not have authority to modify implementation directly.

The governing principle should be:

If an action materially changes the project, Prime launches the appropriate skill-guided subagent instead of performing the change itself.

This preserves Prime’s role as orchestrator.

⸻

8. Prime and the Human

Prime remains conversational throughout execution.

The human should be able to ask Prime:

* What is BUILD doing?
* Why did TEST fail?
* Why did VERIFY reject the candidate?
* What did the last attempt teach us?
* What is currently blocked?
* What is the next execution unit?
* Are our slices too large?
* Which skills are working well?
* Why did this workflow require three retries?
* Should we change the architecture?
* Should this project have a human UI checkpoint?
* What does the telemetry show?

This conversation should continue even while specialized agents are working.

Prime therefore becomes the operational command center, without becoming the worker.

⸻

9. Skill-Guided Subagents

Prime should launch fresh agents for specialized work.

Examples:

Prime
 ↓
fresh /research agent
Prime
 ↓
fresh /grill-with-docs agent
Prime
 ↓
fresh /diagnosing-bugs agent
Prime
 ↓
fresh /to-spec agent
Prime
 ↓
ITDD controller

The specialized agent receives the procedure.

Prime retains the broader project understanding.

This reduces contamination between roles and keeps individual agent contexts focused.

⸻

10. ITDD as a Subagent

A particularly important architectural conclusion is that ITDD itself should operate beneath Prime.

Prime remains the top-level orchestrator.

When implementation is ready:

Human ↔ Prime
          │
          ▼
   ITDD Controller Agent
          │
          ├── BUILD agent
          ├── TEST agent
          ├── VERIFY agent
          └── integration agents

The ITDD controller can then create the specialized agents required for execution.

This creates hierarchical delegation without giving Prime implementation authority.

⸻

11. Pocock /ask-matt

Purpose:

Route an uncertain situation to the appropriate skill.

Use when Prime knows something needs specialized treatment but does not know which procedure applies.

Examples:

* unclear design problem
* difficult bug
* architectural uncertainty
* feature request
* research question
* implementation task

Prime should be able to use this routing logic directly or eventually reproduce it through QMD recommendations.

⸻

12. /grill-with-docs

Purpose:

Turn a partially understood idea into a precise design through questioning while preserving important knowledge.

It combines:

* grilling
* domain modeling
* durable project documentation

It is appropriate when requirements or terminology remain unclear.

Typical outputs include:

* clarified requirements
* canonical terminology
* CONTEXT.md
* ADRs where appropriate

It should normally be preferred over stateless grilling when operating inside an existing repository.

⸻

13. /grill-me

Purpose:

Run the same aggressive clarification process without maintaining repository documentation.

Best suited to situations where no working project directory exists.

Inside an active project, /grill-with-docs is generally preferable.

⸻

14. /grilling

Purpose:

Underlying interrogation procedure.

Its purpose is to expose:

* hidden assumptions
* unanswered questions
* contradictions
* fuzzy requirements
* ambiguous boundaries

Other skills may invoke it internally.

⸻

15. /domain-modeling

Purpose:

Maintain precise shared vocabulary.

This is particularly important to ITDD because control-plane systems depend heavily on precise terms.

Terms such as:

* operation
* execution
* run
* worker
* candidate
* intent
* capability
* interruption
* abandonment
* recovery
* retry
* restart

must not acquire inconsistent meanings.

CONTEXT.md should act as the canonical glossary rather than an implementation specification.

ADRs should capture important difficult-to-reverse architectural decisions.

⸻

16. /research

Purpose:

Send factual investigation to a specialized agent.

Examples:

* Git worktree behavior
* runtime capabilities
* testing techniques
* external standards
* APIs
* recovery techniques

Research should produce durable evidence.

Research informs a decision.

It does not automatically make the decision.

Typical flow:

question
 ↓
/research
 ↓
evidence
 ↓
Prime/design discussion

⸻

17. /prototype

Purpose:

Use disposable or experimental code to answer a design question that discussion alone cannot reliably resolve.

Examples:

* Can this state-machine design work?
* Can Prime launch the required process?
* Can Git state be reconstructed this way?
* Does this interaction model actually feel usable?

Prototype code answers questions.

It is not automatically production code.

⸻

18. /handoff

Purpose:

Move durable context across a genuine boundary.

Examples:

* different harness
* different directory
* different person
* separate long-running context

Routine ITDD execution should normally use its own durable contracts and evidence rather than excessive handoff documents.

⸻

19. /wayfinder

Purpose:

Navigate genuinely large and uncertain efforts where the path itself is not yet understood.

Wayfinder creates decision tickets, not ordinary implementation tickets.

It should be used sparingly.

Correct use:

large unknown destination
        ↓
decision map
        ↓
resolve uncertainty
        ↓
/to-spec

Incorrect use:

Using Wayfinder merely because a known feature is large.

The key trigger is fog, not size.

⸻

20. /to-spec

Purpose:

Convert understood discussion and decisions into an authoritative implementation specification.

The spec should describe:

* problem
* solution
* user stories
* implementation decisions
* testing decisions
* testing seams
* exclusions
* relevant architectural decisions

An especially important function is agreeing on testing seams before implementation begins.

This supports proper TDD.

⸻

21. /to-tickets

Purpose:

Break the specification into vertical tracer-bullet slices.

A bad decomposition is horizontal:

database
API
tests
UI

A better decomposition is behavioral:

User can abandon an interrupted execution
and start a new execution while preserving
the previous attempt's evidence.

That vertical slice may touch multiple architectural layers but produces one observable behavior.

Tickets should declare blocking relationships.

This maps naturally onto ITDD Execution Units.

⸻

22. /implement

Purpose:

Implement one bounded piece of work.

It should internally use /tdd.

At completion it uses /code-review.

Conceptually:

ticket
 ↓
/implement
 ↓
/tdd
 ↓
red → green
 ↓
additional vertical slices
 ↓
tests
 ↓
/code-review

ITDD must adapt the upstream skill where necessary so the worker does not assume lifecycle authority that belongs to the controller.

For example, ITDD should remain authoritative for candidate identity, commits where required by the control model, promotion, and acceptance.

⸻

23. /tdd

Purpose:

Drive implementation through real test-first development.

The essential loop is:

RED
 ↓
GREEN
 ↓
next behavior

The failing test comes first.

Then only enough implementation is added to make it pass.

Testing should occur through agreed public seams.

Tests should describe behavior rather than implementation internals.

Important anti-patterns include:

* tests written after implementation merely to certify it
* tautological assertions
* excessive mocking
* testing private internals
* horizontal “write every test first” development
* tests that remain green even when the actual behavior is broken

The Pocock approach favors one vertical behavioral slice at a time.

⸻

24. TDD Does Not Replace Independent Testing

BUILD using TDD is only one layer.

The stronger ITDD structure is:

BUILD
 /implement
 /tdd
      ↓
TEST
 independent acceptance
      ↓
VERIFY
 independent verification

The Builder proving its own tests pass is not sufficient.

Independent testing and verification remain essential.

⸻

25. /code-review

Purpose:

Review a candidate independently along two separate dimensions.

Standards Review

Does the implementation meet repository engineering standards?

Spec Review

Does the implementation actually satisfy the requested behavior?

These questions must remain distinct.

Code can be:

* well written but wrong
* correct but structurally poor

Separate review catches both classes.

This maps naturally onto ITDD’s independent verification architecture.

⸻

26. /diagnosing-bugs

Purpose:

Diagnose difficult failures scientifically rather than by guessing.

The critical principle is:

Establish a tight feedback loop before theorizing about the cause.

Typical process:

reproduce
 ↓
make deterministic
 ↓
minimize
 ↓
investigate
 ↓
regression test
 ↓
repair

This is highly valuable to ITDD.

Instead of allowing a Builder to thrash after a failure, ITDD can launch a fresh diagnosis agent using /diagnosing-bugs.

⸻

27. /triage

Purpose:

Convert externally arriving bugs, feature requests, and similar work into agent-ready work.

It should generally not be applied to tickets produced by /to-tickets, because those tickets are already supposed to be ready for agents.

⸻

28. /resolving-merge-conflicts

Purpose:

Resolve existing merge/rebase conflicts based on intended behavior rather than mechanically selecting one side.

Within ITDD this should operate under narrowly bounded integration authority.

⸻

29. /improve-codebase-architecture

Purpose:

Identify structural weaknesses that make a codebase harder for humans and agents to maintain.

This is not ordinary feature work.

It produces architectural improvement opportunities that may subsequently enter the normal design flow.

⸻

30. /codebase-design

Purpose:

Provide vocabulary and principles for strong module/interface design.

Important concepts include:

* modules
* interfaces
* depth
* seams
* adapters
* leverage
* locality

This is especially useful when selecting good testing seams.

⸻

31. /to-questionnaire

Purpose:

Gather information held by another person when the project team does not possess the required knowledge.

The result feeds back into planning rather than directly becoming implementation authority.

⸻

32. /wizard

Purpose:

Structure operations that genuinely require a human.

Examples:

* credentials
* third-party dashboards
* external provisioning
* secret entry
* external approval

It should not become a generic excuse for inserting human gates into otherwise automatable work.

⸻

33. /wait-what

Purpose:

Repair communication when an explanation failed to communicate effectively.

It does not alter project authority.

⸻

34. /teach

Purpose:

Support structured learning over multiple sessions.

It is generally outside the normal production lifecycle.

⸻

35. /writing-for-agents

Purpose:

Produce documents intended primarily for agents.

Potential ITDD uses include:

* skill definitions
* execution contracts
* agent instructions
* AGENTS.md
* durable context documents

This may become particularly valuable as ITDD begins developing its own compound skills.

⸻

36. /setup-matt-pocock-skills

Purpose:

Initialize the Pocock engineering environment and conventions expected by the other skills.

This is project infrastructure rather than a recurring execution step.

⸻

37. Human Validation Philosophy

A major refinement during this discussion concerned human checkpoints.

The system should NOT use either extreme:

human approves everything

or:

human never participates

Instead:

Prime and the human determine the meaningful human-validation points on a project-by-project basis.

Human validation should be part of the verification strategy, not a generic security mechanism.

⸻

38. When Human Testing Is Appropriate

Some properties are difficult or impossible to prove adequately through automated testing alone.

Examples:

* UI usability
* game feel
* visual correctness
* interaction quality
* understandable visualization
* real-world workflow behavior
* whether the actual application behaves correctly from the user’s perspective

Prime should discuss these requirements with the human during orchestration.

The resulting checkpoints become part of the project’s execution contract.

⸻

39. Human Validation Must Test Real Work

A human checkpoint should not ask:

“Do you approve the agent’s report?”

Instead it should ask the human to exercise the actual deliverable.

Example:

The application is running.
Open the Settings screen.
Change the value from X to Y.
Save it.
Restart the application.
Expected result:
Y remains selected.
Report PASS or FAIL.

A human FAIL is evidence.

ITDD should then automatically route the failure back into diagnosis/build/test/verify without requiring the human to manage the repair process.

⸻

40. Real-System Proof

The conversation established an important proposed invariant:

No simulated success.

Acceptance evidence should exercise the actual deliverable through its real externally observable interface wherever reasonably possible.

The following alone should not substitute for a required real-system proof:

* mocks
* unit tests
* fixtures
* generated reports
* agent claims
* internal state inspection

These may all be valuable evidence.

But they cannot prove something they do not actually exercise.

This principle directly addresses a recurring historical problem: systems producing convincing PASS reports while the real application does not work.

⸻

41. Different Projects Need Different Proof

Human validation is contextual.

A backend library may need no human checkpoint.

A CLI might require one real terminal execution.

A web application may require browser testing.

A game may require actual human play.

A visualization may require human interpretation.

Prime and the human decide these requirements during project orchestration.

ITDD enforces the resulting proof strategy.

⸻

42. Autonomous Execution After Authority Is Established

The desired system is not “remove the human.”

It is:

Establish human authority and important validation requirements first, then allow routine engineering execution to proceed autonomously.

Once intent, scope, architecture constraints, and proof requirements are established, routine work should not continually interrupt the human.

Routine events include:

* BUILD failures
* TEST failures
* VERIFY failures
* regression failures
* ordinary repair
* retries
* expected integration work

These should normally be handled automatically.

⸻

43. Example Autonomous Failure Routing

BUILD failure
     ↓
/diagnosing-bugs
     ↓
new BUILD
TEST failure
     ↓
diagnosis if required
     ↓
new BUILD
     ↓
new TEST
VERIFY failure
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

Each new attempt receives fresh identity.

Previous evidence remains immutable.

⸻

44. Skills as an Evolvable Procedure Layer

Another major conclusion is that the existing Pocock skills should not be considered the final possible skill system.

They provide a strong starting methodology.

As ITDD accumulates operational evidence, new skills or composed workflows may emerge.

Examples:

/itdd-feature

could compose:

/grill-with-docs
→ /to-spec
→ /to-tickets
→ ITDD execution

An /itdd-bug procedure might compose:

/diagnosing-bugs
→ regression TDD
→ TEST
→ VERIFY

An /itdd-recovery procedure might compose:

diagnose state
→ preserve attempt
→ abandon authority
→ reconstruct
→ fresh execution
→ recovery proof

An /itdd-ui-proof procedure might compose:

automated verification
→ real application launch
→ human validation
→ evidence

These should preferably be compositions of smaller proven procedures, rather than enormous prompts.

⸻

45. Prime as Operational Analyst

Prime should not merely orchestrate current work.

Because Prime has read access to project history and telemetry, it should become the system’s operational analyst.

Prime should examine accumulated execution data and identify patterns.

Examples:

* Which skill sequences produce the fewest retries?
* Which vertical-slice sizes perform best?
* Which testing seams catch real failures?
* Which verification failures repeat?
* Which skills frequently precede successful builds?
* Which human checkpoints detect failures automation misses?
* Which agent contexts are too large?
* Which tasks consume excessive tokens?
* Which work repeatedly requires recovery?
* Which standards violations recur?
* Which areas have false PASS problems?
* Which procedures generate unnecessary human intervention?

Prime can then discuss operational improvements with the human.

⸻

46. Telemetry as a First-Class Product

Telemetry should not be treated merely as debugging logs.

It is one of the system’s most valuable outputs.

Useful telemetry may include:

* project
* intent
* execution unit
* execution identity
* agent role
* skill used
* skill sequence
* context size
* token usage
* elapsed time
* files touched
* vertical-slice size
* RED cycles
* GREEN cycles
* tests added
* test failures
* regression failures
* TEST result
* VERIFY result
* standards findings
* spec findings
* retry count
* diagnosis events
* recovery events
* human checkpoints
* human PASS/FAIL
* real-system proof
* eventual promotion outcome

The exact schema should be designed deliberately rather than inferred later from unstructured logs.

⸻

47. Operational Learning Loop

Prime should convert telemetry into an explicit learning process.

Recommended model:

OBSERVATION
    ↓
PATTERN
    ↓
PROPOSED PROCESS CHANGE
    ↓
Prime + Human discussion
    ↓
CONTROLLED EXPERIMENT
    ↓
measured result
    ↓
ADOPT / REJECT

This prevents accidental policy changes based on isolated events.

⸻

48. Example Operational Learning

Suppose telemetry shows:

Execution units touching more than six files average 2.8 times more repair cycles.

Prime might recommend:

Reduce vertical-slice size for this project class.

That recommendation can then be tested.

Another example:

Standards verification has rejected the same coding pattern eight times.

Prime may recommend moving that rule earlier into BUILD guidance.

Instead of repeatedly detecting the defect, the system learns to prevent it.

Another example:

Four UI changes passed automated verification but subsequently failed human testing.

Prime may recommend introducing a real-system UI proof before promotion for that project class.

This is the kind of learning the system should support.

⸻

49. Reintroducing QMD

The original Obsidian/QMD concept now has a particularly clear role.

QMD should become the operational knowledge and retrieval layer.

ITDD generates evidence and telemetry.

QMD indexes that history.

Prime queries QMD.

Prime and the human use the results to improve future operation.

Architecture:

ITDD executions
      ↓
structured telemetry
      +
evidence/history
      ↓
     QMD
      ↓
Prime queries
      ↓
recommendation
      ↓
Prime ↔ Human
      ↓
chosen procedure
      ↓
ITDD execution

⸻

50. QMD Must Remain Advisory

QMD should not become another authority engine.

The governing rule should be:

QMD recommends procedure. ITDD grants authority.

QMD may say:

Historically /diagnosing-bugs → /implement → /code-review works best for this failure pattern.

QMD may not decide:

Therefore this worker now has permission to modify production.

Authority remains in ITDD.

⸻

51. Three Classes of QMD Knowledge

Operational knowledge should be separated into at least three conceptual categories.

Raw Observations

Direct facts from executions.

Examples:

* BUILD required three attempts.
* VERIFY rejected candidate.
* Human UI test failed.
* /diagnosing-bugs was used.
* execution took 22 minutes.

Derived Patterns

Statistical or analytical observations.

Example:

UI changes without real-system proof have a significantly higher post-verification human failure rate.

These are interpretations of accumulated data.

Validated Operational Knowledge

Rules that Prime and the human have reviewed and intentionally accepted.

Example:

UI-changing tickets in this project require real-system human proof before promotion.

This distinction prevents one unusual run from automatically becoming organizational policy.

⸻

52. QMD as Skill Advisor

One of the most promising QMD functions is skill selection.

Prime could ask:

What skill should I use here?

Or:

What sequence of skills has worked best for similar work?

Or:

Which workflow historically produces the fewest retries for recovery changes?

A future QMD answer might resemble:

Task resembles 14 previous recovery-related changes.
Historically successful sequence:
1. /diagnosing-bugs
2. /to-spec
3. /to-tickets
4. /implement + /tdd
5. /code-review
6. real-system recovery proof
Observation:
Attempts that skipped /diagnosing-bugs required
substantially more rework.

Prime can then discuss that recommendation with the human.

⸻

53. QMD as Skill Documentation Retrieval

QMD can also answer procedural questions.

Examples:

What does /diagnosing-bugs require before forming a hypothesis?

When should /wayfinder be used?

What is the difference between /research and /prototype?

Does /implement already invoke /tdd?

What should happen after /to-tickets?

This means Prime does not need to carry every skill definition permanently in its active context.

It can retrieve the appropriate procedure when needed.

This supports leaner context.

⸻

54. QMD and Obsidian

QMD and Obsidian should serve different purposes.

QMD

Machine-oriented retrieval and querying.

Used by Prime to locate:

* historical evidence
* skill documentation
* operational patterns
* previous decisions
* similar executions
* process results

Obsidian

Human-readable visualization and exploration.

Used to examine:

* relationships
* project history
* decisions
* skill relationships
* operational lessons
* execution maps
* accepted process knowledge

Therefore:

QMD is the query layer. Obsidian is the human knowledge view. ITDD remains the authority layer.

⸻

55. QMD Should Support Longitudinal Analysis

Prime should not merely ask what happened during the latest execution.

It should be able to ask questions across time.

Examples:

What changed after we modified /to-tickets?

Did average retry count improve?

Did smaller execution units reduce verifier failures?

Did adding human UI proof reduce false promotion?

Has the recovery skill improved first-attempt recovery?

This allows actual before/after evaluation of process changes.

⸻

56. Controlled Evolution of Skills

The system should eventually treat skills themselves as testable operational artifacts.

A proposed skill change should follow a lifecycle similar to code:

observed problem
      ↓
proposed skill change
      ↓
controlled use
      ↓
telemetry
      ↓
compare results
      ↓
adopt / modify / reject

This prevents the skill library from becoming a collection of untested prompts.

Skills should improve because evidence shows that they improve engineering outcomes.

⸻

57. Potential Metrics for Skill Effectiveness

Possible measurements include:

* first-pass BUILD success
* first-pass TEST success
* first-pass VERIFY success
* total repair cycles
* time to accepted candidate
* tokens consumed
* context consumed
* human interventions
* human test failures
* regressions introduced
* post-promotion defects
* recovery frequency
* false PASS frequency
* average vertical-slice size
* files touched per EU
* tests added per behavior
* diagnosis time

These measurements can help identify whether a skill or skill sequence actually helps.

⸻

58. Important Architectural Boundary: Prime Must Not Become the Factory

Prime’s broad read access creates a temptation to let Prime perform everything.

That should be resisted.

Prime should be powerful because it can understand the factory, not because it can bypass it.

Prime’s responsibilities are:

UNDERSTAND
DISCUSS
DESIGN
ORCHESTRATE
OBSERVE
ANALYZE
RECOMMEND

ITDD and specialized workers perform:

BUILD
TEST
VERIFY
INTEGRATE
PROMOTE

within explicitly granted authority.

⸻

59. Important Architectural Boundary: ITDD Should Not Become the Engineer

The opposite failure is also possible.

ITDD should not accumulate increasingly sophisticated engineering judgment.

ITDD should remain primarily deterministic.

It should know:

* who may act
* what they may touch
* which candidate is under test
* what evidence is required
* what state transitions are legal
* whether verification succeeded
* whether promotion is authorized

The Pocock skills and reasoning agents determine how to solve the engineering problem.

That separation keeps ITDD understandable and enforceable.

⸻

60. Important Architectural Boundary: QMD Should Not Become Authority

QMD should learn aggressively but act conservatively.

It may identify:

* correlations
* repeated failures
* successful skill combinations
* likely workflow improvements

But it cannot silently modify:

* approved intent
* worker authority
* lifecycle rules
* promotion requirements
* security policy

Those changes require deliberate operational adoption.

⸻

61. Target End-to-End Lifecycle

The mature system should resemble:

Human
  ↕
Prime
  │
  ├── understands request
  ├── reads project/history/QMD
  ├── discusses design with human
  ├── selects skills
  └── launches specialized agents
        │
        ├── /research
        ├── /grill-with-docs
        ├── /prototype
        ├── /to-spec
        └── /to-tickets
                 │
                 ▼
            ITDD Controller
                 │
                 ├── BUILD
                 │     /implement
                 │        ↓
                 │       /tdd
                 │
                 ├── TEST
                 │     independent
                 │
                 ├── VERIFY
                 │     Spec
                 │     Standards
                 │
                 ├── real-system proof
                 │
                 ├── human proof if required
                 │
                 ├── integration
                 │
                 └── promotion
                         │
                         ▼
                     telemetry
                         │
                         ▼
                        QMD
                         │
                         ▼
                       Prime
                         │
                         ▼
                 operational learning

⸻

62. Example Feature Lifecycle

Human:

Prime, I want ITDD to support safe recovery after an interrupted execution.

Prime reads:

* current implementation
* project glossary
* existing recovery specification
* prior failures
* QMD history

Prime determines that requirements remain ambiguous.

Prime launches:

/grill-with-docs

The subagent clarifies recovery semantics and records terminology.

Prime and the human discuss the result.

Prime launches:

/to-spec

The resulting specification defines:

* behavior
* authority
* state transitions
* recovery invariants
* test seams
* real-system proof

Prime launches:

/to-tickets

The work becomes vertical tracer-bullet execution units.

Prime hands execution to ITDD.

ITDD launches BUILD with:

/implement
/tdd

The Builder works red → green.

ITDD launches independent TEST.

ITDD launches independent VERIFY.

If VERIFY fails, ITDD routes the failure through the appropriate repair procedure.

If real-system proof is required, ITDD runs it.

If human observation is required, ITDD presents the real application to the human with concrete PASS/FAIL instructions.

After promotion, telemetry enters QMD.

Prime later analyzes the execution.

⸻

63. Example Learning Cycle

Suppose recovery took four attempts.

Telemetry shows:

Attempt 1
No diagnosis
FAIL
Attempt 2
Direct implementation repair
FAIL
Attempt 3
/diagnosing-bugs
reproduction established
FAIL during verification
Attempt 4
/diagnosing-bugs
/tdd
/code-review
real-system recovery proof
PASS

After similar examples accumulate, QMD identifies a pattern.

Prime reports:

Recovery changes using a reproducible diagnosis loop before implementation have materially higher first-pass verification success.

Prime and the human decide whether recovery work should normally begin with /diagnosing-bugs.

If accepted, that becomes validated operational knowledge.

Future projects benefit from previous failures.

⸻

64. The Emerging Self-Improving Engineering Loop

The resulting architecture forms a closed learning system:

INTENT
  ↓
DESIGN
  ↓
SKILL SELECTION
  ↓
CONTROLLED EXECUTION
  ↓
REAL TESTING
  ↓
VERIFICATION
  ↓
REAL-SYSTEM PROOF
  ↓
TELEMETRY
  ↓
QMD
  ↓
ANALYSIS
  ↓
PROCESS IMPROVEMENT
  ↓
BETTER FUTURE EXECUTION

The system improves because it remembers what happened, not because an agent claims that its new process is better.

⸻

65. Core Principles Established

The discussion produced the following core principles.

1. Prime orchestrates; it does not normally implement.

2. Prime should have broad read-only visibility.

3. Material project changes should be delegated to specialized skill-guided agents.

4. Pocock skills provide engineering methodology.

5. ITDD provides authority and enforcement.

6. QMD provides operational memory and retrieval.

7. Obsidian provides a human-readable knowledge view.

8. BUILD should use real TDD.

9. Work should default to vertical tracer-bullet slices.

10. TEST and VERIFY remain independent of BUILD.

11. Failed attempts remain preserved.

12. Recovery receives fresh execution authority rather than rewriting history.

13. Routine failures should not require human intervention.

14. Human checkpoints are selected because human observation is meaningful, not because the system wants another approval.

15. Human checkpoints must exercise real deliverables.

16. Automated evidence must exercise the real system whenever reasonably possible.

17. A report saying PASS is not equivalent to the product working.

18. Telemetry is a first-class product of execution.

19. Prime should analyze telemetry longitudinally.

20. QMD should recommend skills and workflows from actual history.

21. QMD recommendations do not grant authority.

22. Process changes should be treated as experiments and measured.

23. Skills themselves should evolve from operational evidence.

24. Compound skills should preferably compose smaller proven skills rather than becoming giant prompts.

25. ITDD should enforce good engineering procedures rather than attempting to replace them.

⸻

66. Recommended Next Architectural Work

Once the current ITDD completion work is stable, the next design effort should focus on the Prime/QMD operational-learning layer, without destabilizing the execution control plane.

That work should define:

1. The canonical telemetry schema.
2. Which telemetry is raw immutable evidence.
3. How telemetry enters QMD.
4. How QMD indexes skill usage.
5. How skill versions are identified.
6. How Prime queries historical executions.
7. How QMD distinguishes observation from derived conclusions.
8. How validated operational knowledge is represented.
9. How Prime recommends skill sequences.
10. How process experiments are identified.
11. How before/after results are compared.
12. How Obsidian visualizes this knowledge.
13. How project-specific knowledge remains isolated.
14. How Prime retains read-only access.
15. How proposed process changes enter controlled implementation rather than modifying ITDD automatically.

This should be designed as an observational/advisory layer first.

It should not initially be permitted to modify ITDD policy autonomously.

⸻

67. Long-Term Vision

The goal is larger than building an autonomous coding agent.

The intended system is an evidence-driven software engineering environment.

Prime provides persistent intelligence and conversation.

Pocock skills provide reusable engineering disciplines.

ITDD provides deterministic control and trustworthy evidence.

QMD provides historical memory and operational learning.

Obsidian makes that accumulated knowledge understandable to the human.

Together:

Human judgment
      +
Prime reasoning
      +
Pocock procedures
      +
ITDD enforcement
      +
real-world testing
      +
telemetry
      +
QMD learning
      =
an engineering system that can improve
its own operating procedures from evidence
without surrendering human authority

The most important goal is not maximum autonomy.

It is:

Consistently producing real, tested, verifiable work while learning from every success and every failure.

That is the direction established by this discussion.
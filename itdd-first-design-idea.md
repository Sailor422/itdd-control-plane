ITDD CONTROL PLANE

Complete Codex Bootstrap and Controlled-Development Handoff

You are being given responsibility for establishing a new canonical project:

ITDD Control Plane

Repository name

itdd-control-plane

Full title

ITDD Control Plane — Intent- and Test-Driven Development for Reliable Agentic Software Engineering

You are also being supplied with the current ITDD thesis artifacts.

This repository is intended to become the permanent, shareable, collaborative home for the research, architecture, specifications, code, tests, skills, examples, evidence, and future development of the ITDD Control Plane.

This is not merely another Prime repository.

Prime will be one system developed to operate under ITDD.

ITDD itself must remain framework- and agent-runtime-neutral wherever practical.

⸻

1. Mission

Modern coding agents can reason and implement effectively, but the reasoning agent itself must not own durable intent, lifecycle authority, verification authority, project memory, promotion authority, or unrestricted context selection.

The architectural objective is:

Agents reason. The controller determines what actions are legal.

And:

No agent controls the lifecycle.

Planner does not launch Builder.

Builder does not launch Verifier.

Verifier does not promote.

Integrator does not silently redesign the project.

Conversational Prime does not become Builder merely because it understands the project.

Codex does not advance lifecycle state merely because it believes work is complete.

Agents are disposable reasoning workers.

Durable authority exists outside the reasoning engine.

⸻

2. Important Existing Environment

This Mac already contains a working Codex installation.

There is substantial historical material under:

~/.codex

including a large amount of accumulated data and knowledge/history.

There are also historical knowledge stores associated with Claude and Hermes elsewhere on this machine.

Claude is no longer part of the active development workflow.

Codex must remain operational throughout this transition.

⸻

3. Absolute Safety Rule

DO NOT initially:

* delete ~/.codex
* move ~/.codex
* rename ~/.codex
* purge Codex history
* rewrite its vault
* normalize or reorganize it in place
* merge its historical knowledge
* reset Codex
* disable Codex
* destroy or overwrite its current configuration
* modify historical Claude vaults
* modify Hermes vaults
* modify unrelated Prime projects
* move existing repositories
* bulk-copy private historical data into this new public project

Treat old Codex, Claude, Hermes, and similar stores as:

Read-only legacy source archives until deliberately curated later.

⸻

4. One Prompt, Staged Execution

You are receiving the complete architectural direction now.

Do NOT attempt to implement everything at once.

Work in stages.

For every implementation stage:

1. establish exact baseline
2. write plan
3. commit baseline
4. implement narrowly
5. run tests
6. run negative tests
7. independently verify
8. preserve evidence
9. human review where required
10. commit accepted result
11. establish known-good tag

If a stage fails:

* preserve the failure
* diagnose it
* repair it
* independently verify again

Do not advance because something merely “looks good.”

⸻

5. First Task — Establish the Canonical Repository

Determine the machine’s established permanent development root.

Create a clean sibling repository, not a child of another project.

Target:

<development-root>/itdd-control-plane

Do NOT put it under:

* ~/.codex
* temporary directories
* Prime execution workspaces
* another application repository
* another project’s .idd area

Record the exact absolute path.

Initialize Git immediately.

Use main unless the environment has a compelling established convention otherwise.

⸻

6. Repository Structure

Create an initial structure similar to:

itdd-control-plane/
│
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── ROADMAP.md
├── CHANGELOG.md
│
├── thesis/
│
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── principles.md
│   │   ├── roles-and-authority.md
│   │   ├── lifecycle.md
│   │   ├── context-compiler.md
│   │   ├── project-map.md
│   │   ├── knowledge-model.md
│   │   ├── evidence-model.md
│   │   ├── recovery.md
│   │   └── break-glass.md
│   │
│   ├── research/
│   │
│   ├── specs/
│   │   ├── CODEX-BOOTSTRAP-SPEC.md
│   │   └── CONTROL-PLANE-SPEC.md
│   │
│   └── adr/
│
├── control/
│   ├── controller/
│   ├── context/
│   ├── evidence/
│   ├── project_map/
│   ├── recovery/
│   ├── maintenance/
│   └── break_glass/
│
├── skills/
│
├── schemas/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── negative/
│   └── end_to_end/
│
├── examples/
│   ├── minimal_project/
│   └── demo_project/
│
├── tools/
│
├── work/
│
├── .idd/
│   ├── intent/
│   ├── graph/
│   ├── state/
│   ├── evidence/
│   ├── telemetry/
│   ├── knowledge/
│   ├── context/
│   ├── audit/
│   ├── project_map/
│   ├── human/
│   └── recovery/
│
└── .github/
    ├── ISSUE_TEMPLATE/
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/

You may refine implementation names later, but do not scatter project-specific authority outside the project root.

⸻

7. Thesis

Place the supplied thesis artifacts under:

thesis/

Use durable names such as:

ITDD-Control-Plane-Thesis.docx
ITDD-Control-Plane-Thesis.pdf
ITDD-Control-Plane-Thesis.md

If Markdown source is not supplied, create a faithful Markdown version for version control.

Do not materially rewrite the thesis during repository bootstrap.

The thesis is a research/design artifact explaining:

* the problem
* LPVM
* IDD
* TDD
* Prime/IDD experimentation
* deterministic control
* evidence
* context engineering
* human control
* proposed architecture
* experimental limitations
* future work

Distinguish demonstrated results from proposed architecture.

Do not claim that unfinished systems are proven.

⸻

8. Public Repository Foundation

Create a public-facing README that explains the project quickly.

Opening concept should be similar to:

ITDD Control Plane is an experimental architecture for reliable AI-assisted software engineering. It combines Intent-Driven Development, Test-Driven Development, lean context and knowledge management, deterministic lifecycle control, independent verification, human decision gates, and evidence-backed promotion.

Prominently state:

Agents reason. The controller decides what actions are legal.

Make clear:

* ITDD is not tied permanently to Codex
* ITDD is not tied permanently to Prime
* Prime is one target runtime
* Codex is currently the development agent being brought under control
* the project is experimental
* implemented features must be distinguished from proposed features

Create:

* CONTRIBUTING.md
* CODE_OF_CONDUCT.md
* SECURITY.md
* ROADMAP.md
* ADR template

Contribution principles:

* meaningful changes through pull requests
* architecture changes should use ADRs where appropriate
* controller changes require regression tests
* new skills do not grant themselves authority
* schema breaking changes require migration guidance
* failures must not be rewritten out of history

⸻

9. Git Baseline

Before auditing Codex:

1. inspect repository for accidental sensitive information
2. create .gitignore
3. make initial commit
4. create known-good baseline tag

Suggested commit:

chore: bootstrap ITDD control plane repository

Suggested tag:

bootstrap-0

Record exact SHA.

⸻

10. GitHub Repository

Check authentication:

gh auth status

If valid, create:

itdd-control-plane

Description:

Intent- and Test-Driven Development control architecture for reliable agentic software engineering.

The project is intended to be shareable and open to contributors.

Prefer public unless a material ambiguity requires explicit human decision.

Connect origin.

Push:

* main
* baseline tag

Verify remote state.

If GitHub authentication fails:

* do not destructively modify credentials
* do not waste large amounts of time trying random fixes
* finish the local canonical repository
* report the exact blocker

⸻

11. Project Isolation Invariant

Every controlled ITDD project must ultimately be a self-contained authority domain.

Everything project-specific stays inside that project’s root, including:

* approved intent
* graph
* execution state
* evidence
* telemetry
* knowledge
* context packets
* project map
* approvals
* tests
* implementation
* documentation
* recovery state

External information may enter only through explicit, recorded import or retrieval.

Workers must not silently rely on unrelated project directories or hidden personal vaults.

⸻

12. Git and Sandbox Model

Canonical project repository is durable authority.

Execution workspaces are disposable.

Conceptually:

Canonical Project
      |
      +-- Planner workspace
      +-- Builder EU-001 workspace
      +-- Builder EU-002 workspace
      +-- Verifier workspace
      +-- Integration workspace

Preferred progression:

worker branch/worktree
    -> verification
    -> human gate where required
    -> integration
    -> integration verification
    -> promotion
    -> canonical branch

Failed attempts remain preserved in evidence even if they never reach canonical history.

⸻

13. Intent-Driven Development

Natural conversation is allowed before formal intent development.

Conversation is not implementation authority.

An explicit /idd action begins formal intent development.

The intent agent should:

* inspect resolved project information
* present its current understanding
* identify ambiguity
* grill the human
* establish terminology
* surface assumptions
* capture decisions
* allow human review
* require explicit approval

No implementation during intent development.

⸻

14. Approved Intent

Human approval creates an immutable intent version.

Example:

Intent: I-001
Version: 1
Status: APPROVED

Approved intent cannot be silently edited.

Changing the destination requires:

Intent Amendment

⸻

15. Mutable Plan

Do NOT make the execution plan permanently immutable.

Use:

Intent is immutable authority. Execution plan is versioned mutable state.

Critical distinction:

Replan changes how we get there.

Amendment changes where “there” is.

Graph revisions must preserve:

* previous versions
* reason
* affected EUs
* affected dependencies
* evidence validity
* intent relationship

⸻

16. Vertical Execution Units

Use behavior-oriented vertical tracer-bullet slices wherever practical.

Avoid structures like:

database phase
backend phase
frontend phase

Prefer:

behavior A end-to-end
behavior B end-to-end
behavior C end-to-end

Each EU should:

* represent useful behavior
* have explicit acceptance
* identify blockers
* minimize unnecessary dependencies
* fit reasonably into fresh context
* permit parallel work when safe

The correct size should evolve empirically from telemetry.

Do not pretend we already know the universally perfect EU size.

⸻

17. Two-Agent Decomposition

Use:

Planner

Proposes:

* EUs
* dependencies
* acceptance structure
* vertical slices

Graph Evaluator

Independently examines:

* Is each EU meaningful?
* Is it vertical?
* Can it be independently proven?
* Is it oversized?
* Is it needlessly dependent?
* Are interfaces explicit?
* Can more safe work run in parallel?
* Is architecture missing?
* Does anything drift from intent?

Neither approves the final graph.

Initially, graph approval is human-only.

⸻

18. Kanban / Visible State Machine

Initial flow:

PROPOSED
-> APPROVED
-> READY
-> BUILDING
-> VERIFYING
-> HUMAN REVIEW
-> INTEGRATING
-> INTEGRATION VERIFY
-> PROMOTED
-> DONE

Additional states:

BLOCKED
NEEDS CLARIFICATION
REPLAN REQUIRED
INTENT AMENDMENT REQUIRED
FAILED
INTERRUPTED
ABANDONED

These reflect authoritative controller state.

They are not just UI labels.

⸻

19. Human Gates

Initially require explicit human approval:

* intent
* initial graph
* independently verified EU work
* material integration
* final promotion
* significant replans
* intent amendments
* controller modifications

Autonomy may later increase for proven low-risk classes.

Autonomy must be earned through telemetry and evidence.

⸻

20. Roles

Implement conceptual separation for:

* Conversational Agent / Prime
* Planner
* Graph Evaluator
* Scout / Context Resolver
* Context Compiler
* Builder
* Spec Verifier
* Standards Reviewer
* Integrator
* Integration Verifier
* Promoter
* Controller

Each role gets narrowly defined authority.

⸻

21. Controller Principle

Controller may:

* validate
* authorize
* launch
* stop
* transition
* record

Controller should not:

* invent requirements
* design the application
* write normal implementation code
* alter human intent

It owns lifecycle authority, not creative authority.

⸻

22. Capability-Based Authority

Do not rely on prompt instructions alone.

Example:

ROLE:
Builder
EXECUTION:
EX-1042
EU:
EU-014
BASELINE:
<git SHA>
READ:
exact compiled context
WRITE:
specific authorized files
EXECUTE:
approved commands
MAY REQUEST:
context
clarification
replan
FORBIDDEN:
intent
graph
controller
canonical branch
other EUs
verifier evidence
promotion
policy
global knowledge

Use filesystem, sandbox, Git and controller enforcement where practical.

A worker must lack capabilities it is forbidden to exercise.

⸻

23. Context Compiler

Context programming is a core architectural component.

Core rule:

Execution agents do not discover their working context. They receive resolved context.

Do not hand an agent:

“Look for authentication.py.”

Provide:

PATH:
exact canonical location
PURPOSE:
why it matters
RELEVANT SYMBOLS:
specific functions/classes/interfaces
AUTHORITY:
READ / WRITE / TEST / EXECUTE
REASON INCLUDED:
relationship to current EU

⸻

24. Context Types

Separate:

Authority Context

Binding rules.

Working Context

Required implementation material.

Knowledge Context

Relevant retrieved knowledge.

Evidence Context

Material required for verification.

Do not indiscriminately dump them together.

⸻

25. Context Priority

When constrained:

1. authority
2. EU contract
3. acceptance criteria
4. dependency contracts
5. working files
6. relevant knowledge
7. historical context

Historical chat should not be the primary project database.

⸻

26. Context Provenance

Track:

* source
* reason included
* authority
* freshness
* related EU
* token cost where measurable

When a context failure occurs, determine whether:

* knowledge did not exist
* Scout failed
* Compiler omitted it
* trimming removed it
* worker ignored it

Do not call all of these “agent failure.”

⸻

27. Progressive Disclosure

Start workers with the smallest sufficient context.

If more is required:

CONTEXT REQUEST

A request includes:

* EU
* requested material
* reason
* expected use

Scout/Project Map resolves.

Context Compiler decides what is supplied.

Track context misses.

⸻

28. No Casual File Hunting

Builders and Verifiers should not burn large amounts of time repeatedly doing:

find .
grep everything
browse unrelated directories
read random docs

Known context should arrive resolved.

Discovery is a separate capability.

⸻

29. Scout / Context Resolver

Scout searches.

It may use:

* repo search
* symbol indexes
* Project Map
* Git information
* QMD or project-local retrieval
* documentation
* targeted external material

Scout returns structured findings.

Scout does not implement application changes.

⸻

30. Project Map

Maintain a structural map of project reality.

Track where practical:

* files
* directories
* symbols
* imports
* dependencies
* APIs
* contracts
* architecture components
* tests
* EUs
* verifier findings
* requirements
* knowledge relationships
* history

Target traceability:

Intent Requirement
   -> EU
   -> File/Symbol
   -> Test
   -> Verification Evidence
   -> Integration Result

Use deterministic extraction first.

Examples:

* filesystem
* AST
* symbol index
* imports
* test discovery
* Git
* coverage where useful

Project Map is derived state.

It must be rebuildable.

It is not authority.

⸻

31. Knowledge Architecture

Knowledge is not context.

A project may know a great deal.

A worker should receive only relevant knowledge.

Classify:

* Project Truth
* Historical Evidence
* Learned Operational Knowledge
* External / Reference Knowledge

Authority hierarchy:

Authoritative State
> Verified Project Knowledge
> Validated Operational Knowledge
> Historical Observation
> External Reference

Current authority always wins.

⸻

32. Knowledge Metadata

Track where practical:

* source
* scope
* project
* authority level
* creation date
* verification date
* supersedes
* superseded-by
* related files
* symbols
* EUs
* intent version
* confidence
* provenance
* tags

⸻

33. Knowledge Promotion

Do not allow agent observations or telemetry to become rules automatically.

Use:

Observation
-> Pattern
-> Candidate Rule
-> Validated Rule
-> Policy

Initially require human approval for policy promotion.

⸻

34. Existing Vaults

Legacy sources currently include substantial:

* Codex knowledge/history
* Claude knowledge
* Hermes knowledge
* other scattered research

Do not merge these automatically.

Treat them as untrusted historical source archives.

Later create a dedicated migration/curation workflow:

Source Archive
    ↓
Inventory
    ↓
Deduplicate
    ↓
Classify
    ↓
Detect Staleness
    ↓
Detect Conflict
    ↓
Validate
    ↓
Curated Import

Do not make legacy vaults part of default working context.

⸻

35. TDD and Evidence

Strongly use TDD where appropriate:

RED
-> GREEN
-> REFACTOR

Prefer:

* one behavior at a time
* behavior-oriented tests
* deliberate testing seams
* minimal unnecessary mocking

But do not turn TDD into dogma.

The more important invariant is:

Acceptance evidence is defined before implementation.

⸻

36. Acceptance Contract

Before Builder launch define:

* required behavior
* acceptance criteria
* required tests/evidence
* negative tests
* permitted file changes
* expected artifacts
* integration assumptions
* human review requirement
* evidence schema

⸻

37. Evidence Binding

Every acceptance record should bind to:

intent_version
graph_version
eu_id
execution_id
role
baseline_sha
candidate_sha
context_packet_hash
test_command
observed_test_result
artifact_hashes
timestamp

Evidence from the wrong execution, branch, graph, intent, candidate, or context does not count.

⸻

38. False-Pass Resistance

Explicitly defend against:

* wrong tests returning zero
* incorrect test counts
* stale evidence
* old branch evidence
* pre-change evidence
* Builder self-certification
* verifier provenance mismatch
* partial tests represented as full acceptance
* unauthorized writes
* missing artifacts

Core rule:

Absence of proof is never success.

⸻

39. Independent Review Axes

Adopt separate fresh-context checks for:

Spec Verification

Does the candidate satisfy the EU contract?

Standards Review

Does it satisfy required implementation/architecture/quality standards?

Do not let one substitute for the other.

⸻

40. Failure Routing

Do not turn every failure into “retry.”

Classify:

Implementation defect
-> Builder
Missing context
-> Context Compiler / Scout
Bad decomposition
-> Replan
Requirement ambiguity
-> Human clarification
Destination change
-> Intent Amendment
Integration design conflict
-> Replan
Control failure
-> freeze + maintenance

⸻

41. Replan Request

Include:

* discovery
* affected EUs
* reason
* proposed graph change
* dependencies
* impact on intent
* evidence preserved
* evidence invalidated
* risk

Do not overwrite previous graph versions.

⸻

42. Integration

Verified EUs are not automatically globally correct.

Use a distinct Integrator.

Integrator may combine approved work and perform narrowly permitted integration mechanics.

If substantive redesign is required:

STOP and replan.

Then use a fresh Integration Verifier.

⸻

43. Obsidian

Obsidian should become a first-class human visualization layer.

It is not authoritative.

The controller is authoritative.

Obsidian displays controller/project state.

Provide views for:

* current intent
* amendments
* dependency graph
* Kanban
* EU state
* architecture
* requirement relationships
* files/symbols
* tests
* evidence
* failures
* timeline
* human gates
* knowledge

Support:

Operational View

What is happening?

What is blocked?

What needs human action?

Teaching View

Why does this dependency exist?

Why was this EU split?

Why did verification fail?

Why does this gate exist?

The human should not have to reconstruct state from logs.

⸻

44. Recovery

Any worker may die.

That must be boring.

Persist enough state that a fresh process can resume from disk.

Track:

* active intent
* graph
* EU state
* human gates
* role launches
* execution IDs
* packet hashes
* branches/worktrees
* verifier outcomes
* integration
* promotion
* failures
* audit events

Example:

BUILDING
+ dead worker
+ no completion evidence
= INTERRUPTED

Possible legal response:

* resume safe workspace
* reconstruct workspace
* relaunch same packet
* abandon attempt but preserve history
* human review if safety uncertain

If Verifier dies:

No PASS.

If waiting for human:

Remain waiting for human.

⸻

45. Worker State

Use something similar to:

CREATED
-> LAUNCHED
-> ACTIVE
-> COMPLETED

Terminal states:

FAILED
INTERRUPTED
ABANDONED

Transitions require durable evidence.

⸻

46. Maintenance Mode

The controller must not make itself impossible to repair.

Provide:

Normal Project Execution Mode

Strict enforcement.

Maintenance Mode

Human-authorized controller development.

Maintenance mode must:

* freeze normal execution
* snapshot state
* preserve known-good controller
* create dedicated repair branch/worktree
* allow narrow controller changes
* run control regression tests
* require human approval before activation

Agents cannot grant themselves Maintenance Mode.

⸻

47. Human-Only Break Glass

Create a very small recovery mechanism, as independent of main controller code as practical.

Eventually support commands similar to:

./control/break-glass.sh

and:

./control/break-glass-approve.sh

Agents must not be authorized to invoke these.

Entry should:

1. freeze normal execution
2. snapshot state
3. record controller SHA
4. generate unique nonce/ID
5. obtain explicit human confirmation
6. record reason
7. create repair environment
8. preserve prior known-good controller

Exit requires:

* controller regression PASS
* recovery proof PASS
* new SHA
* explicit human approval
* append-only activation record

Old approvals must not be reusable.

⸻

48. Telemetry

Treat telemetry as a first-class project output.

Capture where practical:

* context size
* context sources
* context misses
* token consumption
* retries
* verifier failures
* standards failures
* integration conflicts
* test effectiveness
* human corrections
* graph revisions
* EU size/complexity
* interruptions
* duration
* failure classification
* knowledge retrieval
* promotion outcomes

Long-term research questions include:

* What EU size works best?
* Which graph patterns fail?
* Which contexts are most effective?
* Which files are commonly omitted?
* Which tests catch real defects?
* When is fresh context better?
* What knowledge retrieval is useful?

Telemetry informs policy.

It does not automatically become policy.

⸻

49. Pocock Skills Research

Study the current public Matt Pocock skills repository.

Do not install the entire suite wholesale.

Treat it as a research/reference source.

Review relevant ideas around:

* grill-with-docs
* domain-modeling
* to-spec
* to-tickets
* TDD
* code-review
* diagnosing-bugs
* writing-for-agents
* wayfinder
* human-only invocation

For each classify:

ADOPT
ADAPT
REFERENCE ONLY
REJECT FOR THIS ARCHITECTURE

Strong candidates already identified conceptually include:

Domain modeling / grilling

Useful for intent clarification.

To-tickets

Useful for vertical slices and dependency graphs.

TDD

Useful for behavior-first implementation/evidence.

Code review

Useful for independent Spec vs Standards review.

Diagnosing bugs

Useful for requiring reproducible feedback loops.

Writing for agents

Useful for lean, precise context packets.

Human-only invocation

Useful for explicit approval/maintenance boundaries.

Critical rule:

Skill does not equal authority.

A skill operates only within a controller-granted capability envelope.

⸻

50. Stage A — Codex Environment Audit

Only after the repository and baseline are established, inspect the current Codex environment read-only.

Inspect:

* ~/.codex
* configuration
* skills
* instructions
* hooks
* scripts
* wrappers
* aliases
* history
* knowledge locations
* environment variables
* local helper tooling
* integrations
* project configurations
* anything that globally changes behavior

Classify:

SAFE
GLOBAL-INFLUENCE
LEGACY-KNOWLEDGE
MIGRATION-CANDIDATE
CONTAMINATION-RISK
UNKNOWN

Record:

* location/mechanism
* function
* scope
* classification
* contamination risk
* whether it affects all Codex sessions
* recommended future handling

DO NOT copy private vault contents into this public repository.

If sensitive machine-specific audit detail is required, store it under a Git-ignored private work area and create a sanitized public report.

⸻

51. Initial Implementation Order

Do not attempt the complete architecture immediately.

After Stage A, proposed rollout should generally proceed:

A  Codex baseline / contamination audit
B  Clean repository + isolation foundations
C  Durable state + append-only audit
D  Intent vs graph representation
E  Role definitions + capability model
F  Context Compiler v1
G  Scout / Context Requests
H  Project Map v1
I  Kanban + Obsidian human views
J  Spec Verifier + Standards Reviewer
K  Evidence binding + false-pass tests
L  Single-EU end-to-end proof
M  Recovery / interruption / resume
N  Integrator + Integration Verification
O  Parallel EU execution
P  Replan / amendment machinery
Q  Project-local knowledge retrieval
R  Legacy vault curation/migration tooling
S  Maintenance Mode
T  Break-glass recovery

Do not implement parallel EU execution until the single-EU path is reliable.

⸻

52. Stage Discipline

Each stage must produce:

* written plan
* explicit baseline
* implementation
* tests
* negative tests
* independent verification
* evidence
* result report
* known-good Git state

Every stage should be independently understandable by a fresh agent.

Do not depend on conversation history to reconstruct what happened.

⸻

53. Human Decisions

Human authority must be explicit.

Conceptual path:

Human decision
-> controller operation
-> validation
-> append-only event
-> state transition

Do not treat random edits to state files as valid human authorization.

⸻

54. Current Stage — DO ONLY THIS NOW

You have been supplied the complete destination so the work can be designed coherently.

However, your current authorized execution scope is ONLY:

1. Create canonical itdd-control-plane repository.

2. Initialize Git.

3. Import supplied thesis.

4. Create the permanent Markdown bootstrap/control specification from this handoff.

Store this document as:

docs/specs/CODEX-BOOTSTRAP-SPEC.md

and derive the stable architecture specification into:

docs/specs/CONTROL-PLANE-SPEC.md

Do not lose material from this handoff.

5. Create the README and public contribution foundation.

6. Commit/tag bootstrap baseline.

7. Create/push GitHub repo if authentication is available.

8. Perform Stage A Codex environment/contamination audit READ-ONLY.

9. Review Pocock’s relevant skills and create research analysis.

10. Produce proposed Stage B implementation plan.

Then STOP.

⸻

55. Required Human Review Report

At the stop point, report concisely:

ITDD repository absolute path:
GitHub repository:
created / blocked
Current main SHA:
Known-good tag:
Thesis files:
Specifications created:
Global Codex influences discovered:
Contamination risks:
Legacy knowledge locations:
Pocock recommendations:
Sensitive/private material handling:
Proposed Stage B scope:
Human decisions required:

Do not begin Stage B.

Do not modify existing Codex global state.

Do not migrate vaults.

Do not modify Prime.

Do not install Pocock’s entire skill collection.

Wait for explicit human approval.

⸻

56. End-State Definition

The eventual ITDD Control Plane should make this true:

A fresh agent can enter a project with no prior conversation history, reconstruct authoritative project state from durable project-local artifacts, receive only the context needed for its role, access exact resolved resources instead of wandering the filesystem, perform only explicitly authorized actions, produce independently verifiable evidence, and advance only through controller-authorized lifecycle transitions.

And:

Human intent remains durable authority while the execution plan may evolve through controlled, auditable replanning.

And:

Agent processes are disposable while project state is durable.

And:

The control plane can itself be safely maintained without giving ordinary project agents authority to bypass it.

And:

If the controller becomes defective, a human-only break-glass mechanism can recover the system.

And:

Telemetry provides the empirical basis for improving decomposition, context programming, testing, retrieval, and safe autonomy over time.

This repository is the permanent home of that work.

Begin with repository bootstrap and Stage A only.
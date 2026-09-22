# ITDD Control Plane

This context defines the language used for controller-owned runtime-role
execution and acceptance evidence.

## Runtime execution

**Frozen candidate**:
A controller-owned Git commit and tree that downstream roles must use exactly.
_Avoid_: mutable candidate, worker candidate, claimed candidate

**Execution assignment**:
A controller-created binding of an execution ID, role, candidate identity, and
allowed lifecycle transition, created before process launch.
_Avoid_: role claim, worker role, role metadata

**Acceptance evidence**:
Controller-preserved raw execution and observation records used to decide a
lifecycle transition.
_Avoid_: summary report, worker assertion, generated PASS

**Invalid PASS**:
A preserved historical PASS-shaped record that failed an independent trust-
boundary check and must not be promoted or rewritten.
_Avoid_: partial acceptance, accepted failure

## Candidate state

**Clean candidate**:
A frozen candidate checkout whose independently observed Git status contains no
tracked or untracked changes.
_Avoid_: unchanged candidate when only commit/tree were compared

**Fail closed**:
Rejecting a lifecycle transition whenever required identity, cleanliness,
assignment, or raw evidence is missing, ambiguous, or mismatched.
_Avoid_: best effort, trust the report

## Skill contract

**Clarification proposal**:
A versioned, provenance-bound proposal produced by a human-invoked skill to
resolve terminology, assumptions, source inputs, and open questions before
intent authority accepts it.
_Avoid_: approved intent, authority decision, lifecycle command

**Direct human workbench**:
Prime interaction in which the human directs research, planning, design,
documentation, and permitted systems work without granting Prime authority to
change project code.
_Avoid_: unrestricted agent mode, autonomous implementation

**Governed execution**:
ITDD-authorized work on project code or a candidate, using scoped execution
identities and controller-owned lifecycle and evidence.
_Avoid_: direct implementation, skill-owned authority

**Project policy**:
A project-owned declaration of its permitted workbench operations and proof
obligations; it cannot weaken Prime-wide restrictions or grant ITDD authority
by itself.
_Avoid_: inferred permission, skill allowlist

**Bootstrap lane**:
Explicit, auditable human-directed work used to establish or repair ITDD when
ordinary ITDD governance is unavailable; it does not claim normal governed
acceptance.
_Avoid_: bypass, untracked setup

**Skill source**:
The installed user-facing skill definition whose identity is recorded by the
repository contract; the repository contract defines the ITDD boundary and
acceptance evidence for using that skill.
_Avoid_: whichever copy is newest, implicit skill behavior

**Skill authority boundary**:
The rule that a skill may produce a clarification proposal but may not approve
intent, grant capability, create human authority, mutate approved intent,
advance lifecycle state, or promote a candidate.
_Avoid_: skill-owned authority, trusted worker decision

## Architectural program

**Architectural vision completion**:
All approved milestones in the full-vision proposal have independently passed their own governed BUILD → TEST → VERIFY cycle and dependency gates. It does not mean every optional capability is enabled by default.
_Avoid_: one giant execution, broad completion claim

**Promotion**:
A controller-owned fast-forward of an independently verified candidate into the canonical branch, with exact commit and tree attestation.
_Avoid_: worker merge, report approval, automatic publication

**Earned autonomy**:
A versioned project policy that explicitly enables bounded automation only after its required evidence gates pass. It is never inferred from successful runs.
_Avoid_: inferred trust, permanent autonomy

**First governed milestone**:
Milestone 0, establishing the controller-owned Prime-native RLM execution route described by issues #27/#28 before later integration, recovery, knowledge, or parallel-execution work.
_Avoid_: direct implementation, manual parent orchestration

**Raw session evidence**:
Complete retained runtime/session and telemetry records preserved for audit, replay, and later analysis. Raw session evidence is not an agent-facing QMD source.
_Avoid_: unrestricted retrieval context, curated lesson

**Curated QMD lesson**:
A provenance-linked best-practice or operational lesson derived by analyzing the complete retained telemetry/session dataset, then reviewed before agent-facing use. It is advisory and cannot grant authority.
_Avoid_: raw transcript, automatic policy

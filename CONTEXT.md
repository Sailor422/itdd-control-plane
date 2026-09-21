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

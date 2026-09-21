# ITDD Source-of-Truth Recovery Audit

LAST TRUSTED: E5 live two-axis independent verification and evidence binding / candidate `34f58b76c678e3f8091b803e4ef9ade018fb04fa`; accepted evidence commit `774c8601cafd1be19a006140df03d5049dbb0e37`; annotated tag object `62550767f2ac655072d508e5f66b6f1b491d1a76` (`stage-e5-live-verifiers-pass`)

FIRST UNTRUSTED: project-local executable `/skills` layer; the first unproven numbered lifecycle capability is clean single-EU end-to-end execution.

NEXT MILESTONE: Executable Skills Baseline v1 — recover and independently prove one project-local ITDD skill contract, without advancing the operational lifecycle.

Audit date: 2026-09-19. Scope: read-only forensic audit of `/Users/herbertfields/itdd-control-plane`.

## 1. Repository state

- Canonical repository: `/Users/herbertfields/itdd-control-plane`.
- Branch: `main`, ahead of `origin/main` by 23 commits.
- HEAD: `f37cc9700301771d1a5ced257efc33638408511c`.
- HEAD tag: `stage-e8-automated-pass`.
- Worktree: dirty. No files were cleaned, reset, rewritten, or staged by this audit.
- Relevant known-good tags: `bootstrap-0`, `stage-b-isolation-events-pass`, `stage-c-intent-graph-pass`, `stage-d-capability-authorization-pass`, `stage-e1-context-compiler-pass`, `stage-e2-scout-resolver-pass`, `stage-e3-project-map-pass`, `stage-e4-evidence-binding-pass`, `stage-e5-live-verifiers-pass`, `stage-e6-human-views-pass`, `stage-e7-integration-pass`, `stage-e8-automated-pass`.
- Uncommitted state includes the recovery plan, operational/I-1001 implementation and proof, human-decision/amendment work, E8 deletions/modifications, and unrelated local workspace files. The complete inventory is the output of `git status --short` at audit time; it is intentionally not reproduced as if it were a clean baseline.
- Test inventory: 95 explicit test functions are discoverable under `tests/`. The repository's current operational work has a larger parameterized/runtime count, but no test run was performed by this read-only audit.

The current HEAD is a documentation-preservation commit, not a clean accepted operational baseline. The E8 evidence itself says human acceptance was pending.

## 2. Primary sources examined

Source priority followed `ITDD-RECOVERY-PLAN.md`, section 18: original thesis, bootstrap/design specification, stable control-plane specification, Pocock research, accepted plans/reports/evidence, explicit architectural documents, implementation, and recaps only as navigation.

Examined repository sources:

- `itdd-first-design-idea.md`
- `thesis/ITDD-Control-Plane-Thesis.md`, plus the preserved DOCX/PDF artifacts
- `docs/specs/CODEX-BOOTSTRAP-SPEC.md`
- `docs/specs/CONTROL-PLANE-SPEC.md`
- `docs/research/pocock-skills-analysis.md`
- `docs/research/stage-a-codex-audit.md`
- `ROADMAP.md`, `CHANGELOG.md`, governance files, and `ITDD-RECOVERY-PLAN.md`
- `work/STAGE-*-IMPLEMENTATION-PLAN.md`
- `docs/research/STAGE-*-RESULT.md`
- `.idd/evidence/STAGE-*-INDEPENDENT-VERIFICATION.md` and the preserved E8 automated report at the tagged E8 commit
- `docs/architecture/*.md`, `control/`, `schemas/`, and `tests/`
- preserved I-1001 state under `work/proofs/operational-multi-eu-integration-recovery-proof/`

The original design requires each stage to have an exact baseline, implementation, positive and negative tests, independent verification, preserved evidence, and a known-good tag (`itdd-first-design-idea.md`, section 52; `ITDD-RECOVERY-PLAN.md`, sections 14 and 20).

## 3. Original capability chain and evidence matrix

Classification is deliberately conservative. A later component depending on an earlier capability is not counted as proof of that earlier capability. A tag is evidence of a frozen repository state, not proof beyond the scope recorded by its independent report.

| Capability | Original requirement/design | Implementation and tests | Independent evidence / Git identity | Classification and limits |
|---|---|---|---|---|
| Baseline / contamination audit | `itdd-first-design-idea.md` Stage A; `docs/research/stage-a-codex-audit.md` | Read-only audit record only | `9633c26` / `bootstrap-0`; `f26c15e` records the audit | `PROVEN` only as a recorded repository/environment audit; not proof of OS isolation or hostile-process resistance. |
| Clean project, Git, isolation | Bootstrap spec project-root and isolation model; Stage B plan | `control/authority/paths.py`, `control/events/`; Stage B unit/integration/negative tests | `.idd/evidence/STAGE-B-INDEPENDENT-VERIFICATION.md`; frozen `01a8f253...`, tag `stage-b-isolation-events-pass` | `PROVEN` for tested application-level path isolation and clean checkout; OS-level sandboxing remains explicitly unproven. |
| Durable state, append-only audit | Bootstrap spec durable event chain; Stage B plan | hash-linked JSONL and head commitment; tamper/deletion/reorder tests | Stage B evidence, frozen `01a8f253...`, tag `stage-b-isolation-events-pass` | `PROVEN` for ordinary divergence detection and replay; an OS user can rewrite all files. |
| Immutable intent / mutable graph | Thesis sections 5.2–5.3; Stage C plan | `control/models/intent.py`, `graph.py`, `store.py`; approval, mutation-negative, graph DAG/version/restart tests | Stage C evidence; `a19d08f...`, tag `stage-c-intent-graph-pass` | `PROVEN` within normal APIs and event replay; not filesystem immutability. |
| Roles and capability enforcement | Bootstrap spec authority separation; Stage D plan | `control/authorization/`; positive and negative authorization tests | Stage D evidence; `3c9088e...`, tag `stage-d-capability-authorization-pass` | `PROVEN` for explicit capability, scope, human-only, tamper, and restart checks; no OS-user containment. |
| Context Compiler / exact resolution | Thesis context model; E1 plan | `control/context/compiler.py`; packet/resource/request tests | E1 evidence; `a5fe51f...`, tag `stage-e1-context-compiler-pass` | `PROVEN` for compiler binding and bounded requests; no retrieval/orchestration. |
| Scout / Context Requests | E2 plan and `docs/architecture/context-resolver.md` | bounded `ScoutResolver`, durable resolutions, compiler revision, negatives | E2 evidence; `aacbda6...`, tag `stage-e2-scout-resolver-pass` | `PROVEN` for deterministic project-local search and honest outcomes; no semantic retrieval. |
| Project Map | E3 plan and `docs/architecture/project-map.md` | `control/project_map.py`; deterministic rebuild/hash and isolation tests | E3 evidence; `739e5af...`, tag `stage-e3-project-map-pass` | `PROVEN` as derived structural map; Python-only symbols and no semantic retrieval. |
| Human-facing views and genuine authority mechanism | Thesis human supervision model; E6 plan | `control/human.py`, decision mechanism and derived views; human gate tests | E6 evidence; `b2c9ee2` / tag `stage-e6-human-views-pass` | `DRIFTED`: the component gate/presentation behavior is independently evidenced, but routine EU/integration gates contradict the later intended autonomous authority model recorded in the recovery plan and operational architecture. |
| Independent Spec Verification | Thesis two-axis verification; E4/E5 plans | `control/verifier.py`; separate fresh subprocess executions and negative tests | E5 evidence; `34f58b7...`, tag `stage-e5-live-verifiers-pass` | `PROVEN` as a component capability, with the exact limitations in the E5 report. |
| Independent Standards Review | Same two-axis design | distinct standards role/capability/packet/contract in `control/verifier.py` | E5 evidence; `34f58b7...`, tag `stage-e5-live-verifiers-pass` | `PROVEN` as a component capability, not proof of a full lifecycle. |
| Evidence binding / false-pass rejection | E4 plan and `docs/architecture/verification-and-evidence.md` | immutable contracts/evidence evaluator; extensive false-pass negatives | E4 evidence; `03eb1a1...`, tag `stage-e4-evidence-binding-pass` | `PROVEN` for the tested contract/evidence model; changed candidate content was not yet VCS-attested at E4. |
| Single-EU end-to-end execution | Thesis clean-folder experiment; recovery plan Phase 5 | Later untagged `control/operational.py` and `tests/end_to_end/test_operational_single_eu.py` | No accepted clean-checkout independent report or tag; E5/E6 reports explicitly exclude orchestration; E7 is integration-focused | `UNPROVEN`. Current tests and later I-1001 state cannot substitute for a frozen clean single-EU acceptance proof. |
| Recovery / interruption / resume | Thesis durable recovery model; recovery plan Phase 6 | interruption/failure primitives exist in later modules and tests | No accepted clean single-EU recovery proof; E5/E7 only prove component interruption/failure states | `UNPROVEN` as an end-to-end capability. Component interruption records are not resume proof. |
| Integration | E7 plan and `docs/architecture/git-attested-integration.md` | `control/integration.py`; Git attestation, worktree, merge/conflict tests | E7 evidence; `bb232df...`, tag `stage-e7-integration-pass` | `PARTIALLY_PROVEN`: controller-owned integration candidate and conflict routing are proven; canonical promotion and complete lifecycle are explicitly out of scope. |
| Integration Verification | E7 plan; fresh Integration Verifier requirement | E7 uses distinct integration verifier through E4 evaluator | E7 evidence; `bb232df...`, tag `stage-e7-integration-pass` | `PARTIALLY_PROVEN`: happy-path launch/binding was accepted at E7, but integration-verifier fail-closed semantics for non-`TEST_COMMAND` kinds are unproven and contradicted by I-1001; no clean end-to-end recovery/promotion chain. |
| Parallel EU execution | Thesis and bootstrap rollout order prohibit it before reliable single-EU | I-1001 contains multi-EU operational artifacts, but no accepted parallel scheduler milestone | No accepted independent report; E7 explicitly defers parallelism; I-1001 was changed during execution | `UNPROVEN`. |
| Replan | Thesis graph evolution and recovery plan Phase 9 | graph revision primitives exist; no accepted replan workflow | Stage C proves graph revision only; no independent replan proof | `UNPROVEN`. |
| Intent Amendment | Thesis amendment boundary; recovery plan Phase 9 | later untagged `control/intent_amendments.py`, human decisions, reconciliation | I-1001 contains approved `IA-1001` and later reconciliation event, but no frozen independent milestone report | `PARTIALLY_PROVEN` as a later operational mechanism; not cleanly accepted as part of the original chain. |
| Project-local knowledge | Thesis project authority and recovery plan Phase 10 | no complete project-local knowledge/retrieval layer | E1–E3 reports explicitly defer retrieval/knowledge | `UNPROVEN`. |
| Maintenance mode | Thesis and stable spec section 8 | no accepted implementation or proof | Bootstrap/stable specs describe it as proposed/deferred | `UNPROVEN`. |
| Break-glass | Thesis recovery model and bootstrap spec sections 50–51 | no accepted `break-glass` implementation in the repository | Stable sources require a tiny human-only path; later evidence excludes it | `UNPROVEN`. |

The last genuinely trusted capability is therefore E5, not E7 or the later operational proof: E5 is the last accepted frozen stage whose report proves its exact capability with independent fresh-process verification and explicit limitations, before the roadmap enters lifecycle orchestration.

## 4. `/skills` recovery matrix

The answer to whether `/skills` was architectural or merely reference material is **architectural and intended to become executable/testable**, not merely reserved reference material. The bootstrap specification includes a top-level `skills/` tree (`docs/specs/CODEX-BOOTSTRAP-SPEC.md`, repository layout), the recovery plan calls its absence “a real architectural gap,” and `ITDD-RECOVERY-PLAN.md` requires a contract, tests, independent verification, and evidence for each implemented skill. The repository has no tracked or executable project-local skill files; the current dirty worktree contains an empty untracked `skills/` directory with no Git identity.

| Skill/concept | Research decision | Intended purpose / lifecycle role | Local implementation | Proof / finding |
|---|---|---|---|---|
| Grilling / `grill-with-docs` | `ADOPT` | Human-only intent clarification, terminology, assumptions, durable glossary/ADR before approval | None | `UNPROVEN`; missing implementation, not explicitly absorbed elsewhere. |
| Domain modeling | `ADOPT` with grilling | Resolve domain language and boundaries before durable intent | None | `UNPROVEN`; no project-local contract or independent proof. |
| `to-spec` | `ADAPT` | Convert settled intent into acceptance contract bound to immutable intent | Partial concepts in intent/evidence schemas; no skill | `UNPROVEN` as a skill; behavior is partially absorbed by Stage C/E4 by explicit research recommendation, but no explicit decision says the skill itself was replaced. |
| `to-tickets` | `ADAPT` | Tracer bullets, vertical EUs, blockers, graph proposals | Partial graph/EU models and later operational code | `UNPROVEN` as a skill; graph primitives are not proof of the researched workflow. |
| TDD | `ADOPT` | Behavior-first implementation and objective evidence | Tests exist; no skill | `UNPROVEN` as a project-local skill; tests are not a skill contract. |
| Code review / two-axis review | `ADAPT` | Independent Spec and Standards review with separate provenance | E4/E5 verifier roles | `PARTIALLY_PROVEN`: equivalent verifier behavior is independently proven at E5, but the project-local skill layer is absent. |
| Diagnosing bugs | `ADOPT` | Reproducible failure/repair/regression loop | Failure tests exist; no skill/recovery loop | `UNPROVEN`; no project-local skill or independent repair-loop proof. |
| Writing for agents | `ADOPT` | Lean precise role/context packets and capability descriptions | Context Compiler and packets implement related behavior | `PARTIALLY_PROVEN` as absorbed controller behavior; no explicit skill absorption decision or skill proof. |
| Wayfinder | `REFERENCE ONLY initially` | Decision maps for research-scale uncertainty | None | `PROVEN` only as a research classification; intentionally not implemented initially. |
| Human-only invocation | `ADOPT` | Genuine human authority boundaries for approval, maintenance, break-glass | Stage D/E6 human-only operations | `PARTIALLY_PROVEN`: authority enforcement exists, but the finished operational authority model drifted through routine gates and maintenance/break-glass remain absent. |
| Vertical slices / tracer bullets | Adopted design idea, not a separately classified upstream skill | Meaningful independently provable EUs and dependency-aware graph | Stage C graph and later operational EUs | `PARTIALLY_PROVEN`; component graph semantics exist, clean single-EU proof does not. |

The missing skills track is not harmless documentation debt. It blocks trustworthy continuation because the controlling recovery plan requires Phase 2 skills recovery before broad orchestration and requires each skill to carry forbidden actions, capability envelope, evidence, tests, and independent verification.

## 5. Original stage to later-stage mapping

| Original capability progression | Later implementation label | Audit result |
|---|---|---|
| Bootstrap / Stage A contamination audit | `bootstrap-0`, `docs/research/stage-a-codex-audit.md` | Accepted as a bounded audit; environmental risks remain. |
| Isolation + durable events | Stage B | Accepted and independently verified. |
| Intent + mutable graph | Stage C | Accepted and independently verified. |
| Roles + capabilities | Stage D | Accepted and independently verified. |
| Context compilation | E1 | Accepted and independently verified. |
| Scout / controlled resolution | E2 | Accepted and independently verified. |
| Project Map | E3 | Accepted and independently verified. |
| Evidence binding / false-pass resistance | E4 | Accepted and independently verified. |
| Independent Spec + Standards axes | E5 | Accepted and independently verified; last trusted capability. |
| Human views / authority surface | E6 | Component accepted, but routine human-gate semantics drift from the later intended model. |
| Git-attested integration | E7 | Component accepted; explicitly excludes promotion, recovery, parallelism, and replan. |
| Automated console | E8 | Automated verification only; human acceptance pending, and it is a console/projection milestone rather than the original clean operational chain. |
| Single-EU → recovery → integration → promotion | Later untagged operational work and I-1001 | Not a clean frozen continuation; implementation and authority semantics changed during the proof. |
| Parallelism, replan, knowledge, maintenance, break-glass | Not accepted | Still future/unproven. |

### First concrete roadmap divergence

The first concrete divergence from the recovered finished operational model is **after E5, when E6 human-view implementation turned lifecycle checkpoints into routine HUMAN_ONLY gates**. This is visible in the E6 plan/evidence (`VERIFIED_EU_REVIEW`, later integration gate assumptions) versus the recovered intended experience: normal lifecycle progress should be autonomous after human approval, and new human authority should be requested only for changed destination/requirements/constraints/authority (`ITDD-RECOVERY-PLAN.md`, sections 3, 9, 16, 20). This is not a divergence from the original bootstrap/thesis, which explicitly required initial human approval for verified EU work, material integration, and final promotion. The E6 component was not fabricated; its semantics were later recognized as architectural drift. E7 then built integration on that gate model and explicitly deferred promotion and recovery. The later operational proof repaired these semantics in place, which makes it useful forensic evidence but not a clean acceptance vehicle.

## 6. Human-authority evolution

The original bootstrap/thesis used human gates as a trust-building design: human approval of intent and, initially, selected graph/EU/integration/promotion checkpoints made the early system legible and conservative. The thesis explicitly calls early human approval a bottleneck by design and says the threshold for reducing gates must be learned empirically.

The later intended operational model is different but explicit: approval authorizes the controller to run the approved destination autonomously; a human decision is required for an actual authority change, maintenance, break-glass, or unresolved ambiguity. The recovery plan records this as the desired finished experience and identifies routine E6 gates as drift. `docs/architecture/operational-lifecycle.md` and later amendment work implement parts of that correction.

Therefore:

- Historical trust-building design: repeated gates were a valid early-control experiment.
- Finished operational model: repeated gates are not normal lifecycle authority when the approved intent already authorizes continuation.
- Explicit correction: Intent Amendment plus gate reconciliation and autonomous continuation.
- Accidental/unsupported drift: presenting the E6 routine-gate lifecycle as the finished architecture without proving the transition from early trust-building gates.

These are not interchangeable claims. E6 proves a human-gate mechanism; it does not prove the finished autonomous human experience.

## 7. I-1001 evidentiary status

I-1001 is preserved and valuable, but it is **not a clean end-to-end acceptance proof**. Valid evidence produced by the run includes:

- approved I-1001 intent and graph history;
- separate Builder executions, candidate commits, Git attestations, Spec/Standards results;
- preserved failure and recovery artifacts;
- exact integration candidate `294ac19a13d6b09bd33f132edc3efea1020d444c`, tree `904354bc804787b03b7e2fe003bd80f4f1aa08a5`, and preserved verifier artifact `VR-782653990`;
- obsolete gate `HG-14001`, historical decision `HD-007`, approved amendment `IA-1001`/`HD-008`, amendment-bound supersession, autonomous promotion, and fresh-process reconstruction.

Claims the run cannot support as an original clean proof:

- that the original control plane passed the whole chain without modification;
- that routine gate semantics were correct from the beginning;
- that the accepted E7/E8 tags prove a clean single-EU-to-promotion lifecycle;
- that multi-EU/parallel execution was enabled only after a separately accepted single-EU path;
- that the final promotion demonstrates a frozen-controller acceptance run.

The reason is direct: the control plane and authority model changed during the run. More specifically, `EV-782653990` records exit code 2, zero observed tests, and one failure; its verification contract used kind `INTEGRATION_TEST_COMMAND`, while `control/verification.py` only enforces `TEST_COMMAND`. Thus `VR-782653990` is a preserved false-pass artifact, not valid integration-verifier evidence. The I-1001 proof files are untracked dirty-worktree evidence with no accepted Git identity. The recovery plan explicitly says to preserve I-1001, not retroactively promote it into an acceptance proof. Its defects become regression requirements for future clean proofs.

## 8. Last trusted milestone

**E5 live Spec Verifier and Standards Reviewer orchestration / candidate `34f58b76c678e3f8091b803e4ef9ade018fb04fa`; accepted evidence commit `774c8601cafd1be19a006140df03d5049dbb0e37`; `stage-e5-live-verifiers-pass`.**

Evidence: `.idd/evidence/STAGE-E5-INDEPENDENT-VERIFICATION.md`; plan: `work/STAGE-E5-IMPLEMENTATION-PLAN.md`; architecture: `docs/architecture/live-verifiers.md`. The verifier used a fresh clean checkout, separate fresh subprocesses, separate roles/capabilities/context/contracts, E4 evidence evaluation, positive two-axis proof, failure/interruption negatives, and restart reconstruction. Limitation: it explicitly does not prove orchestration, integration, promotion, recovery loop, parallelism, maintenance, or break-glass.

## 9. First untrusted/incomplete milestone

The first numbered lifecycle milestone not actually proven is **clean single-EU end-to-end execution**. There is no accepted SHA/tag/report proving the original clean-folder chain from approved intent through planning, exact context, isolated Builder, independent verification, promotion, reconstruction, and forbidden/stale-transition negatives. Later operational tests are untagged and the I-1001 run was changed during execution.

Before that lifecycle proof can be trusted, the missing **project-local executable skills layer** must be recovered. That is the first architectural gap recorded by the controlling recovery plan and is the reason the next milestone is skills recovery rather than more orchestration.

## 10. Next required milestone — do not implement in this audit

### Executable Skills Baseline v1

Objective: implement and independently prove one narrow project-local ITDD skill contract, beginning with the highest-leverage `grill-with-docs`/domain-modeling flow, without launching or mutating an operational proof.

Baseline: current repository state must be frozen in a new, explicitly recorded clean checkout; this dirty HEAD is forensic input, not an accepted implementation baseline. The implementation must not modify I-1001 state or reuse its evidence as acceptance.

Required behavior:

- human-only invocation;
- explicit purpose, role, inputs, produced durable artifact, capability envelope, forbidden actions, deterministic/agent-reasoned boundary, and telemetry record;
- clarification output remains a proposal until the existing intent authority path accepts it;
- skill cannot approve intent, grant capability, advance lifecycle, alter `.idd` authority state outside its grant, or promote;
- fresh-process reconstruction of the produced artifact and its provenance.

Required positive tests:

- valid invocation by the authorized role creates the exact versioned clarification artifact;
- artifact binds project, execution, intent/draft context, capability, and source inputs;
- deterministic portions reproduce byte-identically;
- reconstruction from a fresh process yields the same artifact and event state.

Required negative tests:

- agent or unauthorized role invocation is rejected;
- missing/extra input, wrong project, wrong execution, stale baseline, path escape, capability expansion, and malformed output fail closed;
- skill cannot approve intent, create human authority, mutate approved intent, advance lifecycle, or promote;
- tampered artifact/event history is detected.

Required independent verification:

- fresh checkout at the candidate SHA;
- independent verifier with no builder reasoning;
- full focused positive/negative suite and schema checks;
- fresh-process reconstruction;
- exact diff inventory against the plan;
- preserved evidence and known-good tag.

Acceptance condition: the skill contract is independently verified, evidence is preserved, the candidate is tagged, and no lifecycle state or authority was advanced.

Failure condition: any authority escape, nondeterministic/missing provenance, missing negative proof, reconstruction mismatch, dirty/unfrozen acceptance run, or attempt to use a skill as lifecycle authority fails the milestone and remains preserved as evidence.

After this milestone, the next separate proof should be a clean single-EU lifecycle proof against a frozen controller, not a continuation of I-1001.

## 11. Unresolved contradictions and missing evidence

- E6/E7 accepted reports describe routine human gates, while the recovery plan and later operational architecture say normal lifecycle progress should not require them. This is an explicit historical evolution plus drift, not a contradiction to hide. The original bootstrap/thesis did authorize those gates during the initial trust-building phase.
- Dirty `README.md:32-37` overstates the unaccepted operational single-EU lifecycle; this is an unresolved contradiction in the current worktree, not accepted evidence at HEAD.
- `ROADMAP.md` still describes human views/live verifier orchestration as future work even though later tags and code exist; later tags therefore require source-to-capability mapping rather than blind roadmap trust.
- `stage-e8-automated-pass` says human acceptance is pending; it is not a final E8 acceptance tag.
- No tracked project-local `skills/` implementation, skill contract, skill-specific tests, independent verification, evidence, or tag exists; the current worktree's `skills/` directory is empty and untracked.
- No accepted clean single-EU end-to-end report exists.
- No accepted end-to-end interruption/resume proof exists.
- No accepted replan, project-local knowledge, maintenance, or break-glass proof exists.
- I-1001's later reconciliation/promotion events are preserved evidence, but no independent verifier report accepted them as a frozen milestone.

## 12. Independent challenge

An independent reviewer was requested after this report was created. The reviewer was given the primary sources, this report, and the proposed recovery point and was instructed to try to disprove the last-trusted/first-untrusted classifications, especially the skills conclusion, E6/E7 sequencing, routine human-gate interpretation, and I-1001 claims.

Final verdict: **PASS WITH CORRECTIONS**. The reviewer confirmed the core recovery point, but required correction of the E5 candidate/tag identity, qualification of E7 integration verification because I-1001 preserves a non-`TEST_COMMAND` false-pass, explicit identification of the empty untracked `skills/` directory, qualification of E6 as divergence from the recovered finished operational model rather than the original bootstrap/thesis, and inclusion of the dirty README contradiction. Those corrections are incorporated above.

## 13. Exact recommended next action

Do not modify the operational controller or I-1001. Freeze this forensic state, have the independent challenge review this report, then create a separate clean baseline for **Executable Skills Baseline v1**. Prove one skill contract with positive/negative tests, independent verification, evidence, and a tag. Only then begin the clean single-EU proof from the recovered baseline.

# Independent Review — ITDD #21 Preparation Contract

**Verdict: FAIL — not ready for handoff to `/itdd-execute`.**

Reviewer identity: fresh RLM execution `sub-6f0714d1` (model `openai-codex/gpt-6-luna`; session artifacts `/Users/herbertfields/.prime/agent/session-artifacts/01a0c9a1-c6cf-7659-a446-ada53a2f1aee/sub-6f0714d1`). Review was read-only. No tests, implementation, worktree creation, lifecycle changes, or promotion were performed. The contract remains unapproved.

## Reviewed artifact and integrity

- Exact artifact: `.idd/preparation/ticket-21-prepare-20260922T1952Z/11-revised-execution-contract.md`
- SHA-256 computed from the reviewed bytes: `f8def3c635ccf5f8f7bd234a05ebb56396ac6599ed5edccd52aca35f9a4eaca8` (matches requested hash).
- Reviewed preparation evidence: source manifest/correction, decomposition full/summary, routing research, draft provenance correction, and immutable issue snapshots. #21 snapshot records prior TEST failure and full-scope VERIFY FAIL/INCOMPLETE; #15 is the parent spec. No historical result is treated as a new pass.

## Blocking findings

1. **Manual parent orchestration bypasses the controller authority boundary.** Contract §Allowed operations directs the “controlling parent” to manually orchestrate the three RLM children and have parent/controller copy artifacts. This is not established as the repository’s controller workflow. `CONTEXT.md` defines execution assignment as a controller-created binding before process launch and acceptance evidence as controller-preserved raw records. `skills/itdd-execute/SKILL.md` states the controlling system retains lifecycle authority; `/idd/SKILL.md` directs the exact approved contract to `/itdd-execute`, whose workflow must preserve role provenance and acceptance evidence. Supplemental routing research (`10-evidence-routing-research.md`) explicitly found no generic executor, role-output capture/copy API, or generic run-root standard. The narrow `tools/itdd_execute.py --accept` harness is explicitly unrelated. Naming manual parent actions and a plausible `evidence/` path does not create controller assignments, establish authorized artifact custody, or make the workflow executable without bypass. This alone blocks readiness.

2. **Exact route is asserted, not operationally supported.** The contract says approved `/idd` routes to `/itdd-execute`, but provides no supported executor path to run that workflow for this ticket; explicitly excluding the only identified tool leaves no demonstrated mechanism. Repo `skills/idd/SKILL.md` requires that route and controller-only acceptance. Resolve by requiring a supported controller route/adapter and documenting its assignment, workspace, capture, custody, and lifecycle interfaces; otherwise contract must remain pending until that support exists. Do not treat a manual parent workflow as equivalent.

3. **The positive/hostile matrix is not fully executable as written.** Several probes say “each specified authorization/chronology boundary,” “exact rejection class/reason,” “applicable positive … tests,” or “specified … cases” without enumerating the concrete operation/fixture, exact expected class/reason, state/event files/bytes to snapshot, or exact parser/reducer/promotion boundary. The historical gap categories are mapped, but not every individual probe is a runnable assertion set. This conflicts with the requested concrete-field/readiness bar and the `itdd-execute` evidence rule that hostile probes reach their intended boundary. Minimal correction: enumerate per-case operation, setup/input, intended boundary, expected class/reason, exact authority/event artifacts, and pre/post equality assertion. Keep any unproven behavior explicitly execution-time unknown; do not claim it passed.

## Checks that did not reveal blockers

- Source identities and full baseline are explicit. Snapshot hashes in the contract match the preparation manifest and snapshot names; stale baseline metadata correction is disclosed in `05-source-snapshot-correction.md`.
- Exact BUILD allowlist is the two stated paths; exclusions and stop-on-scope-overrun are explicit.
- `pip install -e .` and plain `pytest -q` are documented in the decomposition as README-based setup/native suite; no shim is allowed and prior collection failures are disclosed as unresolved. No tests were run in this review. Do not claim the command or two-file sufficiency is proven.
- Actual overlapping Git merge, abort, absence of result commit/tree, and canonical HEAD/tree invariance are explicitly required; semantic interruption is expressly ruled out as substitute.
- Role separation, fresh identities, independent VERIFY, Standards/Spec diff-bound reviews, telemetry, and evidence hashing obligations are named. However, these obligations cannot cure the controller-custody blocker above.
- Contract says human approval is PENDING, and does not claim execution/test/implementation success. Final revised-draft identity is consistent with `12-draft-provenance-correction.md`; contract SHA matches that record.

## Smallest required corrections

1. Replace the manual parent orchestration/copy model with an identified, supported controller-authorized `/idd` → `/itdd-execute` route that creates role assignments/workspaces and captures/preserves role evidence; specify verifiable artifact custody and actual identity fields. If none exists, stop preparation as blocked on controller support rather than claiming a ready contract.
2. Make each positive and hostile case concrete at operation/input, enforcement boundary, expected result/reason, and exact state/event before/after assertions.
3. Recompute and record the revised contract hash after any authorized drafting changes; retain explicit human approval as pending until a human approves that exact hash.

**No repair was made.** Preparation evidence, historical TEST/VERIFY failures, and source artifacts were not modified. No approval, execution, or promotion is authorized by this review.

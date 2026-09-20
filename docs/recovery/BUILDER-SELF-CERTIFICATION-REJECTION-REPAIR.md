# Builder self-certification rejection repair

Status: `PASS`

## Root cause and false-proof gap

The prior E4/E5 checks proved that evidence fields matched a verification
contract and that an evidence record had the shape of a verifier record. They
did not prove that `created_by` was the durable execution identity of an
authorized independent verifier. `VerificationStore.record_evidence()` then
accepted a Builder-originated record and emitted it as verifier evidence.

The failed single-EU proof preserved this hostile reprobe and correctly stopped.
The historical E4/E5 PASS records remain unchanged; this repair supersedes
their broader self-certification confidence claim.

## Repair boundary

`VerificationStore.record_evidence()` now requires:

- a certification role (`SPEC_VERIFIER`, `STANDARDS_REVIEWER`, or
  `INTEGRATION_VERIFIER`);
- `created_by == execution_id`;
- a matching durable `verifier.execution.created` record binding execution,
  role, project, baseline, candidate, and contract.

Builder observations use `record_builder_evidence()` and are stored as
`builder.evidence.recorded` under `build-records`; they are not included in
verification reconstruction or acceptance eligibility.

## Traceability

- Changed implementation: `control/verification.py`
- Targeted tests: `tests/integration/test_builder_self_certification.py`
- Existing E4 fixture updated with durable verifier execution provenance:
  `tests/integration/test_stage_e4_verification.py`
- Hostile case: valid Builder execution → certification evidence →
  `VerificationStore.record_evidence()` → deterministic rejection.
- Exact rejection classes exercised: `DENY_BUILDER_CERTIFICATION`,
  `DENY_CERTIFICATION_PROVENANCE_MISMATCH`; the implementation also has an
  explicit `DENY_UNAUTHORIZED_VERIFIER_EXECUTION` branch for missing durable
  verifier provenance.

## Verification record

- Repair baseline: current canonical worktree baseline before this repair;
  prior failed single-EU proof artifacts remain preserved and untouched.
- Fresh independent verifier: a separate `PYTHONDONTWRITEBYTECODE=1 python3 -m
  pytest` process ran the focused adversarial and legitimate-path suites;
  `12 passed`.
- Targeted repair suite: `22 passed`.
- Full regression: `118 passed`.
- Restart/reconstruction: rejected Builder certification is absent from
  reconstructed verification evidence and cannot evaluate to acceptance;
  valid Spec/Standards evidence remains `VERIFIED` after a fresh orchestrator.
- Hostile reprobe: Builder execution with Builder-originated certification was
  rejected at `VerificationStore.record_evidence()` with
  `DENY_BUILDER_CERTIFICATION` or the durable provenance mismatch class before
  any evidence record or acceptance state was written.
- Quality gates: `git diff --check` PASS; Python compilation PASS.

## Known limitations

This repair protects the normal ITDD APIs and durable event provenance. It does
not claim resistance to a process that can rewrite the repository's event log,
materialized files, or Python runtime outside the control-plane trust boundary.
The original clean single-EU proof remains failed and is not converted by this
component repair.

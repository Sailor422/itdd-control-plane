# Ticket #16 VERIFY evidence (independent fresh execution)

## Verdict: FAIL

- Candidate: `dd66558f3bec01119f9d497c653b38997cbd7e37`
- Baseline: `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Role: VERIFY only; no repair, mutation, or promotion
- Fresh source: `git archive` extracted to `/tmp/ticket16-verify-archive`
- Probe process: `/usr/bin/python3 /tmp/verify16.py` with `PYTHONPATH` set to archive

## Identity and scope

Candidate worktree status was clean before and after verification. Exact diff against baseline:

```text
A evidence/ticket-16-build/BUILD.md
M skills/itdd_new/__init__.py
M skills/manifest.json
M skills/runtime.py
A tests/integration/test_workflow_runtime_registration.py
```

The candidate is the exact requested SHA. BUILD and TEST evidence and preserved failed attempts/diagnoses were reviewed. Issue #16 and accepted ticket-2 evidence were reviewed.

## Independent results

Clean archive targeted suites: **31 passed in 1.91s**.

The fresh hostile probe passed controller-only rejection cases, contract identity tamper through `discover()`, project/execution/root binding rejection, worker-role and extra-input rejection, and recorded unchanged-state checks for those reached cases.

The first material VERIFY failure was workflow registration tamper:

```text
workflow_skill_tamper: UNEXPECTED_PASS
registered_id_tamper: UNEXPECTED_PASS
```

Changing a registered workflow step's `skill` from `wayfinder` to another existing project-local skill (`tdd`) was accepted by `discover_workflow()`. Changing the manifest registered skill id to `itdd.other` was also accepted by `discover_workflow()`. These violate exact registration/contract identity and tamper rejection.

The probe then independently found a second failure before completion: source id `..` was accepted, and invocation wrote an artifact, instead of rejecting direct path traversal with unchanged state:

```text
dotdot_source: UNEXPECTED_PASS
AssertionError: dotdot_source
```

Probe source and raw output are preserved beside this file.

## Conclusion

**FAIL.** Per fail-fast VERIFY discipline, later hostile phases were not treated as acceptance evidence after the first material failure. Do not promote or accept this candidate. Candidate was not modified.

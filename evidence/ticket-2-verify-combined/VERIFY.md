# VERIFY Evidence — Issue #2 combined candidate

- Result: **VERIFY PASS**
- Candidate: `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Baseline: `db09daa966a14099ef18cba548b6f608cea5a18b` (resolved from `db09daa`; supplied 41-character value is invalid)
- Candidate worktree: `.worktrees/build-ticket-2-combined`
- Independent execution: this VERIFY process, distinct from BUILD and TEST
- Clean verification checkout: `/var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/ticket2-verify-dy020tho` (git-archive extraction, no candidate modifications)

## Identity and scope

Commands:

```text
git rev-parse HEAD  # in candidate worktree
ecf530dd2f8318c0cc258509bc8dbb5d86d697ee
git status --short  # in candidate worktree
(empty)
git diff --name-status db09daa..ecf530dd2f8318c0cc258509bc8dbb5d86d697ee
M	control/skills.py
M	skills/runtime.py
M	tests/integration/test_grill_with_docs_contract.py
A	work/proofs/ticket-2-build/BUILD.md
```

BUILD recorded candidate `f800458` in its body but the final candidate is the exact requested `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`; TEST recorded that same final candidate. BUILD and TEST evidence explicitly state VERIFY was not run. Prior failed attempts are preserved under `evidence/ticket-2-test*/` and were reviewed.

## Independent reproducible checks

From clean archive extraction `/var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/ticket2-verify-dy020tho`:

```text
PYTHONPATH=. pytest -q tests/integration/test_grill_with_docs_contract.py
.................                                                        [100%]
17 passed in 0.20s
```

Independent fresh-process probe (`verify_probe.py`, executed with `PYTHONPATH=.`) passed:

- direct valid proposal and child-process reconstruction;
- deterministic proposal identity;
- direct wrong project, wrong execution, stale baseline, and parent traversal rejection;
- unchanged artifact/event state after hostile direct requests;
- tampered proposal rejection;
- runtime valid non-authoritative proposal;
- runtime wrong project, wrong execution, and unauthorized role rejection;
- unchanged runtime state after hostile requests.

Probe result (raw output preserved in `probe-output.txt`):

```text
{"direct_root": "/var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/independent-direct-_viqnka4", "proposal_id": "CLAR-b06ee4313df3a31b88a4", "result": "PASS", "runtime_root": "/var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/independent-runtime-mtieuamq"}
```

The full probe source is retained at `evidence/ticket-2-verify-combined/verify_probe.py` and is not part of the candidate. Existing TEST raw evidence additionally covers absolute path escape, missing/extra inputs, capability expansion, forbidden authority actions, event-history tampering, runtime path/malformed/capability probes, and state snapshots; all recorded PASS.

## Boundary and exclusions review

Observed proposals remain `PROPOSED`/`PROPOSAL_ONLY` with `authority_effect`/`authority` set to `NONE`/`none`. No implementation exposes approval, lifecycle advancement, human-authority creation, intent mutation, or promotion. No acceptance evidence relies on installed manual skill use, I-1001, dirty state, or placeholder output. No out-of-scope lifecycle orchestration, single-EU acceptance, planner/evaluator/reviewer orchestration, candidate promotion, retrieval, maintenance, or break-glass behavior was added.

## Conclusion

**PASS.** Independent verification found no contract violation. Candidate is not modified or promoted by this VERIFY execution.

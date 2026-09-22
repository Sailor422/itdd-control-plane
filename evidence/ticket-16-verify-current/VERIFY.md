# Ticket #16 VERIFY evidence (independent fresh execution)

## Verdict: PASS

- Candidate: `495cebd8dd37f4573bb9905fabef3302590cd532`
- Baseline: `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Worktree: `/Users/herbertfields/itdd-control-plane/.worktrees/build-ticket-16-new`
- Role: VERIFY only. Candidate was not modified, repaired, or promoted.
- Fresh source: git archive extracted to `/var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/ticket16-verify-57k8vq_x/src`.
- Probe: `/usr/bin/python3 /var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/ticket16-probe-bl3ten99/verify.py /var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/ticket16-verify-57k8vq_x/src` with `PYTHONPATH=/var/folders/02/92fc_qyd2tg3mr_3wd9sfmfw0000gn/T/ticket16-verify-57k8vq_x/src`.

## Scope reviewed

Issue #16, accepted ticket #2 evidence, accepted ticket #6 evidence where present, latest BUILD evidence, TEST evidence under `evidence/ticket-16-test-current/`, and preserved failures/diagnoses including prior VERIFY failures were reviewed. The candidate worktree was clean before and after verification. Exact diff against baseline is preserved in `changed-paths.txt` and is the five-path allowlist: BUILD evidence, installer, manifest, runtime, and registration tests.

## Commands and results

- `git archive 495cebd8dd37f4573bb9905fabef3302590cd532` followed by clean extraction: PASS.
- Targeted clean-archive suites: **34 passed** (`targeted.txt`).
- Full clean-archive suite: **200 passed** (`full-suite.txt`).
- Fresh independent hostile probe: **PASS** (`probe-output.txt`, `verify_probe.py`).

The probe independently verified exact six-step mapping and controller/worker boundaries; exact manifest and contract identity/tamper rejection; controller-only acceptance with exact identity and no lifecycle/promotion effect; four-field project/execution/root binding; exact capability equality with missing and forbidden extras rejected; direct/runtime relative, absolute, lexical, and parent source traversal rejection with unchanged state; malformed registration rejection; forbidden worker role/lifecycle/promotion behavior; fresh subprocess reconstruction; clean constructor/use; accepted proposal-only behavior; and no mutation on every rejected request.

The valid invocation produced `PROPOSAL_ONLY`, `authority: none`, and no approval/promotion/lifecycle fields. Rejected requests left the project tree byte-identical. No placeholder output, self-certifying evidence, dirty candidate state, or dependency outside the clean archive was used.

## Conclusion

**PASS.** No contract violation was found. Candidate remains unmodified and unpromoted.

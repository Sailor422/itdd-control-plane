# Ticket #16 TEST evidence (fresh execution)

## Verdict: PASS

- Candidate: `495cebd8dd37f4573bb9905fabef3302590cd532`
- Baseline: `ecf530dd2f8318c0cc258509bc8dbb5d86d697ee`
- Worktree: `/Users/herbertfields/itdd-control-plane/.worktrees/build-ticket-16-new`
- TEST only; candidate was not modified. VERIFY was not run.

## Evidence

- Targeted accepted regression suite: `34 passed` (`targeted.txt`).
- Full suite: `200 passed` (`full-suite.txt`).
- Hostile/positive probe: `probe.py`, `probe-output.txt`; all required phases passed, including six-step workflow mapping, identity/tamper, registration shape, controller-only acceptance, project/execution/root binding, exact capability set, lifecycle/worker/input/source rejection, unchanged state, fresh process, and clean proposal invocation.
- Direct controller relative/absolute source path rejection with unchanged state: `supplemental.py`, `supplemental-output.txt`.
- Exact changed-path diff: `changed-paths.txt`; five paths exactly match BUILD declaration plus BUILD evidence itself.
- Candidate status: `candidate-status.txt` (clean).

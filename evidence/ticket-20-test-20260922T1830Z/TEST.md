# Ticket #20 Independent TEST Evidence

- Role: TEST only; candidate was not modified and VERIFY was not run.
- Baseline: `47dbc8afab979d6836b193f23cfa287d3a206533`
- Candidate tested: `bc2b53b6b989cac8ad9ad5948385fe2a65799669`
- Fresh detached test worktree: `/tmp/itdd-ticket-20-test-bc2b53b`

## Results

- Targeted maintenance suite: **PASS**, 5 passed. Raw: `targeted.log`; exit: `targeted.exit`.
- Additional hostile/scope checks: **PASS**, 8 passed. Covers human-only freeze, snapshot/repair, exact repair `git rev-parse HEAD`, proof-gated no-bypass freeze, malformed/nonhex/uppercase/wrong-length/valid-wrong SHA, missing/deleted/replaced/non-Git repair environments with unchanged event/state, and fresh-process reconstruction/preservation. Raw: `scope-corrected.log`; exit: `scope-corrected.exit`.
- Full suite: **PASS**, 214 passed in 25.24s. Raw: `full.log`; exit: `full.exit`.

Existing targeted tests also cover break-glass nonce/reason/approval/proof/activation and replay, agent rejection, and replay event immutability.

An initial ad-hoc scope run had one fixture setup error (parent directory not created), recorded in `scope.log`; the corrected run passed 8/8.

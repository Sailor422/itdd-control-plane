# Ticket 21 TEST Evidence — FAIL

- Role: TEST, fresh execution distinct from BUILD; this report is not VERIFY.
- Candidate: `330e106bcb13eeeb6d7efa42cf941d37f6ee30ec`
- Candidate tree: `4c3ee4718976d73e1227cd4f1c672993b9b50c1c`
- Baseline: `bc2b53b6b989cac8ad9ad5948385fe2a65799669`
- Build integration/evidence commit: `9a3431fbe437bfffb837cbea4f8d0ba8bda42ce4`
- Worktree: `/private/tmp/ticket-21-build`
- Exact candidate HEAD checked out: `9a3431fbe437bfffb837cbea4f8d0ba8bda42ce4`; worktree was clean before tests. Candidate paths are unchanged. The only test-generated `uv.lock` was removed.
- Context: GitHub #21; parent spec #15; map #8; BUILD.md and both independent review records read.

## Executions

1. `uv run pytest -q` — failed collection with 16 import errors (`tests` package unavailable; one `tools` import unavailable). This is the documented plain-pytest baseline collection issue, not accepted as a green test.
2. `PYTHONPATH=. .venv/bin/python -c "import sys,types,pathlib,pytest; m=types.ModuleType('tests'); m.__path__=[str(pathlib.Path('tests').resolve())]; sys.modules['tests']=m; sys.exit(pytest.main(['-q','tests/integration/test_stage_e7_integration.py']))"` — PASS, 4 passed (7.65s).
3. Same import shim with `pytest.main(['-q'])` — PASS, 214 passed (24.26s).
4. `git diff --check` — PASS. `git status --short` after cleanup — clean.

The E7 suite exercises disposable `tmp_path` Git promotion, fresh verifier results, git-attested candidate commit/tree, restart reconstruction via IntegrationStore, human gate and controller attribution, conflict/semantic/interruption routing, and hostile chronology, malformed recognized payloads, timestamp inversion, identity tampering, operational discriminator, terminal promotion, stale evidence, and event-chain alteration.

## FAIL basis / unmet explicit test contract

The candidate test suite does not assert authoritative state and durable event history are byte-for-byte unchanged after each rejected operation. The hostile reconstruction probes inject modified in-memory event lists; they do not establish persistent state/event non-mutation. Also the candidate test's conflict case is semantic `REPLAN_REQUIRED` and interruption; it does not execute a real Git mechanical merge conflict and assert durable conflict routing. These are explicit requested end-to-end acceptance probes. Therefore TEST is FAIL; no repairs, promotion, issue close, or VERIFY were performed. This is a coverage/acceptance failure, not a claim that the implementation necessarily violates those properties.

## Scope / preservation

Only `control/integration.py` and `tests/integration/test_stage_e7_integration.py` differ between baseline and candidate. No candidate files changed. Existing accepted evidence and historical failures were not edited. Promotion was only exercised by the existing test inside disposable pytest temporary repositories; no project promotion was attempted.

# ITDD Execute Evidence Contract

Use this checklist when recording or reviewing one BUILD → TEST → VERIFY cycle.

## BUILD
- Bounded source spec/ticket/milestone
- Baseline SHA/tag
- Fresh Codex execution identity/provenance
- Authorized scope/paths
- Actual changed paths
- Candidate/output identity
- Builder-scoped evidence only

## TEST
- Fresh Codex execution distinct from BUILD
- Exact candidate under test
- Positive commands actually executed
- Negative/hostile operations actually attempted
- Intended enforcement boundary reached
- Exact rejection class/reason captured
- No illegal state advancement
- Evidence bound to exact baseline/candidate/execution

## VERIFY
- Fresh Codex execution distinct from BUILD and TEST
- Reproduce critical claims independently
- Challenge BUILD and TEST evidence
- Check for placeholders, callbacks, fixtures, stale evidence, wrong candidate/baseline, role spoofing, self-certification, and dirty/untrusted state
- Verify any required reconstruction from a fresh process
- Verdict: PASS or FAIL

## Acceptance
Do not create an accepted tag or promotion from Builder or Tester claims alone. Acceptance requires independent VERIFY PASS plus any deterministic controller checks required by the project.

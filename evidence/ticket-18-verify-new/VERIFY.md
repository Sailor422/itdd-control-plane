# Ticket 18 VERIFY evidence — PASS

- Issue: #18; parent spec: #15
- Candidate: `95b8cc06108383fa1dc1f77004fc81a7bd1bd02b`
- Exact accepted baseline: `ticket-17-lifecycle-pass/85a0b2142d4b61bc62ed1a4ba1729e649d4ed846`
- Fresh verification archive: `/tmp/ticket-18-verify-new/candidate-archive`
- Fresh Git checkout: `/tmp/ticket-18-verify-new/candidate-git`
- Prior failed candidate/diagnosis and BUILD/TEST evidence were read; neither was modified.

## Independent commands and results

All commands ran in fresh processes with `PYTHONPATH` set only to the fresh checkout.

```text
python3 -m pytest -q tests/integration/test_operational_builder_boundary.py tests/end_to_end/test_operational_single_eu.py tests/integration/test_prime_builder_adapter.py
12 passed in 4.57s

python3 -m pytest -q
203 passed in 23.40s

git rev-parse HEAD
95b8cc06108383fa1dc1f77004fc81a7bd1bd02b

git status --porcelain=v1 --untracked-files=all
(empty)

git diff --exit-code
(exit 0)

git diff --check 85a0b2142d4b61bc62ed1a4ba1729e649d4ed846 95b8cc06108383fa1dc1f77004fc81a7bd1bd02b
(exit 0)
```

A separate positive fresh-project run produced `VERIFIED`, a controller `candidate.git.attested` event and attestation ID, `observed_changed_paths=["src/feature.py"]`, separate SPEC and STANDARDS verifier executions, and no remaining disposable worktree. Output is in `/tmp/ticket-18-verify-new/positive.txt`.

## Coverage reviewed

The targeted hostile seam tests cover the forbidden canonical `project_root` argument, external disposable worktree, canonical HEAD/tree/status and `.idd` guard, symlink/path escape, unrelated paths, direct commits, interrupted/failing workers, missing provenance, cleanup, quarantine, single `eu.build_failed`, absence of `worker.execution.completed`/`eu.built`, and absence of candidate SHA on failure. Prime adapter tests cover fresh bounded no-session/no-context/no-skills/no-extensions/no-prompt-templates/no-themes launch, provenance binding, and fail-closed timeout/process failure.

The full suite independently exercises lifecycle generations, authorization, event integrity/reconstruction, stale capability handling, worker isolation, evidence binding, exact scope, verifier separation, and self-certification rejection.

Candidate changed-paths are exactly the expected five files; no candidate, BUILD evidence, TEST evidence, or accepted evidence was altered by this VERIFY run. VERIFY did not modify, repair, or promote the candidate.

**Result: PASS.**

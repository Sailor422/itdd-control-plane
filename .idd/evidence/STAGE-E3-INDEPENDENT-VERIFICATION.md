# Stage E3 independent verification

- Stage: E3 Project Map v1 and bounded structural indexing
- Baseline: `a3b1fa1e19dcf7155c3f51d2653e689382b0d7e1`
- Candidate implementation: `739e5af9e075a3a580d134199aa9bc613c481725`
- Verifier execution: `stage-e3-verifier-20260919T194500Z-clean-checkout`
- Verification checkout: fresh clone of the candidate, with no local modifications

## Commands and results

1. `python3 -m pytest -q tests` — PASS, `56 passed in 0.48s`.
2. JSON parsing of `schemas/project-map.schema.json` and `schemas/context-resolution.schema.json` — PASS.
3. Two separate fresh Python processes built the same fixture map for the same baseline, state, timestamp, and generator — PASS; hashes compared byte-for-byte with `cmp`.
4. `git status --short --branch` in the verifier checkout — clean.

## Acceptance evidence

- Project Map artifact contains the required identity, baseline, generator, file, symbol, relationship, intent, graph, test, and hash fields.
- File indexing is sorted and project-local; `.git`, nested repositories, caches/build output, private directories, symlinks, external legacy paths, and `.idd/project_map` are excluded.
- Python classes/functions and imports are extracted deterministically; unsupported or invalid Python is not assigned invented symbols.
- Stage C durable requirement-to-EU bindings and graph dependency bindings are copied as separate map collections; source imports do not create graph dependencies.
- Baseline mismatch returns `STALE_MAP`; modified map content returns hash mismatch; malformed relationships and duplicate file identities fail validation.
- Scout exact symbol lookup uses `PROJECT_MAP` with zero search files examined; a valid map is optional and E2 deterministic search remains the fallback.
- Map-derived findings remain read-only context candidates and are accepted only through the existing Context Compiler/capability gate; the map does not grant worker authority.
- Existing Stage B through E2 regressions remain green.

## Limitations

Stage E3 supports deterministic Python symbol/import extraction only; other languages are indexed as files without fabricated symbols. Test-to-code relationships remain `UNKNOWN` unless deterministic metadata exists. Full rebuild is the correctness path; incremental indexing is documented as future work. Semantic retrieval, orchestration, Obsidian, parallelism, and later stages were not implemented.

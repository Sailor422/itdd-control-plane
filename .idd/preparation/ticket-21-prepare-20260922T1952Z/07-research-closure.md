# Supplemental RESEARCH fact closure

Execution identity: fresh sub-agent `itdd21-research-closure`, RLM child id `sub-2e1b312a`; session artifacts `/Users/herbertfields/.prime/agent/session-artifacts/01a0c9a1-c6cf-7659-a446-ada53a2f1aee/sub-2e1b312a`. Read-only; no test execution or edits. Baseline for repository facts: `80284553d571d5d92e2a8f66b7b8c312f9c283ef`.

- README documents `pip install -e .` under Installation, then `pytest -q` (full suite); also integration/E2E subsets. `pyproject.toml` configures pytest; `pytest.ini` excludes `.git`, `.idd`, caches, and `work`. No `.github/workflows`, CI test entrypoint, or typechecker/typecheck command exists. Historic `uv run pytest -q` collection errors occurred; shimmed runs do not count. Contract should use documented editable installation followed by plain `pytest -q`, without `sys.modules` or other import shim.
- Historical #21 candidate evidence (`9a3431f`, from parent baseline `bc2b53b...`) identifies exactly two product/test implementation paths: `control/integration.py` and `tests/integration/test_stage_e7_integration.py`. Those paths are pre-existing at selected baseline; they form proposed strict allowlist. Existing integration store/controller handles reconstruction, materialization, run/verify/promote; named test file is E7 integration seam. No extra implementation/test path identified. Do not use the historical baseline/candidate as the selected execution baseline; it is evidence only.
- `/idd` is the top-level router and authority entry; it routes an approved contract to `/itdd-execute`, which launches distinct BUILD/TEST/VERIFY executions. `/implement` is an implementation helper within BUILD only, restricted by the contract.
- No typecheck should be invented.
- The selected baseline SHA and historical candidate parent `bc2b53...` are not related by ancestry; do not reuse candidate.

Sources examined: baseline README, pyproject.toml, pytest.ini, tests/README.md, tools/README.md, skills/idd/SKILL.md, skills/itdd-execute/SKILL.md, skills/implement/SKILL.md, skills/manifest.json, integration docs/ADRs, historical BUILD/TEST/VERIFY artifacts and diffs.

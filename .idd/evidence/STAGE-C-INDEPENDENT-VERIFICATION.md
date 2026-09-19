# Stage C Independent Verification

Status: PASS  
Verification execution ID: `stage-c-verifier-20260919T185532Z-clean-checkout`  
Baseline SHA: `4e69db26b0d9c7b54035f5bb3dbfc7a372cf0fae`  
Plan SHA: `d7dd6445a4624ea3328aecdd310e9d6186db1546`  
Frozen candidate SHA: `a19d08f7a7d0c914f113c2c7725495cdd05e8962`

## Role separation

The verifier used a fresh local checkout and fresh Python processes. Builder reasoning was not used as acceptance authority.

## Required test command

```text
PYTHONPATH=. python3 -m pytest -q tests
```

Result: exit `0`; `30 passed`; `0 failed`.

## Independent checks

- Clean checkout at the frozen candidate: PASS.
- No untracked or local modifications in the verifier checkout: PASS.
- Diff from Stage B final to candidate matched the Stage C plan inventory exactly: PASS.
- `schemas/intent.schema.json` and `schemas/graph.schema.json` parse: PASS.
- Draft intent creation and stable requirement IDs: PASS.
- Human approval event and approved status: PASS.
- Agent-originated approval rejection: PASS.
- Approved intent mutation rejection: PASS.
- Graph binding to exact intent ID/version: PASS.
- Nonexistent requirement, duplicate EU, missing edge target, self-dependency, and cycle rejection: PASS.
- Graph v1 preservation after graph v2 revision: PASS.
- Active graph reconstruction selects v2 while retaining v1: PASS.
- Fresh-process reconstruction of approved intent and graph history: PASS.
- Event-chain verification: PASS.
- Materialized-artifact tampering detection: PASS.

## Required proof scenario

The verifier created draft `I-001 v1`, approved it as a human, created `G-001 v1`, revised to `G-001 v2` with changed dependencies, and confirmed that intent v1 remained unchanged while graph v1 remained present and graph v2 became active after replay.

## Evidence interpretation

Stage C proves immutability through normal ITDD APIs and detects ordinary materialized-artifact divergence through event replay. It does not provide OS-level immutability against a user or malicious process with filesystem permissions.


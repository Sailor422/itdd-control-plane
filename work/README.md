# Work Directory

This directory contains development artifacts, experimental proofs, and temporary files.

## Preserved Evidence

- `proofs/prime-single-eu-20260921T034058Z-clean4/` - **The clean single-EU Prime proof** (PASS)

This proof demonstrates:
- Real prime-agent binary execution via PrimeBuilderAdapter
- Controller-owned candidate commit
- Independent verification (spec + standards)
- Clean worktree (no contamination)
- Immutable evidence preservation

**Evidence files:**
- `PASS.md` - All checks passed
- `candidate-identity.json` - Controller-owned commit
- `controller-result.json` - Status: VERIFIED
- `independent-verification.json` - All probes exit 0
- `runtime-provenance.json` - Prime CLI with SHA-256 hashes
- `final-status.txt` - Clean candidate (empty git status)

All other proofs in this directory are development artifacts and are gitignored.

## Structure

- `proofs/` - Immutable evidence from lifecycle executions
- `CODEX-*` - Legacy remediation plans (historical)

For documentation, see `docs/`.

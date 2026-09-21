# Accepted Evidence

This directory contains canonical, immutable evidence artifacts that are **committed to the repository**.

## Purpose

Unlike the working proof artifacts in `work/proofs/` (which are gitignored and may be large or numerous), this directory contains only the essential evidence files for **accepted milestones**.

## Current Accepted Proofs

### prime-single-eu-v1/

**Date:** 2026-09-21  
**Milestone:** Clean single-EU Prime execution proof  
**Status:** ✅ PASS

**Evidence files:**
- `PASS.md` - All verification checks passed
- `candidate-identity.json` - Controller-owned commit identity
- `controller-result.json` - Execution status: VERIFIED
- `independent-verification.json` - Spec + standards checks (exit 0)
- `runtime-provenance.json` - Prime CLI invocation with SHA-256 hashes
- `candidate-identity.json` - Deterministic proposal identity
- `events.json` - Complete event log
- `reconstructed.json` - Reconstructed state from events
- `final-status.txt` - Clean worktree (empty git status)

**What this proves:**
- Real `prime-agent` binary execution via `PrimeBuilderAdapter`
- Controller-owned candidate commit (not agent-authored)
- Independent verification (fresh spec + standards checks)
- Clean worktree (no contamination)
- Deterministic proposal identity (separate from event identity)

## Adding New Evidence

To add a new accepted proof:

1. Create a subdirectory: `evidence/accepted/<milestone-name>/`
2. Include only essential evidence files (keep under 100KB total if possible)
3. Update this README with the new proof
4. Commit to the repository

**Do NOT include:**
- Raw JSON dumps over 100KB
- Temporary files
- Intermediate artifacts
- Full event logs (use reconstructed summaries instead)

## Relationship to work/proofs/

- `work/proofs/` - Working artifacts, gitignored, may be large, development-only
- `evidence/accepted/` - Canonical proofs, committed, sanitized, public-facing

When a proof is "accepted" (passes independent verification and is approved for inclusion), copy only the essential files here.

---

**See also:**
- [Verification Architecture](../../docs/architecture/verification-and-evidence.md)
- [Single-EU Proof Details](../../work/README.md)

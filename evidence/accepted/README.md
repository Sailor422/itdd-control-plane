# Historical Milestone Evidence

> These records describe a specific historical candidate and milestone. Their PASS/accepted status is not a product release, production-readiness claim, or claim that the product is currently in use. The repository is in development and unreleased.


This directory contains committed evidence artifacts for named historical milestones. Review each artifact’s provenance and scope before relying on it.

## Purpose

This directory stores selected evidence files for historical milestones. Its presence does not certify that the artifacts are complete, independently re-verified, or free of machine-specific data. Review each source before relying on or republishing it.

## Historical Milestone Records

### `prime-single-eu-v1/` (historical candidate)

**Date:** 2026-09-21  
**Milestone:** Single-EU Prime execution experiment
**Status:** ✅ PASS

**Evidence files:**
- `PASS.md` - Historical report recording a PASS result
- `candidate-identity.json` - Candidate identity recorded in the historical artifacts
- `controller-result.json` - Historical report of execution status: VERIFIED
- `independent-verification.json` - Historical spec/standards check report
- `runtime-provenance.json` - Historical invocation and hash record
- `events.json` - Historical event record
- `reconstructed.json` - Reconstructed state from events
- `final-status.txt` - Historical final-status output

The artifact files contain the detailed historical claims and results. This index does not independently re-run or verify those checks. Treat them as candidate-specific research evidence, not proof of release, production readiness, or current product behavior.

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
- `evidence/accepted/` - Historical candidate evidence committed to this repository; not a product-release status or a guarantee that every artifact is free of machine-specific data

When a specific candidate is accepted for evidence storage, copy only the essential files here after scope and public-safety review. This does not mean the product has been released.

---

**See also:**
- [Verification Architecture](../../docs/architecture/verification-and-evidence.md)
- [Single-EU Proof Details](../../work/README.md)

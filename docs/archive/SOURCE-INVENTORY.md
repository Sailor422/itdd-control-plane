# Archive source inventory

**Collected:** 2026-09-24, before onboarding/archive edits
**Repository visibility:** Public
**Purpose:** First-pass source map before changing onboarding material. This inventory is not a release statement, proof of current behavior, or approval of every source for publication.

## Preservation boundary

The checkout contained pre-existing edits and untracked or ignored artifacts, including runtime records and worktrees. They are outside this documentation change. Preserve them; do not clean, rewrite, or bulk-move them as part of archive work. This inventory deliberately omits local checkout identifiers, machine paths, and artifact counts because they are not needed by contributors.

## Onboarding sources assessed

- `README.md` — described the project as a work in progress but mixed planning with later-stage setup and broad implementation/evidence claims. It was revised to reflect the current unreleased planning-first direction.
- `docs/GETTING-STARTED.md` — the former guide presented initialization and execution as the default path. It was superseded by the active planning-first guide; the former guide is preserved in the archive as historical material.
- `docs/agents/itdd-in-prime-usage.md` — kept active as the Prime planning guide; legacy execution walkthroughs and controller examples were moved out of active onboarding.
- `docs/agents/itdd-preparation-execution-handoff.md` — historical execution-era guidance, preserved under `docs/archive/guides/`.
- `RELEASE-NOTES.md`, `docs/THESIS.md`, `skills/itdd-new/`, and tests also contained onboarding or maturity references and were reviewed for consistency.

## Research and engineering-history sources

- `docs/research/` contains research notes on Pocock skills, staged execution experiments, and Prime Agent lifecycle investigations. These are historical research, not current product policy.
- `docs/reports/` contains forensic work reports. They include private session context and local references; they are not included in the public contributor archive.
- `docs/specs/` includes draft material. Drafts must remain labeled as drafts unless separately approved.
- `docs/architecture/` and `docs/adr/` describe broader control-plane design. Distinguish that research/later-stage work from the current planning workflow.
- `evidence/` mixes historical acceptance records with logs and scripts. Keep evidence distinct from contributor narrative. Historical verdicts do not establish product release or production use. Review any raw evidence individually before public reuse.
- `.idd/` contains authority, audit, telemetry, workspace, and raw execution records. It is not a bulk-public-archive source. Preserve it in place unless separately reviewed and explicitly selected.
- Some untracked root documents are upstream copies or raw terminal/session notes. Preserve them in place; do not duplicate upstream material or publish raw session notes without provenance and privacy review.

## Public-safety and provenance checks

The initial text scan found machine-specific paths, email-like strings, and token-like patterns in tracked and untracked source material. These are heuristic flags, not confirmed credentials; their values are intentionally not reproduced here, and this inventory does not certify the source set as sanitized. Some records also contain private session metadata. Do not copy raw sources into the contributor archive without individual review and redaction. No raw evidence or runtime record was rewritten as part of the onboarding work, and Git history was not rewritten. The repository is public, so any later committed archive content will be public.

## First-pass disposition

1. Collect and index sources before changing the onboarding path.
2. Preserve original research, decisions, drafts, and evidence with provenance and a clear historical/current status.
3. Archive superseded onboarding guides and move legacy controller examples out of active onboarding.
4. Curate contributor-facing research and engineering reports only after source, status, path, and public-safety review.
5. Exclude bulk runtime data, worktrees, private/audit material, and scratch output from the public archive unless individually reviewed and selected.
6. Do not discard or rewrite prior failures or accepted evidence; describe their scope accurately.

This is a first-pass catalog, not an exhaustive audit. It does not claim that every historical artifact has been read or cleared for public release.

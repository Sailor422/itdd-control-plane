# Research and engineering notes catalog

This catalog helps contributors find the project’s research without treating historical records as current requirements or release evidence. It records source status and safe takeaways; it is not a complete activity log or independent re-verification. Collect source data before proposing follow-up work.

## Curated research records

### Skills and development practices

- [Pocock skills analysis](../research/pocock-skills-analysis.md) reviews public upstream documentation as of its stated date. It recommends clarification, vertical slices, test-first loops, independent review, and concise agent-facing writing. These are recommendations, not authority or current project policy; check upstream sources before reuse.
- [Stage A environment audit](../research/stage-a-codex-audit.md) is a sanitized summary of a read-only review on one host. It identifies categories of global-context and legacy-store risk; it is not a system-wide security audit.

### Controller experiments

The following notes summarize local research milestones. Their labels and results apply to the named historical work only. The summaries do not establish current product status or independently prove reproducibility.

| Source note | Reported research focus | Status caveat |
|---|---|---|
| [Stage B plan](../research/STAGE-B-PLAN.md), [result](../research/STAGE-B-RESULT.md) | Project isolation and append-only, hash-linked event records | Plan is a proposal; result records a historical local verification claim. |
| [Stage C result](../research/STAGE-C-RESULT.md) | Separate approved intent from versioned execution strategy | Historical result summary; not current product acceptance. |
| [Stage D result](../research/STAGE-D-RESULT.md) | Role definitions, capability authorization, and restart reconstruction | Historical local result; not a security guarantee. |
| [Stage E1 result](../research/STAGE-E1-RESULT.md) | Bounded, provenance-bearing context packets and requests | Historical result summary. |
| [Stage E2 result](../research/STAGE-E2-RESULT.md) | Bounded project-local search and structured resolution outcomes | Historical result summary. |
| [Stage E3 result](../research/STAGE-E3-RESULT.md) | Rebuildable, baseline-bound project map | Descriptive derived state, not lifecycle authority. |
| [Stage E4 result](../research/STAGE-E4-RESULT.md) | Execution-bound verification contracts and evidence evaluation | Historical result summary; not current product acceptance. |
| [Stage E5 result](../research/STAGE-E5-RESULT.md) | Separate Spec and Standards verifier executions | Historical result summary; not proof of present-day behavior. |

These notes point to more detailed project-local evidence records. Those records are not reproduced here; inspect their own provenance and scope, and do not interpret them as evidence of a release or production use.

## Research not copied into this catalog

- Prime Agent lifecycle research is version-specific. The local source notes report that documentation identifies a pre-compaction extension seam, but do not establish post-compaction timing guarantees. They also distinguish session usage signals from the size of serialized context. Host configuration observations are local, not API guarantees; the raw notes are not included here.
- Detailed operational forensic reports contain private session context and granular local evidence. Their high-level lessons are summarized in [curated engineering history](ENGINEERING-HISTORY.md); the reports themselves are not copied here.
- The [context-budget and session-handoff discussion](../specs/CONTEXT-BUDGET-AND-SESSION-HANDOFF-DISCUSSION-DRAFT.md) is a planning draft, not an approved design or implementation commitment.
- The [control-plane specification](../specs/CONTROL-PLANE-SPEC.md) and [executable-skills baseline](../specs/EXECUTABLE-SKILLS-BASELINE-V1.md) are design proposals, not proof of implementation. The [Codex bootstrap summary](../specs/CODEX-BOOTSTRAP-SPEC.md) is historical and sanitized.
- Raw execution and acceptance artifacts are not copied into this catalog. The [evidence index](../../evidence/accepted/README.md) describes their historical scope; supporting artifacts require their own provenance and public-safety review. A scoped review found machine-specific environment metadata in some existing candidate JSONs, so the index must not be read as a sanitization or reproducibility claim.

## Public-history limitation

Some earlier repository revisions and already-tracked evidence may contain host-specific or other operational details. This curation does not rewrite Git history or certify the whole repository as sanitized. Review older material separately before redistribution.

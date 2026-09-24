# Curated engineering history

This is a short, contributor-facing summary of earlier research and engineering work. It is not a complete activity log, release record, or independent re-verification. The underlying reports are dated snapshots, and some rely on local evidence that is not part of this summary.

## What the records describe

- The project explored a controller-owned execution architecture alongside human-invoked planning skills. The current product direction is narrower: planning and a human-agreed handoff, then stop.
- Earlier stage notes record design and implementation experiments across bootstrap, isolation, state, roles, context, evidence, and verification. Their stage labels describe those experiments; they do not mean the current product is released or in use.
- Operational retrospectives describe a workflow that collected substantial planning material but encountered repeated revisions and difficulty at the execution handoff. They call out clearer assignment/baseline binding, reproducible tests, and explicit failure handling as areas for further research.
- Later retrospective notes discuss separate workstreams on execution attempts, approval-record handling, and context/session handoff. These are not all part of the current planning product.

## Reading historical results

The `docs/research/STAGE-*-RESULT.md` files and records in `evidence/` are useful for understanding decisions and experiments. Read each item with its date, baseline, and scope. A historical local “accepted” or “PASS” label is not a product release, a claim of current use, or proof that the result can be reproduced against today's source.

Detailed forensic reports under `docs/reports/` and machine-specific research notes are not reproduced here because their source material includes private session or local-environment details. The [source inventory](SOURCE-INVENTORY.md) records those candidates and the review needed before any public sharing. Nothing was discarded or rewritten to create this summary.

## Current direction

Start with the current [planning-first Getting Started guide](../GETTING-STARTED.md). Collect and verify source data before drafting a spec or proposing work. Treat execution architecture and raw historical logs as research until separately reviewed and authorized.

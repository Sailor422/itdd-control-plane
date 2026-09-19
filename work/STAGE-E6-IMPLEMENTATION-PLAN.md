# Stage E6 Implementation Plan

| Requirement | Acceptance | Implementation | Evidence |
|---|---|---|---|
| Durable human gate | VERIFIED_EU_REVIEW has exact project/EU/candidate/evidence bindings | `control/human.py`, `human-gate.schema.json` | `test_human_approval...` |
| Human-only decision | Agent approval fails through Stage D | `HUMAN_GATE_APPROVAL` in capability authorization | `test_rejection_agent...` |
| Durable approval/rejection | Controller appends decision and materializes state | `HumanGateStore.transition` | same test, event reconstruction |
| Stale protection | candidate mismatch supersedes waiting gate | `HumanGateStore.supersede` | stale binding assertion |
| Derived views | deterministic project-local Markdown, no authority | `HumanViewGenerator`, `tools/itdd.py` | rebuild/tamper tests |
| Optional Obsidian | no Obsidian dependency | plain `.idd/views/*.md` | full offline suite |

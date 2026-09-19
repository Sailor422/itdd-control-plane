# Stage B Implementation Plan

Status: approved for implementation by the Stage B authorization dated 2026-09-19  
Baseline: `f26c15ee3aac5a118499216e51cb5653fc0280a0`  
Scope: project-root authority, JSONL event history, schema validation, derived reconstruction, append-only detection, and isolation tests

## Traceability

| Requirement | Acceptance | Planned change | Verification |
|---|---|---|---|
| Root authority | Traversal, symlink, unrelated, legacy, and broad-trust paths are rejected | `control/authority/paths.py` | Unit and negative isolation tests |
| Durable events | Deterministic versioned JSONL with required fields and optional bindings | `control/events/format.py`, `control/events/log.py`, `schemas/event.schema.json` | Schema fixtures and event tests |
| Reconstruction | Restarting from history yields the same current state | `control/events/reducer.py` | Fresh-process reconstruction test |
| Append-only detection | Edit, delete, reorder, broken chain, malformed injection are detected | Hash-linked records plus committed head metadata | Integrity negative tests |
| Documentation | Authority, isolation, limitation, and threat model are explicit | `docs/architecture/isolation-and-events.md` | Independent documentation inspection |

## Design decisions

- Use Python standard library only for the first implementation.
- Store events at `<project-root>/.idd/state/events.jsonl` and a chain commitment at `<project-root>/.idd/state/events.head.json`.
- Include `event_hash` and `previous_event_hash` in addition to the required event fields. Hashes detect ordinary edits, deletion, reorder, and injection; they do not prevent a user with OS permissions from rewriting both files.
- Derive current state only by replaying valid events. The derived state is never authoritative.
- Resolve all candidate paths with `Path.resolve()` and compare with `os.path.commonpath`; reject lexical `..` components before resolution as well.
- Treat Codex trust as external capability, not ITDD authorization. No code reads or changes Codex configuration.

## Out of scope

Context Compiler, Scout, Project Map, Obsidian, role launching, parallel execution, integration, maintenance, break-glass, vault migration, Prime, global trust settings, and database storage.

## Build and verification sequence

1. Add schema, implementation, fixtures, and focused tests.
2. Run unit, event, reconstruction, and negative suites from a fresh process.
3. Freeze the candidate SHA and changed-file inventory.
4. Run independent verification against the frozen candidate, including a fresh checkout and a fresh Python process.
5. Preserve the verifier artifact under `.idd/evidence/`.
6. Commit only after verification passes and create `stage-b-isolation-events-pass`.


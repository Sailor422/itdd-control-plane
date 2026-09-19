# Stage B Isolation and Durable Events

## Authority domain

An ITDD project root is an explicitly supplied, existing directory resolved to its canonical filesystem path. Every ITDD path is resolved beneath that root. Lexical parent traversal is rejected before resolution; resolved paths are compared with `commonpath`, so absolute paths, symlink targets, and unrelated repositories cannot become authorized merely through textual prefix matching.

Codex may technically access a path because of its global configuration, including the existing `/` trust entry. That capability is not ITDD authorization. Stage B does not read, modify, or depend on Codex trust settings.

## Durable event model

Events are canonical JSONL records at `.idd/state/events.jsonl`. Each record is schema-versioned and contains the event identity, type, timestamp, project, actor, chain relationship, payload, and SHA-256 content hash. Optional intent, graph, execution, and Git bindings are written only when they exist. `.idd/state/events.head.json` commits the count and current tail, allowing normal ITDD verification to detect tail deletion as well as record edits, reorder, broken chains, and malformed injection.

Current state is derived by replaying verified history. It is not authoritative and is not stored as a competing source of truth. A fresh process can reconstruct the same state without conversation history.

## What is enforced now

- Explicit root resolution and canonical path containment.
- Rejection of lexical traversal and resolved symlink escapes.
- Rejection of unrelated repositories and discovered legacy vault paths.
- Schema validation, canonical serialization, hash chaining, duplicate detection, and head-commitment checks.
- Normal append operations do not rewrite prior event lines.

## Known limitation

The event file and head commitment are ordinary files. A human or malicious process already running with the user's OS permissions can rewrite both and defeat this detection mechanism. Stage B provides application-level integrity checks, not OS-level immutability, sandboxing, or protection against a compromised account. Later stages may add capability enforcement and stronger recovery controls.

## Threat model

| Threat | Stage B response | Remaining limitation |
|---|---|---|
| Accidental agent wandering | Canonical root/path checks | A caller must use the ITDD helper. |
| Model attempting unauthorized access | Explicit authorization rejects paths outside root | Stage B does not sandbox arbitrary model tools. |
| Malformed path input | Lexical and resolved containment checks | No protection if the host filesystem itself is compromised. |
| Stale or incorrect context | No global vault auto-discovery; events are project-local | Context Compiler and provenance controls are later stages. |
| Malicious code with user OS permissions | Out of scope for application-level checks | Requires OS sandboxing, least privilege, and human security controls. |


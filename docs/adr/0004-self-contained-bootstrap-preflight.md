# ADR 0004: Self-contained bootstrap preflight and safe payload copying

- **Status:** Accepted
- **Date:** 2026-09-21

## Context

A new ITDD project must work from the installed package, not from the control-plane source checkout or a network connection. The bootstrap writes project state and may initialize Git, so a late refusal can leave a partial project. Existing project-local skill manifests also must not be silently replaced. Untrusted or damaged package contents must not escape the intended destination through symlinks.

## Decision

`install_itdd_bundle` performs a complete read-only preflight before any destination mutation. It checks the required bundled runtime and contracts, validates an existing manifest as a non-empty list of entries with safe relative contract paths, and verifies every contract against the bundled local `skills` tree. Missing, malformed, empty, or unrelated manifests are refused and preserved. A valid manifest is retained deterministically.

Copying rejects source and destination symlinks and checks resolved paths remain within their bundle or project roots. The copy filter excludes `__pycache__` and `.pyc`; setuptools package-data exclusions apply the same rule to wheels. The generated manifest points at the bundled `grill_with_docs/skill.json` contract, allowing runtime discovery from local files.

## Consequences

- Refusal paths leave the destination unchanged, including Git state.
- Existing local contracts outside the package must be handled before bootstrap; they are not overwritten.
- The installed wheel contains the runtime and contracts needed for offline bootstrap, without transient Python build artifacts.
- Adding a new bundled contract requires updating the package payload and its manifest/runtime tests.

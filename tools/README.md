# Tools

Reserved for deterministic inspection and verification tools. Tools do not grant themselves lifecycle authority.



## Proposal approval adapter

The human-only `/approved` skill is the only supported entrypoint for proposal approval. It invokes `uv run python tools/itdd.py proposal-approval record` after its current-turn marker check. The command is an adapter, not an authenticator; arbitrary callers are not protected. Its exact invocation and artifact contract are in [`docs/agents/human-approval-records.md`](../docs/agents/human-approval-records.md). Approval records do not execute or promote work.

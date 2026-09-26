# Human approval records for saved proposals

The installed human-only `/approved` skill is the sole supported entrypoint. It checks Prime's current-turn `PRIME_APPROVED_INVOCATION_V1` marker, confirms one pending proposal, and rechecks the saved bytes, scope, identity, and independent PASS review immediately before calling the adapter. If the marker is absent, the skill must not call the adapter. The controller does not independently authenticate arbitrary callers or claim identity proof.

## Artifact contract

The skill passes one proposal object with exactly `proposal_id`, `proposal_path`, `scope`, and `proposal_sha256`. The path is relative to the project root; the controller resolves it within that root, reads the saved bytes, and recomputes SHA-256. Scope is the exact scope text presented to the human; its SHA-256 is computed from UTF-8 bytes.

The review receipt is a repo-contained JSON file with exactly these fields:

```json
{"schema_version":1,"review_id":"REV-1","proposal_id":"PROP-1","proposal_sha256":"<sha256>","scope_sha256":"<sha256>","verdict":"PASS","reviewer_execution_id":"EXEC-REVIEW-1","report_path":"work/review.md","report_sha256":"<sha256>"}
```

The controller re-reads the receipt, requires PASS and a nonempty independent reviewer execution ID, verifies exact proposal and scope bindings, and hashes the report bytes. Paths that escape the project root, missing artifacts, changed bytes, malformed receipts, or mismatches fail without appending an approval event.

## Adapter contract

The human-only skill invokes this documented project command only after it has checked Prime's current-turn marker:

```sh
uv run python tools/itdd.py proposal-approval record \
  --project-root "$PROJECT_ROOT" --project-id "$PROJECT_ID" \
  --proposal-json "$PROPOSAL_JSON" --review "$REVIEW_RECEIPT" \
  --invocation-id "$PRIME_INVOCATION_ID" --timestamp "$UTC_TIMESTAMP"
```

`PROJECT_ID` must be the active project's existing ID; do not make one up. The proposal JSON contains exactly `proposal_id`, `proposal_path`, `scope`, and `proposal_sha256`. `proposal_path` and the review receipt/report paths are relative to the project root. The command produces a JSON receipt on stdout, exits nonzero on failure, and prints an explicit `persisted: false` response to stderr. It constructs invocation metadata as `command: "/approved"`, `source: "interactive"`, and the invocation ID from Prime's marker. The command itself does not authenticate callers. Its only supported caller is the human-only skill after the host marker gate; never use it as a generic approval route.

The corresponding Python entry point is `ProposalApprovalController(project_root, project_id=...).record(...)`. This adapter validates artifacts and writes the event; it does not establish the invocation trust boundary.

Successful recording appends one controller-owned `proposal.approval.recorded` event and returns a receipt with `persisted: true`, the durable approval/event identity, the exact proposal/scope/review/invocation bindings, and `executed: false`. An identical repeat returns the same receipt without another event. A changed binding for an already-recorded proposal is rejected. `read(approval_id)` reconstructs the full receipt and bindings from the event log.

Approval records authority to approve that exact proposal only. Recording never executes, publishes, promotes, or mutates proposal work. On any adapter error or uncertain persistence, the skill must say approval was not persisted and stop; it must not retry through a different route. The adapter is not a defense against arbitrary malicious same-user processes.

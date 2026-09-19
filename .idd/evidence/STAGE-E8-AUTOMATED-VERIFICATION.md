# Stage E8 Automated Verification

Status: **PASS — human acceptance pending**

## Identity

- Baseline: `9d0200c` (`stage-e7-integration-pass`)
- Implementation candidate: `fb2f229`
- Independent verifier: clean checkout `/tmp/itdd-e8-verify-demo.Z20elx`
- Verification execution ID: `stage-e8-automated-verifier-20260920T050000Z-clean-checkout`

## Checks

- Full Stage B–E7 regression and E8 console suite: `85 passed`
- Clean checkout status: PASS
- Console status JSON from `examples/human-demo`: PASS
- Console reports `REVIEW_GRAPH` as the next legal action: PASS
- Console reports promotion as `NOT IMPLEMENTED`: PASS
- `git diff --check`: PASS
- Project discovery rejects a directory without local ITDD event state: PASS
- Obsidian is not imported, launched, or required: PASS

## E8 behavior verified

- Console is a projection/control interface over reconstructed state; it does not read Markdown for authority.
- Intent review and approval use Stage C plus Stage D human-only authorization.
- Graph approval is now an enforced human gate; EU eligibility is rejected before graph approval.
- Agent graph approval is denied with `DENY_HUMAN_ONLY`.
- Approval requires a visible review and typed `APPROVE`; navigation or exit cannot approve.
- Failed verifier state is surfaced with a concise reason and no approval action.
- JSON status and restart reconstruction are available without conversation history.
- The preserved temperature-demo source, durable state, and views remain present.

## Human acceptance boundary

Automated verification does not constitute final E8 acceptance. The final
`stage-e8-human-console-pass` tag must wait until the human operates the normal
console entry command and confirms usability through the demonstration. No
promotion, repair loop, parallel scheduler, replan execution, or global state
change was implemented.

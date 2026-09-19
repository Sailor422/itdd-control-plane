# Stage E8 Implementation Plan

| Requirement | Acceptance | Implementation | Evidence |
|---|---|---|---|
| Safe project entry | Nearest project-local event history only; clear no-project failure | `control/console.py` | console discovery tests |
| Authoritative dashboard | State and legal actions reconstructed from controller artifacts | `HumanConsole.state/render` | status/restart tests |
| Graph human gate | Proposed graph cannot authorize EU work before human approval | `GRAPH_APPROVAL`, `assert_eu_eligible` | graph gate tests |
| HUMAN_ONLY routing | Agent approval denied; confirmation required | `HumanGateController.decide`, console confirmation | console tests |
| Failure presentation | Failed verifier exposes concise reason and no approval | console verifier rows/failure action | E5-compatible state derivation |
| Portable interface | JSON status, no Obsidian/Codex dependency | `tools/itdd.py` | clean-checkout verification |
| Preserved demonstration | Existing `examples/human-demo` remains durable and inspectable | tracked demo source/state/views | demo artifacts and report |

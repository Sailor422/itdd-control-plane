# Stage E8 Human Console

`tools/itdd.py` is a thin terminal interface over controller APIs. It discovers
the nearest project-local durable event history, reconstructs Stage C/E5/E6/E7
state, presents one legal action at a time, and requires typed confirmation for
authority-bearing decisions. It never reads generated Markdown as authority.

Stage E8 adds an enforced `GRAPH_APPROVAL` gate. A proposed graph can be
reviewed, but EU execution is blocked until the controller records a human
approval using the existing Stage D `HUMAN_GATE_APPROVAL` operation. Agent
actors receive `DENY_HUMAN_ONLY`.

Obsidian remains optional. `itdd status --json` exposes the same reconstructed
state for later interfaces. Promotion remains explicitly `NOT IMPLEMENTED`.

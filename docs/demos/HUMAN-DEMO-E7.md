# Human Demo Through E7 — Current Durable Checkpoint

This is the preserved disposable temperature-converter demonstration. It is
not the ITDD implementation itself.

## Project

- Location: `examples/human-demo/`
- Intent: `I-701 v1`, human-approved
- Requirements: `REQ-001` valid Fahrenheit-to-Celsius conversion; `REQ-002`
  non-numeric input returns a non-zero status and clear error
- Graph: `G-701 v1`, with `EU-001` mapped to REQ-001 and `EU-002` mapped to
  REQ-002
- Current durable position: intent approved and graph created; no graph gate is
  introduced by the visualization

## Read-only inspection

From anywhere inside the project, run:

```bash
python3 /Users/herbertfields/itdd-control-plane/tools/itdd.py view
```

The command regenerates the derived Markdown projection and opens its dashboard
in Obsidian when available. It does not approve intent or graph, create a gate,
pause execution, or append an authoritative event. Closing Obsidian and editing
the generated Markdown are likewise non-authoritative.

## Demonstration status

The deliberately bad EU-001 candidate, corrected candidates, Git attestations,
integration result, and final integration human decision have not been run in
this cleanup turn. No promotion has occurred. Failed history remains preserved.

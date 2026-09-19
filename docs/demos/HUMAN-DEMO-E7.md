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
- Current durable position: graph review required

## Human operation

The normal entry point is:

```bash
python3 /Users/herbertfields/itdd-control-plane/tools/itdd.py
```

The console presents the graph review and uses controller validation for the
decision. It does not expose internal event paths or require Obsidian.

## Demonstration status

The deliberately bad EU-001 candidate, corrected candidates, Git attestations,
integration result, and final integration human decision have not been run in
this E8 implementation turn. No promotion has occurred. The next interactive
acceptance phase must be performed by the human through the console, with failed
history preserved.

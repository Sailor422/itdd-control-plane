# ITDD Human Demonstration

This disposable Python project preserves a durable ITDD checkpoint and its
derived read-only human views. From this directory, inspect the current state:

```bash
python3 /Users/herbertfields/itdd-control-plane/tools/itdd.py view
```

The command does not approve anything, create gates, or pause lifecycle work.
It regenerates the Markdown projection from authoritative ITDD state and opens
the dashboard in Obsidian when available. The deliberately bad EU-001
candidate remains a later demonstration checkpoint; failed history must be
preserved.

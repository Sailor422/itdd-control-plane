---
name: itdd-new
description: Initialize ITDD infrastructure (requires /setup-matt-pocock-skills first).
disable-model-invocation: false
---

# ITDD New Project

Initialize ITDD infrastructure in a project that has Matt Pocock skills configured.

## ⚠️ PREREQUISITE (MANDATORY)

**You MUST run `/setup-matt-pocock-skills` BEFORE running `/itdd-new`.**

This skill will **FAIL** if Matt Pocock setup is not detected.

```bash
cd ~/Projects/my-project
prime-agent
/setup-matt-pocock-skills   # REQUIRED FIRST
/itdd-new                   # Then run this
```

**Why?**
- Matt Pocock engineering skills require per-repo configuration
- Setup writes `docs/agents/` config and `AGENTS.md`/`CLAUDE.md`
- There is no global substitute - every repo needs its own setup
- `/itdd-new` checks for this config and refuses to run without it

## Usage

```bash
cd ~/Projects/my-project
prime-agent
/itdd-new
```

## What it does

### Creates ITDD Infrastructure

- `.idd/intent/` - approved intents
- `.idd/graph/` - execution graphs
- `.idd/capabilities/` - issued capabilities
- `.idd/context/packets/` - context packets
- `.idd/evidence/contracts/` - verification contracts
- `.idd/evidence/records/` - evidence records
- `.idd/verifiers/executions/` - verifier executions
- `.idd/human_decisions/registry/` - decision registry
- `.idd/human_decisions/pending/` - pending decisions
- `.idd/operations/` - operation proposals
- `.idd/attestations/` - candidate attestations
- `.idd/state/` - current state snapshots
- `.idd/views/` - generated views
- `.idd/build_workspaces/` - isolated EU worktrees

### Creates Project Scaffolding

- `CONTEXT.md` - domain glossary template
- `docs/adr/` - architectural decision records directory
- `src/` - source code directory
- `tests/` - test directory
- `skills/manifest.json` - project-local ITDD skills manifest (empty)
- `.gitignore` - excludes `__pycache__/`, `.idd/build_workspaces/`, etc.

### Git Initialization

- Initializes git repository if not present
- Creates initial commit: "ITDD infrastructure initialized"

## Constraints

- **FAILS** if `/setup-matt-pocock-skills` has not been run
- Must be invoked in a directory without existing `.idd/` folder
- Will not overwrite existing project files
- Only creates `AGENTS.md` if neither `AGENTS.md` nor `CLAUDE.md` exists

## After running

1. **Edit** `CONTEXT.md` with your domain glossary
2. **Use** `/grill-with-docs` to clarify requirements
3. **Create** and approve an intent
4. **Propose** an execution graph
5. **Run** EUs with Prime or other builders

## Complete Initialization Sequence

```bash
cd ~/Projects/my-project
prime-agent
/setup-matt-pocock-skills   # Step 1: Configure Pocock skills (interactive)
/itdd-new                   # Step 2: Create ITDD infrastructure
```

Then:
1. Review `docs/agents/*.md` (issue tracker, triage labels, domain docs)
2. Edit `CONTEXT.md` with domain glossary
3. `/grill-with-docs`
4. Create/approve intent
5. Propose graph
6. Run EUs

## See Also

- `/setup-matt-pocock-skills` - Configure Matt Pocock engineering skills
- `docs/GETTING-STARTED.md` - Complete setup guide
- `docs/agents/itdd-in-prime-usage.md` - Full ITDD workflow

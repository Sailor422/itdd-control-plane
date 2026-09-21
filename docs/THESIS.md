# ITDD Control Plane Research Thesis

## Overview

This project implements a research thesis on **reliable autonomous software engineering**. The core argument is that AI agents should be treated as powerful but disposable reasoning workers, while durable authority over intent, lifecycle, state, and verification must live outside the probabilistic reasoning process.

## The Central Proposition

> Reliable autonomous software engineering requires moving durable intent, lifecycle authority, project state, context selection, and verification evidence outside the probabilistic reasoning process, while preserving AI agents as powerful but disposable reasoning workers.

## Why This Matters

AI coding agents have shifted software engineering from a primarily code-production problem toward a **control, context, and verification problem**. Agents can generate substantial implementations, inspect repositories, run tools, and execute multi-step plans, yet long-running agentic work remains vulnerable to:

- **Intent drift** - The agent loses sight of the original human goal
- **Context pollution** - Conversational state becomes unreliable
- **Self-verification** - Agents judge their own work without independent checks
- **Stale knowledge** - Project facts become outdated
- **Scope expansion** - Work creeps beyond approved boundaries
- **False-positive acceptance** - Work is marked complete when it isn't
- **Unrecoverable state** - Interruptions leave the system in limbo

## Key Innovations

This thesis combines several research strands into a unified architecture:

1. **Intent-Driven Development (IDD)** - Human intent as durable authority, separate from mutable execution plans
2. **Test-Driven Development (TDD)** - Evidence-bound verification before acceptance
3. **Lean Production Vault Modeling (LPVM)** - Minimal context loading, reconstructable state
4. **Deterministic Lifecycle Control** - Controller (not agent) owns state transitions
5. **Role-Separated Execution** - Planner, Builder, Verifier, Integrator as separate capabilities
6. **Project-Local Knowledge** - Git-backed authority domain for project facts
7. **Independent Verification** - Fresh spec and standards checks per execution unit

## The Original Thesis Document

The full research thesis is preserved in three formats:

- [`thesis/ITDD-Control-Plane-Thesis.md`](../thesis/ITDD-Control-Plane-Thesis.md) - Markdown
- [`thesis/ITDD-Control-Plane-Thesis.pdf`](../thesis/ITDD-Control-Plane-Thesis.pdf) - PDF
- [`thesis/ITDD-Control-Plane-Thesis.docx`](../thesis/ITDD-Control-Plane-Thesis.docx) - Word document

**Do not materially rewrite the thesis during development.** It is a frozen research artifact explaining the problem, proposed solution, and design rationale. Implementation evolves; the thesis documents the original research proposition.

## Attribution

This thesis implements and extends:

### Prof Matt Pocock's AI-Assisted Engineering Methodology
- Engineering skills for issue tracking, domain modeling, and specification
- Context-driven development patterns
- See [`@total-typescript`](https://github.com/total-typescript) and his AI engineering talks

### Intent-Driven Development (IDD) Research
- Human-intent-first development with AI execution
- Controller-owned lifecycle architecture
- Independent verification frameworks

### Lean Production Vault Modeling (LPVM)
- Reconstructable state and minimal context loading
- Project-local knowledge authority
- Evidence-backed operations

## Thesis Structure

The thesis document covers:

1. **Introduction** - The shift from code generation to controlled delegation
2. **Research Problem & Questions** - What reliable autonomy requires
3. **Background** - IDD, TDD, LPVM, context engineering, evidence-based execution
4. **Architecture** - Controller, roles, capabilities, isolation, events
5. **Lifecycle** - Intent approval, graph execution, verification, integration, promotion
6. **Human Supervision** - Kanban gates, views, authority boundaries
7. **Knowledge & Context** - Project Map, Context Compiler, authority hierarchy
8. **Recovery & Maintenance** - Interruption handling, break-glass, repair
9. **Evaluation Plan** - Metrics, milestones, empirical validation
10. **Limitations & Future Work** - What this thesis does not yet prove

## Current Implementation Status

This repo implements the thesis architecture with **Prime Agent** as the execution harness:

- ✅ Single-EU execution verified (see [`work/proofs/`](work/proofs/))
- ✅ Controller-owned lifecycle (`control/operational.py`)
- ✅ Prime integration via `PrimeBuilderAdapter`
- ✅ Independent verification (spec + standards)
- ✅ Evidence-backed operations
- ⏳ Multi-EU orchestration (roadmap)
- ⏳ Additional harness support (Codex, Claude, custom)

> **⚠️ Work in Progress** — This is a research prototype, not production-ready.
> APIs and workflows may change as the project evolves.

## For Researchers

If you're evaluating this work:

1. **Read the thesis first** - Understand the research proposition
2. **Examine the proof** - See `work/proofs/prime-single-eu-20260921T034058Z-clean4/`
3. **Review the architecture** - See `docs/architecture/` for component details
4. **Check the evidence** - Each stage has independent verification reports
5. **Test the implementation** - Run `PYTHONPATH=. pytest -q` (156 tests pass)

## Citation

If referencing this work:

```
ITDD Control Plane: A Control-Plane Architecture for Reliable Autonomous Software Engineering
Research Thesis, September 2026
https://github.com/Sailor422/itdd-control-plane
```

---

**Related:**
- [Getting Started](GETTING-STARTED.md) - Setup and initialization
- [Architecture Overview](architecture/README.md) - Component details
- [Contributing](../CONTRIBUTING.md) - How to contribute to this research

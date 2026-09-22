# Prime Workbench and ITDD Authority Contract

- Status: accepted
- Date: 2026-09-22
- Deciders: human reviewer

Prime is the default human-directed workbench for research, design, documentation, planning, and explicitly requested systems work, but Prime must never write project code. All project code construction, testing, verification, integration, and promotion use ITDD; Prime's code-write restriction is a Prime-wide invariant that no project manifest may weaken. Project policy may describe allowed support work and project-specific proof obligations, but an absent or inferred policy grants no write or execution authority. Where ITDD cannot yet govern its own establishment or repair, use an explicit, auditable bootstrap lane rather than disguising it as normal execution. The Prime-side tool host enforces the restriction; ITDD owns candidate identity, scoped worker authority, lifecycle transitions, evidence, and promotion. After grilling resolves intent, Prime advances through the appropriate research/prototype, specification, ticketing, and ITDD execution procedures without routine human checkpoints; it pauses for unresolved human decisions, required real-system/human proof, or explicit retry/resource limits.

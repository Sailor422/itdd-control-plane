# Pocock Skills Research

## Scope and source

On 2026-09-19 the public `mattpocock/skills` repository was inspected at its current `main` branch. Relevant upstream material was reviewed without installing the suite. The repository describes a flow centered on `grill-with-docs -> to-spec -> to-tickets -> implement -> code-review`, with `wayfinder` for larger efforts and `diagnosing-bugs` for tight feedback loops.

## Recommendations

| Skill or idea | Classification | ITDD treatment |
|---|---|---|
| `grill-with-docs` / domain modeling | ADOPT | Use for human-only intent clarification, terminology, assumptions, and durable glossary/ADR output. It cannot approve or launch work. |
| `to-spec` | ADAPT | Translate settled intent into an acceptance contract, but publish through the ITDD controller and bind it to an immutable intent version. |
| `to-tickets` | ADAPT | Use its tracer-bullet and blocking-edge ideas for vertical EUs and graph proposals; human/controller approval remains separate. |
| `tdd` | ADOPT | Use red-green-refactor as an implementation discipline where appropriate, with acceptance evidence defined before Builder launch. |
| `code-review` | ADAPT | Split its standards/spec review concept into independent Spec Verifier and Standards Reviewer executions with distinct provenance. |
| `diagnosing-bugs` | ADOPT | Require a reproducible failing loop and regression evidence before classifying an implementation defect. |
| `writing-for-agents` | ADOPT | Apply to lean, precise context packets, role instructions, and capability descriptions. The Compiler controls what is actually supplied. |
| `wayfinder` | REFERENCE ONLY initially | Its decision-map approach is useful for research-scale uncertainty, but ITDD needs controller-owned durable graph and authority semantics before adoption. |
| human-only invocation | ADOPT | Preserve explicit human invocation for intent approval, maintenance, break-glass, and other authority-bearing actions. |

## Guardrails

The strongest transferable ideas are domain-language clarification, vertical slices with dependencies, test-first behavior loops, two-axis review, reproducible debugging, and concise agent-facing writing. The main adaptation is authority: upstream skills are procedural aids, not lifecycle authorities. Do not install the full collection or allow a skill to grant itself permissions.

## Sources

- [Pocock skills repository](https://github.com/mattpocock/skills)
- [Grill with docs](https://github.com/mattpocock/skills/blob/main/docs/engineering/grill-with-docs.md)
- [To-spec](https://github.com/mattpocock/skills/blob/main/docs/engineering/to-spec.md)
- [To-tickets](https://github.com/mattpocock/skills/blob/main/docs/engineering/to-tickets.md)
- [TDD](https://github.com/mattpocock/skills/blob/main/docs/engineering/tdd.md)
- [Code review](https://github.com/mattpocock/skills/blob/main/docs/engineering/code-review.md)
- [Diagnosing bugs](https://github.com/mattpocock/skills/blob/main/docs/engineering/diagnosing-bugs.md)
- [Writing for agents](https://github.com/mattpocock/skills/blob/main/docs/productivity/writing-for-agents.md)
- [Wayfinder](https://github.com/mattpocock/skills/blob/main/docs/engineering/wayfinder.md)


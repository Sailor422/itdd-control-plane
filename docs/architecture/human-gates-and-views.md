# Human Gates and Derived Views

Stage E6 keeps the controller and append-only event chain authoritative. A
`VERIFIED_EU_REVIEW` gate binds one project, EU, candidate SHA, Spec result,
Standards result, and gate identity. `approve` and `reject` are controller
validated transitions using the Stage D `HUMAN_GATE_APPROVAL` operation, which
is `HUMAN_ONLY`; an agent cannot create an approval.

The files under `.idd/views/` are generated Markdown for project-local viewers
such as Obsidian. They contain a source head and generator marker, are never
read for lifecycle authority, and can be deleted or manually edited without
changing controller state. Regeneration restores their projection. A candidate
SHA is still an ITDD binding rather than independently attested Git/VCS
identity; integration and promotion remain deferred to E7.

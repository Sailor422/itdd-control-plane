# Project-Local Skill Contract Boundary

- Status: accepted
- Date: 2026-09-20
- Deciders: human reviewers

The installed user-facing skill remains the authoritative behavioral source,
while the repository records the ITDD contract and evidence boundary for its
use. The first contract is for `grill-with-docs`: a human-only invocation may
produce a versioned, provenance-bound clarification proposal, but it may not
approve intent, grant capability, create authority, mutate approved intent,
advance lifecycle state, or promote a candidate. Acceptance must prove the
contract, forbidden actions, deterministic identity fields, provenance, and
fresh-process reconstruction without advancing the lifecycle.

This boundary separates skill assistance from controller and human authority.
It also prevents differences between the installed source and repository copy
from being silently treated as equivalent: the source identity and contract
version must be explicit in any future acceptance evidence.

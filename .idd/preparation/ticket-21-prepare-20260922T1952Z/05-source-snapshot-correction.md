# Source snapshot correction

The initial `04-source-snapshot-manifest.md` incorrectly rendered its “Baseline selected for preparation” field from a stale kernel variable (`prime-idd`). This value is erroneous and is not the approved baseline. The approved baseline is the exact SHA `80284553d571d5d92e2a8f66b7b8c312f9c283ef` on branch `main`, as recorded in `03-human-decisions.md`. No Git state or project source was changed by this metadata error.

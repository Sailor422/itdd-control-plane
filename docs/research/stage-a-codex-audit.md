# Stage A Codex Environment and Contamination Audit

Date: 2026-09-19  
Mode: read-only  
Scope: Codex environment and legacy knowledge locations on the local Mac

## Result

Codex remains operational and was not modified. No Codex, Claude, Hermes, Prime, or vault state was deleted, moved, renamed, normalized, reset, or migrated. Private contents and credentials were not copied into this repository.

## Findings

| Location or mechanism | Observed function | Classification | Contamination risk |
|---|---|---|---|
| `/Users/herbertfields/.codex/config.toml` | Codex configuration | GLOBAL-INFLUENCE | High: can affect all Codex sessions; retained read-only. |
| `/Users/herbertfields/.codex/skills/` | Local Codex skills, including system and user skills | GLOBAL-INFLUENCE | High: skills can alter agent behavior; inspect before any future adoption. |
| `/Users/herbertfields/.codex/history.jsonl` and `state_5.sqlite` | Conversation/history and durable app state | LEGACY-KNOWLEDGE | High privacy and stale-context risk; never default project context. |
| `/Users/herbertfields/.codex/attachments/` | Imported task material | LEGACY-KNOWLEDGE | Medium/high: may contain private or project-specific material. |
| `/Users/herbertfields/.codex/workspace Codex CODEX_VAULT_DIR/` | Codex workspace/vault-like documents | LEGACY-KNOWLEDGE | High: hidden durable knowledge can contaminate project context. |
| `/Users/herbertfields/.codex/computer-use/`, process manager, IPC, temp/plugin caches | Runtime integrations and helper processes | GLOBAL-INFLUENCE | Medium/high: can affect execution or tool behavior. |
| `/Users/herbertfields/.claude/` | Historical Claude configuration, projects, workspace, sessions | LEGACY-KNOWLEDGE | High: private historical material; do not modify or import. |
| `/Users/herbertfields/.hermes/` and `/Users/herbertfields/hermes/` | Historical Hermes runtime, pastes, evaluations, projects | LEGACY-KNOWLEDGE | High: private/stale runtime and knowledge material. |
| `/Users/herbertfields/.agent-vault/` and `/Users/herbertfields/agent-vault/` | Agent knowledge, runtime, tests, migrations, and project material | CONTAMINATION-RISK | High: mixed scope and private data; curate only through a future import workflow. |
| Environment variable names containing `CODEX_*` | Current Codex app/runtime integration markers | GLOBAL-INFLUENCE | Medium: values intentionally withheld; do not persist secrets. |

## Safety conclusions

The principal contamination risks are hidden global instructions/skills, project-agnostic conversation history, mixed-scope vaults, and runtime integrations that make behavior differ between sessions. The public repository therefore records only paths, mechanisms, classifications, and recommendations. Detailed inventories, values, transcripts, and credentials remain outside Git.

## Future handling

Treat all legacy stores as read-only source archives. A later migration stage may inventory, deduplicate, classify, detect staleness/conflict, validate, and curate explicit imports. Until then, workers must operate from project-local artifacts and compiled context only.


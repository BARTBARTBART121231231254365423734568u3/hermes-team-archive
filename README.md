> **Verouderd – zie [hermes-team-setup](https://github.com/BARTBARTBART121231231254365423734568u3/hermes-team-setup)** (en [hermes-discord-setup](https://github.com/BARTBARTBART121231231254365423734568u3/hermes-discord-setup) voor Discord).

# Hermes team setup — review snapshot

Private snapshot of Thomas's Hermes agent/team configuration for architecture and workflow review. **This is not a runnable restore, nor a dump of all of `~/.hermes`.** It contains the actual instructions, configuration shape, profile-specific skills, delegation/team workflows, cron definitions, local scripts/plugins, desktop plugins, and deployment instructions, with detected credentials and routing IDs replaced by placeholders. The exporter is in `export_setup.py`.

## Where to look

| Topic | Files |
| --- | --- |
| Manager prompt / system instructions | `setup/SOUL.md`, `setup/team/TEAM.md`, `setup/team/task-template.md` |
| Each specialist's prompt and available skills | `setup/profiles/<profile>/SOUL.md`, `setup/profiles/<profile>/skills/` |
| Configured models, toolsets, plugin switches, dispatch | `setup/config.yaml`, `setup/profiles/<profile>/config.yaml` |
| All installed skill source and references | `setup/skills/`, and profile-specific `setup/profiles/<profile>/skills/` |
| Automations and scheduled workflows | `setup/cron/`, `setup/scripts/`, profile `cron/jobs.json` where present |
| Plugins and hooks | `setup/plugins/`, `setup/profiles/<profile>/plugins/`, `setup/hooks/`, `setup/desktop-plugins/` |
| Deployment integration and workflows | `setup/deployment/` (selected tracked-file working-tree snapshot) |
| Hermes core assistant development instructions | `setup/core-instructions/` |

Core framework source is maintained separately by Nous Research: https://github.com/NousResearch/hermes-agent/tree/42e7471c6422df5983c29f046aa2122202f305d7 . This snapshot includes its agent instruction files, **not the 12,884-file upstream source tree**. The private Railway integration source lives at https://github.com/BARTBARTBART121231231254365423734568u3/hermes-agent-railway (local baseline `9ec922921d4eacfe2723436816ce940e3441a1be`); `setup/deployment/` shows relevant working-tree files, including local uncommitted changes, and is only for review, not a release.

## Boundaries / security

- No `.env`, OAuth credentials, authentication stores, personal memory, chat sessions, Kanban database/attachments, logs, caches, runtime backups, node_modules, worktrees or full application repositories are exported.
- No standalone MCP configuration file was found in the root or specialist-profile directories; do not infer an active MCP server merely from an installed skill mentioning MCP. Likewise no root `.hermes.md`, `HERMES.md`, `AGENTS.md` or `CLAUDE.md` was present in the live setup; the upstream source `AGENTS.md` instructions are included in `core-instructions`.
- Redacted config values are **not functional**. Do not deploy or replace a live configuration from this snapshot.
- Profile skills are exported separately on purpose: review the actual per-agent load and overlaps. Bundled skills may recur across profiles.
- A private repository is not a permission to share unreviewed source publicly. Re-run the exporter and inspect the diff plus credential scan before future pushes. Never commit real tokens.
- This is an architecture-review corpus, not a one-command recreation of Thomas's host. For a complete code audit of the upstream agent, use the pinned upstream commit; for deployment behavior, inspect the Railway repository separately.

Regenerate locally on the Hermes host with `python3 export_setup.py` (requires PyYAML). The exporter reads from `~/.hermes`, applies basic credential and ID redaction, and aborts on remaining high-confidence signatures. Automated redaction is not infallible; human review remains necessary before sharing with third parties.

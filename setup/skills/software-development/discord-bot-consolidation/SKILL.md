---
title: Discord Bot Consolidation Workflow
name: discord-bot-consolidation
description: Merge multiple Discord bots into a single bot.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when merging two or more Discord bots into one to reduce operational overhead.
metadata:
  hermes:
    tags: ["discord-bots", "consolidation", "multi-tenant", "refactoring"]
    related_skills: ["discord-bot-multi-tenant", "serenity-discord-bot-debugging"]
---

# Discord Bot Consolidation Workflow

When a user wants to consolidate multiple Discord bots into a single bot (reduce operational overhead, unified management), follow a structured 4-task dependency chain: **audit → design → implement → deploy**.

## When to Apply

- User wants to merge 2+ bots into 1
- Reason: Operational simplicity, single token management, unified feature set
- Scope: Keep per-guild isolation and settings (no cross-bot data loss)

## The 4-Task Pipeline

### Task 1: Audit (Coder)

**Scope**: Inventory both bots comprehensively.

**Deliverables**:
- Feature list for each bot (slash commands, button handlers, scheduled tasks)
- Database schema for each (tables, tenant/guild scoping)
- Hosting/environment (Railway project, service names, env vars)
- Permission models (how admins are gated, custom role overrides)
- Language/framework for each (Rust/Serenity, TypeScript/discord.js, etc.)
- Any command name collisions
- Active guild(s) and usage data

**Questions to answer**:
1. Is one bot already live on production?
2. Which guilds does each bot serve?
3. Is there existing data in either bot's database to migrate?
4. Which bot token should survive post-merge?

**Output**: Feature matrix + architectural conflicts identified.

### Task 2: Design (Coder)

**Blocked on**: Audit completion.

**Scope**: Lock down architecture and strategy.

**Deliverables**:
- Command namespace (how to merge commands without collision; `/wipe create` vs `/wipe-create`?)
- Database strategy (consolidate to 1 DB or 2? SQL schema changes?)
- Code structure (new module paths for merged bot)
- Permission model consolidation (which gating logic wins?)
- Env vars (any new vars needed?)
- Cutover strategy (big-bang deploy vs. staged rollout)

**Questions to answer from user**:
1. Confirmed which bot token to keep?
2. Any data migration needed, or start fresh?
3. Any per-guild settings to preserve?
4. Acceptable downtime for cutover?

**Output**: Signed-off architecture doc.

### Task 3: Implementation (Coder)

**Blocked on**: Design approval.

**Scope**: Port one bot's features into the other's codebase.

**Typical challenges**:
- Language mismatch (TypeScript → Rust rewrite, not copy-paste)
- Database differences (Postgres + Prisma → SQLite + sqlx)
- Testing for tenant isolation (ensure per-guild settings remain separate)
- New Discord intents may be needed

**Deliverables**:
- Branch on the target bot repo (e.g., `wipe-merge/t_<taskid>`)
- All tests passing (including new cross-bot integration tests)
- Clean cargo check / npm build
- Commit(s) ready for review

**Output**: Branch + commit hash ready for security review.

### Task 4: Security Review + Deploy (Security + Devops)

**Blocked on**: Implementation approval.

**Scope**: Security clearance, then production deployment.

**Security checks**:
- Tenant isolation (per-guild data scoped correctly)
- No SQL injection (parameterized queries)
- No secrets in diff
- Admin gating on admin commands
- No unexpected permissions required

**Deployment checks**:
- Redeploy merged bot to production
- Live smoke tests (all commands from both bots responsive)
- Verify bot is in correct guilds
- Monitor logs for 5+ minutes post-deploy

**Decommission old bot** (if approved):
- Remove old bot from guilds
- Revoke old bot token
- Archive old repository or mark as deprecated

**Output**: Merged bot live, old bot decommissioned.

## Kanban Setup

Create 4 linked tasks with explicit dependencies:

```bash
kanban_create --title "Audit both bots" --assignee coder --parents [] # t_audit
kanban_create --title "Design consolidation" --assignee coder --parents [t_audit] # t_design
kanban_create --title "Implement merged bot" --assignee coder --parents [t_design] # t_impl
kanban_create --title "Security + Deploy" --assignee security --parents [t_impl] # t_deploy
# After security approves:
kanban_create --title "Deploy merged bot" --assignee devops --parents [t_deploy] # t_liveDeploy
```

Each task blocks on its parent. Pipeline flows automatically as tasks complete.

## Key Decisions to Lock Early

**Before Task 2 (Design) starts, confirm with user:**

1. **Bot token**: Which bot survives? (Usually the more mature one)
2. **Database**: Consolidate to one DB or keep two?
3. **Data migration**: Migrate existing data or start fresh?
4. **Per-guild preservation**: Do guild-specific settings need to survive the merge?
5. **Cutover strategy**: Big-bang (one deploy) or staged (pilot guild first)?

**If these are unclear, add a clarification comment on the Design task and ask user to reply before proceeding.**

## Typical Challenges & Patterns

### Language Mismatch (e.g., TypeScript → Rust)

**Challenge**: Cannot copy-paste code; must rewrite logic.

**Pattern**:
1. Read the TypeScript bot's core logic (command handlers, event listeners)
2. Understand the business logic (what does `/wipe create` actually do?)
3. Implement that logic in Rust using the target bot's patterns
4. Test extensively (unit tests for handlers, integration tests for guild isolation)

**Time**: Rewrite is ~2-3x slower than copy-paste, but same-language migrations are nearly 1:1.

### Database Schema Mismatch (Postgres + Prisma → SQLite + sqlx)

**Challenge**: Different SQL dialects, different ORM patterns.

**Pattern**:
1. Add new tables to target bot's DB (SQLite schema)
2. Migrate existing data via migration script (if keeping data)
3. Update queries to use target bot's query style (sqlx prepared statements)
4. Test data isolation (ensure tenant/guild scoping is enforced)

### Permission Model Differences

**Challenge**: One bot gates on Discord perms (Manage Server), other uses custom roles.

**Pattern**:
- Choose one model as the "standard" (usually the more sophisticated one)
- Upgrade the simpler bot's commands to use the standard model
- Document the new permission behavior in Settings

**Example**:
- AuthList uses: `caller_is_admin()` = (has Manage Server) OR (has custom admin_role_id)
- wipe-react-bot used: `caller_is_admin()` = (has Manage Server)
- Merged: Both use AuthList's model (more flexible)

### Per-Guild Settings Must Survive

**Challenge**: Each bot has guild-specific configs that users have set up.

**Pattern**:
1. Inventory guild settings in both bots (wipe member role, auth list config, etc.)
2. Ensure new DB schema has columns for all settings
3. Migrate existing settings from old bot DB to merged bot DB (or preserve via manual step)
4. Test that settings are tenant-scoped (guild A's settings don't leak to guild B)

## Real Example: AuthList + wipe-react-bot

**Audit found**:
- AuthList: 10 slash commands, SQLite, Rust/Serenity, 86 members in 1 guild, per-guild admin role config
- wipe-react-bot: 5 slash commands + buttons, Postgres/Prisma, TypeScript/discord.js, RSVP scheduler, no data (starting fresh)
- No command collisions
- No language overlap (decided to keep Rust + SQLite)

**Design decided**:
- Merge wipe-react-bot into AuthList codebase
- New `/wipe` command namespace (wipe create/cancel/list/check/config)
- New SQLite tables (wipe_guild_settings, wipe_events, wipe_rsvps)
- Reuse AuthList's `caller_is_admin()` gate
- Big-bang deploy (single redeploy)

**Implementation**:
- Ported wipe logic from TypeScript to Rust (new module bot/src/discord/commands/wipe/)
- New component handler for RSVP buttons
- New scheduler for 15-min voice-presence reminders
- 71 tests (9 new for wipe tenant isolation)
- Commit 1068f6f on branch wipe-merge/t_dc282247

**Security + Deploy**:
- Security: 5 checks passed (isolation, injection, auth, credentials, intents)
- Devops: Redeploy live, smoke tests passed (all 15 commands responsive)
- Outcome: Single consolidated bot, wipe-react-bot decommissioned

## Anti-Patterns to Avoid

❌ **Skipping the audit** — Surprise complexity emerges mid-design

❌ **Locking design without user input** — User discovers their guild settings are lost

❌ **Big design change at implementation time** — "Oh, we can't consolidate the databases" discovered in code

❌ **Skipping security review** — Tenant isolation bug ships to production

❌ **Deploying without smoke tests** — Bot appears online but commands don't work

❌ **Not decommissioning the old bot** — Confusion (which bot am I in?), token still valid (security risk)

## References

- `references/audit-checklist.md` — What to inventory in both bots
- `references/design-template.md` — Architecture document template
- `references/migration-script-example.md` — Data migration pattern (if needed)
- `discord-bot-multi-tenant` — Per-guild isolation patterns
- `serenity-discord-bot-debugging` — Rust Discord bot debugging

---

**Golden Rule: 4-task pipeline flow is critical.** Decisions locked at each stage prevent surprises later. Do not attempt full implementation before Design is approved by user.

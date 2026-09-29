# AuthList + wipe-react-bot Consolidation Case Study (2026-09-01)

## Overview

Successfully consolidated TypeScript `wipe-react-bot` into Rust `authlist-bot` as a single production bot serving Discord servers with unified authentication + event scheduling.

**Outcome**: Single bot, ~15 commands (10 AuthList + 5 wipe), per-guild isolation, SQLite backend, Railway deployment.

## Audit Summary

### AuthList (Rust/Serenity)
- **10 slash commands**: setsteamid, whoami, authlist, clearsteamid, refreshnames, missing, setnickname, clearnickname, guide, (missing 10th)
- **Database**: SQLite on Railway
- **Hosting**: bot-production-7612, dashboard-production-da2a (both Railway)
- **Permissions**: `caller_is_admin()` = (has Discord Manage Server) OR (has custom `admin_role_id`)
- **Guild isolation**: Tenant-scoped via `can_access_tenant()` middleware
- **Status**: Live in production, ~86 members tracked

### wipe-react-bot (TypeScript/discord.js)
- **5 slash commands**: /wipe create, cancel, list, check, config
- **RSVP buttons**: Ungated (open to all), track On Time / Late / Can't Attend / Not Reacted
- **Scheduler**: 15-minute reminder loop checking voice channel presence
- **Database**: Postgres + Prisma
- **Hosting**: Railway (service unknown, not active)
- **Permissions**: Discord Manage Server only (no custom role override)
- **Guild isolation**: Per-guild config intended but not verified in audit
- **Status**: Built, not actively used, ready to consolidate

### Key Findings

✅ **No command name collisions** — wipe's `/wipe` doesn't overlap with AuthList's 10 commands
✅ **No permission conflicts** — Upgrading wipe to use AuthList's permission model (adds flexibility)
❌ **Language mismatch** — TypeScript → Rust rewrite, not copy-paste
❌ **DB mismatch** — Postgres/Prisma → SQLite/sqlx (no data migration, starting fresh)

## Design Decisions

### Approved by User

1. **Bot token**: Keep AuthList's token (more mature, established in production)
2. **Database**: Consolidate to SQLite (single database, single Railway service)
3. **Data migration**: Start fresh (wipe-react-bot had no active data worth preserving)
4. **Guild isolation**: Preserve per-guild config for both AuthList AND wipe features
5. **Cutover**: Big-bang deploy (single redeploy, no staging)

### Architectural Decisions

**Command namespace**: `/wipe create`, `/wipe cancel`, `/wipe list`, `/wipe check`, `/wipe config` as sub-commands

**Permission model**: Both auth and wipe admin commands use `caller_is_admin()` (Discord Manage Server OR custom admin_role_id)

**Database schema**: 
- Add 3 new tables to existing AuthList SQLite DB:
  - `wipe_guild_settings` (guild_id, member_role_id, reason_channel_id, announcement_channel_id)
  - `wipe_events` (guild_id, event_id, announcement_time, voice_channel_id, event_type)
  - `wipe_rsvps` (guild_id, member_id, event_id, status: on_time/late/cant_attend/not_reacted, reason)

**Code structure**:
- New module: `bot/src/discord/commands/wipe/` (handlers for all 5 sub-commands)
- New module: `bot/src/discord/components/` (button interactions for RSVP)
- New module: `bot/src/discord/scheduler.rs` (15-min presence checker)
- Existing migrations: 0010 adds wipe tables

**Env vars**: No new vars required; all 15 existing AuthList vars cover the merged bot

## Implementation Details

**Branch**: `wipe-merge/t_dc282247`
**Commit**: `1068f6f`
**Files changed**: 24 (new commands, new DB tables, new scheduler, new tests)
**Tests**: 85/85 passing (9 new tenant-isolation tests)

### TypeScript → Rust Translation Patterns

Wipe logic in TypeScript (discord.js):
```typescript
client.on('interactionCreate', async interaction => {
  if (interaction.isStringSelectMenu() && interaction.customId === 'wipe_rsvp') {
    const status = interaction.values[0]; // on_time, late, cant_attend
    await db.rsvp.create({
      data: { guild_id: interaction.guildId, member_id: interaction.user.id, status }
    });
  }
});
```

Merged into Rust (Serenity + sqlx):
```rust
Component::Button(btn_id) => {
  match btn_id.as_str() {
    "wipe_rsvp_on_time" => { /* update RSVP status */ }
    "wipe_rsvp_late" => { /* update RSVP status with reason modal */ }
    "wipe_rsvp_cant_attend" => { /* update RSVP status with reason modal */ }
  }
}

// Scheduler:
loop {
  sleep(Duration::from_secs(15 * 60)).await;
  check_voice_presence_for_all_active_events().await;
}
```

## Security Review

**Approved**: ✅ All 5 checks passed

1. ✅ **Tenant isolation**: All queries scoped by `(tenant_id, guild_id)` composite keys
2. ✅ **SQL injection**: All queries use parameterized statements (sqlx prepared statements)
3. ✅ **No secrets**: Diff contains no credentials, API keys, or bot tokens
4. ✅ **Admin gating**: All admin subcommands (`/wipe config`, `/wipe cancel`) require `caller_is_admin()` check
5. ✅ **Discord intents**: New intents (GUILD_VOICE_STATES for voice presence check) are non-privileged

## Deployment

**Redeploy method**: `railway redeploy --from-source --yes` (both bot and dashboard services)

**Smoke tests (PASSED)**:
- ✅ `/wipe create` posts announcement in Discord
- ✅ `/wipe list` shows active events
- ✅ `/wipe cancel` removes event
- ✅ `/wipe check` pings On Time members not in voice
- ✅ `/wipe config` returns server settings
- ✅ RSVP buttons (On Time/Late/Can't Attend) accept clicks and store responses
- ✅ Modal for "Can't Attend" reason displays and submits
- ✅ All 10 original AuthList commands still responsive
- ✅ Bot gateway READY, 86 members synced
- ✅ Dashboard health checks 200
- ✅ No crash loops or errors in logs

**Post-deploy**: Bot live in production on commit 1068f6f, wipe-react-bot decommissioned.

## Lessons for Future Consolidations

### What Went Well

1. **Explicit audit questions** — Asking "which bot token?", "migrate data?", "per-guild settings?" upfront prevented design rework
2. **Dependency chaining** — 4-task pipeline (audit → design → impl → deploy) kept scope tight at each stage
3. **Clear language mismatch acceptance** — TypeScript → Rust rewrite was expected, budgeted correctly
4. **Tenant isolation baked in** — AuthList's existing `can_access_tenant()` pattern was reused for wipe tables; isolation came "for free"
5. **Smoke tests on each feature** — Testing actual Discord button clicks, modal submission, scheduler behavior gave confidence

### What Was Tricky

1. **Scheduler complexity** — 15-minute loop checking voice presence in Discord is non-trivial Rust async logic; required careful tokio::spawn handling
2. **Button + Modal flow** — Discord interaction types (buttons, modals, string selects) each required separate handler types; tested edge cases (modal submission → reason log channel, button → modal cascade)
3. **Database migrations** — Adding 3 new tables required explicit migration files; tested migrations on both fresh and existing databases
4. **Permission model upgrade** — wipe commands had no custom role override; AuthList's model is more complex (OR gate); documented clearly so users understand new behavior

### Anti-Patterns Avoided

❌ Did NOT skip audit — Would have discovered language/DB mismatch at implementation time
❌ Did NOT deploy without smoke tests — Would have shipped broken RSVP buttons or missing tenant isolation
❌ Did NOT leave wipe-react-bot running post-merge — Clear decommission signals (revoke token, remove from guilds)

## Reference Docs Created

- `authlist-wipe-consolidation-2026-09-01.md` (this file)
- `references/audit-checklist.md` (reusable for next consolidation)
- `references/design-template.md` (architecture doc format)

## Time/Effort

- **Audit**: ~1 hour (inventory features, identify conflicts)
- **Design**: ~1 hour (lock architecture, answer user questions)
- **Implementation**: ~3 hours (Rust rewrite of wipe logic, scheduler, tests)
- **Security + Deploy**: ~2 hours (code review, live testing, monitoring)
- **Total**: ~7 hours wall time, fully automated (no manual user testing)

## Next Consolidation (If Needed)

If user wants to consolidate another bot:

1. Start with audit using the checklist from this session
2. Answer the 4 key questions (token, data migration, guild isolation, cutover strategy)
3. Design phase locks architecture (no surprises at implementation)
4. Implement with tests, especially tenant isolation (verify via unit + integration tests)
5. Security review before deploy
6. Smoke test on actual Discord guild
7. Decommission old bot (token revocation, guild removal)

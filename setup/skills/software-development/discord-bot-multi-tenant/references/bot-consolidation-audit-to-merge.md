# Bot Consolidation: Audit-to-Merge Pattern

**Session:** 2026-09-01 (AuthList + wipe-react-bot consolidation)

**Goal:** Merge feature-specific bot (wipe-react-bot: TypeScript/discord.js/Postgres RSVP scheduling) into the main multi-tenant bot (AuthList-bot: Rust/serenity/SQLite Steam ID + role management) while preserving per-guild configuration isolation.

## Audit Phase (Read-Only Discovery)

Before any code changes, discover what each bot actually does:

### Coder's Deliverable

1. **Runtime & deployment:**
   - Language, frameworks (discord.js vs serenity, ORM)
   - Database (SQLite vs Postgres, schema)
   - Hosting (Railway, separate services?)
   - Scheduled jobs (crons, in-process timers?)

2. **Command inventory:**
   - All slash commands + subcommands
   - Permission gates (Discord perms, app-level role checks)
   - What each command does end-to-end

3. **Overlaps & conflicts:**
   - Command name collisions (rename needed?)
   - Permission model differences (one uses custom admin_role override, other relies on Discord perms only)
   - Intents (Discord Gateway intents required by each bot)
   - Shared guilds where both bots run (affects cutover strategy)

4. **Credentials & tokens:**
   - Bot token names (separate DISCORD_TOKEN vars?)
   - Will merge need to consolidate to one bot application?

5. **Open questions for the user:**
   - Is the feature bot (wipe-react-bot) actually running?
   - Which guild(s) does it serve? (Needed to seed the merged bot's config)
   - Which bot application to keep post-merge? (Usually the main one)
   - Any data to migrate, or start fresh?

**CRITICAL FINDING:** Check the feature bot's current HEAD commit. If it includes self-disabling code (e.g., bot.leave() + process.exit() on startup), it may already be offline and the merge has zero cutover urgency.

## Architecture Phase (Design & Consolidation Strategy)

Once audit is complete, coder designs the merge:

### Key Decisions

1. **Language/Runtime:** If the bots use different languages (TypeScript vs Rust), a real rewrite/port is needed, not a code paste. This is a significant effort signal.

2. **Database consolidation:**
   - Main bot uses SQLite (journaling, simple), feature bot uses Postgres (heavyweight but separate).
   - Decision: move feature bot's tables into the main bot's SQLite DB, or keep separate DBs?
   - Recommendation: single DB (SQLite) for simplicity; migrate feature tables into the main schema.

3. **Bot application/token:**
   - Two separate Discord bots today.
   - Decision: keep the main bot's application, retire the feature bot's.
   - Post-merge: re-invite the main bot to the feature bot's guilds with the added Gateway intents.

4. **Permission model alignment:**
   - Feature bot: Discord default_member_permissions only (no app-level role override).
   - Main bot: custom caller_is_admin() (Manage Server OR per-tenant admin_role_id).
   - Decision: Keep feature commands using Discord perms only; keep main commands using the custom gate. No forced unification (two different feature sets, two different gating models is OK).

5. **Data migration:**
   - Feature bot has past event/RSVP data in Postgres.
   - Decision: start the merged bot's wipe tables empty (confirmed with user: no data migration needed).

### Coder's Deliverable

A design doc (posted as kanban_comment + metadata) that locks down:
- Database schema additions (wipe tables for SQLite)
- Command handler structure (new `/wipe` command with subcommands)
- Tenant isolation (wipe events are tenant-scoped, same as members)
- Gateway intents (add GUILD_VOICE_STATES)
- Deployment order (implement → security review → deploy merged bot → decommission feature bot)

## Implementation Phase (Porting & Integration)

Coder ports the feature bot's logic into the main bot:

1. **Database migrations:** Add wipe tables (Guild, WipeEvent, RSVP) to AuthList's SQLite schema.
2. **Command handler:** Implement `/wipe` command with all subcommands (create, cancel, list, check, config).
3. **Event handler:** In-process timer (serenity::spawn) for voice-presence reminders 15 min before wipeTimeUtc.
4. **Tenant isolation:** All wipe queries scoped by tenant_id (same as members queries).
5. **Tests:** Unit tests for time zone conversion, RSVP state machine, voice-presence logic. Integration tests for multi-guild isolation.

### Branch & Safety

- Work on a feature branch (not main).
- No production changes until security review passes.
- Tests must pass (existing AuthList tests still pass + new wipe tests pass).
- Build must succeed (Rust compile clean, no warnings).

## Security Review Phase

Security agent reviews the merged bot before deployment:

1. **Input validation:** Time zone strings, event titles (no SQL injection, XSS).
2. **Permissions:** Wipe commands properly gated (MANAGE_GUILD as Discord checks, no bypass).
3. **Data isolation:** Wipe events can't be viewed/modified across tenant boundaries.
4. **Timer safety:** In-process reminder timer won't crash on malformed data or timezone edge cases.
5. **Discord intents:** GUILD_VOICE_STATES intent is legitimate and properly scoped.

## Deployment Phase

1. **Merged bot:** Push to main, Railway auto-deploys both bot + dashboard services.
2. **Command registration:** Bot's ready() event registers /wipe commands globally (same as existing commands).
3. **Feature bot decommission:** Stop the feature bot's Railway service (no active users).
4. **Token retirement:** Remove the feature bot's DISCORD_TOKEN from secrets; invite the main bot to the feature bot's guilds with the added GUILD_VOICE_STATES intent.

## Multi-Tenant Implication

The merged bot already supports multi-tenant (per-guild configuration). Wipe feature integrates seamlessly:
- Each guild gets its own WipeEvent rows (filtered by guild_id).
- Member role config (memberRoleId) lives in Guild tenants row (existing table).
- RSVP reactions are tied to specific WipeEvent (guild-scoped).
- Voice-presence reminders ping only members in that guild.

**No new tenant isolation logic needed** — inherit the main bot's existing tenant scoping.

## Pitfalls

1. **Language mismatch underestimated:** TypeScript → Rust is not a quick port. Expect 2-3x effort vs direct code paste. Time zone handling, state machine logic, and in-process timer all need Rust equivalents.

2. **Separate database assumption:** If both bots live in separate databases and you consolidate to one, data migration scripts need testing. Starting fresh (user's decision here) sidesteps this.

3. **Cutover with live users:** If the feature bot has active users, a staged cutover (run both in parallel, migrate guild config gradually) is needed. If already offline (commit says so), cutover is a simple switch.

4. **Intents not updated:** Adding GUILD_VOICE_STATES intent but forgetting to re-invite the bot to guilds means voice presence lookups won't work. Plan for bot re-invite post-merge.

5. **Command registration in merged bot:** If the merged bot's ready() doesn't call command registration, /wipe commands won't appear in Discord despite the code being there. Existing AuthList bot already registers commands; just add the new /wipe commands to the same registration call.

## Timeline Expectation

- **Audit:** 30-60 min (read-only discovery).
- **Design:** 30-60 min (decision doc).
- **Implementation:** 2-4 hours (port TS logic to Rust, add schema, wire commands).
- **Security review:** 30-60 min (verify isolation, permissions, input validation).
- **Deploy:** 15-30 min (build, deploy, smoke test).

**Total:** ~5-8 hours, heavily weighted toward implementation (language port).

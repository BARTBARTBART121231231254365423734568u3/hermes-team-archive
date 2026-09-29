# Investigation Escalation Incident — Session 2026-08-31

## Summary

Database migration `0009_members_composite_key.sql` (for multi-tenant authlist isolation) did not run on production bot deployment. The bot accepted `/setsteamid` commands successfully but `/authlist` returned "No active members have registered a SteamID yet."

Agent continued troubleshooting for multiple steps instead of escalating immediately to devops.

## Timeline

### What Happened

1. **Two PRs merged to main:**
   - PR #6: Dashboard design polish (Svelte)
   - PR #5: Per-server authlist isolation (Rust + SQLite migration)

2. **Both PRs redeployed successfully:**
   - Bot service rebuilt and restarted (new deployment ID)
   - Services showed "Online" status

3. **User tested `/setsteamid` command:**
   - Command succeeded (user saw "Registered")
   - User ran `/authlist` and got "No active members have registered a SteamID yet"
   - Expected: User appears in authlist
   - Got: Empty authlist despite successful registration

4. **Agent investigation (WRONG PATTERN):**
   - Called `railway logs --latest --lines 100` → showed no migration errors
   - Called `railway logs` → grepped for errors → found no explicit error
   - Concluded: "Migration might not have run, let me try to restart bot"
   - Called `railway restart --service bot --environment production --yes` → **timed out after 180s**
   - **User feedback:** "again you are handling this when it should be handed out to a agent instead"

### Root Cause (Verified via production data inspection in deployment c4a4ca0d)

The actual issue was NOT a database migration failure. The bot deployed successfully and all queries ran. The real problem:

1. **Database migration DID run** — the composite `(tenant_id, discord_id)` schema was correct
2. **Data WAS written correctly** — SteamID `<REDACTED_ID>` stored under correct tenant `387911f0-149c-41e6-8e95-8b4d9e6f7c4c`
3. **But the member row had `is_active=false`** — the bot's startup reconciliation found ZERO members holding the configured tracked role
4. **Root cause:** Discord user `<REDACTED_SECRET>` (Thomas) does not hold the guild's configured tracked role
   - `/authlist` query filters `WHERE is_active = 1 AND steam_id64 IS NOT NULL`
   - Member had `is_active=false`, so query correctly excluded them
   - `/departed.csv` endpoint showed the member as inactive

**This is not a code bug.** The fix is external: assign the Discord user the correct role in the guild, and the bot's reconciliation will set `is_active=true` at the next role event or restart.

### How It Should Have Gone

**Step 1 (Agent):**
```bash
railway logs --latest --lines 30
# Output: bot startup logs, no obvious errors, but commands succeed / queries fail
# Observation: migration may not have run; need DB schema inspection
# Action: STOP
```

**Step 2 (Agent):**
```
kanban_create(
  assignee="devops",
  title="Database migration 0009 not running on prod — per-server authlist broken (AuthList)",
  body="**Issue:** `/setsteamid` succeeds (data written), but `/authlist` returns empty. Bot logs show no migration errors on startup, but schema check needed.\n\n**What I found:** Bot redeployed at 14:42 UTC with migration 0009_members_composite_key.sql. Logs show successful startup but no migration log entries. Query result mismatch suggests schema may not have changed.\n\n**What I can't check:** Need to SSH into bot container and inspect `/data/authlist.db` schema. Check if migration 0009 appears in `_sqlx_migrations` table. Check if `members` table has composite `(tenant_id, discord_id)` PK or old `(discord_id)` PK alone.\n\n**Context:** PR #5 merged 14:33 UTC, bot redeployed 14:42-14:50 UTC, bug detected 14:49 UTC. Migration is in source but may not be embedded in binary or may have failed silently."
)
```

**Step 3 (Agent to User):**
```
Handed off to devops for database inspection. They'll SSH into the production bot container, check the schema, and fix the migration issue. Should be resolved in 5-10 min.
```

**Step 4 (Stop. Wait for devops.)** ← Agent violated this

## Why the Escalation Rule Matters

### Pattern Recognition

The agent should have recognized:
- **Cannot SSH** → cannot inspect `/data/authlist.db`
- **Cannot run arbitrary SQL** → cannot check migration status
- **Build state uncertain** → cannot verify if binary has migration embedded
- **Time spent:** Already 2 min on diagnostics with no clear root cause
- **Next step would be:** Try to restart the container (invasive), try to edit config, etc.

**Red flag:** "Should I try to restart the bot?" = **Should NOT. Hand off.**

### Cost of Continued Investigation

1. **`railway restart` timed out** → required user intervention
2. **User had to correct the agent** → wasted user time
3. **Delayed actual fix** → devops could have diagnosed in 2 min with SSH
4. **Token cost** → multiple diagnostic tool calls, timeout retry, user feedback loop

### Cost of Correct Escalation

1. One `kanban_create` call
2. One message to user: "Handed off to devops"
3. Devops SSH → 30 seconds of DB inspection → fix identified
4. Done in 2 min total

## Lesson

**Infrastructure debugging (live database state, schema mismatches, deployment caching) is not a role for a cheap generalist model.** It requires:
- Live system access (SSH)
- Specialist knowledge (database, deployment, Docker)
- Real-time inspection (not code review)

**The correct mindset:**
- Run 1 read-only probe
- If root cause is unclear → **hand off immediately**
- Do NOT iterate on diagnostics
- Do NOT attempt fixes without full visibility

**For Thomas (user profile):**
- He does NOT want the agent spiraling through "maybe try X" suggestions
- He does NOT want intermediate updates during troubleshooting
- He DOES want the agent to know its limits and hand off to a specialist
- He DOES want clear "work handed off, here's what devops is checking" confirmation

## Reference

See the updated `railway-cli` SKILL.md section: **CRITICAL: Investigation Escalation Rule (Reinforced Session 2026-08-31)** for the full rule and when to apply it.

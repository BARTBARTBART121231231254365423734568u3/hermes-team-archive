# BattleMetrics vs Steam Web API for Rust Activity Tracking

## Context
When building Discord bot features that track Rust player activity between wipes, there are two primary data sources. This reference clarifies when to use each, based on session data availability and infrastructure requirements.

## Industry Standard: BattleMetrics Sessions API

**Source:** BattleMetrics paid subscription servers provide real join/leave timestamps and session-level granularity.

**Advantages:**
- Exact wipe-to-wipe playtime delta: sum of all sessions between `wipe_start` and `now`
- Late-joiner backfill: retroactively includes sessions from before they registered the bot account
- Real session data, not approximation via lifetime counters
- Industry standard used by Hexaytron, RustOps, aleksilassila's tracker
- Leaderboard accuracy is inherent to the session model

**Requirements:**
- BattleMetrics API token (free account can request, token creation is gated to paid tiers)
- Server must have BattleMetrics session-history feature enabled (~$5/month per server, separate from the token cost)
- API endpoints: `/players?filter[search]={steam_id64}` and `/servers/{server_id}/relationships/sessions` with pagination

**Data caching strategy:**
- Store `baseline_timestamp` when wipe starts (not a snapshot of lifetime counter)
- Cache last `stopped_at` per player/server pair for incremental refresh
- Query all sessions where `start >= baseline_timestamp and start <= now`
- Upsert logic: close "ongoing" sessions (where `stop = NULL`) when later API calls report they disconnected
- TTL: 30-minute cached display, hourly background refresh for active wipe members

**Implementation schema (reference):**
```sql
-- When wipe is created:
INSERT INTO wipe_playtime_snapshots (wipe_event_id, discord_id, baseline_timestamp, cached_seconds, cache_refreshed_at)
VALUES (..., datetime('now'), NULL, NULL);

-- Hourly job or on /activity call:
SELECT SUM((julianday(COALESCE(stopped_at, 'now')) - julianday(started_at)) * 86400) as seconds_played
FROM battlemetrics_sessions_cache
WHERE server_id = ? AND battlemetrics_player_id = ?
  AND started_at >= (SELECT baseline_timestamp FROM wipe_playtime_snapshots WHERE ...)
  AND started_at <= datetime('now');
```

## Alternative: Steam Web API Snapshot

**Source:** Steam's `GetPlayerSummaries` returns lifetime Rust playtime counter (total hours ever played).

**Limitations:**
- Only provides total lifetime counter, no session granularity
- Wipe delta is approximation: `(current_total - baseline_total)` assumes no out-of-wipe play
- Late-joiner problem: if they register day 5 of a wipe, day 1-4 sessions are lost forever
- Cannot distinguish "played before wipe started" from "played during this wipe"
- Leaderboard is coarse approximation

**Advantages:**
- Simpler setup: just a Steam Web API key (free)
- No server-side subscription required
- Fast queries (one call per member per refresh)

**When to use:** Only if the server does NOT have BattleMetrics, OR if lifetime-total curiosity ("who has the most Rust hours ever?") is sufficient and wipe-specific tracking is nice-to-have, not core.

## Decision Tree

**Is wipe-specific activity tracking a core feature (leaderboard between wipes)?**
- **YES → Use BattleMetrics.** The user expects accurate "X hours THIS wipe," and late-joiners should auto-backfill. Accept the ~$5/month server cost and token setup requirement. Implement incremental session caching to avoid hammering the API.
- **NO → Use Steam.** Simpler setup, good enough for "who has played most ever." Accept that wipe deltas are approximations.

**Does the user already have a BattleMetrics subscription on their server?**
- **YES → Confirm session-history feature is enabled** (not just base BattleMetrics) and **proceed with BattleMetrics approach.**
- **NO → Ask user to confirm if $5/month cost is acceptable.** If not, fall back to Steam snapshot approach. If yes, create `/servertrack add <server_id>` command and initialize the token + database setup.

**Is the server already tracked on BattleMetrics?**
- **YES → Get server_id and proceed.**
- **NO → User must add it to BattleMetrics account first** (battlemetrics.com UI); bot can only query servers already indexed there.

## Deployment Pattern

**Feature gates:**
- New commands (`/activity`, `/servertrack`) only exist if `BATTLEMETRICS_API_TOKEN` env var is set
- Without the token, bot works normally; the activity feature is invisible
- Allows zero-downtime deploy and selective enablement per guild

**Rollout:**
1. Implement both tables + commands
2. Deploy to production with feature flag (token env var unset)
3. Once token is live, manually `/servertrack add <id>` per guild
4. Existing wipe events are unaffected; tracking starts at next `/wipe create`

## Pitfall: Free vs Paid BattleMetrics Accounts

BattleMetrics requires a **paid subscription** to create personal access tokens and query session history. Free accounts cannot use the API. If the user has a free account:

1. Confirm account status at battlemetrics.com/developers
2. If free, explain the cost (token creation + server subscription) and confirm user wants to proceed
3. Do NOT build a half-featured "wait for user to upgrade" flow — either use Steam, or block with a clear prerequisite

## Testing

Once token is set and server is configured:

```bash
# Verify player lookup
curl -H "Authorization: Bearer $BATTLEMETRICS_API_TOKEN" \
  "https://api.battlemetrics.com/players?filter[search]=<steam_id64>"

# Verify session query (replace IDs)
curl -H "Authorization: Bearer $BATTLEMETRICS_API_TOKEN" \
  "https://api.battlemetrics.com/servers/<server_id>/relationships/sessions?filter[players]=<bm_player_id>"
```

If these return data (not 403/401), the integration is live.

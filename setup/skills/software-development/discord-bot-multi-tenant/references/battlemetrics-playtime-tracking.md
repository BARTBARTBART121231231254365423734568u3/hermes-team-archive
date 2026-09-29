# BattleMetrics API Integration for Rust Playtime Tracking

**Context:** Standard Rust Discord bots (Hexaytron, RustOps, aleksilassila's tracker) use BattleMetrics API to track player playtime, not the Steam Web API.

**Key difference:** BattleMetrics provides **actual session data** (join/leave timestamps per server), not just lifetime playtime counters. This enables accurate wipe-based leaderboards and activity tracking.

## When to Use BattleMetrics vs Steam Web API

| Use case | BattleMetrics | Steam Web API |
|---|---|---|
| **Total lifetime Rust hours** | ❌ No direct data | ✅ Yes (`/GetPlayerSummaries`) |
| **Playtime this wipe** | ✅ Session data (join/leave times) | ❌ Approximation only (snapshot delta) |
| **Exact join/leave times** | ✅ Per-session detail | ❌ Not available |
| **Per-server activity** | ✅ Filterable by server | ❌ Global total only |
| **Cost** | Free (basic), $5/month (premium for sessions) | Free |
| **Privacy gaps** | Doesn't track servers on BattleMetrics' anonymized list | Doesn't track private Steam profiles |

**TL;DR:** For wipe-based leaderboards and session tracking, BattleMetrics is the standard. For one-time "has this player ever played Rust" checks, Steam is fine.

## API Endpoints

### Authentication

All BattleMetrics API calls require an API token in the `Authorization` header:

```bash
Authorization: Bearer YOUR_API_TOKEN
```

Get your token at: https://www.battlemetrics.com/developers (create an API token from your account dashboard).

### 1. Resolve Steam ID to BattleMetrics Player ID

**Endpoint:** `GET /api/players?filter[steamID]=STEAM_ID_64`

**Why:** BattleMetrics uses its own player IDs internally. You must convert Steam ID → BattleMetrics ID once, then cache it.

**Example:**

```bash
curl -s 'https://api.battlemetrics.com/api/players?filter[steamID]=<REDACTED_ID>' \
  -H 'Authorization: Bearer YOUR_TOKEN' | jq '.data[0].id'
# Output: "123456789"
```

**Cache this result** — the mapping is stable and doesn't change.

### 2. Get Player's Sessions on a Server

**Endpoint:** `GET /api/servers/{serverId}/players/{battlemetrics_player_id}`

**Returns:** Current online status and last-seen time.

```bash
curl -s 'https://api.battlemetrics.com/api/servers/12345678/players/123456789' \
  -H 'Authorization: Bearer YOUR_TOKEN' | jq
```

**Response snippet:**

```json
{
  "data": {
    "id": "12345678-123456789",
    "attributes": {
      "status": "online",  // or "offline"
      "firstSeen": "2026-09-01T14:30:00Z",
      "lastSeen": "2026-09-02T18:45:00Z"
    }
  }
}
```

### 3. Get All Sessions for a Player (Premium API)

**Endpoint:** `GET /api/players/{battlemetrics_player_id}/sessions?filter[server]={serverId}`

**Requires:** Premium API tier ($5/month).

**Returns:** Complete session history with exact join/leave timestamps.

```json
{
  "data": [
    {
      "id": "session-1",
      "attributes": {
        "server": { "id": "12345678", "name": "My Rust Server" },
        "start": "2026-09-01T14:30:00Z",
        "stop": "2026-09-01T17:45:00Z",
        "duration": 12300  // seconds
      }
    },
    { /* more sessions */ }
  ]
}
```

### 4. Get Server Details

**Endpoint:** `GET /api/servers/{serverId}`

**Returns:** Server name, map, last wipe timestamp, etc.

```bash
curl -s 'https://api.battlemetrics.com/api/servers/12345678' \
  -H 'Authorization: Bearer YOUR_TOKEN' | jq '.data.attributes'
```

## Rate Limits

- **Free tier:** 60 requests/minute
- **Premium tier:** Higher limits, but check docs for exact numbers
- **Recommended strategy:** Cache player IDs (never expires), cache session data for 15 minutes, implement exponential backoff on 429 responses

## Implementation Pattern (Rust)

### 1. Add BattleMetrics Client to State

```rust
use reqwest::Client;
use serde::{Deserialize, Serialize};

pub struct BattleMetricsClient {
    http: Client,
    api_token: String,
    base_url: String,
}

impl BattleMetricsClient {
    pub fn new(api_token: String) -> Self {
        Self {
            http: Client::new(),
            api_token,
            base_url: "https://api.battlemetrics.com".to_string(),
        }
    }

    async fn get(&self, path: &str) -> anyhow::Result<String> {
        let url = format!("{}{}", self.base_url, path);
        let response = self
            .http
            .get(&url)
            .header("Authorization", format!("Bearer {}", self.api_token))
            .send()
            .await?;
        Ok(response.text().await?)
    }
}
```

### 2. Resolve Steam ID to BattleMetrics ID

```rust
#[derive(Deserialize)]
struct PlayerResponse {
    data: Vec<PlayerData>,
}

#[derive(Deserialize, Serialize)]
struct PlayerData {
    id: String,
}

impl BattleMetricsClient {
    pub async fn resolve_steam_id_to_bm_id(&self, steam_id64: &str) -> anyhow::Result<Option<String>> {
        let path = format!("/api/players?filter[steamID]={}", steam_id64);
        let response = self.get(&path).await?;
        let parsed: PlayerResponse = serde_json::from_str(&response)?;
        Ok(parsed.data.first().map(|p| p.id.clone()))
    }
}
```

### 3. Get Sessions Since Wipe Start (Premium)

```rust
#[derive(Deserialize)]
struct SessionsResponse {
    data: Vec<SessionData>,
}

#[derive(Deserialize)]
struct SessionData {
    attributes: SessionAttributes,
}

#[derive(Deserialize)]
struct SessionAttributes {
    start: String,  // ISO8601
    stop: Option<String>,  // ISO8601, None if still online
    duration: Option<i64>,  // seconds
}

impl BattleMetricsClient {
    pub async fn get_playtime_since(
        &self,
        bm_player_id: &str,
        server_id: &str,
        since: &str,  // ISO8601 timestamp (wipe start)
    ) -> anyhow::Result<i64> {
        let path = format!(
            "/api/players/{}/sessions?filter[server]={}",
            bm_player_id, server_id
        );
        let response = self.get(&path).await?;
        let parsed: SessionsResponse = serde_json::from_str(&response)?;

        // Sum all sessions where start >= wipe_start
        let wipe_start = chrono::DateTime::parse_from_rfc3339(since)?
            .with_timezone(&chrono::Utc);

        let total_seconds: i64 = parsed
            .data
            .iter()
            .filter_map(|s| {
                let session_start =
                    chrono::DateTime::parse_from_rfc3339(&s.attributes.start)
                        .ok()?
                        .with_timezone(&chrono::Utc);
                if session_start >= wipe_start {
                    s.attributes.duration
                } else {
                    None
                }
            })
            .sum();

        Ok(total_seconds)
    }
}
```

### 4. Store in wipe_playtime_snapshots

When `/wipe create` fires:

```rust
// For each member with a Steam ID:
if let Ok(Some(bm_id)) = bm_client.resolve_steam_id_to_bm_id(steam_id64).await {
    if let Ok(playtime_seconds) = bm_client
        .get_playtime_since(&bm_id, &server_id, &wipe_start_iso)
        .await
    {
        let now = Utc::now().to_rfc3339();
        sqlx::query!(
            "INSERT INTO wipe_playtime_snapshots
                (wipe_event_id, tenant_id, discord_id, steam_id64, bm_player_id, wipe_start_timestamp, last_fetched_playtime_seconds, last_fetched_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
             ON CONFLICT (wipe_event_id, discord_id) DO NOTHING",
            wipe_event_id, tenant_id, discord_id, steam_id64, bm_id, wipe_start_timestamp, playtime_seconds, now
        )
        .execute(&pool)
        .await?;
    }
}
```

## Updated Schema

Replace the `baseline_minutes` approach with BattleMetrics fields:

```sql
CREATE TABLE wipe_playtime_snapshots (
    wipe_event_id        TEXT NOT NULL REFERENCES wipe_events(id) ON DELETE CASCADE,
    tenant_id            TEXT NOT NULL,
    discord_id           TEXT NOT NULL,
    steam_id64           TEXT NOT NULL,
    bm_player_id         TEXT,  -- BattleMetrics ID (stable cache)
    wipe_start_timestamp TEXT NOT NULL,  -- ISO8601, when wipe created
    captured_at          TEXT NOT NULL,  -- ISO8601, when baseline recorded
    last_fetched_playtime_seconds INTEGER,  -- most recent playtime fetch
    last_fetched_at      TEXT,  -- when last_fetched was updated
    PRIMARY KEY (wipe_event_id, discord_id)
);
```

## `/activity` Query Logic

Instead of `delta = current - baseline`:

```rust
// For each member's row in wipe_playtime_snapshots:
let playtime_this_wipe = bm_client
    .get_playtime_since(&row.bm_player_id, &server_id, &row.wipe_start_timestamp)
    .await?;

// Cache it
sqlx::query!(
    "UPDATE wipe_playtime_snapshots SET last_fetched_playtime_seconds = ?1, last_fetched_at = ?2 WHERE wipe_event_id = ?3 AND discord_id = ?4",
    playtime_this_wipe,
    Utc::now().to_rfc3339(),
    wipe_event_id,
    discord_id
)
.execute(&pool)
.await?;

// Sort and display
let hours = playtime_this_wipe as f64 / 3600.0;
embed.field(format!("{}. <@{}>", rank, discord_id), format!("{:.1}h", hours), false);
```

## Caching Strategy

1. **BattleMetrics Player ID:** Cache indefinitely in `bm_player_id` column. Never re-resolve unless the Steam ID changes.
2. **Playtime for current wipe:** Cache for 15 minutes (same as Steam snapshot strategy). Store in `last_fetched_playtime_seconds` + `last_fetched_at`.
3. **Rate limit handling:** On 429 response, exponential backoff (1s, 2s, 4s, 8s, etc.) up to 60s max.

## Testing

1. **API token validity:** `curl -s https://api.battlemetrics.com/api/servers -H 'Authorization: Bearer YOUR_TOKEN'` should return 200 + server list, not 401.
2. **Steam ID resolution:** Pick a known Rust player's Steam ID, call the resolution endpoint, confirm it returns a BattleMetrics ID.
3. **Session data:** For that player and a Rust server ID, call the sessions endpoint (premium API), confirm you get session timestamps.
4. **Wipe start filtering:** Manually compute "sum of sessions where start >= wipe_start_time", verify it matches bot's computed playtime.

## Common Issues

- **401 Unauthorized:** API token is invalid or expired. Regenerate at battlemetrics.com/developers.
- **404 for sessions endpoint:** Server ID might be wrong, or you're using the free API tier (premium required for `/sessions`).
- **Slow responses (>5s):** BattleMetrics can be slow during peak times. Increase client timeout to 10s+ and implement aggressive caching.
- **Session data starts 2026-09-01 but wipe was 2026-09-02:** BattleMetrics backlog lag — sessions are logged with a ~1-hour delay. For real-time wipe leaderboards, this is acceptable (users see mostly-correct rankings, not live-to-the-second). Document this caveat in `/activity` output.

## References

- BattleMetrics API docs: https://www.battlemetrics.com/developers/documentation
- Industry bots using this pattern: Hexaytron (top.gg), RustOps (GitHub), aleksilassila's tracker (GitHub)

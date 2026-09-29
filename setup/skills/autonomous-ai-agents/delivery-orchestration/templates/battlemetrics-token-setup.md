# BattleMetrics API Token Setup Checklist

Use this when the user needs to create a BattleMetrics API token for AuthList or similar Rust tracking bots.

## Prerequisites

- BattleMetrics account (free account OK for creation; token creation is gated to **paid subscribers**)
- If user has free account, they must upgrade to a paid tier first or confirm willingness to pay
- Server already added to BattleMetrics (go to battlemetrics.com, find your server by IP, confirm it's indexed)
- Session-history data available on the server (requires ~$5/month BattleMetrics+ feature enabled on the server itself, not just the account)

## Setup Flow

### Step 1: Confirm Subscriber Status

Ask user:
> "Do you have a **paid BattleMetrics subscription**? (Free accounts cannot create API tokens.)"

If NO:
- User must upgrade at battlemetrics.com/account → Subscription Plans
- Recommend $5/month minimum tier
- Pause until upgrade is live

If YES:
- Proceed

### Step 2: Navigate to Token Creation

1. Go to https://www.battlemetrics.com/developers
2. Log in if needed
3. Click "New Token" (under Personal Access Tokens section)
4. Fill in:
   - **Note:** `authlist-bot-wipe-tracking` (or similar identifier)
   - **Permissions:** Check the following scopes (minimal required):
     - `Servers` → Read/Query server data
     - (Session-level queries are typically open API; check if any permission blocking occurs)

### Step 3: Token Creation & Copy

Once form is filled, click **"Create Token"**.

The token will be displayed once. Copy it immediately to a secure location (don't paste in chat; instead:
- Store in Bitwarden / password manager
- Set as Railway env var: `BATTLEMETRICS_API_TOKEN=<token>`
- **Do NOT commit to git or paste in Hermes chat**

### Step 4: Verify Token Works

Test the token with a curl command:

```bash
# Replace <steam_id64> and <server_id> with real values
curl -H "Authorization: Bearer $BATTLEMETRICS_API_TOKEN" \
  "https://api.battlemetrics.com/players?filter[search]=<steam_id64>"
```

Expected: JSON response with player data or empty array (not 401 Unauthorized).

If 401 or 403, the token is invalid or expired.

### Step 5: Set Environment Variable

Set `BATTLEMETRICS_API_TOKEN` on Railway:

```bash
unset RAILWAY_PROJECT_ID RAILWAY_SERVICE_ID RAILWAY_ENVIRONMENT_ID
railway variable set BATTLEMETRICS_API_TOKEN="<token>" \
  --project authlist-bot \
  --service bot \
  --environment production
```

Then redeploy or wait for the next push to activate it.

### Step 6: Confirm Server Integration

The bot needs to know which BattleMetrics server IDs to query. Use `/servertrack` command:

```
/servertrack add <battlemetrics_server_id> [optional_label]
```

To find the server ID, go to battlemetrics.com, search for your server, and copy the numeric ID from the URL (`servers/<ID>`/...).

## Troubleshooting

| Issue | Fix |
|---|---|
| "Free account, cannot create token" | User must upgrade to paid BattleMetrics subscription first |
| Token works locally but 401 in production | Token may not be set as env var; re-check `railway variable list` |
| Sessions endpoint returns empty | Server may not have session-history feature enabled; check battlemetrics.com/servers/<id>/settings |
| Curl works but `/activity` command 404s | Feature flag may be off; check `BATTLEMETRICS_API_TOKEN` is actually set in running bot (not just env var) |

## Gotchas

- **One-time visibility:** Token is only shown once during creation. If missed, regenerate or revoke and create new.
- **Paid tier required:** Cannot emphasize enough — free BattleMetrics accounts cannot create API tokens. User must have an active subscription.
- **Server subscription separate:** The account-level subscription and the per-server session-history feature are different costs. Both needed for full tracking.
- **Permissions scoping:** If future API calls return 403 Forbidden despite valid token, the permissions on the token may be too restrictive. Create a new, less-scoped token (or contact BattleMetrics support).

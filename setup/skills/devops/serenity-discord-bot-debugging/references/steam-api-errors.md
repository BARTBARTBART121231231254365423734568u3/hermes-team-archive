# Steam Web API Error Reference

## HTTP 403 Forbidden

**Most common:** Invalid, expired, or revoked API key.

### Diagnosis

1. Check bot logs for the exact URL and key being used:
   ```
   HTTP status client error (403 Forbidden) for url
   https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=8590A462BC7425EC05D507E89A4FB94E&steamids=<REDACTED_ID>
   ```

2. Extract the key and test independently:
   ```bash
   curl "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=8590A462BC7425EC05D507E89A4FB94E&steamids=<REDACTED_ID>"
   ```

3. If curl also returns 403, the key is invalid. If curl succeeds, the bot's request is malformed.

### Fix

1. User regenerates Steam Web API key:
   - Go to https://steamcommunity.com/dev/apikey
   - Log in with Steam account
   - Click **"Register New API Key"** (or "View your current API key")
   - Copy the key

2. Update bot's configuration:
   - If key is stored in Railway env var: `railway variable set STEAM_WEB_API_KEY="<newkey>" --project <proj> --service bot --environment production`
   - If stored in database: update `tenant_settings.steam_web_api_key` directly
   - **If using encryption-at-rest:** the key in DB is encrypted; migration script must decrypt old key, encrypt new key with same encryption key

3. Redeploy bot:
   ```bash
   railway redeploy --project authlist-bot --service bot --environment production --yes
   ```

4. Verify in logs within 30 seconds: logs should show bot restarting and `logged in as` message.

5. Test the command again in Discord.

## HTTP 400 Bad Request

Malformed request — wrong parameter names, missing required fields, or invalid steamid format.

### Common causes

- `steamids` parameter is not a valid 17-digit Steam ID (e.g., missing leading '7')
- Query parameter names are spelled wrong (`steamid` instead of `steamids`)
- User provided a Steam vanity URL instead of numeric ID (bot must convert it first)

### Fix

1. Validate input before calling API:
   ```rust
   // Verify steamid is 17 digits
   if steam_id.len() != 17 || !steam_id.chars().all(|c| c.is_ascii_digit()) {
       return Err(anyhow!("Invalid Steam ID format"));
   }
   ```

2. Check parameter names in request match Steam API docs exactly.

## HTTP 500 Internal Server Error

Steam API is down or experiencing issues (rare). Usually transient.

### Fix

- Retry after 30 seconds
- Check https://steamstat.us for Steam service status
- If persistent, file issue with Steam support or check Steam Community forums

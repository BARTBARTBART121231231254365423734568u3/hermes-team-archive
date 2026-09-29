---
name: discord-bot-multi-tenant
description: Multi-tenant Discord bot with per-guild config.
tags: [Discord, Serenity, Rust, Multi-Tenant, Bot Architecture]
---

# Multi-Tenant Discord Bot Pattern (Serenity/Rust)

**Scope:** Rust Discord bots using Serenity library that need to support multiple Discord servers (guilds) with independent configuration per server. Each guild has its own settings, roles, channels, and permissions.

## Core Pattern

### 1. Database Schema

Store tenants (Discord servers) and their configuration:

```sql
CREATE TABLE tenants (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  guild_id TEXT UNIQUE NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tenant_settings (
  tenant_id TEXT PRIMARY KEY UNIQUE,
  guild_id TEXT NOT NULL,
  tracked_role_id TEXT NOT NULL,
  admin_role_id TEXT,
  log_channel_id TEXT NOT NULL,
  FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);
```

### 2. Models & State

Define Rust structs for tenants and settings:

```rust
pub struct Tenant {
    pub id: String,
    pub name: String,
    pub guild_id: GuildId,
    pub active: bool,
}

pub struct TenantSettings {
    pub tenant_id: String,
    pub guild_id: GuildId,
    pub tracked_role_id: RoleId,
    pub admin_role_id: Option<RoleId>,
    pub log_channel_id: ChannelId,
}

pub struct AppState {
    pub db: SqlitePool,
    pub guild_id: GuildId,           // Will be overridden per-command
    pub tracked_role_id: RoleId,     // Will be overridden per-command
    pub admin_role_id: Option<RoleId>,
    pub log_channel_id: ChannelId,
    // ... other fields
}
```

Initialize AppState with a "default" guild for startup, but override it per command.

### 3. Command Registration

**Register commands globally**, not per-guild. This makes them available in all servers the bot joins:

```rust
pub async fn register(ctx: &Context, state: &AppState) -> anyhow::Result<()> {
    let commands: Vec<CreateCommand> = vec![
        command1(),
        command2(),
        // ...
    ];

    // Register globally, not per guild
    serenity::all::Command::set_global_commands(&ctx.http, commands).await?;
    tracing::info!("registered {} global commands", commands.len());
    Ok(())
}
```

Call this in the `ready()` event handler so commands are registered on bot startup.

### 4. Command Dispatcher with Dynamic Tenant Lookup

**Key insight:** Don't use the AppState's hardcoded guild_id. Instead:
1. Extract guild_id from the incoming CommandInteraction
2. Look up the tenant by guild_id
3. Load the tenant's settings from the database
4. Construct a **tenant-specific AppState** with the correct settings
5. Pass the tenant-specific state to the command handler

```rust
pub async fn dispatch(ctx: &Context, command: &CommandInteraction, state: &AppState) -> anyhow::Result<()> {
    // Get guild ID from the command
    let guild_id = match command.guild_id {
        Some(gid) => gid.to_string(),
        None => {
            tracing::warn!("command received outside of guild");
            return Ok(());
        }
    };

    // Look up tenant for this guild
    let tenant = match crate::db::get_tenant_by_guild_id(&state.db, &guild_id).await {
        Ok(Some(t)) => t,
        Ok(None) => {
            tracing::warn!("no tenant configured for guild {guild_id}");
            return Ok(());
        }
        Err(e) => {
            tracing::error!("failed to load tenant for guild {guild_id}: {e}");
            return Ok(());
        }
    };

    // Load tenant settings
    let settings = match crate::db::get_tenant_settings(&state.db, &tenant.id).await {
        Ok(s) => s,
        Err(e) => {
            tracing::error!("failed to load settings for tenant {}: {e}", tenant.id);
            return Ok(());
        }
    };

    // Create tenant-specific state
    let tenant_state = crate::state::AppState {
        db: state.db.clone(),
        steam: state.steam.clone(),
        guild_id: settings.guild_id,
        tracked_role_id: settings.tracked_role_id,
        admin_role_id: settings.admin_role_id,
        log_channel_id: settings.log_channel_id,
        // ... copy other fields
    };

    // Dispatch to the actual command handler with tenant-specific state
    match command.data.name.as_str() {
        "command1" => command1::run(ctx, command, &tenant_state).await,
        "command2" => command2::run(ctx, command, &tenant_state).await,
        // ...
        other => {
            tracing::warn!("received unknown command: {other}");
            Ok(())
        }
    }
}
```

### 5. Event Handlers (Member Updates, Removals)

Same pattern for non-command events: look up the tenant by guild_id, then construct tenant-specific state before processing:

```rust
async fn guild_member_update(
    &self,
    ctx: Context,
    new: Option<Member>,
) {
    let Some(member) = new else { return };

    // Look up tenant for this member's guild
    match crate::db::get_tenant_by_guild_id(&self.state.db, &member.guild_id.to_string()).await {
        Ok(Some(tenant)) => {
            // Load settings and construct tenant state
            // Then process the member event with that state
        }
        _ => {
            // Guild not registered, ignore
        }
    }
}
```

## Deployment Checklist

- [ ] Bot registered as global commands (not per-guild)
- [ ] `ready()` event calls `commands::register()`
- [ ] Command dispatcher looks up guild_id from CommandInteraction
- [ ] Tenant lookup queries database by guild_id
- [ ] Tenant-specific state constructed before command execution
- [ ] Event handlers (member update, role change) also use dynamic lookup
- [ ] **Bot invited with `applications.commands` scope** (critical: without it, commands won't register)
- [ ] Test: Create 2+ servers, add bot to each, verify commands work independently per server

### OAuth Invite URL

Generate the invite link with both `bot` and `applications.commands` scopes:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=268435456&scope=bot%20applications.commands
```

Without `applications.commands`, the bot can join servers but cannot register slash commands, and the `ready()` event's call to `Command::set_global_commands()` will silently fail with no error logged.

### Ready Event Handler

Make sure your `ready()` implementation explicitly calls `commands::register()`:

```rust
#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, ready: Ready) {
        tracing::warn!("🚀 READY EVENT FIRING");  // Use WARN level for visibility
        tracing::info!("logged in as {}", ready.user.name);
        
        // Load tenants and log configuration
        // ...
        
        // CRITICAL: Register commands on startup
        if let Err(e) = commands::register(&ctx, &self.state).await {
            tracing::error!("❌ failed to register commands: {e}");
        } else {
            tracing::warn!("✅ commands registered successfully");
        }
    }
}
```

**Verbose logging is CRITICAL for debugging.** Use `warn!` level (not `info!`) so logs aren't filtered out. Log entry and exit of `ready()` and `commands::register()`.

If you see the bot log in but don't see registration logs, check:
1. Is `ready()` actually being called? (Log at the start of the function with WARN level)
2. Does the bot have the `applications.commands` OAuth scope?
3. Has the bot been re-invited after adding the scope?
4. Is the platform (Railway, Heroku, etc.) actually redeploying? (See **Deployment Delays** below)

### Deployment Delays & Cache Issues

When deploying to containerized platforms:
- **Auto-deploy may stall:** Even after `git push`, the new container might not start. Use `railway redeploy --yes` or equivalent to force it.
- **Logs are buffered:** Log timestamps may be out of order or delayed. Logs from the old container may linger. Wait 2+ minutes and check for NEW logs with fresh timestamps.
- **Silent failures:** Registration calls can silently fail if the bot lacks `applications.commands` scope. No error is logged, just no output. Always add explicit logging around `set_global_commands()` call.

**Workaround during debugging:** Add prefix commands (e.g., `!whoami`, `!guide`) as an immediate test while slash command registration issues are resolved. Prefix commands don't require registration and respond instantly (see **Prefix Commands Fallback** below).

## Pitfalls

1. **Commands only registered to one guild:** If you call `guild_id.set_commands()` instead of `Command::set_global_commands()`, commands won't appear in other guilds. Use global registration.

2. **Hardcoded state in handlers:** If you pass `&self.state` directly to all handlers, they'll all use the original AppState's guild_id. Instead, construct a new AppState with the current guild's settings.

3. **Guild ID not extracted from CommandInteraction:** Don't assume `command.guild_id` is always present. Check it and early-return if it's None (commands in DMs would fail).

4. **Forgetting to call `commands::register()` in `ready()`:** The `ready()` event handler must explicitly call command registration. Just having the function defined is not enough — it won't be called unless you wire it into the event handler.

5. **Missing `applications.commands` OAuth scope:** If the bot can't register commands despite `ready()` firing, check the Discord OAuth invite URL. The scope must include `applications.commands` (not just `bot`). Invite the bot again with the corrected URL after updating the scope.

6. **Database lookup errors logged but ignored:** If tenant lookup fails, make sure you log it and early-return rather than panicking or using a default. Multi-tenant means graceful degradation is critical.

7. **Deployment delays masking registration failures:** When deploying to containerized platforms (Railway, Heroku, etc.), the bot may appear to be running before command registration finishes. Log verbosely at the start and end of `ready()` and `commands::register()`. If logs show the bot connected but no registration logs appear, the function wasn't called — check (4) and (5) above.

8. **Testing in a guild that's not configured:** If the bot is registered for Guild A but you test in Guild B, commands won't appear in Guild B even though the bot is present there. The dispatch function looks up the guild ID in the database, finds no tenant configured for it, and ignores the command. Always test in the guild you registered the bot for, or register the bot for the test guild via the dashboard/API.

9. **Using slash commands when `applications.commands` registration fails silently:** Command registration can fail silently with no error logged if OAuth scope is wrong. As a workaround during debugging, implement prefix commands (`!whoami`, `!guide`, etc.) as an immediate test. Prefix commands don't require registration and will work immediately, allowing you to verify the bot is receiving messages while you debug slash command setup.

## Testing

1. **Single guild:** Verify bot works in one server (existing single-tenant test).
2. **Multiple guilds:** Add bot to 2+ servers. Run same commands in each. Verify each server's settings are respected independently.
3. **New server joins:** After bot is running, have it join a new server (via invite link). Don't restart the bot. Commands should work in the new guild immediately because of dynamic lookup.
4. **Settings isolation:** Change a setting in Guild A's tenant_settings, verify it doesn't affect Guild B.
5. **Test in the correct configured guild:** If you register the bot for Guild A but test commands in Guild B, commands won't work — the bot doesn't know about Guild B's configuration. Either:
   - Test in the guild you configured the bot for (check tenant_settings.guild_id in the database)
   - OR add Guild B via the dashboard/API and re-invite the bot to it

## Dashboard/Admin API Integration

When building an admin dashboard for the multi-tenant bot:

**Problem:** Dashboard makes API calls to `/api/tenants`, `/api/settings`, etc., but frontend auth tokens don't match bot's admin token scheme.

**Solution:** Store the admin API token (hardcoded or env-based) in the frontend auth store and include it in ALL API fetch() calls:

```svelte
// In auth store:
export const adminApi<REDACTED_SECRET>'; // Or from env

// In API calls:
const response = await fetch(`${apiBase}/api/tenants`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${adminApiToken}`, // Always include this
  },
  body: JSON.stringify(payload)
});
```

If API returns 401, **do NOT silently fallback** — check if the token is actually being sent. Common mistake: forgetting the Authorization header entirely, causing 401 errors that look like auth failure but are really just missing headers.

**Testing:** After setting the admin token, curl-test the API immediately:
```bash
<REDACTED_SECRET>"
curl -s https://bot-api.railway.app/api/tenants \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nHTTP: %{http_code}\n"
```
Must return 200 + JSON, not 401. If 401, the token is invalid or not being sent.

## Troubleshooting

If slash commands don't appear in Discord despite deploying code:
- See **references/slash-commands-troubleshooting.md** for diagnosis steps
- Common issue: bot missing `applications.commands` OAuth scope (re-invite with correct scopes)
- Second common issue: `ready()` event handler not calling `commands::register()`
- **Fallback:** See **references/prefix-commands-fallback.md** for using prefix commands (`!cmd`) while debugging slash command issues

If dashboard API calls return 401:
- Verify Authorization header is being sent (check browser DevTools Network tab)
- Curl-test the endpoint with the token to confirm token is valid
- Confirm token is the admin token, not a per-tenant token (admin token should work on `/api/tenants`)

## Authentication & Security

When adding a dashboard or admin API that authenticates to the bot:
- **Never store secrets as plaintext** — Use AES-256-GCM encryption for sensitive fields (discord_token, api_keys, etc.) at the application layer with random nonces per message. See **references/multi-tenant-auth-security.md**.
- **Scope OAuth sessions by tenant** — OAuth login should grant access only to the tenant (guild) the user is a member of, never blanket Admin. See **references/multi-tenant-auth-security.md** for the session-scoping pattern.
- **Verify OAuth CSRF state** — State tokens must be generated on `/oauth/login`, stored server-side, and validated on callback to prevent hijacking. See **references/multi-tenant-auth-security.md**.
- **Test each pattern independently** — Encryption round-trip tests, OAuth session scoping tests (one session sees only its tenant's data), CSRF state validation tests. See **references/multi-tenant-auth-security.md** for test scenarios.

## See Also

- `references/battlemetrics-playtime-tracking.md` — BattleMetrics API integration for Rust playtime tracking (session-based, not Steam snapshots; wipe leaderboards; caching strategy; cost/premium tiers)
- `references/railway-monorepo-deployment.md` — Debugging CORS lag after deployment, monorepo build configuration, forcing Railway rebuilds (Aug 30, 2026)
- `references/dashboard-server-deletion-modal.md` — Modal component + backend CASCADE DELETE for removing servers from dashboard (Aug 30, 2026)
- `references/multi-tenant-auth-security.md` — Encryption, OAuth scoping, CSRF state validation (three critical vulnerabilities and fixes)
- `references/prefix-commands-fallback.md` — Using prefix commands while debugging slash command registration
- `references/slash-commands-troubleshooting.md` — Diagnosing why slash commands don't appear in Discord

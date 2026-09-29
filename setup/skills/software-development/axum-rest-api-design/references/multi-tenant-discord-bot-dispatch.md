# Multi-Tenant Discord Bot Command Dispatch Pattern

**Session:** AuthList Aug 29, 2026  
**Problem:** Discord bot couldn't handle commands from multiple servers (guilds) when each guild has its own configuration (roles, channels, admin settings).  
**Solution:** Dynamic tenant lookup in command dispatcher + global command registration  

## The Issue

### Single-Guild Bot (Old Approach)

Bots typically store guild configuration in `AppState`:

```rust
pub struct AppState {
    pub guild_id: GuildId,
    pub tracked_role_id: RoleId,
    pub admin_role_id: Option<RoleId>,
    pub log_channel_id: ChannelId,
}
```

Commands look up settings from shared state:

```rust
async fn whoami_command(ctx: &Context, command: &CommandInteraction, state: &AppState) {
    let role = state.tracked_role_id;  // Always the SAME role for all guilds
    // Check if user has this role...
}
```

**Problem:** If bot joins multiple guilds, every guild's commands check the same hardcoded roles/channels. Guild 2's members are checked against Guild 1's roles. Results are wrong or commands fail silently.

### Multi-Tenant Database Schema (New Approach)

```sql
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    guild_id TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE tenant_settings (
    tenant_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    tracked_role_id TEXT NOT NULL,
    admin_role_id TEXT,
    log_channel_id TEXT NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

Now each guild has its own settings row. The challenge: how does the bot know which settings to use for each command?

## Solution: Dynamic Tenant Lookup in Dispatcher

### 1. Register Commands Globally (Not Per-Guild)

**Bad: Only works in one guild**
```rust
state.guild_id.set_commands(&ctx.http, commands).await?
```

**Good: Works in all guilds**
```rust
serenity::all::Command::set_global_commands(&ctx.http, vec![
    setsteamid::command(),
    whoami::command(),
    // ... all commands
]).await?
```

Global commands take ~15 minutes to propagate in Discord but work in every guild the bot joins.

### 2. Look Up Tenant for This Guild

When a command is executed, the `CommandInteraction` includes the guild_id:

```rust
pub async fn dispatch(ctx: &Context, command: &CommandInteraction, state: &AppState) {
    // 1. Extract guild_id from interaction
    let guild_id = match command.guild_id {
        Some(gid) => gid.to_string(),
        None => return,  // Ignore DMs
    };

    // 2. Look up tenant for this guild
    let tenant = match crate::db::get_tenant_by_guild_id(&state.db, &guild_id).await {
        Ok(Some(t)) => t,
        Ok(None) => {
            tracing::warn!("guild {guild_id} not registered");
            return;  // Guild not in our system
        }
        Err(e) => {
            tracing::error!("DB error: {e}");
            return;  // Database error, skip
        }
    };

    // 3. Load this tenant's settings
    let settings = crate::db::get_tenant_settings(&state.db, &tenant.id)
        .await
        .ok()?;

    // 4. Create guild-specific AppState
    let guild_state = AppState {
        guild_id: settings.guild_id,        // THIS guild
        tracked_role_id: settings.tracked_role_id,  // THIS guild's role
        admin_role_id: settings.admin_role_id,
        log_channel_id: settings.log_channel_id,
        // ... other fields
    };

    // 5. Dispatch with guild-specific state
    match command.data.name.as_str() {
        "setsteamid" => setsteamid::run(ctx, command, &guild_state).await,
        "whoami" => whoami::run(ctx, command, &guild_state).await,
        // ... all commands now use guild_state
        _ => {}
    }
}
```

### 3. Commands Work With Guild-Specific State

Since `guild_state` is created fresh for each command, every command handler automatically uses the correct settings:

```rust
async fn whoami_command(ctx: &Context, command: &CommandInteraction, state: &AppState) {
    // state.tracked_role_id is NOW the correct role for THIS guild
    let role = state.tracked_role_id;
    
    // Look up member and check if they have this role
    let member = command.member.as_ref().unwrap();
    if member.roles.contains(&role) {
        // Show their Steam ID
    } else {
        // Not authorized for this guild
    }
}
```

## Implementation in AuthList (Aug 29, 2026)

### Before (Single Guild)

```rust
// Loaded only 1 guild at startup
let state = AppState {
    guild_id: GuildId::new(<REDACTED_ID>),  // Hardcoded
    tracked_role_id: RoleId::new(567890123),
    // ...
};

// Commands only worked in that one guild
```

### After (Multi-Tenant)

```rust
// Startup: Log all tenants
async fn ready(&self, ctx: Context) {
    let tenants = crate::db::get_all_active_tenants(&self.state.db).await.ok();
    for tenant in tenants {
        let settings = crate::db::get_tenant_settings(&self.state.db, &tenant.id).await.ok();
        tracing::info!(
            "tenant {} ({}): configured for guild {}",
            tenant.name, tenant.id, settings.guild_id
        );
    }
    
    // Register global commands
    serenity::all::Command::set_global_commands(&ctx.http, vec![...]).await;
}

// Dispatch: Look up tenant for THIS guild
pub async fn dispatch(ctx: &Context, command: &CommandInteraction, state: &AppState) {
    let guild_id = command.guild_id.ok_or("no guild")?;
    let tenant = crate::db::get_tenant_by_guild_id(&state.db, &guild_id.to_string()).await?;
    let settings = crate::db::get_tenant_settings(&state.db, &tenant.id).await?;
    
    let guild_state = AppState {
        guild_id: settings.guild_id,
        tracked_role_id: settings.tracked_role_id,
        // ... other fields
    };
    
    match command.data.name.as_str() {
        "whoami" => whoami::run(ctx, command, &guild_state).await,
        // ...
    }
}
```

**Result:** Bot startup logs:
```
loaded 3 active tenants
tenant Legacy Single Guild (legacy): configured for guild <REDACTED_ID>
tenant New Test Server (87514073-4497-4237-9c0b-65c8beb8dc53): configured for guild 999888777
tenant Test (b5991de0-5714-4735-928c-49cffa241de9): configured for guild <REDACTED_ID>
```

Now commands work in all 3 guilds. New tenants created in the dashboard work immediately without code changes.

## Key Advantages

| Aspect | Single Guild | Multi-Tenant |
|--------|--------------|---------------|
| Guilds supported | 1 | Unlimited |
| Settings per guild | None | Yes |
| New guild registration | Code change | Dashboard |
| Commands in new guild | Fail silently | Work immediately |
| Settings isolation | N/A | Database-backed |
| Bot restart needed for new tenant | Yes | No (if using dynamic lookup) |

## Pitfall: Bot Doesn't Pick Up New Tenants Until Restart

### The Problem

1. Bot starts, loads tenants from DB
2. User creates new server via dashboard
3. Bot is still running, only knows about old tenants
4. User invites bot to new guild
5. Bot ignores it (not in startup list)

### Why It Happens

Many implementations cache the tenant list at startup:

```rust
// Bad: Cache at startup, no refresh
let tenants = db::get_all_active_tenants(&pool).await?;
for tenant in tenants {
    GUILD_REGISTRY.insert(tenant.guild_id, tenant);  // Cache it
}
```

New tenants aren't in the cache, so they're ignored.

### Solutions

**Option A: Dynamic Lookup (Recommended)**

Don't cache. Look up on every command:

```rust
pub async fn dispatch(ctx: &Context, cmd: &CommandInteraction, state: &AppState) {
    // Fresh DB lookup every time
    let tenant = db::get_tenant_by_guild_id(&state.db, &cmd.guild_id.to_string()).await?;
    // ...
}
```

✅ New tenants work immediately  
✅ Settings changes take effect right away  
❌ One DB query per command (acceptable for SaaS)  

**Option B: Periodic Refresh**

Cache the tenant list but refresh periodically:

```rust
// Refresh every 5 minutes
tokio::spawn(async move {
    loop {
        tokio::time::sleep(Duration::from_secs(300)).await;
        let tenants = db::get_all_active_tenants(&db).await.ok();
        GUILD_REGISTRY.clear();
        for tenant in tenants {
            GUILD_REGISTRY.insert(tenant.guild_id, tenant);
        }
    }
});
```

✅ New tenants work after 5 min  
✅ Minimal DB load (1 query / 5 min)  
❌ Settings changes delayed by up to 5 min  

**Option C: Restart After New Tenant**

If you can't use Options A or B, document that bot restart is required:

```rust
// Dashboard: After creating new tenant
// Instruct user: "Restart the bot to use the new server"
// Or: Auto-restart via webhook
railway redeploy --service bot  // Restart bot
```

✅ Guaranteed consistency  
❌ Downtime for new server creation  

### AuthList's Approach (Aug 29, 2026)

Uses **Option A: Dynamic Lookup**. The dispatcher looks up tenant on every command:

```rust
let tenant = crate::db::get_tenant_by_guild_id(&state.db, &guild_id).await?;
```

Result: New servers created via dashboard work immediately without restart.

## Testing Multi-Tenant Dispatch

### Unit Test: Correct Tenant Loaded

```rust
#[tokio::test]
async fn test_command_uses_correct_tenant_settings() {
    let db = setup_test_db().await;
    
    // Create two tenants
    db.create_tenant("Guild A", "guild-1", "role-123").await;
    db.create_tenant("Guild B", "guild-2", "role-456").await;
    
    // Simulate command in Guild B
    let interaction = mock_command(
        "guild-2",  // In Guild B
        "whoami"
    );
    
    // Dispatch should look up Guild B's settings
    dispatch(&mock_ctx(), &interaction, &test_state(&db)).await.ok();
    
    // Verify Guild B's role was used (not Guild A's)
    assert_eq!(last_role_checked(), "role-456");
}
```

### Integration Test: Bot Handles Multiple Guilds

```rust
#[tokio::test]
async fn test_bot_handles_commands_from_multiple_guilds() {
    let db = setup_test_db().await;
    
    // Create 3 tenants
    for i in 1..=3 {
        db.create_tenant(&format!("Guild {}", i), &format!("guild-{}", i), ...).await;
    }
    
    // Send commands from each guild
    for guild_id in 1..=3 {
        let interaction = mock_command(&format!("guild-{}", guild_id), "setsteamid");
        let result = dispatch(&mock_ctx(), &interaction, &test_state(&db)).await;
        assert!(result.is_ok(), "Guild {} should be recognized", guild_id);
    }
}
```

## Performance Notes

**Database load:** One additional query per command (get_tenant_by_guild_id + get_tenant_settings).

For a busy bot with 100 commands/sec in 10 servers:
- Startup: 1 query (get all tenants)
- Per-command: 2 queries (get tenant + get settings)
- Total: ~200 queries/sec

**Optimization:** If this is slow, add caching with TTL:

```rust
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use std::collections::HashMap;

pub struct TenantCache {
    cache: Arc<RwLock<HashMap<String, (Tenant, Instant)>>>,
    ttl: Duration,
}

impl TenantCache {
    pub async fn get(&self, guild_id: &str, db: &SqlitePool) -> Result<Tenant> {
        let read = self.cache.read().await;
        if let Some((tenant, created_at)) = read.get(guild_id) {
            if created_at.elapsed() < self.ttl {
                return Ok(tenant.clone());
            }
        }
        drop(read);

        // Cache miss or expired: fetch from DB
        let tenant = db::get_tenant_by_guild_id(db, guild_id).await?;
        let mut write = self.cache.write().await;
        write.insert(guild_id.to_string(), (tenant.clone(), Instant::now()));
        Ok(tenant)
    }
}
```

Now tenants are cached for 5 minutes, reducing DB load to 1 query per server per 5 minutes.

## Related

- `axum-rest-api-design` Pattern 10: Full multi-tenant command dispatch
- `database-schema-refactoring`: Multi-tenant schema design
- Serenity docs: [EventHandler trait](https://docs.rs/serenity/latest/serenity/client/struct.EventHandler.html)
- Discord docs: [Global Application Commands](https://discord.com/developers/docs/interactions/application-commands#global-commands)

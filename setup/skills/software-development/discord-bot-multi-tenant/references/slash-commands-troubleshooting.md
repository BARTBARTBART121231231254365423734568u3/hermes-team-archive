# Slash Commands Troubleshooting

## Symptom: Commands Don't Appear in Discord

### Diagnosis Checklist

1. **Bot has correct OAuth scope**
   - Go to Discord Developer Portal → Your Application → OAuth2 → URL Generator
   - Check scopes: must include both `bot` AND `applications.commands`
   - Re-invite the bot with the corrected URL and try again
   - Evidence: Bot joins server but `/` shows no commands

2. **`ready()` event is firing**
   - Add a tracing::warn! at the very start of `ready()`
   - Redeploy and check logs for that message
   - If you see bot logging in but NOT the ready() message, the event isn't being called
   - Evidence: Missing log line, but bot is running

3. **`commands::register()` is actually being called**
   - Add tracing logs before, during, and after the registration call
   - Use `warn!` level to ensure visibility (INFO may be filtered)
   - Check for any error logs like "failed to register commands"
   - Evidence: No registration logs despite `ready()` firing

4. **Serenity version supports the registration API**
   - Confirm `Cargo.toml` has serenity >= 0.12
   - API signature: `serenity::all::Command::set_global_commands(&ctx.http, commands).await?`
   - If using an older version, the method may not exist

5. **Global vs. per-guild registration**
   - Use `Command::set_global_commands()` for availability in all guilds
   - Do NOT use `guild_id.set_commands()` (that only works for one guild)
   - Global commands take ~1 hour to sync to Discord's CDN (but are instant in most cases)

### Common Causes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Bot online but commands don't show | Missing `applications.commands` scope | Re-invite with correct scopes |
| Logs show bot connected but no register logs | `ready()` handler not calling register() | Check EventHandler impl, add explicit call |
| Commands registered but don't appear for >30 min | Discord global command sync delay | Wait, or re-invite to speed up |
| Registration fails with error (seen in logs) | OAuth scope still missing | Same as first row |
| Only works in one guild | Using per-guild registration | Switch to `set_global_commands()` |

## Deployment-Specific Issues

### Railway/Heroku

- **Logs are batched/delayed:** Log timestamps may be out of order or delayed. Don't assume missing logs mean the code didn't run.
- **Auto-deploy may not trigger:** Push → git commit → wait → deployment. Sometimes requires manual `railway redeploy` even if auto-deploy is enabled.
- **Container restart required:** If you change code, the old container keeps running until you explicitly redeploy. Commands may not re-register until then.

### Testing Locally

- **Use `RUST_LOG=debug`** to see more detailed serenity logs
- **Check Discord Developer Portal → OAuth2 → Installed Apps** to see which scopes were actually granted
- **Re-invite after scope changes** — just re-running the bot with the same invite doesn't update scopes

## Working Example (Tested)

This pattern works with Serenity 0.12, multi-tenant Rust Discord bots:

```rust
#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, ready: Ready) {
        tracing::warn!("🚀 READY EVENT FIRING");
        tracing::info!("logged in as {}", ready.user.name);
        
        if let Err(e) = commands::register(&ctx, &self.state).await {
            tracing::error!("❌ failed to register commands: {e}");
        } else {
            tracing::warn!("✅ commands registered successfully");
        }
    }
}

pub async fn register(ctx: &Context, state: &AppState) -> anyhow::Result<()> {
    let commands: Vec<CreateCommand> = vec![
        command1(), command2(), // ...
    ];
    
    tracing::warn!("📤 registering {} global commands", commands.len());
    serenity::all::Command::set_global_commands(&ctx.http, commands).await?;
    tracing::warn!("✅ global commands sent to Discord");
    Ok(())
}
```

If you see both the ready log AND the registration logs, commands are working. Check Discord client after 30-60 seconds.
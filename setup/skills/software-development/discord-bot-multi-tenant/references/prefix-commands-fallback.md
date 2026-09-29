# Prefix Commands as Slash Command Debugging Fallback

## When to Use

If slash commands fail to register or don't appear in Discord:
1. Implement prefix commands (`!command`) as an immediate workaround
2. Prefix commands require NO registration with Discord
3. They work instantly and prove the bot is receiving messages
4. Use them to test bot logic while debugging slash command issues

## Implementation Pattern (Serenity 0.12)

Add a `message` event handler to your EventHandler implementation:

```rust
async fn message(&self, ctx: Context, msg: serenity::all::Message) {
    // Ignore bot's own messages
    if msg.author.bot {
        return;
    }

    // Handle prefix commands (!whoami, !guide, !help, etc.)
    if !msg.content.starts_with('!') {
        return;
    }

    let args: Vec<&str> = msg.content.split_whitespace().collect();
    if args.is_empty() {
        return;
    }

    let command_name = args[0][1..].to_lowercase();
    tracing::info!("Prefix command: {}", command_name);

    match command_name.as_str() {
        "whoami" => {
            let _ = msg.reply(&ctx, "✅ **Prefix commands work!** Bot is receiving messages.").await;
        }
        "guide" => {
            let _ = msg.reply(&ctx, "📖 **Guide command received** - Prefix commands functional!").await;
        }
        "help" => {
            let _ = msg.reply(&ctx, 
                "**Available Prefix Commands:**\n`!whoami` - Test\n`!guide` - Guide\n`!help` - This message"
            ).await;
        }
        _ => {
            let _ = msg.reply(&ctx, format!("❓ Unknown command: `!{}`\nTry `!help`", command_name)).await;
        }
    }
}
```

## Key Points

1. **Instant response:** No Discord registration needed, no caching delays
2. **Proves connectivity:** If prefix commands work, the bot is definitely receiving messages
3. **Multi-tenant ready:** Can apply same tenant lookup logic as slash commands:
   ```rust
   // Look up guild, load tenant settings, apply per-guild logic
   let tenant = match crate::db::get_tenant_by_guild_id(&self.state.db, &msg.guild_id.to_string()).await {
       Ok(Some(t)) => t,
       Ok(None) => {
           let _ = msg.reply(&ctx, "❌ Server not configured. Add via dashboard.").await;
           return;
       }
       Err(e) => {
           tracing::error!("lookup failed: {e}");
           return;
       }
   };
   ```
4. **Ignore bot's own messages:** Check `if msg.author.bot { return; }` to avoid loops

## Testing Workflow

1. Deploy code with prefix commands
2. In your Discord server, type `!whoami`
3. Bot replies instantly → **connectivity confirmed**
4. Then debug slash command registration separately (OAuth scope, ready() logs, etc.)
5. Once slash commands work, keep prefix commands as fallback for future issues

## Example Session Flow

```
User: !whoami
Bot: ✅ **Prefix commands work!** Bot is receiving messages.

User: /whoami
Bot: (no response - slash commands not registered yet)

→ Now you know:
  - Bot definitely connected and receiving messages ✅
  - Problem is specifically slash command registration ✅
  - Check OAuth scope, ready() logs, Discord API errors
```

## Limitations

- Prefix commands are less discoverable than slash commands (`/` doesn't autocomplete them)
- They don't show in Discord's command browser
- Users have to remember the prefix
- More message spam in chat

**Use prefix commands only as a debugging tool, not a permanent replacement.**

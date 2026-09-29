# Form UX: Hiding System-Wide Constants from Per-Instance Forms

## The Problem

When building setup wizards or onboarding forms, you often have two types of fields:

1. **System-wide constants** — Same for every instance (e.g., Discord bot token, Steam API key)
2. **Per-instance variables** — Unique to each tenant/server (e.g., server ID, role IDs)

If you ask users to enter BOTH in the form, you create friction:
- **Cognitive load** — Users must understand which fields are "global" vs "local"
- **Errors** — Users paste the wrong value into the wrong field
- **Redundancy** — Typing the same token dozens of times for dozens of servers
- **Copy-paste mistakes** — Easy to accidentally use one server's value for another

## The Solution: Hide System Constants

**Don't ask users for values that are the same for every server. Pre-fill or omit them entirely.**

### Pattern 1: Pre-Fill from Environment

Set system constants as environment variables, then auto-populate in the form:

```typescript
// src/components/SetupWizard.svelte
<script>
  // Pre-fill from environment (set via Dockerfile or deployment config)
  let discord<REDACTED_SECRET> || ''
  let steam<REDACTED_SECRET> || ''
  
  // User enters only per-instance values
  let serverName = ''
  let serverId = ''
  let trackedRoleId = ''
</script>

<input type="text" placeholder="Server name" bind:value={serverName} />
<input type="text" placeholder="Server ID" bind:value={serverId} />
<input type="text" placeholder="Tracked role ID" bind:value={trackedRoleId} />

{/* Discord token and Steam key are pre-filled, not shown */}
```

**Advantages:**
- ✅ Admin sets up once (environment variable)
- ✅ Users only enter server-specific info
- ✅ No risk of pasting wrong token
- ✅ Scales to dozens of servers

**Setup:**

```dockerfile
# Dockerfile
FROM node:18
WORKDIR /app
COPY . .

# Build with environment variables
ARG VITE_DISCORD_TOKEN="your-token-here"
ARG VITE_STEAM_API_KEY="your-key-here"

RUN VITE_DISCORD_TOKEN=$VITE_DISCORD_TOKEN \
    VITE_STEAM_API_KEY=$VITE_STEAM_API_KEY \
    npm run build

CMD ["npm", "start"]
```

Or in `.env.production`:
```bash
VITE_DISCORD_TOKEN=your-actual-token
VITE_STEAM_API_KEY=your-actual-key
```

### Pattern 2: Admin Settings Page

If you need flexibility, create a separate admin page for configuring system constants:

```typescript
// src/pages/AdminSettings.svelte (password-protected)
<script>
  let discord<REDACTED_SECRET>('admin_discord_token') || ''
  let steam<REDACTED_SECRET>('admin_steam_api_key') || ''
  
  function saveSettings() {
    localStorage.setItem('admin_discord_token', discordToken)
    localStorage.setItem('admin_steam_api_key', steamApiKey)
    // Reload setup wizard with new values
  }
</script>

<h2>Admin Settings</h2>
<p>Configure system-wide credentials (used by all servers)</p>

<label>Discord Bot Token</label>
<input type="password" bind:value={discordToken} />

<label>Steam Web API Key</label>
<input type="password" bind:value={steamApiKey} />

<button on:click={saveSettings}>Save Settings</button>
```

**Then in setup wizard:**

```typescript
// src/components/SetupWizard.svelte
<script>
  const discord<REDACTED_SECRET>('admin_discord_token')
  const steam<REDACTED_SECRET>('admin_steam_api_key')
  
  if (!discordToken || !steamApiKey) {
    // Redirect to admin settings
    window.location.href = '/admin/settings'
    return
  }
  
  // User only sees per-instance fields
</script>
```

### Pattern 3: Hidden Fields (API Handles It)

If system constants are really global, don't even show them in the UI—just send them automatically:

```typescript
// User-facing form
<script>
  let serverName = ''
  let serverId = ''
  let trackedRoleId = ''
  
  async function submitForm() {
    // Bot/API knows the global values; don't ask user
    const res = await fetch('/api/tenants', {
      method: 'POST',
      body: JSON.stringify({
        name: serverName,
        guild_id: serverId,
        tracked_role_id: trackedRoleId,
        // discord_token and steam_key are added by the backend
      })
    })
  }
</script>

<input bind:value={serverName} />
<input bind:value={serverId} />
<input bind:value={trackedRoleId} />
<button on:click={submitForm}>Create Server</button>
```

**Backend (Rust/Axum):**

```rust
async fn create_tenant(
    State(state): State<Arc<AppState>>,
    Json(mut payload): Json<CreateTenantRequest>,
) -> Result<Json<TenantResponse>, Error> {
    // Backend fills in the global values
    payload.discord_<REDACTED_SECRET>();
    payload.steam_web_<REDACTED_SECRET>();
    
    // Now create the tenant
    db::create_tenant(&state.db, &payload).await
}
```

**Advantages:**
- ✅ Zero user friction
- ✅ Impossible to get wrong
- ✅ Backend controls the values (security)
- ✅ No need to rotate values client-side

**Disadvantages:**
- ❌ Requires backend to always have the values
- ❌ Users can't override if needed

## Real-World Example: AuthList

**Before (User Confusion):**

```typescript
// Step 2 of setup wizard had FIVE fields:
// 1. Discord Bot Token (same every time)
// 2. Tracked Role ID (different per server) ← USER ENTRY
// 3. Admin Role ID (optional, different per server) ← USER ENTRY
// 4. Steam Web API Key (same every time)
// 5. Log Channel ID (different per server) ← USER ENTRY

// Users saw: "Why do I need to paste the same bot token 100 times?"
```

**After (Simplified):**

```typescript
// Step 2 now has TWO fields only:
// 1. Tracked Role ID (different per server) ← USER ENTRY
// 2. Log Channel ID (different per server) ← USER ENTRY

// Discord token and Steam key are pre-configured by admin
// Users see: "Simple! Just copy the role ID and channel ID."
```

## User Preferences Embedded Here

This session's key learning: **Users prefer direct solutions over choice paralysis.**

When building forms:
- ❌ "Should we show option X or hide it?" (creates cognitive load)
- ✅ "Let's just hide it and pre-fill it." (one clear path)

The user's frustration signal ("i think it should not even show") directly shaped this pattern.

## Checklist: Before You Add a Field

For every field in a form, ask:

1. **Is this value the same across all instances?**
   - YES → Hide it, pre-fill from env/admin settings
   - NO → Show it

2. **Can the backend provide this value?**
   - YES → Remove the field, backend fills it automatically
   - NO → Ask the user

3. **Will users enter this value 100+ times?**
   - YES → Move to admin settings, pre-fill, or hide
   - NO → OK to ask

4. **Is this a security credential (token, key, secret)?**
   - YES → Never show in frontend form if possible; backend only
   - NO → Can show in frontend

## Deployment Example

```bash
# Set system constants once
export VITE_DISCORD_TOKEN="xoxb-123456..." 

export VITE_STEAM_API_KEY="ABC123..." 

# Build dashboard (tokens baked in)
npm run build

# Deploy to Railway
railway deploy --service dashboard

# Now every user who creates a server automatically uses these tokens
# They only enter server-specific data (ID, role IDs, etc.)
```

## See Also

- `frontend-auth-testing-patterns` — Full authentication patterns including fallback modes
- `rapid-code-deploy-cycle` — Environment variables in Docker deployments

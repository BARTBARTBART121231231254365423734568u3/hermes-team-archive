# SvelteKit Dashboard Setup Forms: Hiding System-Wide Constants

## The Problem

When building a multi-tenant SaaS dashboard, you often have two kinds of configuration:

1. **System-wide constants** — Same for every instance (Discord bot token, Steam API key, payment processor keys)
2. **Per-instance settings** — Different for each server/tenant (server name, role IDs, channel IDs)

A common UX mistake is mixing them in the same setup form, forcing users to enter data that should never change:

### Bad UX Example

**Setup Wizard Step 2:**
```
☐ Server Name ← Different per server
☐ Tracked Role ID ← Different per server
☐ Admin Role ID ← Different per server
☐ Discord Bot Token ← SAME FOR ALL SERVERS
☐ Steam Web API Key ← SAME FOR ALL SERVERS  
☐ Log Channel ID ← Different per server

[Back] [Next]
```

User thinks: "Wait, I have to paste the Discord token AND Steam key for every server? That can't be right."

Issue: Form validation also requires these fields, so if they're not filled, the form shows "Please fill in all required fields" — confusing users about what's actually required.

## The Solution: Pre-Fill System Constants, Hide from Forms

### Pattern 1: Environment Variables (Best for Production)

**Define system constants in Railway/deployment environment:**

```bash
# railway.toml or environment configuration
VITE_DISCORD_TOKEN=xoxb-1234567890
VITE_STEAM_API_KEY=abc123def456
```

**Load at build time, inject into component:**

```typescript
// dashboard/src/components/SetupWizard.svelte
<script lang="ts">
  // These are pre-filled from build environment
  let discord<REDACTED_SECRET> || ''
  let steam<REDACTED_SECRET> || ''
  
  // Send to backend (user never sees them)
  async function handleStep3() {
    const payload = {
      name: tenantName,
      guild_id: guildId,
      tracked_role_id: trackedRoleId,
      admin_role_id: adminRoleId,
      steam_web_api_key: steamApiKey,  // Pre-filled, not from user input
      log_channel_id: logChannelId,
      discord_token: discordToken,     // Pre-filled, not from user input
      oauth_redirect_url: oauthRedirectUrl,
    }
    // ... POST to /api/tenants
  }
</script>
```

**Form only shows user-specific fields:**

```svelte
<!-- Step 1 -->
<label>Server Name *</label>
<input bind:value={tenantName} />

<label>Discord Server ID *</label>
<input bind:value={guildId} />

<!-- Step 2 -->
<label>Tracked Role ID *</label>
<input bind:value={trackedRoleId} />

<label>Admin Role ID (Optional)</label>
<input bind:value={adminRoleId} />

<label>Log Channel ID *</label>
<input bind:value={logChannelId} />

<!-- NO Discord Token field ✅ -->
<!-- NO Steam API Key field ✅ -->
```

**Advantages:**
- ✅ Form only shows what users need to enter
- ✅ System constants are never visible to users
- ✅ Validation only checks user-provided fields
- ✅ Can update constants without rebuilding entire dashboard (if using secrets/config management)
- ✅ Clear separation: "What we provide" vs. "What you provide"

### Pattern 2: Admin Dashboard (for Updating Constants)

If system constants need to change without rebuilding, add an admin-only settings page:

```typescript
// dashboard/src/pages/AdminSettings.svelte
<script>
  let discordToken = ''
  let steamApiKey = ''
  
  async function saveSettings() {
    const res = await fetch(`${apiBase}/admin/settings`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        discord_token: discordToken,
        steam_api_key: steamApiKey,
      })
    })
    
    if (res.ok) {
      alert('Settings saved. New servers will use these values.')
    }
  }
</script>

<h2>System Configuration</h2>
<p>These values apply to all new servers created after this point.</p>

<label>Discord Bot Token</label>
<input type="password" bind:value={discordToken} />
<small>From Discord Developer Portal → Application → Token</small>

<label>Steam Web API Key</label>
<input type="password" bind:value={steamApiKey} />
<small>Get free key at steamcommunity.com/dev/apikey</small>

<button on:click={saveSettings}>Save Settings</button>
```

**Backend (Rust):**

```rust
#[derive(serde::Deserialize)]
pub struct AdminSettingsRequest {
    discord_token: String,
    steam_api_key: String,
}

async fn update_admin_settings(
    ApiAuth(principal): ApiAuth,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<AdminSettingsRequest>,
) -> Result<StatusCode, (StatusCode, Json<ErrorResponse>)> {
    // Only super-admin can change system settings
    if !principal.is_admin() {
        return Err(forbidden());
    }
    
    // Store in database or config file
    db::queries::update_system_settings(
        &state.db,
        &payload.discord_token,
        &payload.steam_api_key,
    )
    .await
    .map_err(|_| database_error())?;
    
    Ok(StatusCode::OK)
}
```

### Pattern 3: Hybrid (Environment Variables + Runtime Override)

Best of both worlds: start with env vars, allow admin to override:

```typescript
// Load from env at initialization
let discord<REDACTED_SECRET> || ''
let steam<REDACTED_SECRET> || ''

// On admin settings fetch, override with database values
onMount(async () => {
  try {
    const res = await fetch(`${apiBase}/admin/settings`)
    if (res.ok) {
      const settings = await res.json()
      discord<REDACTED_SECRET>
      steam<REDACTED_SECRET>
    }
  } catch (err) {
    console.warn('Could not load admin settings, using defaults')
    // Falls back to env vars
  }
})
```

## UX Impact: Before vs. After

### BEFORE (Bad UX)

```
Add New Server — Step 2 of 3

☐ Tracked Role ID *      (I need to look this up...)
☐ Admin Role ID           (Optional, I can skip this)
☐ Discord Bot Token *     (Wait, why does every server need this?)
☐ Steam Web API Key *     (And this? I thought this was global...)
☐ Log Channel ID *        (Okay, let me find this...)

"Please fill in all required fields" ❌
  → User confused: Are Discord/Steam really required per server?
  → User asks: "Do I paste the same token every time?"
  → Support burden increases
```

### AFTER (Good UX)

```
Add New Server — Step 2 of 3

☐ Tracked Role ID *      (I need to look this up...)
☐ Admin Role ID           (Optional, I can skip this)
☐ Log Channel ID *        (Okay, let me find this...)

"Please fill in all required fields" ✅
  → User knows these are the only 3 required things
  → Clear: Discord token/Steam key are system-managed
  → Self-service setup, no support needed
```

## Decision Matrix

| Scenario | Approach | How to Implement |
|----------|----------|------------------|
| Small SaaS, one Discord bot | Environment vars only | Set `VITE_DISCORD_TOKEN` in Railway, load in setup wizard |
| Large SaaS, multiple teams | Environment vars + admin override | Env vars as default, admin page to change |
| Internal tool, manual setup | Ask once at config time | Single admin config page, not in user workflows |
| Fully self-hosted | Docker config | Mount config file, read at startup |

## Implementation Checklist

- [ ] Identify which fields are system-wide (same for all servers/tenants)
- [ ] Move those fields OUT of the per-server setup form
- [ ] Create `.env.example` documenting system-wide constants
- [ ] Document where to set these constants (Railway vars, .env file, admin page, etc.)
- [ ] Update form validation to only check user-provided fields
- [ ] Update form description to clarify which fields are user-specific
- [ ] Test setup wizard with only required user fields visible
- [ ] (Optional) Add admin settings page to manage system constants

## Anti-Pattern: Required Fields That Aren't Required

❌ **Bad:**
```typescript
async function handleStep2() {
  // Checks for fields that come from environment
  if (!discordToken.trim() || !steamApiKey.trim() || !trackedRoleId.trim()) {
    error = 'Please fill in all required fields'  // Confusing!
    return
  }
}
```

User sees "Please fill in all required fields" but two of those fields should already be filled from environment. Confusing message.

✅ **Good:**
```typescript
async function handleStep2() {
  // Only checks fields the user actually needs to provide
  if (!trackedRoleId.trim()) {
    error = 'Please fill in all required fields'  // Now accurate
    return
  }
  
  // System constants are handled by component initialization
  oauthRedirectUrl = `${window.location.origin}/oauth/callback`
  step = 3
}
```

User sees "Please fill in all required fields" and that matches what's on the form. Clear and accurate.

## Related Patterns

- **Setup Wizard State Management**: Keeping track of which fields are required vs. optional
- **Form Validation**: Only validate fields that users see
- **Environment Configuration**: Setting system-wide values at deployment time
- **Admin Dashboard**: Where operators manage system settings

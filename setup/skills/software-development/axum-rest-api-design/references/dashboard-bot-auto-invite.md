# Dashboard Bot Auto-Invite Pattern

**Session:** AuthList Aug 29, 2026  
**Problem:** After user creates a Discord server via dashboard, they had to manually find and click a bot invite link. Friction point in onboarding.  
**Solution:** Multi-step wizard with success screen that opens Discord OAuth invite automatically  

## The UX Flow

### Before (Manual Invite)

1. User fills out form: "Server Name", "Guild ID", etc.
2. User clicks "Create Server"
3. Dashboard says "Server created! Your bot must be invited."
4. User has to:
   - Go to Discord Developer Portal
   - Copy bot's Client ID
   - Construct OAuth URL manually
   - Paste into browser
   - Select server from dropdown
   - Click "Authorize"

**Problem:** 7 manual steps, high friction, user forgets their place.

### After (Auto-Invite)

1. User fills out form: "Server Name", "Guild ID", etc.
2. User clicks "Create Server"
3. Dashboard shows success screen with **one big button**: "🔗 Invite Bot to [ServerName]"
4. User clicks button → Discord OAuth opens automatically
5. User selects server from dropdown
6. User clicks "Authorize"
7. Bot joins automatically

**Result:** Reduced from 7 steps to 2 user actions.

## Implementation

### Step 1: Add Step 4 to Wizard Component

```svelte
<!-- SetupWizard.svelte -->
<script lang="ts">
  let step: 1 | 2 | 3 | 4 = 1
  let createdTenantId: string | null = null
  let tenantName: string = ''
  
  async function handleStep3() {
    loading = true
    error = null
    
    try {
      const response = await fetch(`${apiBase}/api/tenants`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: tenantName,
          guild_id: guildId,
          tracked_role_id: trackedRoleId,
          admin_role_id: adminRoleId,
          log_channel_id: logChannelId
        })
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to create server')
      }
      
      // ✅ Store tenant ID and move to Step 4
      const result = await response.json()
      createdTenantId = result.id
      step = 4  // Success screen
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to create server'
    } finally {
      loading = false
    }
  }
</script>

<!-- Step 4: Success + Bot Invite -->
{#if step === 4}
  <div class="wizard-step">
    <h3>✅ Server Created!</h3>
    <p class="step-description">
      Your server "{tenantName}" has been created successfully!
    </p>

    <!-- Main invite button -->
    <div class="success-box">
      <p>Now invite the bot to your Discord server:</p>
      <button 
        class="btn btn-primary btn-large" 
        on:click={() => inviteBot()}
      >
        🔗 Invite Bot to {tenantName}
      </button>
    </div>

    <!-- Help text -->
    <div class="info-box">
      <strong>What happens next:</strong>
      <ul>
        <li>Discord will ask you to select a server</li>
        <li>Choose "{tenantName}"</li>
        <li>Click "Authorize"</li>
        <li>Bot joins your server automatically! ✅</li>
      </ul>
    </div>

    <!-- Done button -->
    <div class="wizard-actions">
      <button class="btn btn-primary" on:click={onClose}>Done</button>
    </div>
  </div>
{/if}

<script>
  function inviteBot() {
    // Your bot's Client ID from Discord Developer Portal
    const clientId = '<REDACTED_ID>'
    
    // Permissions: read messages, manage nicknames, view channels, etc.
    // 268435456 = calculated from individual permission flags
    const permissions = '268435456'
    
    // OAuth2 scope: bot (standard bot OAuth)
    const scope = 'bot'
    
    // Construct Discord OAuth URL
    const inviteUrl = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=${permissions}&scope=${scope}`
    
    // Open in new tab
    window.open(inviteUrl, '_blank')
  }
</script>

<style>
  .success-box {
    background: rgba(31, 191, 130, 0.1);
    border: 1px solid rgba(31, 191, 130, 0.3);
    border-radius: 6px;
    padding: 16px;
    margin: 16px 0;
  }

  .success-box p {
    margin: 0 0 12px;
    font-size: 13px;
    color: #a0a8b0;
  }

  .btn-large {
    font-size: 14px;
    padding: 12px 20px;
    width: 100%;
  }

  .info-box {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 12px;
    margin: 16px 0;
    font-size: 12px;
  }

  .info-box ul {
    margin: 8px 0 0;
    padding-left: 20px;
  }

  .info-box li {
    margin: 6px 0;
  }
</style>
```

### Step 2: Discord OAuth URL Components

**Client ID:**
Go to Discord Developer Portal → Your Application → General Information → Copy "Application ID"

**Permissions:**
Permissions are calculated as a bitwise OR of individual flags:

```javascript
// Common bot permissions (bitwise OR'd together)
const PERMISSIONS = {
  VIEW_CHANNELS: 1024,           // 0x400
  SEND_MESSAGES: 2048,           // 0x800
  MANAGE_MESSAGES: 4096,         // 0x1000
  MANAGE_NICKNAMES: 134217728,   // 0x8000000
  CHANGE_NICKNAME: 67108864,     // 0x4000000
  READ_MESSAGE_HISTORY: 65536,   // 0x10000
  CONNECT: 1048576,              // 0x100000
}

// Combined: 268435456 = MANAGE_NICKNAMES + CHANGE_NICKNAME + others
// For production, calculate based on what your bot actually needs
```

**OAuth URL Structure:**
```
https://discord.com/api/oauth2/authorize
  ?client_id={YOUR_CLIENT_ID}
  &permissions={DECIMAL_PERMISSIONS}
  &scope=bot
  &response_type=code          (optional)
  &state={RANDOM_STATE_ID}     (optional, for security)
```

Example: `https://discord.com/api/oauth2/authorize?client_id=<REDACTED_ID>&permissions=268435456&scope=bot`

### Step 3: Store Invite Status in Database

Optional: Track whether bot has been invited for each tenant:

```sql
ALTER TABLE tenants ADD COLUMN bot_invited_at TEXT;

-- Later, when bot joins a guild:
UPDATE tenants
SET bot_invited_at = datetime('now')
WHERE guild_id = ?;
```

Dashboard can then show status:
```svelte
{#if server.bot_invited_at}
  ✅ Bot Invited
{:else}
  ⏳ Waiting for bot invite (Click to invite)
{/if}
```

## UX Enhancements

### Enhancement 1: Show Discord OAuth Progress

If Discord's OAuth is slow, show feedback:

```svelte
<script>
  let inviteInProgress = false
  
  async function inviteBot() {
    inviteInProgress = true
    const url = buildInviteUrl()
    window.open(url, '_blank')
    
    // Show message for 2 seconds
    setTimeout(() => {
      inviteInProgress = false
    }, 2000)
  }
</script>

{#if inviteInProgress}
  <p>Opening Discord...</p>
{/if}
```

### Enhancement 2: Detect If User Completed Invite

(Advanced) Poll the backend to check if bot joined:

```svelte
<script>
  async function checkBotStatus() {
    const res = await fetch(`${apiBase}/api/tenants/${tenantId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    const server = await res.json()
    if (server.bot_invited_at) {
      // Bot has joined!
      showNotification('Bot joined your server!')
    }
  }
  
  // Poll every 5 seconds
  setInterval(checkBotStatus, 5000)
</script>
```

### Enhancement 3: Pre-fill Server Selection

(Limited) Discord OAuth supports `guild_id` parameter to pre-select server:

```javascript
const inviteUrl = `https://discord.com/api/oauth2/authorize
  ?client_id=${clientId}
  &permissions=${permissions}
  &scope=bot
  &guild_id=${guildId}`  // Discord pre-selects this guild
```

**Note:** This only works if the OAuth app has permission to see that guild. It's not guaranteed to pre-fill.

## Pitfalls

### Pitfall 1: Hardcoded Client ID

Don't hardcode in the component—it's public information (visible to anyone who inspects the DOM).

```typescript
// OK: Public information, fine to hardcode
const clientId = '<REDACTED_ID>'
```

This is the bot's public ID, not a secret.

### Pitfall 2: User Closes Browser After Clicking

If user clicks "Invite Bot" but closes the browser before authorizing:
- Tenant is created ✅
- Bot is not invited yet ❌

**Solution:** Next time user logs in, show "Invite Bot" button on server list:

```svelte
{#each servers as server}
  <div class="server-card">
    <h4>{server.name}</h4>
    {#if server.bot_invited_at}
      ✅ Bot Invited
    {:else}
      <button on:click={() => inviteBot(server.guild_id)}>
        Invite Bot
      </button>
    {/if}
  </div>
{/each}
```

### Pitfall 3: Wrong Permissions Set

If permissions value is wrong, bot joins but lacks needed capabilities:

```javascript
// ❌ Missing permissions, bot can't do anything
const permissions = '0'

// ✅ Correct permissions for steam nickname bot
const permissions = '268435456'  // Calculated from: MANAGE_NICKNAMES + CHANGE_NICKNAME + READ_MESSAGE_HISTORY, etc.
```

Calculate permissions here: https://discordapp.com/developers/tools/permissions-calculator

## Testing

### Test Step 4 Renders

```svelte
<script>
  import SetupWizard from './SetupWizard.svelte'
  import { render } from '@testing-library/svelte'
  
  test('step 4 shows after successful creation', async () => {
    const { getByText } = render(SetupWizard)
    
    // Simulate step 3 completion
    await userEvent.click(getByText('Create Server'))
    
    // Should show success screen
    expect(getByText('✅ Server Created!')).toBeInTheDocument()
    expect(getByText(/Invite Bot to/)).toBeInTheDocument()
  })
  
  test('invite button constructs correct Discord OAuth URL', () => {
    const button = document.querySelector('.btn-invite')
    expect(button.href).toContain('client_id=<REDACTED_ID>')
    expect(button.href).toContain('scope=bot')
  })
</script>
```

## Related

- `axum-rest-api-design` Pattern 10.5: Dashboard Auto-Invite After Server Creation
- Discord OAuth Docs: https://discord.com/developers/docs/topics/oauth2
- Permissions Calculator: https://discordapp.com/developers/tools/permissions-calculator
- Discord API Reference: https://discord.com/developers/docs/resources/guild

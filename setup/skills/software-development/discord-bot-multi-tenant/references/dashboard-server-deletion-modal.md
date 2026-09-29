# Dashboard Server Deletion Modal with Backend Cascade

**When to use:** Multi-tenant dashboard where users can delete a server (tenant), and you need:
- A confirmation modal with Danger Zone styling
- Double-confirm pattern (prevent accidental deletion)
- Automatic bot guild-leave on deletion
- Cascade delete of all tenant data
- Error handling if external API (Discord) fails

**Real example:** AuthList dashboard — Settings modal with red Delete Server button in Danger Zone.

## Pattern: Modal Component + Parent Integration

### Frontend: SettingsModal Component (Svelte)

**File: `dashboard/src/components/SettingsModal.svelte`**

```svelte
<script lang="ts">
  export let apiBase: string = 'http://localhost:8080/api'
  export let serverId: string = ''
  export let onClose: () => void = () => {}
  export let onDelete: () => void = () => {}

  let isDeleting = false
  let error = ''
  let confirmDelete = false  // Double-confirm flag

  function authHeaders(): Record<string, string> {
    const <REDACTED_SECRET>('authlist_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async function handleDelete() {
    if (!confirmDelete) {
      // First click: just set the confirm flag
      confirmDelete = true
      return
    }
    
    // Second click: actually delete
    isDeleting = true
    error = ''
    
    try {
      const response = await fetch(`${apiBase}/dashboard/servers/${serverId}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        error = data.message || `Server deletion failed (HTTP ${response.status})`
        isDeleting = false
        return
      }
      
      // Success: notify parent and close
      onDelete()
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unknown error occurred'
      isDeleting = false
    }
  }
  
  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget && !isDeleting) {
      onClose()
    }
  }
  
  function handleCancel() {
    if (!isDeleting) {
      onClose()
    }
  }
</script>

<div class="modal-backdrop" on:click={handleBackdropClick}>
  <div class="modal">
    <div class="modal-header">
      <h2>Server Settings</h2>
      <button class="close-btn" on:click={handleCancel} disabled={isDeleting}>
        ✕
      </button>
    </div>
    
    <div class="modal-content">
      <div class="info-section">
        <label>Server ID</label>
        <code>{serverId}</code>
      </div>
      
      <div class="danger-zone">
        <div class="danger-header">
          <h3>Danger Zone</h3>
          <p>This action cannot be undone.</p>
        </div>
        
        {#if error}
          <div class="error-message">
            <span class="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        {/if}
        
        <button
          class="delete-btn"
          on:click={handleDelete}
          disabled={isDeleting}
        >
          {#if isDeleting}
            <span class="spinner">⏳</span> Deleting...
          {:else if confirmDelete}
            <span>⚠️ Click Again to Confirm</span>
          {:else}
            <span>🗑️ Delete Server</span>
          {/if}
        </button>
        
        {#if confirmDelete && !isDeleting}
          <p class="warning-text">
            This will remove the bot from the Discord server and delete all associated data.
          </p>
        {/if}
      </div>
    </div>
    
    <div class="modal-footer">
      <button class="cancel-btn" on:click={handleCancel} disabled={isDeleting}>
        Cancel
      </button>
    </div>
  </div>
</div>

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: #0f1420;
    border-radius: 8px;
    border: 1px solid #1a2332;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    width: 100%;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #1a2332;
  }

  .modal-header h2 {
    font-size: 18px;
    font-weight: 600;
    color: #ffffff;
    margin: 0;
  }

  .close-btn {
    background: transparent;
    border: none;
    color: #5a6370;
    font-size: 20px;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .close-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }

  .close-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .modal-content {
    padding: 20px;
  }

  .info-section {
    margin-bottom: 24px;
  }

  .info-section label {
    display: block;
    font-size: 12px;
    color: #5a6370;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }

  .info-section code {
    background: #1a2332;
    border: 1px solid #2a3342;
    border-radius: 4px;
    padding: 8px 12px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: #a0a8b0;
    word-break: break-all;
    display: block;
  }

  .danger-zone {
    background: rgba(231, 76, 60, 0.05);
    border: 1px solid #8b2d2d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
  }

  .danger-header {
    margin-bottom: 16px;
  }

  .danger-header h3 {
    font-size: 14px;
    font-weight: 600;
    color: #e74c3c;
    margin: 0 0 4px 0;
  }

  .danger-header p {
    font-size: 12px;
    color: #e74c3c;
    margin: 0;
    opacity: 0.8;
  }

  .error-message {
    background: rgba(231, 76, 60, 0.1);
    border: 1px solid #e74c3c;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 12px;
    display: flex;
    gap: 8px;
    align-items: flex-start;
    font-size: 13px;
    color: #e74c3c;
  }

  .error-icon {
    flex-shrink: 0;
  }

  .delete-btn {
    width: 100%;
    padding: 10px 16px;
    background: #e74c3c;
    color: #ffffff;
    border: 1px solid #c0392b;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-bottom: 12px;
  }

  .delete-btn:hover:not(:disabled) {
    background: #c0392b;
    box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
  }

  .delete-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .warning-text {
    font-size: 12px;
    color: #e74c3c;
    margin: 0;
    margin-top: 12px;
  }

  .modal-footer {
    display: flex;
    gap: 8px;
    padding: 16px 20px;
    border-top: 1px solid #1a2332;
    justify-content: flex-end;
  }

  .cancel-btn {
    padding: 8px 16px;
    background: transparent;
    color: #a0a8b0;
    border: 1px solid #1a2332;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .cancel-btn:hover:not(:disabled) {
    background: rgba(124, 92, 255, 0.1);
    border-color: #7c5cff;
    color: #7c5cff;
  }

  .cancel-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
```

**Key design points:**
- Server ID displayed in `<code>` block (easy to copy/reference)
- Error message area for API failures (displayed prominently in red)
- Double-confirm: first click shows warning, second click actually deletes
- Disabled state during deletion (button grayed out, shows spinner)
- Backdrop click closes modal only if not deleting
- Cancel button only works when not deleting
- `authHeaders()` pulls token from localStorage and includes in DELETE request

### Parent Component: Dashboard.svelte

**Integration:**

```svelte
<script lang="ts">
  import { onMount } from 'svelte'
  import SettingsModal from '../components/SettingsModal.svelte'
  
  let showSettings = false
  let selectedServerId = ''
</script>

<!-- Server list grid -->
<div class="servers-grid">
  {#each servers as server}
    <div class="server-card">
      <h3>{server.name}</h3>
      <p>Guild ID: {server.id}</p>
      <div class="server-actions">
        <button on:click={() => onSelectServer(server.id)}>Manage</button>
        <button 
          on:click={() => {
            selectedServerId = server.id
            showSettings = true
          }}
        >
          Settings
        </button>
      </div>
    </div>
  {/each}
</div>

<!-- Modal -->
{#if showSettings}
  <SettingsModal 
    {apiBase} 
    serverId={selectedServerId} 
    onClose={() => showSettings = false}
    onDelete={() => {
      showSettings = false
      window.location.reload()  // Refresh to update server list
    }}
  />
{/if}
```

**Key points:**
- Pass `serverId` to modal when Settings button is clicked
- On successful deletion, reload page to refresh server list
- Modal closes when user clicks Cancel or backdrop (if not deleting)

### Backend: DELETE Endpoint

**See:** `references/cascade-delete-with-external-api-calls.md` for full backend pattern

Quick summary:
```rust
async fn delete_server(
    ApiAuth(principal): ApiAuth,
    State(state): State<Arc<AppState>>,
    Path(tenant_id): Path<String>,
) -> Result<StatusCode, (StatusCode, Json<ErrorResponse>)> {
    // Auth check
    if !principal.can_access_tenant(&tenant_id) {
        return Err((StatusCode::UNAUTHORIZED, Json(...)));
    }

    // Get guild_id to tell bot to leave
    let settings = crate::db::get_tenant_settings(&state.db, &tenant_id, &state.encryptor).await
        .map_err(|_| (StatusCode::NOT_FOUND, Json(...)))?;

    let guild_id: u64 = settings.guild_id.parse()
        .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(...)))?;

    // Tell Discord bot to leave (non-blocking failure)
    let client = reqwest::Client::new();
    if let Err(e) = client
        .delete(format!("https://discord.com/api/v10/users/@me/guilds/{}", guild_id))
        .bearer_auth(&state.discord_token)
        .send()
        .await
    {
        tracing::warn!("bot failed to leave guild {}: {}", guild_id, e);
    }

    // Cascade delete all tenant data
    crate::db::delete_tenant(&state.db, &tenant_id).await
        .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(...)))?;

    Ok(StatusCode::NO_CONTENT)
}
```

## UX Flow Diagram

```
User sees server list
    ↓
User clicks Settings button on a server
    ↓
[SettingsModal opens]
  - Shows Server ID
  - Shows Danger Zone section
  - Delete button says: "🗑️ Delete Server"
    ↓
User clicks Delete button (1st click)
    ↓
  - Button text changes: "⚠️ Click Again to Confirm"
  - Warning text appears: "This will remove the bot from the Discord server..."
    ↓
User clicks Delete button (2nd click)
    ↓
  - Button shows spinner: "⏳ Deleting..."
  - Button is disabled
  - Cancel button is disabled
  - Modal can't be closed
    ↓
API DELETE /dashboard/servers/{id} 
  - Bot leaves Discord guild
  - Database cascade deletes all tenant data
  - Returns 204 No Content
    ↓
onDelete() callback fires
  - Modal closes
  - Page refreshes: window.location.reload()
  - Server list updates (server is gone)
```

## Error Handling

**If DELETE returns error:**

```json
{
  "error": "not_found",
  "message": "Server not found"
}
```

Modal shows:
```
⚠️ Server not found

[🗑️ Delete Server]
```

User can close modal and try again, or contact support if persistent.

**Common error scenarios:**

| Status | Cause | UX |
|--------|-------|----|
| 401 | User not authorized | "You don't have permission to delete this server" |
| 403 | User is not admin | "Only admins can delete servers" |
| 404 | Server doesn't exist | "Server not found" |
| 500 | Database error | "Failed to delete server. Please try again." |

## Testing Checklist

- [ ] Modal opens when Settings button is clicked
- [ ] Server ID is displayed correctly
- [ ] First Delete click shows confirmation text
- [ ] Second Delete click makes API request
- [ ] Loading spinner appears during deletion
- [ ] Modal closes on successful deletion
- [ ] Page refreshes and server list is updated
- [ ] API error is displayed in red
- [ ] Cancel button works (closes modal)
- [ ] Backdrop click closes modal (unless deleting)
- [ ] Buttons are disabled during deletion
- [ ] Bot actually leaves the Discord guild
- [ ] All tenant data is deleted from database

## Deployment Notes

- **Test in staging:** Create a test Discord server, configure bot for it, then delete it via dashboard to verify end-to-end flow
- **Monitor logs:** Watch bot logs to confirm guild-leave requests are successful
- **Verify cascade:** Query database after deletion to confirm tenant_settings, discord_users, sessions are all gone
- **User communication:** Notify admins that deletion is permanent and affects the entire server configuration

## See Also

- `cascade-delete-with-external-api-calls.md` — Backend pattern for this modal
- `axum-rest-api-design` skill — Pattern 4 (DELETE requests) for endpoint details

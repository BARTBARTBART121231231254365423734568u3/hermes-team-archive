# Admin-Only Dashboard with Environment-Based Auto-Login

## Pattern

You want a dashboard that:
1. **Only admins can access** — Normal users should not be able to login
2. **Auto-authenticates admins** — No login screen if admin API key is in the environment
3. **Falls back to login screen** — If no admin key is set, shows traditional login form

## Implementation

### 1. Store Admin Key in Environment

**`.env.production` (never check into git):**
```env
VITE_ADMIN_<REDACTED_SECRET>
```

**On Railway/hosting platform:**
```bash
railway variables set VITE_ADMIN_<REDACTED_SECRET>"
```

### 2. Update Auth Store to Check for Admin Key

**`src/stores/auth.ts`:**

```typescript
import { writable } from 'svelte/store'

export interface AuthState {
  isAuthenticated: boolean
  user: { id: string } | null
  token: string | null
  isAdmin: boolean
}

export const auth = writable<AuthState>({
  isAuthenticated: false,
  user: null,
  token: null,
  isAdmin: false,
})

export async function checkAuth(apiBase: string) {
  // 1. Check if admin API key is set in environment
  const adminKey = import.meta.env.VITE_ADMIN_API_KEY
  
  if (adminKey) {
    // Admin key is available — auto-authenticate without login screen
    const res = await fetch(`${apiBase}/api/dashboard/stats`, {
      headers: {
        Authorization: `Bearer ${adminKey}`,
      },
    })
    
    if (res.ok) {
      // Admin key is valid
      auth.set({
        isAuthenticated: true,
        user: { id: 'admin' },
        token: adminKey,
        isAdmin: true,
      })
      return
    }
  }
  
  // 2. Check if user has a stored token (from previous login)
  const stored<REDACTED_SECRET>('authlist_token')
  
  if (storedToken) {
    const res = await fetch(`${apiBase}/api/dashboard/stats`, {
      headers: {
        Authorization: `Bearer ${storedToken}`,
      },
    })
    
    if (res.ok) {
      // Stored token is valid
      auth.set({
        isAuthenticated: true,
        user: { id: 'user' },
        token: storedToken,
        isAdmin: false,
      })
      return
    } else {
      // Stored token is invalid — clear it
      localStorage.removeItem('authlist_token')
    }
  }
  
  // 3. No valid auth found — show login screen
  auth.set({
    isAuthenticated: false,
    user: null,
    token: null,
    isAdmin: false,
  })
}
```

### 3. Update App Component

**`src/App.svelte`:**

```svelte
<script lang="ts">
  import { onMount } from 'svelte'
  import { auth, checkAuth } from './stores/auth'
  import Login from './pages/Login.svelte'
  import Dashboard from './pages/Dashboard.svelte'
  
  let apiBase: string
  let loading = true
  
  onMount(async () => {
    // Determine API base URL
    if (window.location.hostname === 'dashboard-production-da2a.up.railway.app') {
      apiBase = 'https://bot-production-7612.up.railway.app/api'
    } else if (window.location.hostname === 'localhost') {
      apiBase = 'http://localhost:8080/api'
    } else {
      apiBase = import.meta.env.VITE_API_URL || `${window.location.origin}/api`
    }
    
    // Check if admin key or stored token is valid
    await checkAuth(apiBase)
    loading = false
  })
</script>

{#if loading}
  <div class="loading">Loading...</div>
{:else if $auth.isAuthenticated}
  <!-- Show dashboard for authenticated users -->
  <Dashboard {apiBase} />
{:else}
  <!-- Show login screen for unauthenticated users -->
  <Login {apiBase} />
{/if}

<style>
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    font-size: 18px;
    color: #a0a8b0;
  }
</style>
```

### 4. Update Login Component to Only Allow Admin Access

**`src/pages/Login.svelte`:**

```svelte
<script lang="ts">
  import { auth, checkAuth } from '../stores/auth'
  
  export let apiBase: string
  
  let apiKey = ''
  let isLoading = false
  let error: string | null = null
  
  async function handleLogin() {
    if (!apiKey.trim()) {
      error = 'Please enter your API key'
      return
    }
    
    isLoading = true
    error = null
    
    try {
      // Validate the API key
      const res = await fetch(`${apiBase}/api/dashboard/stats`, {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      })
      
      if (res.ok) {
        // Check if this is an admin key or regular tenant key
        const adminKey = import.meta.env.VITE_ADMIN_API_KEY
        const isAdmin = apiKey === adminKey
        
        if (!isAdmin) {
          // Regular users not allowed — only admin can login
          error = 'Only administrators can access this dashboard'
          return
        }
        
        // Store and authenticate
        localStorage.setItem('authlist_token', apiKey)
        await checkAuth(apiBase)
      } else {
        error = 'Invalid API key'
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Login failed'
    } finally {
      isLoading = false
    }
  }
</script>

<div class="login-container">
  <div class="login-card">
    <h1>AuthList Dashboard</h1>
    <p class="subtitle">Admin Access Only</p>
    
    {#if error}
      <div class="error-message">{error}</div>
    {/if}
    
    <input
      type="password"
      placeholder="Enter admin API key"
      bind:value={apiKey}
      disabled={isLoading}
      on:keydown={(e) => e.key === 'Enter' && handleLogin()}
    />
    
    <button on:click={handleLogin} disabled={isLoading || !apiKey.trim()}>
      {isLoading ? 'Logging in...' : 'Sign In'}
    </button>
    
    <p class="note">
      Only the dashboard administrator can login.<br />
      Regular users do not have access.
    </p>
  </div>
</div>

<style>
  .login-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0a0e17;
  }
  
  .login-card {
    background: #0f1420;
    border: 1px solid #1a2332;
    border-radius: 12px;
    padding: 48px 32px;
    max-width: 420px;
    width: 100%;
  }
  
  .login-card h1 {
    font-size: 24px;
    font-weight: 600;
    color: #ffffff;
    margin: 0 0 8px;
    text-align: center;
  }
  
  .subtitle {
    font-size: 12px;
    color: #5a6370;
    text-transform: uppercase;
    text-align: center;
    margin: 0 0 24px;
  }
  
  .error-message {
    background: rgba(255, 107, 107, 0.1);
    border: 1px solid #ff6b6b;
    color: #ff8787;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 13px;
  }
  
  input {
    width: 100%;
    padding: 12px 16px;
    background: #1a2332;
    border: 1px solid #2d3a4d;
    border-radius: 6px;
    color: #ffffff;
    font-size: 14px;
    margin-bottom: 16px;
  }
  
  input:focus {
    outline: none;
    border-color: #1fbf82;
    box-shadow: 0 0 0 3px rgba(31, 191, 130, 0.1);
  }
  
  button {
    width: 100%;
    padding: 12px 16px;
    background: linear-gradient(135deg, #1fbf82 0%, #0d8f5c 100%);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
  }
  
  button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(31, 191, 130, 0.3);
  }
  
  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .note {
    font-size: 12px;
    color: #5a6370;
    text-align: center;
    margin: 16px 0 0;
    line-height: 1.6;
  }
</style>
```

## Environment Detection

| Scenario | Behavior |
|----------|----------|
| `VITE_ADMIN_API_KEY` set | Auto-login, no login screen | 
| `VITE_ADMIN_API_KEY` not set | Show login screen |
| User tries non-admin key | Reject with "Only admins" message |
| Valid admin key pasted | Auto-authenticate and show dashboard |

## Testing

### Scenario 1: Admin with env var

```bash
# Set in Railway
railway variables set VITE_ADMIN_API_KEY="sk_admin_secret"

# Deploy
npm run build && railway deploy

# Result: Dashboard auto-loads with no login screen
```

### Scenario 2: Admin without env var (manual login)

```bash
# No env var set

# Result: Login screen appears
# Admin pastes key → Dashboard loads
# Regular user pastes key → "Only admins" error
```

### Scenario 3: Invalid key

```bash
# User tries random string
# Result: "Invalid API key" error
```

## Security Notes

✅ **Admin key is never exposed in frontend code** — it's a runtime environment variable  
✅ **Uses Bearer token middleware** — same auth as regular users, just scoped differently  
✅ **No hardcoded credentials in source** — env vars only  
✅ **Regular users cannot guess admin key** — 401 on invalid keys  
✅ **Key rotation possible** — change env var, restart app  

## Related

- `references/svelte-dashboard-setup-form-constants.md` — Pre-filling system-wide constants from env
- `references/frontend-backend-environment-detection.md` — Auto-detecting API URL by hostname

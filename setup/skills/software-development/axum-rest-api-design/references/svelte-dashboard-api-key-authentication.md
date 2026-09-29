# SvelteKit Dashboard Authentication with API Keys

## Problem

You have a SvelteKit dashboard that needs to authenticate users and make API calls to a protected Rust backend. Common approaches:

1. **Discord OAuth** — Complex, requires OAuth app setup, external provider
2. **JWT tokens** — Requires symmetric/asymmetric key management
3. **API keys** — Simple, works great if you already have per-tenant API keys in your backend

This reference covers **Option 3**, which is ideal for multi-tenant systems where each tenant already has a unique, long-lived API key.

## Implementation

### 1. Auth Store (Svelte)

```typescript
// src/stores/auth.ts
import { writable } from 'svelte/store'

export interface AuthState {
  isAuthenticated: boolean
  token: string | null
}

const initialState: AuthState = {
  isAuthenticated: false,
  <REDACTED_SECRET>('api_token'),
}

export const auth = writable<AuthState>(initialState)

/// Check if stored token is valid by calling the API
export async function checkAuth(apiBase: string) {
  const <REDACTED_SECRET>('api_token')
  
  if (!token) {
    auth.set({
      isAuthenticated: false,
      token: null,
    })
    return
  }

  try {
    // Verify token by calling an authenticated endpoint
    const res = await fetch(`${apiBase}/dashboard/stats`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (res.ok) {
      auth.set({
        isAuthenticated: true,
        token,
      })
    } else {
      // Token is invalid
      localStorage.removeItem('api_token')
      auth.set({
        isAuthenticated: false,
        token: null,
      })
    }
  } catch (e) {
    console.error('Failed to verify auth:', e)
  }
}

export function logout() {
  localStorage.removeItem('api_token')
  auth.set({
    isAuthenticated: false,
    token: null,
  })
}
```

### 2. Login Component

```svelte
<!-- src/pages/Login.svelte -->
<script lang="ts">
  import { onMount } from 'svelte'
  import { auth, checkAuth } from '../stores/auth'

  export let apiBase: string = 'http://localhost:8080/api'

  let isLoading = false
  let error: string | null = null
  let apiKey: string = ''

  onMount(async () => {
    // Check if we already have a valid token
    await checkAuth(apiBase)
  })

  async function handleLogin() {
    isLoading = true
    error = null
    
    if (!apiKey.trim()) {
      error = 'Please enter your API key'
      isLoading = false
      return
    }

    try {
      // Store the API key as token
      localStorage.setItem('api_token', apiKey.trim())
      // Verify it works by checking auth
      await checkAuth(apiBase)
      if (!$auth.isAuthenticated) {
        error = 'Invalid API key'
        localStorage.removeItem('api_token')
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Login failed'
      localStorage.removeItem('api_token')
      isLoading = false
    }
  }
</script>

{#if $auth.isAuthenticated}
  <div style="text-align: center; padding: 40px;">
    <p>Welcome! You are logged in.</p>
  </div>
{:else}
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-large">A</div>
        <h1>Dashboard</h1>
        <p class="subtitle">API Access</p>
      </div>

      <div class="login-body">
        <p class="login-description">
          Enter your API key to access the dashboard.
        </p>

        {#if error}
          <div class="error-message">{error}</div>
        {/if}

        <input
          type="password"
          placeholder="Paste your API key here"
          bind:value={apiKey}
          class="input-api-key"
          on:keydown={(e) => {
            if (e.key === 'Enter' && !isLoading) {
              handleLogin()
            }
          }}
        />

        <button
          class="btn-login"
          on:click={handleLogin}
          disabled={isLoading}
        >
          {#if isLoading}
            Authenticating...
          {:else}
            Sign In
          {/if}
        </button>

        <div class="help-text">
          <p><strong>Don't have an API key?</strong></p>
          <p>Contact your administrator to create a tenant and receive an API key.</p>
          <p style="font-size: 12px; color: #5a6370; margin-top: 12px;">
            Keys look like: <code>550e8400-e29b-41d4-a716-446655440000</code>
          </p>
        </div>

        <p class="login-footer">
          Your API key is secure and only used for authentication.
          <a href="/privacy" target="_blank">Privacy Policy</a>
        </p>
      </div>
    </div>
  </div>
{/if}

<style>
  .login-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: #0a0e17;
  }

  .login-card {
    width: 100%;
    max-width: 420px;
    background: #0f1420;
    border: 1px solid #1a2332;
    border-radius: 12px;
    padding: 48px 32px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
  }

  .login-header {
    text-align: center;
    margin-bottom: 32px;
  }

  .logo-large {
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, #1fbf82 0%, #1a9d6e 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    font-weight: 700;
    color: white;
    margin: 0 auto 16px;
  }

  .login-header h1 {
    font-size: 24px;
    font-weight: 600;
    color: #ffffff;
    margin: 0 0 8px;
  }

  .subtitle {
    font-size: 12px;
    color: #5a6370;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0;
  }

  .login-body {
    margin-bottom: 24px;
  }

  .login-description {
    font-size: 14px;
    color: #a0a8b0;
    line-height: 1.6;
    margin: 0 0 20px;
  }

  .error-message {
    background: rgba(255, 107, 107, 0.1);
    border: 1px solid #ff6b6b;
    border-radius: 6px;
    padding: 12px;
    font-size: 13px;
    color: #ff6b6b;
    margin-bottom: 16px;
  }

  .input-api-key {
    width: 100%;
    padding: 12px 14px;
    background: #0a0e17;
    border: 1px solid #1a2332;
    border-radius: 6px;
    font-size: 14px;
    color: #ffffff;
    margin-bottom: 12px;
    transition: all 0.2s;
    font-family: 'Monaco', 'Courier New', monospace;
  }

  .input-api-key:focus {
    outline: none;
    border-color: #1fbf82;
    box-shadow: 0 0 0 3px rgba(31, 191, 130, 0.1);
  }

  .input-api-key::placeholder {
    color: #5a6370;
  }

  .btn-login {
    width: 100%;
    padding: 12px 16px;
    background: #1fbf82;
    color: #0a0e17;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 16px;
  }

  .btn-login:hover:not(:disabled) {
    background: #17a267;
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(31, 191, 130, 0.3);
  }

  .btn-login:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .help-text {
    background: rgba(31, 191, 130, 0.05);
    border: 1px solid rgba(31, 191, 130, 0.2);
    border-radius: 6px;
    padding: 12px;
    font-size: 12px;
    color: #a0a8b0;
    margin-bottom: 16px;
  }

  .help-text p {
    margin: 0 0 8px;
  }

  .help-text p:last-child {
    margin: 0;
  }

  .help-text strong {
    color: #1fbf82;
  }

  .help-text code {
    background: #0a0e17;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Courier New', monospace;
    color: #1fbf82;
  }

  .login-footer {
    font-size: 12px;
    color: #5a6370;
    line-height: 1.5;
    margin: 0;
    text-align: center;
  }

  .login-footer a {
    color: #1fbf82;
    text-decoration: none;
  }

  .login-footer a:hover {
    text-decoration: underline;
  }
</style>
```

### 3. Protected API Calls

```typescript
// In any component that needs to call the API
import { auth } from '../stores/auth'

async function fetchDashboardStats(apiBase: string) {
  const <REDACTED_SECRET>('api_token')
  
  if (!token) {
    throw new Error('Not authenticated')
  }

  const res = await fetch(`${apiBase}/dashboard/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (res.status === 401) {
    // Token expired or invalid
    auth.set({
      isAuthenticated: false,
      token: null,
    })
    throw new Error('Authentication failed')
  }

  return res.json()
}
```

### 4. Main App Component (Routing)

```svelte
<!-- src/App.svelte -->
<script lang="ts">
  import { onMount } from 'svelte'
  import { auth, checkAuth } from './stores/auth'
  import Login from './pages/Login.svelte'
  import Dashboard from './pages/Dashboard.svelte'

  let apiBase: string

  // Auto-detect API base URL from deployment environment
  onMount(async () => {
    if (typeof window !== 'undefined') {
      if (window.location.hostname === 'dashboard-production-da2a.up.railway.app') {
        apiBase = 'https://bot-production-7612.up.railway.app/api'
      } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        apiBase = 'http://localhost:8080/api'
      } else {
        apiBase = import.meta.env.VITE_API_URL || `${window.location.origin}/api`
      }
    }

    // Check if user is already logged in
    await checkAuth(apiBase)
  })
</script>

{#if $auth.isAuthenticated}
  <Dashboard {apiBase} />
{:else}
  <Login {apiBase} />
{/if}
```

## Advantages of API Key Authentication for Dashboards

| Aspect | Discord OAuth | API Keys |
|--------|---------------|----------|
| Setup complexity | High (OAuth app config) | Low (just paste key) |
| External dependency | Yes (Discord API) | No |
| Time to implement | 4-6 hours | 1-2 hours |
| User experience | "Sign in with Discord" button | Paste key into form |
| Ideal for | User-facing apps | Internal tools, dashboards |
| Per-tenant isolation | Requires extra queries | Built-in |
| Key rotation | Via Discord | Via database update |

## When NOT to Use API Keys for Login

- **User-facing web app** where users sign up themselves → Use OAuth or JWT
- **Mobile app** where you want SSO → Use OAuth
- **Multiple permission levels per user** → Use JWT with claims
- **Very short session windows** (minutes) → Use Bearer tokens with expiry

## When TO Use API Keys for Login

- **Internal dashboards** (admins only)
- **B2B/Multi-tenant SaaS** (each tenant gets a key)
- **Service-to-service** (API-to-API auth)
- **Long-lived credentials** (months/years)
- **Simple per-tenant isolation** (no role-based access)

## Security Considerations

### What You Get (Secure)
- ✅ HTTPS-only transmission (if deployed on HTTPS)
- ✅ Per-tenant scoping (tenant key can't see other tenants)
- ✅ Easy revocation (delete key from database)
- ✅ No external dependencies (no OAuth leaks)

### What You DON'T Get (Not Secure Enough For)
- ❌ User sign-up flows (no password reset, no email verification)
- ❌ Public-facing apps (keys shouldn't be shared widely)
- ❌ Granular role-based access (keys are all-or-nothing per tenant)
- ❌ Expiring credentials (keys live indefinitely unless rotated)

### Best Practices

1. **Store admin token as environment variable:**
   ```bash
   export API_<REDACTED_SECRET>"
   ```
   Never commit to git.

2. **Generate tenant keys as UUIDs:**
   ```rust
   let api_key = uuid::Uuid::new_v4().to_string();
   ```
   Not user-friendly passwords.

3. **Return key only once:**
   ```rust
   // When creating tenant:
   "api_key": "550e8400-e29b-41d4-a716-446655440000"
   
   // When listing tenants:
   "api_key": null  // Don't echo keys
   ```

4. **Use password input field:**
   ```svelte
   <input type="password" bind:value={apiKey} />
   ```
   Masks the key on screen.

5. **Log sensitive operations:**
   ```rust
   tracing::info!("Tenant API key rotated for tenant_id={}", tenant_id);
   ```
   Not the key itself, just the action.

6. **Support key rotation:**
   ```sql
   UPDATE tenant_settings SET api_key = ? WHERE tenant_id = ?;
   ```
   So users can refresh compromised keys.

## Testing

```bash
# Create test tenant (returns api_key)
curl -X POST http://localhost:8080/api/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "name": "Test", "guild_id": "123" }'

# Response:
# { "id": "uuid", "name": "Test", "api_key": "550e8400-..." }

# Use the API key to authenticate
curl http://localhost:8080/api/dashboard/stats \
  -H "Authorization: <REDACTED_SECRET>"

# Response: Dashboard stats for that tenant only
```

## Troubleshooting

### Login Form Shows "Invalid API Key"
1. Verify the key is pasted correctly (no extra spaces)
2. Check that the backend `/api/dashboard/stats` endpoint works: `curl -H "Authorization: Bearer $KEY" ...`
3. Verify the key exists in `tenant_settings` table
4. Check database connection in the backend

### Dashboard Loads But Says "Not Connected"
1. Open browser DevTools → Network tab
2. Check if API calls are failing (status 401, 403, 5xx)
3. If 401: Check token in localStorage (`localStorage.getItem('api_token')`)
4. If 403: Check that token's tenant_id matches the resource being accessed
5. If 5xx: Check backend logs

### Key Works in curl But Not in Dashboard
1. Check that the Authorization header is being sent: DevTools → Network → Headers
2. Verify the format is exactly `Authorization: Bearer <key>` (no extra spaces)
3. Check that `apiBase` URL is correct
4. Check CORS headers if API is on different domain

## Related Patterns

- **Scoped API Key Middleware** — Backend implementation in Axum
- **Environment-aware Frontend URL** — Detecting deployment environment at runtime
- **Bearer Token Authentication** — Alternative for session-based auth

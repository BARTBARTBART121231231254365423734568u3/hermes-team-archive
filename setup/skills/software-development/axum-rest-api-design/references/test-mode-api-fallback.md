# Test Mode Fallback: Graceful Degradation When Backend APIs Are Incomplete

## Problem

During development, your backend is incomplete or has stub endpoints:
- OAuth endpoints exist but don't work
- Admin token deployment delayed
- Database API key lookup failing
- External API (Discord, Steam) temporarily unavailable

**Without fallback:** Frontend breaks, users can't test anything.  
**With fallback:** Frontend works in test mode, using dummy/relaxed validation.

## Pattern: Test Mode Flag

### 1. Add Test Mode to Auth Store

**`src/stores/auth.ts`:**

```typescript
const IS_TEST_MODE = import.meta.env.MODE === 'development' || 
                    import.meta.env.DEV === true

export async function checkAuth(apiBase: string) {
  const <REDACTED_SECRET>('authlist_token')
  
  if (!token) {
    auth.set({
      isAuthenticated: false,
      user: null,
      token: null,
    })
    return
  }
  
  try {
    // Try real validation
    const res = await fetch(`${apiBase}/api/dashboard/stats`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    
    if (res.ok) {
      // Real auth succeeded
      auth.set({
        isAuthenticated: true,
        user: { id: 'user' },
        token,
      })
      return
    }
    
    if (res.status === 401) {
      // Invalid token
      localStorage.removeItem('authlist_token')
      auth.set({
        isAuthenticated: false,
        user: null,
        token: null,
      })
      return
    }
    
    // 500 or 503 (backend error/incomplete) — fall back to test mode
    if (IS_TEST_MODE && (res.status === 500 || res.status === 503)) {
      console.warn('Backend API incomplete — enabling test mode')
      auth.set({
        isAuthenticated: true,
        user: { id: 'test-user' },
        token,
      })
      return
    }
    
    // Other error
    throw new Error(`Auth check failed: ${res.status}`)
  } catch (err) {
    if (IS_TEST_MODE) {
      // Network error in dev — allow login anyway
      console.warn('Auth check failed (dev mode) — proceeding with test token', err)
      auth.set({
        isAuthenticated: true,
        user: { id: 'test-user' },
        token,
      })
    } else {
      // Production — fail hard
      auth.set({
        isAuthenticated: false,
        user: null,
        token: null,
      })
    }
  }
}
```

### 2. Relax Login Validation in Test Mode

**`src/pages/Login.svelte`:**

```svelte
<script lang="ts">
  import { auth, checkAuth } from '../stores/auth'
  
  const IS_TEST_MODE = import.meta.env.MODE === 'development'
  
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
      // Try real validation
      const res = await fetch(`${apiBase}/api/dashboard/stats`, {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      })
      
      if (res.ok) {
        // Valid key
        localStorage.setItem('authlist_token', apiKey)
        await checkAuth(apiBase)
        return
      }
      
      if (res.status === 401) {
        error = 'Invalid API key'
        return
      }
      
      // Backend error — test mode fallback
      if (IS_TEST_MODE && (res.status === 500 || res.status === 503)) {
        console.warn('Backend unavailable — using test mode')
        localStorage.setItem('authlist_token', apiKey)
        auth.set({
          isAuthenticated: true,
          user: { id: 'test-user' },
          token: apiKey,
        })
        return
      }
      
      error = 'Login failed — please try again'
    } catch (err) {
      if (IS_TEST_MODE) {
        // Network error in dev — allow anyway
        console.warn('Network error in test mode — proceeding', err)
        localStorage.setItem('authlist_token', apiKey)
        auth.set({
          isAuthenticated: true,
          user: { id: 'test-user' },
          token: apiKey,
        })
      } else {
        error = 'Network error — please check your connection'
      }
    } finally {
      isLoading = false
    }
  }
</script>

{#if IS_TEST_MODE}
  <div class="test-mode-banner">🔧 TEST MODE: Any non-empty key will login</div>
{/if}

<!-- Login form -->
```

### 3. Mock Incomplete API Endpoints

When parts of the backend aren't ready, create a local mock:

**`src/lib/api.ts`:**

```typescript
const IS_TEST_MODE = import.meta.env.MODE === 'development'

export async function fetchDashboardStats(apiBase: string, token: string) {
  try {
    const res = await fetch(`${apiBase}/api/dashboard/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    
    if (res.ok) {
      return res.json()
    }
    
    if (IS_TEST_MODE) {
      // Return mock data for incomplete backend
      console.warn('Dashboard stats not ready — using mock data')
      return {
        servers: [
          { id: '1', name: 'Test Server 1', members: 150 },
          { id: '2', name: 'Test Server 2', members: 320 },
        ],
        totalMembers: 470,
        activeNow: 42,
      }
    }
    
    throw new Error(`Failed to fetch stats: ${res.status}`)
  } catch (err) {
    if (IS_TEST_MODE) {
      console.warn('Returning mock data due to error', err)
      return {
        servers: [
          { id: '1', name: 'Test Server 1', members: 150 },
        ],
        totalMembers: 150,
        activeNow: 10,
      }
    }
    throw err
  }
}
```

### 4. Mark Test Mode in UI

**`src/App.svelte`:**

```svelte
<script lang="ts">
  const IS_TEST_MODE = import.meta.env.MODE === 'development'
</script>

{#if IS_TEST_MODE}
  <div class="test-mode-badge">⚙️ TEST MODE</div>
{/if}

<!-- Rest of app -->

<style>
  .test-mode-badge {
    position: fixed;
    top: 12px;
    right: 12px;
    background: rgba(255, 152, 0, 0.2);
    border: 1px solid #ff9800;
    color: #ffb74d;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    z-index: 1000;
  }
</style>
```

## When Test Mode Should Be Enabled

✅ **Enable when:**
- Building/testing dashboard locally with incomplete backend
- Backend auth API not yet deployed
- External API (Discord, Steam) temporarily down
- Developing frontend UI independently from backend
- Writing UI tests that need data fixtures

❌ **Never enable in production:**
- Always set `IS_TEST_MODE = false` in production builds
- Test mode credentials should never work on production servers
- Production auth must be real and strict

## Implementation Checklist

- [ ] Add `IS_TEST_MODE` flag based on build environment
- [ ] Relax validation in test mode (optional: allow any non-empty key)
- [ ] Add visual indicator (banner/badge) that test mode is active
- [ ] Mock incomplete API endpoints with dummy data
- [ ] Log warnings when test mode is being used
- [ ] Ensure test mode cannot be enabled in production
- [ ] Remove or disable test mode before shipping
- [ ] Add comment: "TEST MODE: Remove before production"

## Code Comment Example

```typescript
// TEST MODE: This allows any non-empty API key in development.
// Remove or disable this before deploying to production.
// In production, auth must validate keys against the database.
if (IS_TEST_MODE && token.trim()) {
  auth.set({
    isAuthenticated: true,
    user: { id: 'test-user' },
    token,
  })
}
```

## Pitfall: Forgetting to Remove Test Mode

**Bad (left in production):**
```typescript
// ❌ This allows ANY key to work on production
auth.set({
  isAuthenticated: true,  // Always succeeds!
  token: apiKey,
})
```

**Good (removed before shipping):**
```typescript
// ✅ Production only accepts real keys from database
const res = await fetch(`${apiBase}/api/validate-key`, {
  headers: { Authorization: `Bearer ${apiKey}` },
})

if (res.status === 401) {
  error = 'Invalid key'
  return
}
```

## Migration Path: From Test Mode to Real Auth

### Phase 1: Build with Test Mode
```typescript
const IS_TEST_MODE = true  // Any key works
```

### Phase 2: Backend Ready
```typescript
const IS_TEST_MODE = import.meta.env.MODE === 'development'  // Only in dev
```

### Phase 3: Disable Test Mode
```typescript
const IS_TEST_MODE = false  // Real auth only
```

## Related

- `frontend-auth-testing-patterns` skill — Full auth testing patterns
- `references/admin-only-dashboard-auto-login.md` — Secure admin authentication

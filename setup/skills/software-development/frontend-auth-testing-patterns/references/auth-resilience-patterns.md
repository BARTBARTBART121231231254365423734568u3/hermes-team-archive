# Auth Resilience Patterns: Protecting Stored Credentials

## The Problem

When a frontend auth check makes a network round-trip to validate a token, it can fail for reasons completely unrelated to the token's validity:

- API server mid-restart (transient 5xx)
- Database connection timeout
- Network blip or timeout
- Deployment in progress
- Rate limiter rejection

**Anti-pattern:** Clearing stored credentials on ANY non-2xx response, treating transient failures as auth failures.

Result: Single transient error anywhere in the auth flow → token wiped → user logged out → "Invalid username or password" on next login, even though nothing was wrong with the password.

### Real Example (AuthList, Aug 31 2026)

```typescript
// ❌ WRONG: Clears token on ANY non-2xx
export async function checkAuth(apiBase: string) {
  const <REDACTED_SECRET>('authlist_token')
  
  try {
    const res = await fetch(`${apiBase}/dashboard/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    
    if (!res.ok) { // 4xx, 5xx, anything!
      localStorage.removeItem('authlist_token') // WRONG
    }
  } catch (err) {
    localStorage.removeItem('authlist_token') // WRONG
  }
}
```

**Scenario that breaks this:**
1. User deletes a server
2. Dashboard reloads immediately
3. Backend is restarting (intentional deploy or auto-restart after deletion)
4. `/dashboard/stats` returns 502 Bad Gateway
5. Code clears the token
6. User is logged out
7. Tries to log back in with correct password
8. Backend eventually recovers and accepts token
9. But token is gone — looks like "Invalid username or password"

## The Fix

**Only clear credentials on ACTUAL auth failures (401, 403).** Keep them on transient failures.

```typescript
// ✅ CORRECT: Distinguish auth failures from transient failures
export async function checkAuth(apiBase: string) {
  const <REDACTED_SECRET>('authlist_token')
  
  if (!token) {
    auth.set({ isAuthenticated: false, user: null, token: null })
    return
  }
  
  try {
    const res = await fetch(`${apiBase}/dashboard/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    
    if (res.status === 401 || res.status === 403) {
      // Real auth failure — token is invalid/expired
      localStorage.removeItem('authlist_token')
      auth.set({ isAuthenticated: false, user: null, token: null })
      return
    }
    
    if (!res.ok) {
      // Transient error (5xx, network, timeout)
      // Keep token, just don't mark authenticated for this check
      auth.set({
        isAuthenticated: false,
        user: null,
        token: null, // Don't wipe localStorage!
      })
      return
    }
    
    // Success
    auth.set({
      isAuthenticated: true,
      user: { id: 'admin', name: 'Administrator' },
      token,
    })
  } catch (err) {
    // Network error reaching the API at all
    // Keep token, just don't authenticate
    auth.set({
      isAuthenticated: false,
      user: null,
      token: null,
    })
  }
}
```

**Key behaviors:**

| Response | Action | Reasoning |
|----------|--------|----------|
| **200 OK** | Authenticate | Real success |
| **401/403** | Clear token, reject | Real auth failure; token is invalid |
| **5xx, timeout, network error** | Keep token, show login page | Transient backend issue; retry on next page load or refresh |

## Why This Matters

1. **Token validity ≠ API availability** — A valid token is still valid if the backend is temporarily down.
2. **Transient failures are common in production** — Deploys, restarts, DB timeouts, network hiccups.
3. **Silent token loss is a UX disaster** — User tries to log back in, "wrong password" error, but password is correct.
4. **Retry is automatic** — Browser refresh, next page load, or 30s poll hits healthy backend and re-authenticates without user action.

## Testing the Pattern

Write tests that verify each behavior:

```typescript
// Test: 200 OK → authenticate
it('authenticates on 200 OK', async () => {
  localStorage.setItem('authlist_token', 'test_token')
  
  fetch.mockResolvedValueOnce({
    status: 200,
    ok: true,
    json: async () => ({ /* data */ })
  })
  
  await checkAuth('http://localhost/api')
  
  expect(localStorage.getItem('authlist_token')).toBe('test_token') // Still there
  expect($auth).toHaveProperty('isAuthenticated', true)
})

// Test: 401 → clear token
it('clears token on 401', async () => {
  localStorage.setItem('authlist_token', 'test_token')
  
  fetch.mockResolvedValueOnce({
    status: 401,
    ok: false,
  })
  
  await checkAuth('http://localhost/api')
  
  expect(localStorage.getItem('authlist_token')).toBeNull() // Cleared
  expect($auth).toHaveProperty('isAuthenticated', false)
})

// Test: 502 → keep token
it('keeps token on 502', async () => {
  localStorage.setItem('authlist_token', 'test_token')
  
  fetch.mockResolvedValueOnce({
    status: 502,
    ok: false,
  })
  
  await checkAuth('http://localhost/api')
  
  expect(localStorage.getItem('authlist_token')).toBe('test_token') // Still there
  expect($auth).toHaveProperty('isAuthenticated', false) // Not authenticated now
  // But token survives for retry
})

// Test: Network timeout → keep token
it('keeps token on network error', async () => {
  localStorage.setItem('authlist_token', 'test_token')
  
  fetch.mockRejectedValueOnce(new Error('Network timeout'))
  
  await checkAuth('http://localhost/api')
  
  expect(localStorage.getItem('authlist_token')).toBe('test_token') // Still there
  expect($auth).toHaveProperty('isAuthenticated', false) // Not authenticated now
})
```

## Checklist for Production

- [ ] 401/403 responses clear token from localStorage
- [ ] Other error statuses (4xx, 5xx) do NOT clear token
- [ ] Network errors (timeouts, connection refused) do NOT clear token
- [ ] Token value is a string, not an object
- [ ] Store state includes `isAuthenticated`, `token`, and `user` fields
- [ ] Tests verify each scenario (200, 401, 5xx, network error)
- [ ] Error messages distinguish between "token invalid" (401) and "server down" (5xx)
- [ ] Page reload after transient failure re-authenticates without user action

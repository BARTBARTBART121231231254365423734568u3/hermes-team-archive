# OAuth Endpoint Stubs: A Debugging Nightmare

## The Problem

You're building a web app with a Rust backend and SvelteKit dashboard. You want Discord OAuth eventually, so you add the routes:

```rust
// bot/src/api/routes.rs
pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/oauth/login", get(oauth_login))
        .route("/oauth/callback", get(oauth_callback))
        .route("/oauth/logout", get(oauth_logout))
        .with_state(state)
}

async fn oauth_login() -> Redirect {
    Redirect::temporary("/oauth/callback")
}

async fn oauth_callback() -> Html<&'static str> {
    Html("<h1>OAuth Callback</h1>")
}
```

Then your dashboard tries to use them:

```typescript
// dashboard/src/stores/auth.ts
export async function loginWithDiscord(apiBase: string) {
  const loginUrl = `${apiBase}/oauth/login`
  window.location.href = loginUrl  // Calls the stub
}
```

## What Happens

1. User clicks "Sign in with Discord"
2. Browser navigates to `https://bot.example.com/oauth/login`
3. Stub handler returns `Redirect::temporary("/oauth/callback")` (HTTP 307)
4. Browser follows redirect to `/oauth/callback`
5. Stub handler returns HTML: `<h1>OAuth Callback</h1>`
6. User is NOT logged in
7. Frontend checks authentication, finds no token
8. "Invalid Token" or "Not Authenticated" error
9. Confused user. Confused developer. Hours of debugging.

## Why This Is a Trap

### 1. **Silent Failure**
No error messages. The routes exist and respond (with garbage), so it LOOKS like they work.

```bash
$ curl https://bot.example.com/oauth/login
# Returns 307 redirect (looks fine!)

$ curl -L https://bot.example.com/oauth/login
# Follows redirect, returns <h1>OAuth Callback</h1> (looks fine!)
```

But the frontend is broken.

### 2. **Dead Code Accumulation**
You add OAuth stubs intending to implement them "later." But:
- Feature freeze comes, no time for OAuth
- You move to other projects
- OAuth stubs never get completed
- Years later, someone finds half-working OAuth code and wastes time trying to use it

### 3. **Mixed Authentication Patterns**
Now your codebase has:
- OAuth stub routes (non-functional)
- API key routes (working)
- Session token routes (maybe working)
- Bearer token middleware (for API)

Which auth method actually works? Nobody knows.

### 4. **Deployment Coupling**
If you COMMIT the OAuth stubs, they end up in production, wasting:
- Binary size (unused code)
- Maintenance burden (stale code)
- Confusion for future developers

## Real-World Case Study: AuthList Session

**Timeline:**
1. Built bot with Discord OAuth scaffold (planning for future)
2. Deployed to Railway
3. Built SvelteKit dashboard, added Discord OAuth button
4. Dashboard tries to call `/api/oauth/login`
5. Gets 307 redirect (stub)
6. User sees login failure
7. Debugged for 2+ hours:
   - Checked Discord app config (doesn't exist yet)
   - Checked middleware (fine)
   - Checked routes (exist but are stubs)
   - Checked deployment (working)
8. **Root cause:** OAuth endpoints were never implemented
9. **Solution:** Remove OAuth stubs, switch to API key auth
10. **Time wasted:** 2+ hours
11. **Lesson:** Don't create stubs for things you won't implement immediately

## The Fix

### Short-Term: Remove Stubs

Delete the OAuth endpoint stubs entirely:

```rust
// ✓ DO THIS: Don't even add the routes if they're not functional
pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        // NO oauth routes at all
        .route("/api/health", get(health_check))
        .route("/api/dashboard/stats", get(get_stats))
        .with_state(state)
}
```

### Medium-Term: Use a Working Auth Pattern

Pick ONE auth pattern and implement it completely:

#### Option A: API Keys (Recommended for Dashboards)

```rust
// Middleware validates Bearer tokens against database
pub struct ApiAuth(pub AuthPrincipal);

#[axum::async_trait]
impl<S> FromRequestParts<S> for ApiAuth where ...
{
    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, StatusCode> {
        let <REDACTED_SECRET>(parts)?;
        let tenant_id = db::get_tenant_by_api_key(token).await?;
        Ok(ApiAuth(AuthPrincipal::Tenant(tenant_id)))
    }
}
```

**Frontend:**
```typescript
// dashboard/src/pages/Login.svelte
let apiKey = ''

async function handleLogin() {
  localStorage.setItem('api_token', apiKey)
  const res = await fetch(`${apiBase}/api/health`, {
    headers: { Authorization: `Bearer ${apiKey}` }
  })
  if (res.ok) {
    // Logged in
  }
}
```

**Implementation time:** 1-2 hours
**Status:** Production-ready immediately

#### Option B: Session Tokens (If You Have Sessions Table)

Just validate existing tokens:

```rust
// middleware checks sessions table
let session = db::get_session(token).await?;
if !session.is_valid() {
    return Err(StatusCode::UNAUTHORIZED);
}
```

**Implementation time:** 0 hours (already have it)
**Status:** Use immediately

#### Option C: JWT (If You Need Expiring Tokens)

```rust
use jsonwebtoken::{encode, decode};

// Issue token
let claims = Claims { sub: user_id, exp: now + 24h };
let token = encode(&Header::default(), &claims, &key)?;

// Validate token
let claims = decode::<Claims>(token, &key, &Validation::default())?;
```

**Implementation time:** 2-3 hours
**Status:** Production-ready after testing

### Long-Term: Do OAuth Right (or Not at All)

If you really need Discord OAuth:

1. Create Discord developer app
2. Implement full OAuth2 flow:
   - `GET /oauth/login` → Redirect to Discord
   - `GET /oauth/callback` → Exchange code for token
   - Store session or issue JWT
   - Return login success to frontend
3. Test end-to-end
4. **Then** deploy

**Implementation time:** 4-6 hours
**Status:** Don't start until you have the time

**Or:** Decide you don't need Discord auth and just use API keys / sessions instead.

## Decision Framework

### Before Adding Any Auth Endpoint:

Ask yourself:
1. **Do I have time to fully implement this auth method now?**
   - Yes → Implement it now
   - No → Don't add ANY stubs

2. **What auth method will actually work with my current setup?**
   - Sessions table exists → Validate sessions
   - Need long-lived creds → Use API keys
   - Need user sign-up → Use OAuth (only if doing it right)

3. **Can I implement it in < 4 hours?**
   - Yes → Do it now (sessions, API keys, JWT)
   - No → Pick a simpler method, or wait until you have time

### Checklist: Is This Auth Pattern Actually Working?

Before deploying, verify:

- [ ] Frontend can log in (not stuck on login page)
- [ ] API calls include authentication header
- [ ] API validates the credential (returns 401 if missing/invalid)
- [ ] Logged-in user can access protected routes
- [ ] Unauthenticated requests are rejected
- [ ] No console errors or network 307s
- [ ] Tested in local dev, staging, and production

If ANY of these fail, the auth pattern isn't working. Fix it before deploying.

## Anti-Patterns to Avoid

### ❌ Don't: Auth Routes That Redirect Nowhere
```rust
async fn oauth_login() -> Redirect {
    Redirect::temporary("/oauth/callback")  // Why? Callback is empty anyway
}
```

### ❌ Don't: Auth Routes That Return Placeholders
```rust
async fn oauth_callback() -> Html<&'static str> {
    Html("<h1>OAuth Callback</h1>")  // This isn't authentication
}
```

### ❌ Don't: Mix Multiple Auth Methods Without Documentation
```rust
// Which one actually works? OAuth? Sessions? API keys? Nobody knows.
.route("/oauth/login", get(oauth_login))
.route("/api/auth/login", post(api_login))
.route("/sessions/new", post(new_session))
```

### ❌ Don't: Commit Unfinished OAuth Without a Ticket/Plan
```bash
# If you commit OAuth stubs, also commit a GitHub issue
# saying WHY they exist and WHEN you'll finish them
# Otherwise, future developers waste time trying to use them
```

### ✓ Do: Pick ONE Auth Method
```rust
// Our app uses: API key authentication (Bearer token)
// Admin token in env var, per-tenant keys in database
// See: axum-rest-api-design skill, Pattern 8

pub struct ApiAuth(pub AuthPrincipal);
// ... implementation ...
```

### ✓ Do: Document Your Choice
```markdown
# Authentication

This app uses Bearer token authentication.

- **Admin Token:** Set `API_TOKEN` environment variable
- **Tenant Keys:** Generated at tenant creation time, stored in `tenant_settings.api_key`
- **Frontend:** Uses API key from localStorage, sent as `Authorization: Bearer <key>` header

See: `axum-rest-api-design/references/svelte-dashboard-api-key-authentication.md`
```

### ✓ Do: Remove Stubs Immediately

If you realize a stub isn't being used:

```bash
# Delete it
git rm bot/src/api/oauth.rs

# Remove from routes
# (no more dangling references)

# Commit with clear message
git commit -m "Remove unused OAuth stub endpoints

The OAuth flow is not yet implemented.
Using API key authentication instead (see Pattern 8)."
```

## Lessons Learned

1. **Don't scaffold future auth** — Implement what you need now
2. **Auth must work end-to-end** — Test it before merging
3. **Stubs are easy to commit and forget** — Actively avoid this
4. **One auth method per app** — Pick the simplest one that works
5. **Document your choice** — Future developers will thank you

## See Also

- `Pattern 8: Scoped API Key Authentication` in main SKILL.md
- `references/svelte-dashboard-api-key-authentication.md` — Working implementation
- Real-world case: AuthList session (multi-tenant SaaS, used API keys after removing OAuth stubs)

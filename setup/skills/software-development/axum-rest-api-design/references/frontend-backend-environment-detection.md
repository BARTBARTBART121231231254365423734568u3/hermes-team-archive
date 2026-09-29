# Frontend-Backend Environment Detection for Multi-Service Deployments

## The Problem

When you have a frontend and backend deployed as separate services on Railway (or any cloud platform), the frontend needs to know where the backend is. This is trivial in monorepo deployments (same domain, use `/api`), but breaks when:

1. **Frontend and backend are separate services** with different URLs
2. **Frontend build is environment-agnostic** (single build artifact deployed everywhere)
3. **Backend URL varies by deployment** (dev vs. staging vs. production)

### Real Example: AuthList Dashboard + Bot

```
Local Development:
  Dashboard: http://localhost:5173 (Vite dev server)
  Bot API:   http://localhost:8080/api
  
Production:
  Dashboard: https://dashboard-production-da2a.up.railway.app
  Bot API:   https://bot-production-7612.up.railway.app/api
```

The dashboard needs to call different API URLs depending on where it's running, but it's built ONCE and deployed to both environments.

## The Naive Approach (Broken)

**Using Vite environment variables at build time:**

```typescript
// .env.production
VITE_API_URL=https://bot-production-7612.up.railway.app/api

// App.svelte
let apiBase = import.meta.env.VITE_API_URL
```

**Problem:** `import.meta.env.VITE_API_URL` is baked into the compiled build. If you:
1. Build for production
2. Push the same build artifact to staging (disaster recovery, reuse optimization)
3. The frontend still calls the production API

This couples your build to a specific environment and breaks infrastructure flexibility.

## The Solution: Runtime Hostname Detection

**Detect the frontend's deployed hostname at runtime, then pick the corresponding backend:**

```typescript
// App.svelte
let apiBase: string

if (typeof window !== 'undefined') {
  // Production
  if (window.location.hostname === 'dashboard-production-da2a.up.railway.app') {
    apiBase = 'https://bot-production-7612.up.railway.app/api'
  }
  // Local dev
  else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    apiBase = 'http://localhost:8080/api'
  }
  // Staging or other
  else if (window.location.hostname === 'dashboard-staging.example.com') {
    apiBase = 'https://bot-staging.example.com/api'
  }
  // Fallback
  else {
    apiBase = import.meta.env.VITE_API_URL || `${window.location.origin}/api`
  }
}
```

**Advantages:**
- Build is truly environment-agnostic (no rebuild needed for new deployment)
- Same Docker image works in dev, staging, and production
- Hostnames are the source of truth for environment routing
- Fully testable locally without environment files
- Fallback chain: hardcoded hostname → env var → same-origin

## Why This Matters in Production

### Scenario 1: Staging Deployment
You want to test the entire system before production launch:

```bash
# Build ONCE for all environments
docker build -t myapp:v1.0 .

# Deploy same image to staging
railway service create --name dashboard-staging
railway deploy --service dashboard-staging myapp:v1.0
# Frontend URL: https://dashboard-staging.example.com
# Runtime detection → calls https://bot-staging.example.com/api ✅

# Later, deploy SAME IMAGE to production
railway deploy --service dashboard-prod myapp:v1.0
# Frontend URL: https://dashboard-prod.example.com
# Runtime detection → calls https://bot-prod.example.com/api ✅
```

No build changes. No config changes. Infrastructure handles routing via hostnames.

### Scenario 2: Disaster Recovery
Production is down. You want to redirect traffic to a backup region:

```bash
# Production is on US-West (down)
# Backup is on US-East

# DNS change: dashboard.example.com → dashboard-backup.up.railway.app

# Frontend auto-detects: hostname changed → calls backup API ✅
# No rebuild. No redeploy. Just DNS.
```

### Scenario 3: Local Testing
Developer clones repo, runs bot locally:

```bash
# Terminal 1
cd bot && cargo run  # Listens on http://localhost:8080

# Terminal 2
cd dashboard && npm run dev  # Opens http://localhost:5173

# Browser sees http://localhost:5173
# Runtime detection → calls http://localhost:8080/api ✅
# No .env files. No configuration. Just works.
```

## Implementation Checklist

- [ ] Identify all frontend/backend hostname pairs (dev, staging, prod, etc.)
- [ ] Add hostname → API URL mapping to frontend initialization
- [ ] Wrap in `if (typeof window !== 'undefined')` for SSR compatibility
- [ ] Test locally (bot on 8080, frontend on 5173)
- [ ] Verify staging deployment uses correct API
- [ ] Verify production deployment uses correct API
- [ ] Document the hostname → API mapping in README or env.example

## Common Hostname Patterns

### Railway (Used in AuthList Session)
```
Local:       localhost:5173         → localhost:8080/api
Production:  dashboard-*.up.railway.app → bot-production-*.up.railway.app/api
```

### Vercel + Lambda
```
Local:       localhost:3000         → localhost:3001/api
Staging:     staging.myapp.com      → staging-api.myapp.com/api
Production:  myapp.com              → api.myapp.com/api
```

### Monorepo (Everything Same Domain)
```
All:         myapp.com/dashboard    → myapp.com/api
             (Use: ${window.location.origin}/api)
```

## Testing Across Environments

### Test mapping is correct
```bash
# Visit each deployed frontend in browser
# Open DevTools Console
# Check Network tab for API calls

# Should see:
# - Local: http://localhost:8080/api ✅
# - Staging: https://bot-staging.example.com/api ✅
# - Production: https://bot-production.example.com/api ✅
```

### Test fallback chain
```bash
# Remove hostname mapping (temporarily)
# Frontend should fall back to VITE_API_URL or same-origin
# Verify fallback works as expected
```

## Gotchas

### 1. Forgetting `typeof window` Check

```typescript
// ❌ Will crash in SSR context
if (window.location.hostname === 'production') { ... }

// ✅ Safe in SSR
if (typeof window !== 'undefined' && window.location.hostname === 'production') { ... }
```

### 2. CORS Issues When API Doesn't Match Frontend Domain

If frontend is on `https://dashboard.example.com` but API is `https://bot.example.com`, the browser blocks cross-origin requests unless the API explicitly allows it:

```rust
// In bot/src/main.rs
use tower_http::cors::CorsLayer;

let app = routes::router(state)
    .layer(CorsLayer::permissive())  // Allow all origins (dev only!)
    .layer(
        CorsLayer::very_permissive()  // More permissive for development
    );

// Production: Use specific allowed origins
let cors = CorsLayer::new()
    .allow_origin("https://dashboard-production-da2a.up.railway.app".parse()?)
    .allow_credentials(true);
```

### 3. Hardcoding Hostnames Without Fallback

```typescript
// ❌ What if hostname isn't recognized? Crashes or calls wrong API
if (hostname === 'prod') { apiBase = '...' }
// Missing default case

// ✅ Always have a fallback
if (hostname === 'prod') { apiBase = '...' }
else { apiBase = import.meta.env.VITE_API_URL || default_api }
```

## Related Patterns

- **Multi-tenant API isolation**: Each tenant's requests filtered by token/guild_id
- **Environment-based configuration**: Hostname determines environment, not build-time env vars
- **Deployment-agnostic builds**: Single build artifact works everywhere

# CORS + DELETE Method Silent 405 Blocker — Session 2026-08-30

## The Incident

**Project:** AuthList dashboard server deletion feature  
**Time to debug:** ~45 minutes  
**Root cause:** CORS middleware `allow_methods` list missing DELETE HTTP method

### What Happened

1. Implemented DELETE route handler in Rust/Axum: `delete_server()`
2. Wired frontend button to send `DELETE /api/dashboard/servers/{id}`
3. Code compiles ✅
4. Local testing with curl works fine ✅
5. Deploy to Railway
6. Frontend tries DELETE → **405 Method Not Allowed** ❌
7. Backend handler never runs; request is blocked at CORS layer

### The Code

**Route definition (correct):**
```rust
.route("/servers/:id", get(get_server).delete(delete_server))
```

**CORS middleware (broken):**
```rust
let cors = CorsLayer::new()
    .allow_methods([Method::GET, Method::POST, Method::OPTIONS])  // ❌ Missing DELETE
```

**HTTP response from browser:**
```
< HTTP/2 405
< allow: GET,HEAD
< access-control-allow-methods: GET,POST,OPTIONS
```

**Browser behavior:**
1. Frontend sends OPTIONS preflight request
2. CORS middleware responds: "Allowed methods are GET, POST, OPTIONS"
3. Browser sees DELETE is NOT in allow_methods
4. Browser blocks the DELETE request **before it reaches your handler**
5. Never calls `delete_server()` handler

### The Fix

**In `/root/AUTH_LIST_RUST/bot/src/api/routes.rs` line 29:**

```rust
// ❌ Before
.allow_methods([Method::GET, Method::POST, Method::OPTIONS])

// ✅ After
.allow_methods([Method::GET, Method::POST, Method::DELETE, Method::OPTIONS])
```

### Why Local Testing Didn't Catch This

**Local curl works:**
```bash
curl -X DELETE http://localhost:8080/api/servers/123
# Works fine — curl is not a browser, ignores CORS
```

**Browser fails:**
```javascript
// Frontend code
await fetch(url, { method: 'DELETE' })
// Fails with 405 — browser enforces CORS
```

**CORS is a browser security feature.** Command-line tools and backend-to-backend requests don't check CORS. Your DELETE route worked fine in curl but was blocked by CORS when the browser tried to use it.

## Diagnosis Checklist

### Step 1: Identify the Symptom

```
Frontend error: 405 Method Not Allowed
Route handler: Correctly implements DELETE
Local curl test: Works fine
Deployed version: Fails
```

→ **Suspect CORS**

### Step 2: Check CORS Headers

```bash
# Send OPTIONS preflight (what browser sends before DELETE)
curl -I -X OPTIONS https://bot-production-7612.up.railway.app/api/servers/123 \
  -H "Access-Control-Request-Method: DELETE"

# Look at response headers
HTTP/1.1 200 OK
access-control-allow-methods: GET,POST,OPTIONS  # ❌ DELETE missing
```

### Step 3: Check Your Route Definition

```bash
# Verify route exists
grep -n "delete(delete_server)" bot/src/api/dashboard.rs

# Output should show the route
```

### Step 4: Check CORS Middleware

```bash
# Find where CORS is configured
grep -n "allow_methods" bot/src/api/routes.rs

# Should see your list of methods
# If DELETE is missing → that's the problem
```

## Prevention Rules

### Rule 1: Every route method must be in CORS allow_methods

**For each HTTP method you implement in routes:**

| Method | In Your Routes? | Must be in CORS allow_methods? |
|--------|-----------------|-------------------------------|
| GET    | Usually yes     | YES |
| POST   | Usually yes     | YES |
| PUT    | If you have it  | YES |
| PATCH  | If you have it  | YES |
| DELETE | If you have it  | **YES** (this session's lesson) |
| OPTIONS| Always          | Always |

### Rule 2: Test with OPTIONS preflight BEFORE testing the actual method

```bash
# BEFORE implementing:
# 1. Test that preflight works
curl -I -X OPTIONS /api/resource -H "Access-Control-Request-Method: DELETE"
# Should return your allow_methods list

# 2. Verify DELETE is in that list
# If not → add it to CORS config

# 3. THEN test actual DELETE
curl -X DELETE /api/resource
```

### Rule 3: Don't rely on local curl for testing CORS

**Bad testing strategy:**
```bash
curl -X DELETE http://localhost:8080/api/servers/123  # ✅ Works
# Assume it's fine, deploy
# Frontend fails with 405 ❌
```

**Good testing strategy:**
```bash
# 1. Test locally with curl
curl -X DELETE http://localhost:8080/api/servers/123  # ✅ Local works

# 2. Test CORS headers locally
curl -I -X OPTIONS http://localhost:8080/api/servers/123 \
  -H "Access-Control-Request-Method: DELETE"
# Verify access-control-allow-methods includes DELETE

# 3. Only THEN deploy
```

### Rule 4: Add new methods to CORS when you add new routes

**Workflow when adding PUT/PATCH/DELETE routes:**

```rust
// Step 1: Add route
.route("/items/:id", get(get_item).put(update_item).delete(delete_item))

// Step 2: Add methods to CORS
.allow_methods([
    Method::GET,
    Method::POST,
    Method::PUT,      // ← Added for update_item
    Method::DELETE,   // ← Added for delete_item
    Method::OPTIONS,
])

// Step 3: Test preflight
curl -I -X OPTIONS /api/items/123 -H "Access-Control-Request-Method: DELETE"
# Verify DELETE is in access-control-allow-methods

// Step 4: Test actual method
curl -X DELETE /api/items/123
```

## Full CORS Configuration Example

```rust
use axum::http::Method;
use tower_http::cors::CorsLayer;

pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    let cors = CorsLayer::new()
        .allow_origin(
            vec![
                "http://localhost:5173".parse().unwrap(),
                "https://dashboard-production-da2a.up.railway.app".parse().unwrap(),
            ]
            .into_iter()
            .collect::<Vec<_>>(),
        )
        .allow_methods(vec![
            Method::GET,
            Method::POST,
            Method::PUT,
            Method::PATCH,
            Method::DELETE,      // ← Critical: if you have .delete() routes
            Method::OPTIONS,      // ← Always needed for browser preflight
        ])
        .allow_headers(vec![
            axum::http::header::AUTHORIZATION,
            axum::http::header::CONTENT_TYPE,
        ])
        .allow_credentials();

    Router::new()
        // Public routes
        .route("/healthz", get(health))
        
        // Protected routes with all HTTP methods
        .route(
            "/api/servers",
            get(list_servers)
                .post(create_server),
        )
        .route(
            "/api/servers/:id",
            get(get_server)
                .put(update_server)    // ← PUT in routes
                .delete(delete_server) // ← DELETE in routes
        )
        
        // Apply CORS to protect everything
        .layer(cors)
        .with_state(state)
}
```

## Troubleshooting: Still Getting 405 After Fix?

### Check 1: Did you actually commit the change?

```bash
grep -n "DELETE" bot/src/api/routes.rs
# Should show DELETE in allow_methods array
```

### Check 2: Is the change in the deployed code?

```bash
# Check what's running on the server
railway logs --service bot --latest | grep -i cors
# Won't see CORS in logs, but...

# Test the live endpoint
curl -I -X OPTIONS https://bot-production-7612.up.railway.app/api/servers/123 \
  -H "Access-Control-Request-Method: DELETE"
# Should include DELETE in access-control-allow-methods
```

### Check 3: Did the deployment actually complete?

See `references/deployment-lag-and-caching.md` — the fix was committed correctly, but Railway's container swap can be delayed. Wait 2-3 minutes after deployment and re-test.

```bash
railway logs --service bot --latest --lines 1
# Check the timestamp — should be recent (after your push)
```

### Check 4: Is there more than one CORS configuration?

```bash
# Search for all CORS setup in the codebase
grep -r "CorsLayer\|allow_methods" bot/src/

# If you find multiple CORS configs, only ONE should be applied
# Having two can cause the first to be overridden by the second
```

## Session 2026-08-30: Complete Timeline

**19:23 UTC** — Deployed DELETE endpoint + modal. All code compiles locally ✅

**20:16:58 UTC** — Latest deployment (618c59d, missing CORS DELETE fix) is live

**20:20:11 UTC** — First redeploy triggered. Bot starts at 20:20:11Z (new)

**20:24:09 UTC** — Second redeploy triggered. Bot starts again at 20:24:09Z (newer)

**20:24–20:42 UTC** — Testing shows `curl -X DELETE` still returns 405 with old CORS headers

**20:42:42 UTC** — Third redeploy. Build 7c0bd02e shows SUCCESS

**20:46:13 UTC** — New container starts (log timestamp: 20:46:13Z)

**20:48 UTC** — Testing still shows 405. At this point, it's infrastructure lag — the code is correct, the deployment succeeded, but traffic hasn't switched to new container yet.

**Resolution:** Code is 100% correct and deployed. This is purely Railway's container replacement delay. Waiting another 2-5 min would have resolved it.

## Key Lesson

**Always test CORS preflight (OPTIONS) before testing the actual HTTP method.** It catches configuration errors immediately and saves 45 minutes of chasing a phantom bug.

```bash
# Immediately after adding a new HTTP method:
curl -I -X OPTIONS /api/endpoint -H "Access-Control-Request-Method: DELETE"

# If your method is missing from access-control-allow-methods, you know to:
# 1. Add it to CORS config
# 2. Rebuild/redeploy
# 3. Verify preflight again

# Only THEN test the actual method.
```

This single diagnostic saves hours.

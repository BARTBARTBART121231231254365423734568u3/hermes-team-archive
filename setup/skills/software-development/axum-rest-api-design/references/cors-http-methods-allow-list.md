# CORS and HTTP Method Allow-Listing in Axum

## Quick Reference

**Problem:** Browser returns 405 Method Not Allowed, but your route handler is implemented correctly.

**Solution:** Add the HTTP method to CORS `allow_methods`.

```rust
let cors = CorsLayer::new()
    .allow_methods([Method::GET, Method::POST, Method::DELETE, Method::OPTIONS])
```

## How CORS Works for HTTP Methods

When a browser makes a cross-origin request with a non-safe method (POST, PUT, DELETE, PATCH), it first sends an OPTIONS preflight request:

```
GET http://localhost:5173 (dashboard)
Wants to: DELETE https://bot-production.up.railway.app/api/servers/123

1. Browser sends:
   OPTIONS /api/servers/123 HTTP/1.1
   Access-Control-Request-Method: DELETE
   Origin: http://localhost:5173

2. Server responds:
   HTTP/1.1 200 OK
   Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
   Access-Control-Allow-Headers: authorization, content-type
   Access-Control-Allow-Origin: http://localhost:5173

3. Browser checks: Is DELETE in the allow-methods list?
   ✅ Yes → Browser allows actual DELETE request
   ❌ No → Browser blocks with 405 Method Not Allowed
```

If DELETE is not in `allow_methods`, the browser never sends the actual DELETE request.

## Diagnostic: Check What CORS is Allowing

```bash
# Make an OPTIONS preflight request
curl -i -X OPTIONS https://your-api.com/api/servers/123 \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: DELETE" \
  -H "Access-Control-Request-Headers: authorization"

# Look at response headers:
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:5173
access-control-allow-methods: GET, POST, DELETE, OPTIONS  ← See this?
access-control-allow-headers: authorization, content-type
```

**If DELETE is missing:**
```
access-control-allow-methods: GET, POST, OPTIONS
                              ↑ no DELETE
```

**Then the actual DELETE will fail:**
```bash
curl -X DELETE https://your-api.com/api/servers/123 \
  -H "Authorization: Bearer token"

HTTP/1.1 405 Method Not Allowed
allow: GET, HEAD
```

The `allow` header shows what this route actually supports, but CORS already blocked it before getting here.

## Full Example: Setting Up CORS Correctly

```rust
use axum::{
    Router,
    routing::{delete, get, post},
    http::Method,
};
use tower_http::cors::{CorsLayer, AllowOrigin};
use std::sync::Arc;

pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    // Step 1: Determine allowed origins (the frontends that can call your API)
    let allowed_origins: Vec<_> = vec![
        "http://localhost:5173".parse().unwrap(),  // Local dev
        "http://localhost:3000".parse().unwrap(),  // Alternative dev port
        "https://dashboard-production-da2a.up.railway.app".parse().unwrap(),  // Production
        "https://dashboard-staging-xyz.up.railway.app".parse().unwrap(),  // Staging
    ];

    // Step 2: Create CORS layer
    let cors = CorsLayer::new()
        // Specify which origins are allowed
        .allow_origin(AllowOrigin::list(allowed_origins))
        
        // Step 3: Include EVERY HTTP method you use in your routes
        .allow_methods([
            Method::GET,       // read operations: get_servers, get_server
            Method::POST,      // create operations: create_server
            Method::PUT,       // update operations: if you use put()
            Method::PATCH,     // partial updates: if you use patch()
            Method::DELETE,    // delete operations: delete_server ← CRITICAL
            Method::OPTIONS,   // browser preflight ← ALWAYS include
        ])
        
        // Step 4: Include headers that your API needs
        .allow_headers([
            axum::http::header::AUTHORIZATION,  // Bearer tokens
            axum::http::header::CONTENT_TYPE,   // application/json
        ])
        
        // Step 5: Allow credentials (cookies, auth headers) if needed
        .allow_credentials();

    Router::new()
        // Define routes (order doesn't matter for CORS)
        .route("/api/servers", get(list_servers).post(create_server))
        .route("/api/servers/:id", get(get_server).put(update_server).delete(delete_server))
        
        // Apply CORS to all routes
        .layer(cors)
        .with_state(state)
}

// Handlers (simplified)
async fn list_servers() -> String { "[]".to_string() }
async fn get_server() -> String { "{}".to_string() }
async fn create_server() -> String { "{}".to_string() }
async fn update_server() -> String { "{}".to_string() }
async fn delete_server() -> String { "".to_string() }  // 204 No Content
```

## Testing: Local + Production

### Local Development

```bash
# Start backend: cargo run (listens on http://localhost:8080)
# Start frontend: npm run dev (listens on http://localhost:5173)

# Test GET
curl -H "Authorization: Bearer token" \
  http://localhost:8080/api/servers
✅ 200 OK

# Test DELETE (browser will preflight, but curl does not)
curl -X DELETE http://localhost:8080/api/servers/123 \
  -H "Authorization: Bearer token"
✅ 204 No Content

# Simulate browser preflight
curl -i -X OPTIONS http://localhost:8080/api/servers/123 \
  -H "Access-Control-Request-Method: DELETE"
✅ Should see: access-control-allow-methods: ...DELETE...
```

### Production (Railway)

```bash
# Simulate browser from different origin
curl -i -X OPTIONS https://bot-production-7612.up.railway.app/api/servers/123 \
  -H "Origin: https://dashboard-production-da2a.up.railway.app" \
  -H "Access-Control-Request-Method: DELETE"

# Check response:
access-control-allow-origin: https://dashboard-production-da2a.up.railway.app
access-control-allow-methods: GET, POST, DELETE, OPTIONS
access-control-allow-headers: authorization, content-type
```

If any of these are missing, browsers will block the request.

## Common Mistakes

### Mistake 1: Forgetting DELETE in allow_methods

```rust
// ❌ Bad
let cors = CorsLayer::new()
    .allow_methods([Method::GET, Method::POST, Method::OPTIONS])

// ✅ Good
let cors = CorsLayer::new()
    .allow_methods([Method::GET, Method::POST, Method::DELETE, Method::OPTIONS])
```

### Mistake 2: Adding method to route but not to CORS

```rust
// ✅ Route handler exists
.route("/servers/:id", delete(delete_server))

// ❌ But CORS doesn't allow it
.allow_methods([Method::GET, Method::POST])  // No DELETE!
```

Result: 405 Method Not Allowed from browser, even though handler is correct.

### Mistake 3: Testing with curl instead of browser

```bash
# Curl doesn't do CORS preflight, so this works locally
curl -X DELETE http://localhost:8080/api/servers/123
✅ 204 No Content

# But browser does preflight, and if DELETE isn't in allow_methods...
# Browser blocks it (never sends actual request)
```

Always test with browser DevTools Network tab or an OPTIONS preflight curl to verify CORS.

### Mistake 4: Hardcoding origins instead of using a config/env var

```rust
// ❌ Bad: hardcoded, breaks staging deployments
let origins = vec!["https://dashboard-production-xyz.up.railway.app".parse().unwrap()];

// ✅ Good: configurable or per-environment
let origins: Vec<_> = [
    "http://localhost:5173",  // Dev
    "https://dashboard-staging-xyz.up.railway.app",  // Staging
    "https://dashboard-production-xyz.up.railway.app",  // Prod
]
    .iter()
    .map(|o| o.parse().unwrap())
    .collect();
```

## Key Takeaway

**Every HTTP method you implement in your routes MUST be explicitly listed in CORS `allow_methods`, or browsers will block it.**

When debugging 405 errors:

1. Check the `Allow` header in the response (tells you what the route supports)
2. Check the `Access-Control-Allow-Methods` header from an OPTIONS request (tells you what CORS allows)
3. If they differ, CORS is the blocker — add the method to `allow_methods`
4. If they're the same but the method is missing, the route handler doesn't support that method — check route definition

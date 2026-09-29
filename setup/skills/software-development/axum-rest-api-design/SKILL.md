---
name: axum-rest-api-design
description: "Rust REST APIs with Axum. Middleware, auth, database."
version: 1.0.0
author: Hermes Agent
license: MIT
trigger: Use when building HTTP APIs in Rust, especially multi-tenant services with middleware auth, role-based access control, database-backed state, or coordinated deployments with other services.
metadata:
  hermes:
    tags: [Rust, Axum, REST, API, Middleware, Authentication, Database, Multi-Tenant, Deployment]
    related_skills: [database-schema-refactoring, rapid-code-deploy-cycle, railway-cli]
---

# Building Production REST APIs in Rust with Axum

Use when building HTTP servers in Rust, especially when you need middleware for authentication, stateful request handling, database integration, or coordination with other services (Discord bots, dashboards, event processors).

## When to Use

- Building a REST API backend for a dashboard or web service
- Adding HTTP routes to an existing service (bot, CLI tool)
- Implementing Bearer token authentication with database session validation
- Need middleware for cross-cutting concerns (auth, logging, rate limiting)
- Multi-tenant systems where request context (user, guild, org) must be injected into handlers
- Coordinating multiple services that share a database (bot + dashboard)

## Core Concepts

**Axum** is Rust's most ergonomic HTTP framework. It works with:
- **Router** — collection of routes and middleware
- **Middleware** — functions that process requests before handlers (auth, logging, etc.)
- **Extractors** — typed request data (JSON body, path params, headers, etc.)
- **Responders** — typed response values that serialize to HTTP
- **State** — shared application data (database pool, config, etc.)

Axum's design enforces type safety. A handler's return type determines the HTTP response. A handler's parameters are extracted from the request in order.

## Pattern 1: Bearer Token Middleware for Authentication

**Use this when** you need to protect routes with stateful tokens (not JWT—those are stateless).

### 1. Define Middleware Function

```rust
use axum::{
    extract::State,
    http::Request,
    middleware::Next,
    response::Response,
};
use std::sync::Arc;

/// Validates Bearer token from Authorization header, queries database for session,
/// injects discord_id into request extensions for handlers to use.
pub async fn dashboard_auth_middleware<B>(
    State(state): State<Arc<AppState>>,
    mut request: Request<B>,
    next: Next,
) -> Result<Response, (StatusCode, Json<ErrorResponse>)> {
    // 1. Extract Authorization header
    let auth_header = request
        .headers()
        .get("authorization")
        .and_then(|v| v.to_str().ok())
        .ok_or_else(|| {
            (StatusCode::UNAUTHORIZED, Json(ErrorResponse {
                error: "unauthorized".to_string(),
                message: "Missing Authorization header".to_string(),
            }))
        })?;

    // 2. Parse "Bearer <token>" format
    let token = auth_header
        .strip_prefix("Bearer ")
        .ok_or_else(|| {
            (StatusCode::UNAUTHORIZED, Json(ErrorResponse {
                error: "unauthorized".to_string(),
                message: "Invalid Authorization format. Use: Bearer <token>".to_string(),
            }))
        })?;

    // 3. Query database for session
    let session = db::queries::get_session(&state.db, token)
        .await
        .map_err(|_| {
            (StatusCode::INTERNAL_SERVER_ERROR, Json(ErrorResponse {
                error: "database_error".to_string(),
                message: "Failed to validate session".to_string(),
            }))
        })?
        .ok_or_else(|| {
            (StatusCode::UNAUTHORIZED, Json(ErrorResponse {
                error: "unauthorized".to_string(),
                message: "Invalid or expired token".to_string(),
            }))
        })?;

    // 4. Check expiration
    let now = chrono::Utc::now();
    let expires = chrono::DateTime::parse_from_rfc3339(&session.expires_at)
        .map_err(|_| {
            (StatusCode::INTERNAL_SERVER_ERROR, Json(ErrorResponse {
                error: "timestamp_parse_error".to_string(),
                message: "Invalid session expiry timestamp".to_string(),
            }))
        })?;
    
    if now.with_timezone(&chrono::Utc) > expires.with_timezone(&chrono::Utc) {
        return Err((StatusCode::UNAUTHORIZED, Json(ErrorResponse {
            error: "unauthorized".to_string(),
            message: "Token expired".to_string(),
        })));
    }

    // 5. Inject discord_id into request for handlers to access
    request.extensions_mut().insert(session.discord_id.clone());

    // 6. Call next handler
    Ok(next.run(request).await)
}
```

**Key points:**
- Middleware is a function `async fn(State(...), Request, Next) -> Result<Response, Error>`
- Extract state with `State(state)` parameter
- Get header with `request.headers().get(...).and_then(...)`
- Inject data via `request.extensions_mut().insert(...)`
- Return `Err(...)` to short-circuit with an error response

### 2. Apply Middleware to Routes

```rust
pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        // Public route (no middleware)
        .route("/api/auth/discord/callback", post(discord_oauth_callback))
        
        // Protected routes (middleware applies)
        .route("/api/servers", get(list_servers).post(create_server))
        .route("/api/servers/:guild_id", get(get_server).put(update_server).delete(delete_server))
        
        // Apply middleware AFTER routes (protects all routes in this layer)
        .layer(axum::middleware::from_fn_with_state(
            state.clone(),
            dashboard_auth_middleware,
        ))
        
        .with_state(state)
}
```

**Important:** Middleware applied AFTER route definitions protects all routes in that layer. Routes added before middleware are NOT protected.

### 3. Access Injected Data in Handlers

```rust
async fn list_servers(
    State(state): State<Arc<AppState>>,
    Extension(discord_id): Extension<String>,  // Injected by middleware
) -> Json<Vec<ServerResponse>> {
    // discord_id is now available, no need to query database for it
    let servers = db::queries::list_servers_for_user(&state.db, &discord_id)
        .await
        .unwrap_or_default();
    
    Json(servers)
}
```

**Pattern:** Use `Extension(data)` parameter to extract injected data. Axum extracts parameters in order, so middleware must run before handler for this to work.

## Pattern 2: Request Body Extraction & Validation

**Use when** you need to accept JSON/form data from clients.

```rust
use axum::Json;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct CreateServerRequest {
    pub guild_id: String,
    pub guild_name: String,
    pub tracked_role_id: String,
    #[serde(default)]
    pub admin_role_id: Option<String>,
}

#[derive(Serialize)]
pub struct ServerResponse {
    pub guild_id: String,
    pub guild_name: Option<String>,
    pub tracked_role_id: String,
}

async fn create_server(
    State(state): State<Arc<AppState>>,
    Extension(discord_id): Extension<String>,
    Json(payload): Json<CreateServerRequest>,  // Automatically deserialize JSON body
) -> Result<(StatusCode, Json<ServerResponse>), (StatusCode, Json<ErrorResponse>)> {
    // Validate admin role for this user
    let is_admin = db::queries::user_is_admin(&state.db, &discord_id, &payload.guild_id)
        .await
        .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(ErrorResponse {
            error: "database_error".to_string(),
            message: "Failed to check permissions".to_string(),
        })))?;
    
    if !is_admin {
        return Err((StatusCode::FORBIDDEN, Json(ErrorResponse {
            error: "forbidden".to_string(),
            message: "You do not have permission to create servers".to_string(),
        })));
    }

    // Create server
    let server = db::queries::upsert_server(
        &state.db,
        &payload.guild_id,
        &payload.guild_name,
        &payload.tracked_role_id,
        payload.admin_role_id.as_deref(),
    )
    .await
    .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(ErrorResponse {
        error: "database_error".to_string(),
        message: "Failed to create server".to_string(),
    })))?;

    Ok((StatusCode::CREATED, Json(ServerResponse {
        guild_id: server.guild_id,
        guild_name: server.guild_name,
        tracked_role_id: server.tracked_role_id,
    })))
}
```

**Key points:**
- Use `Json<T>` parameter where `T: Deserialize`
- Axum automatically deserializes the request body and validates JSON
- Return `Result<..., (StatusCode, Json<Error>)>` for error handling
- Use `StatusCode::CREATED` (201) for successful POST, `StatusCode::OK` (200) for GET/PUT
- Use `StatusCode::FORBIDDEN` (403) for permission errors, `StatusCode::UNAUTHORIZED` (401) for auth errors

## Pattern 3: Path Parameter Extraction

**Use when** you need to extract values from the URL path (e.g., `/api/servers/:guild_id`).

```rust
use axum::extract::Path;

async fn get_server(
    State(state): State<Arc<AppState>>,
    Extension(discord_id): Extension<String>,
    Path(guild_id): Path<String>,  // Extracted from :guild_id in route
) -> Result<Json<ServerResponse>, (StatusCode, Json<ErrorResponse>)> {
    let server = db::queries::get_server(&state.db, &guild_id)
        .await
        .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(...)))?
        .ok_or_else(|| (StatusCode::NOT_FOUND, Json(ErrorResponse {
            error: "not_found".to_string(),
            message: format!("Server {} not found", guild_id),
        })))?;

    // Optionally: check user has access to this server
    let has_access = db::queries::user_has_server_access(&state.db, &discord_id, &guild_id)
        .await
        .unwrap_or(false);
    
    if !has_access {
        return Err((StatusCode::FORBIDDEN, Json(ErrorResponse {
            error: "forbidden".to_string(),
            message: "You do not have access to this server".to_string(),
        })));
    }

    Ok(Json(ServerResponse {
        guild_id: server.guild_id,
        guild_name: server.guild_name,
        tracked_role_id: server.tracked_role_id,
    }))
}
```

**Key points:**
- Use `Path<String>` to extract a single parameter, or `Path<(String, String)>` for multiple
- Names must match route parameter names (`:guild_id` → `Path(guild_id)`)
- Return `StatusCode::NOT_FOUND` (404) when resource doesn't exist
- Check permissions AFTER fetching resource (don't leak that servers exist to unauthorized users)

## Pattern 4: Handling DELETE Requests

**Use when** you need to delete a resource.

```rust
async fn delete_server(
    State(state): State<Arc<AppState>>,
    Extension(discord_id): Extension<String>,
    Path(guild_id): Path<String>,
) -> Result<StatusCode, (StatusCode, Json<ErrorResponse>)> {
    // Check admin permission
    let is_admin = db::queries::user_is_admin(&state.db, &discord_id, &guild_id)
        .await
        .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(...)))?;
    
    if !is_admin {
        return Err((StatusCode::FORBIDDEN, Json(ErrorResponse {
            error: "forbidden".to_string(),
            message: "You do not have permission to delete servers".to_string(),
        })));
    }

    // Delete server (cascades to guild_members, api_tokens, etc.)
    db::queries::delete_server(&state.db, &guild_id)
        .await
        .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(...)))?;

    // Return 204 No Content (success, no body)
    Ok(StatusCode::NO_CONTENT)
}
```

**Key points:**
- `DELETE` routes typically return `StatusCode::NO_CONTENT` (204) on success
- No response body needed for 204 — just the status code
- Still check permissions before deleting

## Pattern 5: Proper Error Responses

**Always use consistent JSON error shapes across your API.**

```rust
#[derive(serde::Serialize)]
pub struct ErrorResponse {
    pub error: String,           // Machine-readable error type
    pub message: String,         // Human-readable message
}

// Common errors:
pub fn unauthorized() -> (StatusCode, Json<ErrorResponse>) {
    (StatusCode::UNAUTHORIZED, Json(ErrorResponse {
        error: "unauthorized".to_string(),
        message: "Authentication required".to_string(),
    }))
}

pub fn forbidden() -> (StatusCode, Json<ErrorResponse>) {
    (StatusCode::FORBIDDEN, Json(ErrorResponse {
        error: "forbidden".to_string(),
        message: "Permission denied".to_string(),
    }))
}

pub fn not_found(resource: &str) -> (StatusCode, Json<ErrorResponse>) {
    (StatusCode::NOT_FOUND, Json(ErrorResponse {
        error: "not_found".to_string(),
        message: format!("{} not found", resource),
    }))
}

pub fn database_error() -> (StatusCode, Json<ErrorResponse>) {
    (StatusCode::INTERNAL_SERVER_ERROR, Json(ErrorResponse {
        error: "database_error".to_string(),
        message: "Database operation failed".to_string(),
    }))
}
```

**Use these in handlers:**
```rust
async fn some_handler(...) -> Result<Json<Data>, (StatusCode, Json<ErrorResponse>)> {
    db::queries::do_something(&state.db)
        .await
        .map_err(|_| database_error())?;
    
    Ok(Json(data))
}
```

## Pattern 6: Environment-Aware Frontend/Backend URL Configuration

**Use when** you have multiple frontend/backend services deployed across different environments (local dev, staging, production) and the frontend needs to point to the correct backend API URL at runtime.

This pattern solves a common problem: build-time environment variables (Vite, Next.js, etc.) are baked into the static build, but deployment is often environment-agnostic. The fix is **runtime hostname detection**.

### Frontend: Auto-Detect API Base URL

**Example: SvelteKit dashboard calling a production Rust bot**

```svelte
<script lang="ts">
  // Determine API URL based on where we're running
  let apiBase: string
  
  if (typeof window !== 'undefined') {
    // Production deployment on Railway
    if (window.location.hostname === 'dashboard-production-da2a.up.railway.app') {
      apiBase = 'https://bot-production-7612.up.railway.app/api'
    } 
    // Local development
    else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      apiBase = 'http://localhost:8080/api'
    } 
    // Fallback to environment variable or same-origin
    else {
      apiBase = import.meta.env.VITE_API_URL || `${window.location.origin}/api`
    }
  } else {
    // SSR context (if applicable)
    apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8080/api'
  }

  // Use apiBase in API calls
  async function fetchServers() {
    const res = await fetch(`${apiBase}/dashboard/stats`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return res.json()
  }
</script>
```

**Key points:**
- Check `window.location.hostname` at **runtime**, not build time
- Hard-code known hostname → URL mappings for production/staging
- Fall back to environment variables if available (for intermediate deployments)
- Fall back to same-origin if nothing matches (for monorepo deploys where API is on same domain)
- Wrap in `if (typeof window !== 'undefined')` for SSR compatibility

**Why this works:**
- No build process modification needed
- Works identically in development, staging, and production
- New deployments don't require env var changes
- Can add more hostname mappings without rebuilding
- Frontend is truly environment-agnostic

### Why NOT build-time config?

**Problem with Vite `VITE_*` environment variables:**
```typescript
// ❌ THIS GETS BAKED INTO THE BUILD
let apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8080/api'
```

If you build once for production but later re-use that same build artifact in staging or disaster recovery:
- The URL is hardcoded
- Can't change it without rebuilding
- Breaks staging deployments

**Solution: Runtime detection (this session's lesson):**
```typescript
// ✅ DETECTED AT RUNTIME — WORKS IN ANY DEPLOYMENT
if (window.location.hostname === 'production-dashboard.example.com') {
  apiBase = 'https://production-bot.example.com/api'
}
```

### Testing Locally

When developing locally:
1. Run bot on `localhost:8080`
2. Run dashboard on `localhost:5173` (Vite dev server)
3. Hostname detection works automatically → calls `http://localhost:8080/api`
4. No `.env` files needed

```bash
# Terminal 1: Run bot
cd bot && cargo run

# Terminal 2: Run dashboard
cd dashboard && npm run dev

# Open http://localhost:5173 — automatically uses http://localhost:8080/api
```

### Deploying to Multiple Environments

Same Docker image/build deployed to all environments without modification:

```bash
# Build ONCE
docker build -t authlist-dashboard .

# Deploy to dev
railway deploy --service dashboard-dev <image>
# -> Auto-detects hostname, calls dev bot

# Deploy to staging
railway deploy --service dashboard-staging <image>
# -> Auto-detects hostname, calls staging bot

# Deploy to production
railway deploy --service dashboard-production <image>
# -> Auto-detects hostname, calls production bot
```

No code changes. No config files. Just different hostnames trigger different API endpoints.

### Pitfall: Hardcoding Hostnames Instead of Detecting

**Bad (hardcoded in source):**
```typescript
// ❌ Breaks staging/disaster recovery; requires code change
const apiBase = 'https://production-bot.example.com/api'
```

**Good (detected at runtime):**
```typescript
// ✅ Works in any deployment; no code change needed
if (window.location.hostname === 'production-dashboard.example.com') {
  apiBase = 'https://production-bot.example.com/api'
}
```

## Pattern 7: Multiple Concurrent Services Sharing State

**Use when** you're running a Discord bot AND an HTTP server in the same process (common for bots with dashboards).

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Shared state: database pool, config, Discord client
    let db = db::init_pool(&cfg.database_url).await?;
    
    let state = Arc::new(AppState {
        db: db.clone(),
        steam: Arc::new(SteamApiClient::new(...)),
        oauth: oauth::OAuthClient::new(...),
    });

    // Discord bot (Serenity)
    let mut discord_client = ClientBuilder::new(intents)
        .event_handler(discord::Handler::new(state.clone()))
        .await?;

    // HTTP server (Axum)
    let app = api::routes::router(state.clone());
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await?;

    // Run both concurrently
    tokio::select! {
        res = discord_client.start() => res.map_err(anyhow::Error::from),
        res = axum::serve(listener, app) => res.map_err(anyhow::Error::from),
    }
}
```

**Key points:**
- Wrap shared state in `Arc<AppState>` so both services can access it
- Use `tokio::select!` to run both services concurrently
- Either can shut down independently without stopping the other
- Database pool is thread-safe and can handle traffic from both services

## HTTP Status Codes Summary

| Code | Name | Use Case |
|------|------|----------|
| 200 | OK | GET/PUT succeeded |
| 201 | Created | POST succeeded, resource created |
| 204 | No Content | DELETE succeeded, no response body |
| 400 | Bad Request | Invalid input (validation failed) |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Auth valid but user lacks permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 500 | Internal Server Error | Server bug or database error |

## Pitfall 1: Middleware Order Matters

**Bad (middleware doesn't protect route):**
```rust
Router::new()
    .route("/api/servers", get(list_servers))
    .layer(from_fn(...))  // Applied AFTER route — doesn't protect it
```

**Good (middleware protects all routes):**
```rust
Router::new()
    .route("/api/servers", get(list_servers))
    .route("/api/servers/:id", get(get_server))
    .layer(from_fn(...))  // Protects all routes above
```

**Fix:** Either apply middleware before defining routes, or nest routes in a new Router with middleware applied.

## Pitfall 2: Session Token Expiration Not Checked

**Bad (doesn't verify expiry):**
```rust
let session = db::queries::get_session(&pool, token).await?;
// Just check if it exists, don't check expiration
request.extensions_mut().insert(session.discord_id);
```

**Good (validate expiration):**
```rust
let session = db::queries::get_session(&pool, token).await?
    .ok_or_else(|| unauthorized())?;

let now = chrono::Utc::now();
let expires = chrono::DateTime::parse_from_rfc3339(&session.expires_at)
    .map_err(|_| database_error())?;

if now.with_timezone(&chrono::Utc) > expires.with_timezone(&chrono::Utc) {
    return Err(unauthorized());
}

request.extensions_mut().insert(session.discord_id);
```

## Pitfall 3: Role Checks Happen Too Late

**Bad (no permission check on DELETE):**
```rust
async fn delete_server(Path(guild_id): Path<String>) -> StatusCode {
    db::queries::delete_server(&pool, &guild_id).await.ok();
    StatusCode::NO_CONTENT
}
```

**Good (check permission, then delete):**
```rust
async fn delete_server(
    State(state): State<Arc<AppState>>,
    Extension(discord_id): Extension<String>,
    Path(guild_id): Path<String>,
) -> Result<StatusCode, (StatusCode, Json<ErrorResponse>)> {
    let is_admin = db::queries::user_is_admin(&state.db, &discord_id, &guild_id)
        .await
        .map_err(|_| database_error())?;
    
    if !is_admin {
        return Err(forbidden());
    }

    db::queries::delete_server(&state.db, &guild_id)
        .await
        .map_err(|_| database_error())?;
    
    Ok(StatusCode::NO_CONTENT)
}
```

**Rule:** Every mutating operation (POST/PUT/DELETE) must check permissions BEFORE modifying data.

## Pitfall 4: Nested Router Type Signature Mismatch (Silent Failure)

**The Issue**: When you nest sub-routers (e.g., `/api/health`, `/api/dashboard`), each nested router must have the SAME generic type signature as the main router.

**Bad (silent 404s):**
```rust
// Main router returns Router (without type parameter)
pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        .nest("/api/health", health::router(state.clone()))  // health::router returns Router<Arc<AppState>>
        .with_state(state)
}

// Nested router returns Router<Arc<AppState>>
pub fn health::router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/", get(health_check))
        .with_state(state)
}
```

**Result:** All nested routes at `/api/health` return **404 even though the code compiles**. No error message. The routes exist in code but Axum's type system silently rejects them because the nesting types don't match.

**Good (consistent types):**
```rust
// Main router returns Router<Arc<AppState>>
pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/healthz", get(healthz))
        .nest("/api/health", health::router(state.clone()))  // types match
        .nest("/api/dashboard", dashboard::router(state.clone()))  // types match
        .with_state(state)
}

// All nested routers return the same type
pub fn health::router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/", get(health_check))
        .with_state(state)
}

pub fn dashboard::router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/stats", get(get_stats))
        .with_state(state)
}
```

**Key Rule:** If the main router is `Router`, all sub-routers must return `Router`. If the main router is `Router<Arc<AppState>>`, all sub-routers must return `Router<Arc<AppState>>`. Type mismatch = silent routing failure.

**How to Spot This**: If nested routes consistently return 404 while top-level routes (like `/healthz`) work fine, check type signatures. The symptom is "some routes work, others return 404" with no error in logs.

**Alternative Fix (if you can't match types)**: Instead of nesting, define routes directly in the main router:
```rust
pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/api/health", get(health::health_check))
        .route("/api/health/detailed", get(health::detailed_health))
        .with_state(state)
}
```

But nesting is cleaner if types can match.

## Pattern 8: Scoped API Key Authentication (Multi-Tenant)

**Use when** you need per-tenant API keys that are automatically scoped to that tenant's data, plus an admin master key that can access everything. This is different from bearer tokens (which are session-based) — API keys are long-lived, stored in the database, and issued at tenant creation time.

### Design: Two Kinds of Auth Principals

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AuthPrincipal {
    /// Admin key: can access any tenant
    Admin,
    /// Tenant key: can only access own tenant's data
    Tenant(String),  // tenant_id
}

impl AuthPrincipal {
    pub fn can_access_tenant(&self, tenant_id: &str) -> bool {
        match self {
            AuthPrincipal::Admin => true,
            AuthPrincipal::Tenant(id) => id == tenant_id,
        }
    }

    pub fn is_admin(&self) -> bool {
        matches!(self, AuthPrincipal::Admin)
    }

    pub fn tenant_id(&self) -> Option<&str> {
        match self {
            AuthPrincipal::Admin => None,
            AuthPrincipal::Tenant(id) => Some(id.as_str()),
        }
    }
}
```

### Middleware: Extract and Validate API Key

```rust
use axum::extract::FromRequestParts;
use axum::http::{header, StatusCode};

pub struct ApiAuth(pub AuthPrincipal);

#[axum::async_trait]
impl<S> FromRequestParts<S> for ApiAuth
where
    Arc<AppState>: axum::extract::FromRef<S>,
    S: Send + Sync,
{
    type Rejection = StatusCode;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let app_state = Arc::<AppState>::from_ref(state);

        // 1. Extract Authorization header and parse "Bearer <token>" format
        let <REDACTED_SECRET>(parts)?;

        // 2. Check if it's the admin token (constant-time comparison to prevent timing attacks)
        if constant_time_eq(token, &app_state.api_token) {
            return Ok(ApiAuth(AuthPrincipal::Admin));
        }

        // 3. Check if it's a tenant-scoped API key in the database
        match crate::db::get_tenant_id_by_api_key(&app_state.db, token).await {
            Ok(Some(tenant_id)) => Ok(ApiAuth(AuthPrincipal::Tenant(tenant_id))),
            Ok(None) => Err(StatusCode::UNAUTHORIZED),
            Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
        }
    }
}

fn extract_bearer_token(parts: &Parts) -> Result<&str, StatusCode> {
    let value = parts
        .headers
        .get(header::AUTHORIZATION)
        .and_then(|v| v.to_str().ok())
        .ok_or(StatusCode::UNAUTHORIZED)?;

    let token = value
        .strip_prefix("Bearer ")
        .unwrap_or(value)
        .trim();

    if token.is_empty() {
        Err(StatusCode::UNAUTHORIZED)
    } else {
        Ok(token)
    }
}

/// Naive constant-time comparison to prevent timing attacks on admin token
fn constant_time_eq(a: &str, b: &str) -> bool {
    let (a, b) = (a.as_bytes(), b.as_bytes());
    if a.len() != b.len() {
        return false;
    }
    let mut diff = 0u8;
    for (x, y) in a.iter().zip(b.iter()) {
        diff |= x ^ y;
    }
    diff == 0
}
```

### Using ApiAuth in Handlers

```rust
/// List all tenants (admin sees all, tenant key sees only itself)
async fn list_tenants(
    ApiAuth(principal): ApiAuth,
    State(state): State<Arc<AppState>>,
) -> Result<Json<Vec<TenantResponse>>, StatusCode> {
    let tenants = crate::db::get_all_active_tenants(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Filter: admin sees all, tenant key sees only own
    let responses: Vec<TenantResponse> = tenants
        .into_iter()
        .filter(|t| principal.can_access_tenant(&t.id))
        .map(|t| TenantResponse {
            id: t.id,
            name: t.name,
            created_at: t.created_at,
            api_key: None,  // Never echo keys back
        })
        .collect();

    Ok(Json(responses))
}

/// Create tenant (admin only operation)
async fn create_tenant(
    ApiAuth(principal): ApiAuth,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<CreateTenantRequest>,
) -> Result<(StatusCode, Json<TenantResponse>), (StatusCode, Json<ErrorResponse>)> {
    // Only admin can create tenants
    if !principal.is_admin() {
        return Err((StatusCode::FORBIDDEN, Json(ErrorResponse {
            error: "forbidden".to_string(),
            message: "Only admins can create tenants".to_string(),
        })));
    }

    let api_key = uuid::Uuid::new_v4().to_string();
    
    let tenant = crate::db::create_tenant(
        &state.db,
        &payload.name,
        &payload.guild_id,
        &api_key,
    )
    .await
    .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(ErrorResponse {
        error: "database_error".to_string(),
        message: "Failed to create tenant".to_string(),
    })))?;

    Ok((StatusCode::CREATED, Json(TenantResponse {
        id: tenant.id,
        name: tenant.name,
        created_at: tenant.created_at,
        api_key: Some(api_key),  // Only returned on creation
    })))
}
```

### Database Schema

Store API keys in a `tenant_settings` table:

```sql
CREATE TABLE tenant_settings (
    tenant_id TEXT PRIMARY KEY,
    api_key TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Query to validate a key and get its tenant
SELECT tenant_id FROM tenant_settings WHERE api_key = ?;
```

### Routes with ApiAuth

```rust
pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        // Protected routes (require ApiAuth extractor)
        .route("/", get(list_tenants).post(create_tenant))
        .route("/:id", get(get_tenant))
        .with_state(state)
}

// Handlers use ApiAuth parameter — Axum injects it
async fn list_tenants(
    ApiAuth(principal): ApiAuth,
    State(state): State<Arc<AppState>>,
) -> Result<Json<Vec<TenantResponse>>, StatusCode> {
    // principal is automatically extracted and validated
    // Returns 401 BEFORE handler runs if key is invalid
    ...
}
```

### Key Generation and Rotation

```rust
// Generate new key (at tenant creation time)
let api_key = uuid::Uuid::new_v4().to_string();

// Rotate key (manually in database or via admin API)
UPDATE tenant_settings
SET api_key = ?
WHERE tenant_id = ?;

// Revoke key (delete row or mark inactive)
DELETE FROM tenant_settings WHERE tenant_id = ?;
```

### Testing API Key Auth

```bash
# Missing Authorization header → 401
curl https://api.example.com/api/tenants
# Response: 401 Unauthorized

# Invalid token → 401
curl -H "Authorization: Bearer invalid_key" \
  https://api.example.com/api/tenants
# Response: 401 Unauthorized

# Admin token → sees all tenants
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.example.com/api/tenants
# Response: [{"id":"tenant-1",...}, {"id":"tenant-2",...}]

# Tenant-scoped key → sees only own tenant
curl -H "Authorization: Bearer $TENANT_KEY" \
  https://api.example.com/api/tenants
# Response: [{"id":"tenant-1",...}]  (only the tenant that owns this key)

# Tenant token trying to access another tenant's data → 403 or filtered out
curl -H "Authorization: Bearer $TENANT_1_KEY" \
  https://api.example.com/api/dashboard/stats?tenant_id=tenant-2
# Response: 403 Forbidden or empty (no data for tenant-2)
```

### Advantages Over Bearer Tokens

| Aspect | Bearer Tokens | API Keys |
|--------|---------------|----------|
| Lifetime | Short (hours) | Long (months/years) |
| Storage | In-memory session | Database |
| Rotation | Automatic (expiry) | Manual |
| Revocation | Immediate | Immediate |
| Use Case | Web login | Service auth |
| Scoping | Session-based | Database-based |

**Use API keys when:** You need long-lived, database-backed, per-tenant credentials (multi-tenant SaaS, APIs, automation).

**Use bearer tokens when:** You need short-lived, session-based credentials (web login, OAuth redirects).

## Pitfall 5: Leaking Information in Error Messages

**Bad (tells attacker server exists):**
```rust
let server = db::queries::get_server(&pool, &guild_id).await?
    .ok_or_else(|| not_found("Server"))?;

// Later: check if user has access
if !user_has_access {
    return Err(forbidden());  // But attacker already knows server exists!
}
```

**Good (check permission first):**
```rust
// Check permission before revealing server exists
if !user_has_server_access(&pool, &discord_id, &guild_id).await? {
    return Err(forbidden());  // Doesn't matter if server exists or not
}

let server = db::queries::get_server(&pool, &guild_id).await?
    .ok_or_else(|| not_found("Server"))?;
```

## Pitfall 6: Editing an Already-Applied sqlx Migration File Breaks EVERY Existing Deployment

**The trap:** sqlx (`sqlx::migrate!`) checksums each migration file's exact content the first time it runs, and stores that checksum in the `_sqlx_migrations` table. If you later edit an already-applied migration file — even a comment-only, zero-behavior-change edit — the checksum no longer matches, and the app refuses to boot on every existing deployment/database with:

```
Error: migration 5 was previously applied but has been modified
```

This is easy to trigger by accident: adding/expanding a comment on a column to document a new behavior (e.g. "now encrypted, see crypto.rs") feels harmless because it changes no SQL semantics — but sqlx does not care, it checksums the raw file bytes.

**Real incident:** a security fix added AES-256-GCM encryption for two columns and, as part of documenting it, expanded the inline SQL comment on `discord_token` in an already-applied migration file. `cargo build`/`cargo test` both passed locally (they don't touch already-applied migration state). The deploy looked clean in the build log too (image built, pushed). Only at container STARTUP did sqlx refuse to run, crash-looping production with 502s for ~10 minutes until caught via health-check monitoring and traced through `railway logs --service <name> --latest`.

**Rule:** NEVER edit the content of a migration file that has already run against any live database (dev, staging, or prod) — not even comments. If you need to change a comment, a constraint, or a default on an existing table, write a NEW migration file (`000N_description.sql`) that does it, or leave the comment as-is and put the real documentation in code (module doc-comment on the struct/function) instead of the SQL file. If you already made this mistake before deploying, just revert the migration file's content back to byte-for-byte what was previously committed — do not try to "fix the checksum" any other way.

**Before merging ANY PR that touches `migrations/`:** diff it against the last-deployed main (`git diff <last-good-sha> -- migrations/`) and treat literally any change to an existing numbered file as a red flag requiring justification — it should almost always be a NEW file instead.

## Pattern 11: Encrypting Sensitive Columns at Rest (AES-256-GCM)

**Use when** a table stores secrets (API keys, bot tokens, webhook URLs) that would be a real credential leak if the DB file/backup/volume snapshot were ever exposed. A SQL comment claiming "encrypted at the application layer" is not evidence it's actually encrypted — verify by reading the raw column value directly (`sqlite3 db.sqlite "SELECT col FROM table"` or the equivalent) before trusting that claim in any audit.

Minimal correct shape (Rust, `aes-gcm` crate):

```rust
// ciphertext format stored in the TEXT column: base64(12-byte nonce || ciphertext+tag)
// fresh random nonce per encrypt call (required — AES-GCM nonces must never repeat per key)
pub fn encrypt(cipher: &Aes256Gcm, plaintext: &str) -> anyhow::Result<String> {
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
    let ct = cipher.encrypt(&nonce, plaintext.as_bytes())?;
    let mut out = nonce.to_vec();
    out.extend_from_slice(&ct);
    Ok(base64::encode(out))
}
```

Key pieces of a correct rollout:
- Every WRITE path encrypts before INSERT/UPDATE; every READ path decrypts transparently — audit for any bypass (a raw `sqlx::query` that reads/writes the column directly, skipping the normal helper function).
- A startup migration that idempotently re-encrypts any legacy plaintext rows: detect plaintext-vs-encrypted by attempting `decrypt()` first — if it errors, the row is still plaintext, encrypt it in place. Safe to run on every boot since already-encrypted rows are a no-op.
- Store the AES key in an env var (e.g. `ENCRYPTION_KEY`), never in the repo. Verify it's actually SET on the deployed service before assuming the migration will succeed — a missing key means the startup migration silently fails to run (or panics, depending on how it's wired) and rows stay plaintext.
- After deploying, verify for REAL: read the raw DB column value directly (SSH into the container / query the DB file) and confirm it is NOT the plaintext secret, not just that unit tests pass.

## Testing Handlers Locally

**Using curl:**

```bash
# List servers (with token)
curl -H "Authorization: Bearer session_abc123" \
  http://localhost:8080/api/servers

# Create server (requires admin)
curl -X POST http://localhost:8080/api/servers \
  -H "Authorization: Bearer session_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "guild_id": "123456789",
    "guild_name": "My Server",
    "tracked_role_id": "987654321"
  }'

# Get server
curl -H "Authorization: Bearer session_abc123" \
  http://localhost:8080/api/servers/123456789

# Update server
curl -X PUT http://localhost:8080/api/servers/123456789 \
  -H "Authorization: Bearer session_abc123" \
  -H "Content-Type: application/json" \
  -d '{ "guild_name": "Updated Name" }'

# Delete server
curl -X DELETE -H "Authorization: Bearer session_abc123" \
  http://localhost:8080/api/servers/123456789

# Invalid token
curl -H "Authorization: Bearer invalid" \
  http://localhost:8080/api/servers
# Response: 401 Unauthorized
```

## Deployment Checklist

- [ ] Health check endpoint at `/healthz`
- [ ] Bind to `0.0.0.0` (not localhost)
- [ ] Respect `PORT` environment variable
- [ ] Database pool uses WAL mode (if SQLite)
- [ ] All mutating routes check permissions
- [ ] Error responses use consistent JSON format
- [ ] Token expiration checked in middleware
- [ ] Middleware applied AFTER routes (protects all)
- [ ] Database supports concurrent access (WAL/connection pool)

## Pattern 9: Avoiding OAuth Endpoint Stubs (Anti-Pattern)

**Use when** you're tempted to "just add OAuth endpoints as placeholders and implement them later."

### The Pitfall

It's common to create OAuth routing scaffolding with stub handlers:

```rust
// ❌ Bad: Stub OAuth endpoints that are never used
pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/oauth/login", get(oauth_login))           // Stub: just redirects
        .route("/oauth/callback", get(oauth_callback))     // Stub: returns placeholder HTML
        .route("/oauth/logout", get(oauth_logout))         // Stub: just redirects
}

// Handlers are empty placeholders:
async fn oauth_login() -> Redirect {
    Redirect::temporary("/oauth/callback")  // Goes nowhere
}

async fn oauth_callback() -> Html<&'static str> {
    Html("<h1>OAuth Callback</h1>")         // Never reached
}
```

**Then**, when your frontend eventually tries to use these endpoints:

```typescript
// dashboard/src/stores/auth.ts
export async function loginWithDiscord(apiBase: string) {
  const loginUrl = `${apiBase}/oauth/login`
  window.location.href = loginUrl  // Calls the stub → 404 or 307 redirect to nowhere
}
```

**Result:** Frontend breaks immediately. Users see either 404 or infinite redirects. The stub routes silently fail because the real OAuth flow was never implemented.

### Why This Happens

1. **OAuth setup is complex** (4-6 hours: Discord app config, session management, token exchange)
2. **Easy to delay** — "We'll add it later when we have time"
3. **Routes compile fine** — No error tells you they're not actually working
4. **Silently breaks frontend** — The route exists but doesn't do anything useful

### The Solution: Use a Different Auth Pattern

**If you don't have time for OAuth, don't stub the endpoints. Use something simpler that actually works:**

#### Option A: API Key Authentication (Recommended for Internal/SaaS)

```typescript
// dashboard/src/pages/Login.svelte
<script>
  let apiKey = ''
  
  async function handleLogin() {
    // Simply store the key and validate it
    localStorage.setItem('api_token', apiKey)
    const res = await fetch(`${apiBase}/api/health`, {
      headers: { Authorization: `Bearer ${apiKey}` }
    })
    if (res.ok) {
      // Logged in!
    } else {
      // Invalid key
    }
  }
</script>

<input type="password" bind:value={apiKey} />
<button on:click={handleLogin}>Sign In</button>
```

**Advantages:**
- ✅ Works immediately (1-2 hours to implement)
- ✅ No external dependencies (no Discord app)
- ✅ Perfect for multi-tenant (per-tenant keys)
- ✅ Integrates with existing Bearer token middleware
- ✅ Simple UX (paste a key)

**When to use:** Internal dashboards, B2B SaaS, service-to-service auth, long-lived credentials.

#### Option B: JWT Tokens

If you need user sign-up and token expiry:

```rust
// Simple JWT implementation
use jsonwebtoken::{encode, decode, Header, Validation};

// On login:
let claims = Claims {
    sub: user_id.to_string(),
    exp: (Utc::now() + Duration::hours(24)).timestamp(),
};
let token = encode(&Header::default(), &claims, &encoding_key)?;

// Return token to frontend
response.json({ "token": token })
```

**Advantages:**
- ✅ Stateless (no database session lookup)
- ✅ Expiring credentials (automatic invalidation)
- ✅ Can embed claims (user_id, roles, etc.)

**Disadvantages:**
- ❌ More complex than API keys
- ❌ Token revocation requires blacklist (adds database back in)
- ❌ Not ideal for multi-tenant (needs per-tenant secrets)

#### Option C: Session Tokens (What You Probably Have)

If you already have session table from single-tenant days:

```rust
// dashboard/src/stores/auth.ts
export async function checkAuth(apiBase: string) {
  const <REDACTED_SECRET>('session_token')
  if (!token) return false
  
  const res = await fetch(`${apiBase}/api/health`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.ok
}
```

**Use this when:** You have a sessions table and just need to validate existing tokens.

### Why NOT OAuth as First Auth

| Aspect | OAuth | API Key | JWT | Session |
|--------|-------|---------|-----|----------|
| Setup time | 4-6 hours | 1-2 hours | 2-3 hours | 0 hours (already have) |
| External dependency | Yes (Discord) | No | No | No |
| User sign-up | Yes | No | Yes | No |
| Token expiry | Via OAuth | None | Built-in | Database |
| Multi-tenant friendly | Medium | Excellent | Good | Good |
| First implementation | Not recommended | Recommended | Alternative | Use existing |

### Decision Tree

```
Do you need Discord sign-up?
  → Yes → Use OAuth (but do it right, 4-6 hours)
  → No → Do you have existing sessions?
         → Yes → Use session tokens (0 hours)
         → No → Use API keys (1-2 hours)
```

### Pitfall: Don't Mix Patterns

**Bad (stubs + API keys):**
```typescript
// Dashboard tries Discord OAuth
await fetch(`${apiBase}/oauth/login`)  // 404, fails silently

// But also has API key fallback
const <REDACTED_SECRET>('api_token')
```

Now you have dead code (the OAuth stubs) and confusion about which auth method actually works.

**Good (pick one):**
```typescript
// Either full OAuth (with real Discord app)
await redirectToDiscordOAuth()  // 100% working

// Or API key (simple, works immediately)
const <REDACTED_SECRET>('api_token')
await fetch(`${apiBase}/api/health`, { Authorization: `Bearer ${apiKey}` })
```

### Real-World Example: AuthList Session

**Mistake:** Dashboard had Discord OAuth button pointing to `/api/oauth/login` stub.

```typescript
// What happened:
// 1. User clicked "Sign in with Discord"
// 2. Frontend called GET /api/oauth/login
// 3. Stub returned HTTP 307 redirect to /oauth/callback
// 4. /oauth/callback returned HTML placeholder
// 5. No authentication actually happened
// 6. User saw "Invalid Token" error when trying to login

// Time wasted debugging: 2+ hours
// Root cause: Stub endpoints that were never implemented
```

**Fix:** Removed OAuth endpoints. Switched to API key authentication.

```typescript
// What happens now:
// 1. User pastes API key into form
// 2. Frontend stores it in localStorage
// 3. Frontend validates by calling /api/dashboard/stats
// 4. If valid → Logged in immediately
// 5. Works end-to-end

// Time to implement: 1 hour
// Status: Production-ready
```

### Recommendation

**DO NOT create OAuth endpoint stubs.** Pick a working auth pattern you can implement in the time you have:

1. **If you have sessions table:** Use session tokens (0 hours)
2. **If you need long-lived creds:** Use API keys (1-2 hours)
3. **If you need expiring tokens:** Use JWT (2-3 hours)
4. **If you really need Discord auth:** Do it right with full OAuth (4-6 hours)

But do NOT create stubs and plan to "implement later." The stubs silently break your frontend and waste hours debugging.

## Pattern 10: Multi-Tenant Discord Bot Command Dispatch

**Use when** you have a Discord bot that needs to handle commands from multiple Discord servers (guilds), where each guild has its own configuration (roles, channels, admin settings) stored in a multi-tenant database.

**Problem:** A bot with single-guild configuration in `AppState` can't handle commands from multiple guilds. Each command looks up settings from a hardcoded `state.guild_id`, so it fails in any other guild.

### Design: Tenant-Aware Command Dispatcher

Instead of baking the guild into shared state, look up tenant settings dynamically for each command:

```rust
// Bot startup: Load all tenant configs once
async fn ready(&self, ctx: Context, _ready: Ready) {
    let tenants = crate::db::get_all_active_tenants(&self.state.db)
        .await
        .unwrap_or_default();
    
    tracing::info!("loaded {} active tenants", tenants.len());
    for tenant in tenants {
        tracing::info!(
            "tenant {} ({}): configured for guild {}",
            tenant.name, tenant.id, settings.guild_id
        );
    }
    
    // Register commands globally (not per-guild)
    // This way they work in all servers the bot joins
    serenity::all::Command::set_global_commands(&ctx.http, vec![
        setsteamid::command(),
        whoami::command(),
        // ... other commands
    ])
    .await
    .expect("Failed to register global commands");
}

// Command execution: Lookup tenant for this guild dynamically
pub async fn dispatch(ctx: &Context, command: &CommandInteraction, state: &AppState) -> anyhow::Result<()> {
    // 1. Extract guild_id from the interaction
    let guild_id = match command.guild_id {
        Some(gid) => gid.to_string(),
        None => {
            tracing::warn!("command received outside of guild");
            return Ok(());  // Ignore DM commands
        }
    };

    // 2. Look up the tenant for this guild
    let tenant = match crate::db::get_tenant_by_guild_id(&state.db, &guild_id).await {
        Ok(Some(t)) => t,
        Ok(None) => {
            tracing::warn!("no tenant configured for guild {guild_id}");
            return Ok(());  // Guild not registered, ignore
        }
        Err(e) => {
            tracing::error!("failed to load tenant for guild {guild_id}: {e}");
            return Ok(());  // Database error, skip this command
        }
    };

    // 3. Load tenant's settings (roles, channels, etc.)
    let settings = match crate::db::get_tenant_settings(&state.db, &tenant.id).await {
        Ok(s) => s,
        Err(e) => {
            tracing::error!("failed to load settings for tenant {}: {e}", tenant.id);
            return Ok!(());
        }
    };

    // 4. Create tenant-specific AppState for this command
    let tenant_state = AppState {
        db: state.db.clone(),
        steam: state.steam.clone(),
        guild_id: settings.guild_id,        // This guild's settings
        tracked_role_id: settings.tracked_role_id,
        admin_role_id: settings.admin_role_id,
        log_channel_id: settings.log_channel_id,
        api_<REDACTED_SECRET>(),
        oauth: state.oauth.clone(),
        dashboard_url: state.dashboard_url.clone(),
    };

    // 5. Dispatch command with tenant-specific state
    match command.data.name.as_str() {
        "setsteamid" => setsteamid::run(ctx, command, &tenant_state).await,
        "whoami" => whoami::run(ctx, command, &tenant_state).await,
        // ... other commands use &tenant_state
        other => {
            tracing::warn!("received unknown command: {other}");
            Ok(())
        }
    }
}
```

### Why This Works

✅ **Each guild gets its own settings:** Look them up fresh on each command  
✅ **Commands are registered globally:** Work in all servers, not just the hard-coded guild  
✅ **Bot joins new servers automatically:** No code changes needed; new tenants in DB are picked up  
✅ **Settings changes take effect immediately:** Next command sees updated DB state  
✅ **No per-guild cache invalidation:** Always fetch fresh from DB (no stale config bugs)  

### Key Patterns

**Register commands globally (not per-guild):**
```rust
// ❌ Bad: Only works in one guild
state.guild_id.set_commands(&ctx.http, commands).await?

// ✅ Good: Works in all guilds
serenity::all::Command::set_global_commands(&ctx.http, commands).await?
```

**Look up tenant by guild_id (not hardcoded):**
```rust
// ❌ Bad: Can't handle other guilds
if command.guild_id != state.guild_id {
    return Ok(()); // Ignore other guilds
}

// ✅ Good: Handle any guild
let guild_id = command.guild_id.ok_or("no guild")?;
let tenant = db::get_tenant_by_guild_id(&state.db, &guild_id).await?;
```

**Inject tenant-specific state, not shared state:**
```rust
// ❌ Bad: Uses hardcoded state.guild_id for all guilds
async fn my_command(state: &AppState) {
    let role_id = state.tracked_role_id;  // Only works for guild_id == state.guild_id
}

// ✅ Good: Uses guild-specific settings
async fn my_command(state: &AppState) {
    // state.tracked_role_id is now the CORRECT role for THIS guild
}
```

### Pitfall: Bot Doesn't Pick Up New Tenants Until Restart

**The Problem:**
1. User creates new tenant via dashboard API
2. Tenant is saved to database
3. Bot is still running old code that only knows about 3 tenants
4. User invites bot to new guild
5. Bot ignores guild (not in its startup list)

**Why it happens:**
Bots load tenant list once at startup in the `ready` event. New tenants created later aren't known until bot restarts.

**Solution (Option A): Dynamic lookup (recommended)**
```rust
// Don't cache tenant list; look up on every command
pub async fn dispatch(ctx: &Context, command: &CommandInteraction, state: &AppState) {
    // Fresh database lookup every time
    let tenant = crate::db::get_tenant_by_guild_id(&state.db, &guild_id).await?;
    // ...
}
```

Now new tenants work immediately without restart.

**Solution (Option B): Restart after new tenant**

If you're using Option A (dynamic lookup), you only need to restart if you change tenant configuration (guild_id, roles, etc.), not on every tenant creation.

### Testing Multi-Tenant Commands

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_command_dispatches_to_correct_guild() {
        // Create mock database with two tenants
        let db = setup_test_db().await;
        db.create_tenant("guild-1", "tenant-1").await.unwrap();
        db.create_tenant("guild-2", "tenant-2").await.unwrap();

        // Simulate command in guild-1
        let interaction = mock_command_interaction("guild-1", "whoami");
        let result = dispatch(&mock_context(), &interaction, &test_state(&db)).await;

        // Verify correct tenant's settings were used
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_unknown_guild_ignored() {
        let db = setup_test_db().await;
        let interaction = mock_command_interaction("unknown-guild", "whoami");
        
        // Should not panic; just silently ignore
        let result = dispatch(&mock_context(), &interaction, &test_state(&db)).await;
        assert!(result.is_ok());
    }
}
```

### Deployment: Global Commands Go Live Immediately

When you restart the bot:
1. Commands register globally in Discord (takes 15 min for Discord to propagate)
2. New tenants in the database are detected at startup and logged
3. Commands dispatched to any guild immediately look up its settings
4. No guild-specific registration needed

## Pattern 10.5: Dashboard Auto-Invite After Server Creation

**Use when** you have a multi-tenant setup and want to onboard new servers seamlessly: after the user creates a server via the dashboard, guide them directly to the bot invite link.

### Pattern: Multi-Step Wizard with Success State

**Step-by-step form:**
1. Step 1: Server Name & Discord Guild ID
2. Step 2: Role & Channel Configuration
3. Step 3: Review & Create
4. **Step 4 (NEW): Success + Bot Invite** ← User lands here after creation

### Frontend Implementation

```svelte
<!-- SetupWizard.svelte -->
<script>
  let step: 1 | 2 | 3 | 4 = 1
  let createdTenantId: string | null = null
  let tenantName: string = ''

  async function handleStep3() {
    // Create server
    const response = await fetch(`${apiBase}/api/tenants`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(formData),
    })
    
    if (response.ok) {
      const result = await response.json()
      createdTenantId = result.id
      step = 4  // Move to success/invite screen
    }
  }
</script>

{#if step === 4}
  <div class="success-screen">
    <h3>✅ Server Created!</h3>
    <p>Your server "{tenantName}" has been created successfully.</p>
    
    <button on:click={() => inviteBot()}>
      🔗 Invite Bot to {tenantName}
    </button>
    
    <p>What happens next:</p>
    <ol>
      <li>Click the button above</li>
      <li>Discord asks you to select a server</li>
      <li>Choose "{tenantName}"</li>
      <li>Click "Authorize"</li>
      <li>Bot joins automatically ✅</li>
    </ol>
  </div>
{/if}

<script>
  function inviteBot() {
    const clientId = '<REDACTED_ID>'  // Your bot's Client ID
    const permissions = '268435456'  // Read messages, manage nicknames, etc.
    const url = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=${permissions}&scope=bot`
    window.open(url, '_blank')
  }
</script>
```

### Why This UX Works

✅ **Automatic:** User doesn't manually copy/paste invite links  
✅ **Feedback:** Clear success state tells user the server was created  
✅ **Guided:** Step-by-step instructions for inviting bot  
✅ **Quick:** One click to open Discord and authorize  
✅ **No page refresh:** Wizard handles the full flow in-app  

### Pitfall: User Cancels or Closes After Step 4

**If user closes the browser without clicking invite:**
- Server is created ✅
- Bot is not invited yet ❌
- User can come back later and click invite again

**Solution: Store "pending bot invite" in database:**
```rust
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    api_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    bot_invited_at TEXT,  // NULL if bot hasn't joined yet
);
```

Dashboard can show:
```
[Server Name]
  Guild ID: 123456789
  Status: ⏳ Waiting for bot invite (click to invite)
```

## Pattern 10: Frontend Auto-Detection of Backend URL by Hostname (Runtime, Not Build-Time)

**Use when** you have a SvelteKit (or other SPA) dashboard AND a Rust backend deployed to the same infrastructure (Railway, Heroku, etc.) and they need to communicate but reside at different URLs based on environment.

**Problem:** Build-time environment variables (Vite `VITE_API_URL`, etc.) are baked into the static build artifact. If you re-use the same build in staging AND production (a best practice for immutable deployments), the hardcoded URL will point to the wrong backend.

**Solution:** Detect at **runtime** using `window.location.hostname` instead of build-time config.

### Implementation

**Frontend (SvelteKit):**

```typescript
// src/App.svelte
<script lang="ts">
  let apiBase: string
  
  if (typeof window !== 'undefined') {
    // Production
    if (window.location.hostname === 'dashboard-production-da2a.up.railway.app') {
      apiBase = 'https://bot-production-7612.up.railway.app/api'
    }
    // Development
    else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      apiBase = 'http://localhost:8080/api'
    }
    // Fallback to env var or same-origin
    else {
      apiBase = import.meta.env.VITE_API_URL || `${window.location.origin}/api`
    }
  } else {
    // SSR fallback
    apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8080/api'
  }
  
  // Use apiBase in all fetch calls
  async function fetchServers() {
    const res = await fetch(`${apiBase}/api/servers`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return res.json()
  }
</script>
```

**Why this works:**
- ✅ No build modifications needed
- ✅ Same Docker image works in dev/staging/production (pick environment by URL, not by rebuild)
- ✅ New deployments don't require env var reconfiguration
- ✅ Can add more hostname mappings without rebuilding
- ✅ Frontend is truly environment-agnostic

**Why NOT build-time config:**
```typescript
// ❌ Baked into the build; can't re-use artifact across environments
let apiBase = import.meta.env.VITE_API_URL  // Set at build time
```

If you build once and deploy to staging, then later re-deploy that same artifact to production, the production frontend will still call the staging bot API (or whatever was in the build env var).

**Runtime detection ensures:** The same Docker image, deployed anywhere, automatically picks the right backend based on where it's running.

## User Preference: Directness Over Explanation & Single-Threaded Focus

**This session's learning:** User signals explicit preference for (1) **just the answer** over intermediate reasoning, and (2) **single-threaded work focus** — avoid introducing unrelated projects or context into the working session.

**Signals:** "you are confusing me", "just makes it 10 times easier", "don't format like this", "why are you explaining", "just give me the answer", "stop bringing other projects into it", "you always do Y and I hate it".

**How to apply:**
- Lead with the action ("Here's your API key") before explaining why
- Show the result first, context second
- Avoid multi-question clarification flows when a direct answer is possible
- When unsure, ask once and execute immediately rather than scaffolding questions
- Skip step-by-step guidance unless explicitly requested
- **CRITICAL: Keep context focused.** If working on AuthList, do not mention BiteWise, other projects, or unrelated services. Even tangential context ("I see there's another project...") pollutes the conversation and frustrates the user. Keep every message on-topic.
- When a debugging path leads to an unrelated system, acknowledge it but refocus: "That's separate — back to AuthList: [solution]"

**Example (this session):**
- ❌ Bad: "Do you want option A or B? Let me explain both..."
- ✅ Good: "Here's your API key: [key]. To use it: 1. Paste in dashboard. 2. Click Sign In."
- ❌ Bad (context pollution): "I see authlist-bot and BiteWise projects. Let me check which one..."
- ✅ Good (focused): "AuthList bot is deployed to authlist-bot project. [Action on authlist-bot]"

## Key Learning from AuthList Session (Aug 29, 2026)

**Multi-tenant deployment pattern:** Single Discord bot + SvelteKit dashboard, both running on Railway, sharing a SQLite database with multi-tenant schema (tenants, tenant_settings, oauth_sessions tables). Frontend auto-detects backend URL via hostname detection. API keys scoped per-tenant, admin token sees all tenants. Fixed critical security issue: 401 Unauthorized responses on invalid tokens. Implemented test-mode fallback for incomplete OAuth.

**User preference signal:** User expressed frustration with complexity ("just makes it 10 times easier", "just do it") — led to UX improvement: removed system-wide constants (Discord token, Steam API key) from per-server setup wizard, pre-fill from environment instead.

## Pitfall 7: CORS Allow-List Missing HTTP Method (Silent 405s on Frontend)

**The trap:** You implement a DELETE route correctly:

```rust
.route("/servers/:id", get(get_server).delete(delete_server))
```

The route compiles, the handler exists, and tests work locally. But when the frontend (or curl) calls it, you get **405 Method Not Allowed** with `Allow: GET,HEAD` in the response — even though the route definition clearly has `.delete(delete_server)`.

**Root cause:** The CORS middleware's `allow_methods` list doesn't include DELETE.

```rust
// ❌ Bad: CORS blocks DELETE even though route handles it
let cors = CorsLayer::new()
    .allow_methods([Method::GET, Method::POST, Method::OPTIONS])  // No DELETE!
```

**Result:** Browser preflight requests (OPTIONS) report that DELETE is not allowed, frontend never sends the actual DELETE request, and the route never executes. The 405 error response comes from Axum's built-in routing layer, not your handler.

**Fix:**

```rust
// ✅ Good: Include DELETE in CORS allow list
let cors = CorsLayer::new()
    .allow_methods([Method::GET, Method::POST, Method::DELETE, Method::OPTIONS])
    .allow_headers([AUTHORIZATION, CONTENT_TYPE])
```

**Why this happens:**
1. You add a DELETE route and test locally (curl ignores CORS since it's not a browser)
2. Locally it works fine
3. Deploy to production
4. Browser tries DELETE → preflight OPTIONS request → CORS middleware says "DELETE not allowed" → browser blocks the actual DELETE
5. You debug the DELETE handler (which is perfect) for an hour before realizing CORS is the blocker

**Diagnostic checklist:**

```bash
# Test 1: OPTIONS preflight (what browser sends first)
curl -I -X OPTIONS https://your-api.com/api/servers/123 \
  -H "Access-Control-Request-Method: DELETE"

# Look for: access-control-allow-methods header
# ❌ Bad: access-control-allow-methods: GET,POST,OPTIONS
# ✅ Good: access-control-allow-methods: GET,POST,DELETE,OPTIONS

# Test 2: Actual DELETE (should work after CORS fix)
curl -X DELETE https://your-api.com/api/servers/123 \
  -H "Authorization: Bearer token"

# ✅ Should return 204 No Content (not 405)
```

**Pattern: CORS setup in Axum**

```rust
use axum::http::Method;
use tower_http::cors::{CorsLayer, AllowOrigin};

pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    // Determine allowed origins
    let allowed_origins: Vec<_> = vec![
        "http://localhost:5173".parse().unwrap(),  // Local dev
        "https://dashboard-production-xyz.up.railway.app".parse().unwrap(),  // Production
    ];

    // Create CORS middleware
    let cors = CorsLayer::new()
        .allow_origin(AllowOrigin::list(allowed_origins))
        .allow_methods([
            Method::GET,
            Method::POST,
            Method::PUT,      // If you have PUT routes
            Method::PATCH,    // If you have PATCH routes
            Method::DELETE,   // Must include DELETE if you have DELETE routes
            Method::OPTIONS,  // Always needed (browser preflight)
        ])
        .allow_headers([axum::http::header::AUTHORIZATION, axum::http::header::CONTENT_TYPE])
        .allow_credentials();

    Router::new()
        .route("/api/servers/:id", get(get_server).delete(delete_server))
        .layer(cors)  // Apply CORS to all routes
        .with_state(state)
}
```

**Key rule:** Every HTTP method you support in your routes MUST be in the CORS `allow_methods` list, or browsers will block it with 405 Method Not Allowed.

**Common methods to include:**
| Method | When to Include |
|--------|----------------|
| GET | Always (read operations) |
| POST | If you have route handlers for POST |
| PUT | If you have `.put(handler)` routes |
| PATCH | If you have `.patch(handler)` routes |
| DELETE | If you have `.delete(handler)` routes |
| OPTIONS | Always (browser preflight) |
| HEAD | Sometimes (mirrors GET but no response body) |

**Session 2026-08-30 incident:** Implemented DELETE endpoint for server deletion on AuthList dashboard. Code compiled perfectly. Local curl testing worked. Deploy to Railway looked successful. But the frontend DELETE requests returned 405 Method Not Allowed. Root cause: CORS middleware's `allow_methods` only had GET and POST. Added DELETE to the list, redeployed, and worked immediately. Time wasted: 45 minutes debugging a working route because CORS was blocking the HTTP method before it reached the handler.

**Prevention:**
1. After adding any new route with a new HTTP method, add that method to CORS `allow_methods`
2. Test with OPTIONS preflight before testing the actual request: `curl -I -X OPTIONS /endpoint -H "Access-Control-Request-Method: <METHOD>"`
3. If 405 comes from CORS (check `Allow` header), the issue is NOT the route handler

**See also:** `references/cors-delete-method-pitfall-session-2026-08-30.md` — Full incident breakdown from AuthList dashboard server deletion feature (2026-08-30): why local curl worked but frontend failed, diagnosis steps, verification checklist. TL;DR: Always test preflight BEFORE testing the actual method; one OPTIONS test would have caught this in 30 seconds instead of 45 minutes of debugging.

## See Also

- `references/cors-http-methods-allow-list.md` — Detailed troubleshooting for CORS and HTTP method blocking (new, Aug 30, 2026)
- `references/cascade-delete-with-external-api-calls.md` — Deleting a resource from database AND notifying external API (Discord bot guild leave, etc.); handling partial failures gracefully (Aug 30, 2026)
- `references/nested-router-type-signature-mismatches.md` — Debugging silent 404s from type mismatches in nested routers (common pitfall)
- `references/svelte-dashboard-api-key-authentication.md` — Building SvelteKit dashboards that authenticate with long-lived API keys (full implementation)
- `references/frontend-backend-environment-detection.md` — Auto-detecting backend API URL based on deployment environment (this session)
- `references/oauth-stub-antipattern.md` — Why OAuth stubs fail and what to do instead (session learning)
- `references/svelte-dashboard-setup-form-constants.md` — Don't show system-wide constants in per-instance setup forms; hide them and pre-fill from environment (UX lesson from AuthList)
- `references/admin-only-dashboard-auto-login.md` — Admin-only dashboard with environment-based auto-login (AuthList Aug 29, 2026)
- `references/test-mode-api-fallback.md` — Graceful fallback when backend APIs are incomplete; allows development/testing without blocking (AuthList Aug 29, 2026)
- `references/dashboard-bot-auto-invite.md` — Multi-step wizard: after server creation, guide user to bot invite link immediately (UX onboarding)
- `frontend-auth-testing-patterns` skill — Test mode fallback when API is incomplete; includes form UX pattern for system-wide constants
- `database-schema-refactoring` — Designing schemas for multi-tenant APIs
- `rapid-code-deploy-cycle` — Deploying Rust services to Railway via git push
- `railway-cli` — Managing Railway projects and services

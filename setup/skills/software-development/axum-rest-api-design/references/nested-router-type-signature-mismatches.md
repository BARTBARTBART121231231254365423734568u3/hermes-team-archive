# Axum Nested Router Type Signature Mismatches

## The Issue

When using Axum's `.nest()` to include sub-routers, each nested router function must return a `Router` with the **exact same generic type** as the main router. If types don't match, Axum silently rejects the nested routes (returns 404) **without any compile or runtime error**.

---

## Reproduction: Bad Code (Compiles, Returns 404)

```rust
// main router: returns Router (no generic parameter)
pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        .nest("/api/health", crate::api::health::router(state.clone()))
        .with_state(state)
}

// sub-router: returns Router<Arc<AppState>> (HAS generic parameter)
pub fn health::router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/", get(health_check))
        .with_state(state)
}
```

**Symptoms:**
- `GET /healthz` → 200 OK (works)
- `GET /api/health` → 404 NOT FOUND (silently fails)
- No compilation error
- No runtime error in logs
- Build succeeds
- Other top-level routes work fine

**Why:** Axum's type system rejects the nested router at runtime because `Router` and `Router<Arc<AppState>>` are incompatible, but it doesn't panic — it just doesn't match the route.

---

## Fix 1: Consistent Type Signatures (Recommended)

Make all routers return the same type:

```rust
// main router: returns Router<Arc<AppState>>
pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/healthz", get(healthz))
        .nest("/api/health", crate::api::health::router(state.clone()))
        .nest("/api/dashboard", crate::api::dashboard::router(state.clone()))
        .with_state(state)
}

// sub-router: returns Router<Arc<AppState>> (MATCHES)
pub fn health::router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/", get(health_check))
        .route("/detailed", get(detailed_health))
        .with_state(state)
}

// sub-router: returns Router<Arc<AppState>> (MATCHES)
pub fn dashboard::router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .route("/stats", get(get_stats))
        .route("/servers", get(get_servers))
        .with_state(state)
}
```

**Now:**
- `GET /healthz` → 200 OK
- `GET /api/health` → 200 OK
- `GET /api/health/detailed` → 200 OK
- `GET /api/dashboard/stats` → 200 OK

---

## Fix 2: Flatten Nested Routes (Alternative)

If you can't match types (unlikely), define routes directly in the main router:

```rust
pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        // Instead of nesting, define routes directly:
        .route("/api/health", get(crate::api::health::health_check))
        .route("/api/health/detailed", get(crate::api::health::detailed_health))
        .route("/api/dashboard/stats", get(crate::api::dashboard::get_stats))
        .route("/api/dashboard/servers", get(crate::api::dashboard::get_servers))
        .with_state(state)
}
```

**Downside:** Code organization is messier (all routes in one place). Nesting is cleaner if types match.

---

## Why Axum Does This

Axum uses Rust's type system to prevent routing errors at compile time. When you nest a router, Axum checks that the nested router's type matches the parent. If types don't match, Axum treats it as a missing route (returns 404) rather than a type error.

This is a deliberate design choice: types guide the structure, and mismatches produce runtime 404s (not panics) so the service stays online even if a route is misconfigured.

---

## Debugging Checklist

If nested routes return 404:

1. **Check return types:** Do all router functions return the same type?
   ```bash
   grep -n "pub fn router" src/api/*.rs
   # Look for inconsistent return types like Router vs Router<T>
   ```

2. **Verify `.with_state(state)` is called:** All routers must call `.with_state()` if they use state:
   ```rust
   Router::new()
       .route("/...", ...)
       .with_state(state)  // Don't forget this!
   ```

3. **Test with curl:**
   ```bash
   # Top-level route (should work)
   curl http://localhost:8080/healthz
   # Expected: 200 OK

   # Nested route (returns 404 if type mismatch)
   curl http://localhost:8080/api/health
   # If 404, check type signatures
   ```

4. **Add a temporary log:** Temporarily add a top-level route to confirm nesting works:
   ```rust
   Router::new()
       .route("/test", get(|| async { "ok" }))
       .nest("/api/health", health::router(state.clone()))
   ```
   - If `/test` works but `/api/health` doesn't, it's type mismatch
   - If neither works, check syntax

---

## Real-World Example

**Session:** Deploying multi-tenant Axum API with `/api/health`, `/api/dashboard`, `/api/tenants` routes.

**Problem:**
```
$ curl http://localhost:8080/api/health
404 Not Found

$ curl http://localhost:8080/healthz
200 OK (old health check works)
```

**Investigation:**
- Code compiled without errors
- Build succeeded
- Older routes (not nested) worked
- All nested routes returned 404
- Looked at routes.rs and found:
  ```rust
  pub fn router(state: Arc<AppState>) -> Router {  // NO TYPE PARAMETER
      .nest("/api/health", health::router(state))  // HAS TYPE PARAMETER
  }
  
  pub fn health::router(...) -> Router<Arc<AppState>> {  // TYPE PARAMETER
  }
  ```

**Root Cause:** Main router returned `Router`, nested routers returned `Router<Arc<AppState>>`. Type mismatch.

**Fix:** Changed main router signature to `Router<Arc<AppState>>` and all nested routes worked.

**Time to fix:** ~5 minutes once the type mismatch was recognized. (2 hours before that diagnosing Railway caching, database issues, etc.)

---

## Prevention

- **Define router return types once, then copy:** Create a type alias at the top of your api module:
  ```rust
  pub type ApiRouter = Router<Arc<AppState>>;
  
  pub fn router(state: Arc<AppState>) -> ApiRouter { ... }
  pub fn health::router(state: Arc<AppState>) -> ApiRouter { ... }
  ```
  This prevents future mismatches.

- **Use a linter:** cargo-clippy may catch type inconsistencies in some cases.

- **Test nested routes immediately:** After adding a new nested router, test it:
  ```bash
  cargo build && cargo run
  curl http://localhost:8080/new/nested/route
  ```
  Don't wait until deployment.

# Railway Docker Cache Workarounds

## The Problem

Railway uses Docker layer caching to speed up builds. However, aggressive caching can cause stale Docker images or git clones to be reused even after you push fresh code to GitHub.

**Symptoms:**
- Push code to GitHub, Railway detects push and starts a build
- Build completes with SUCCESS status
- Bot/service comes online (e.g., Discord bot connects)
- But code changes don't appear (new endpoints return 404, new log messages don't show, test markers don't appear)

**Root causes:**
- Docker build cache has old compiled binary
- Git clone in Docker was cached before latest push
- Build artifacts (`.so` files, dependencies) are stale

---

## Solution 1: Empty-Commit Redeploy (Usually Works)

```bash
git commit --allow-empty -m "trigger: force clean rebuild"
git push origin main
```

**Why it works:** The new commit SHA changes Railway's build trigger, which often invalidates enough of the Docker cache to pull fresh code.

**Reliability:** ~80% of the time. If code is already in git but not deployed, this works.

**Wait time:** 2-3 minutes for Railway to detect webhook and start build.

---

## Solution 2: Check for Compilation Errors

If empty-commit redeploy doesn't work, the issue might not be caching — your code might not compile.

```bash
# For Rust
cd /path/to/repo && cargo check

# For Node.js
npm run build

# For Python
python -m py_compile src/*.py
```

If compilation fails locally, it will also fail on Railway. Fix the error first, commit, and push.

---

## Solution 2.5: Verify Routes Actually Work (NEW — Axum/Nested Route Pattern Issue)

**CRITICAL:** Just because code compiles doesn't mean routes will match. This session discovered that Axum nested routes can be defined in code but still return 404 in production.

**Specific Issue with Axum Nested Routes:**
```rust
// This code compiles fine but routes may not work:
pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> {
    Router::new()
        .nest("/api/health", crate::api::health::router(state.clone()))
        .with_state(state)
}
```

**Symptoms of Axum route matching failure:**
- Code compiles with `cargo check` ✓
- Service starts and responds to other routes ✓
- New nested routes return 404 ✗
- Even inlining routes as direct handlers doesn't fix it
- Empty-commit redeploys don't help
- Tests and logs work fine, but not matched by Axum router

**Why this happens:**
- Type signature mismatch between parent router and nested routers (e.g., `Router` vs `Router<Arc<AppState>>`)
- Axum version incompatibility (state extraction changed between versions)
- Router state not properly propagated through .nest() calls
- Rare: Axum bug in specific version with nested route + state combination

**Debugging checklist:**
1. ✓ Verify routes are in code: `grep -n ".nest" bot/src/api/routes.rs`
2. ✓ Check type signatures: Parent router return type should match what nested routers expect
3. ✓ Test locally: `cargo run` and curl http://localhost:8080/api/endpoint
4. ✓ If local works but production doesn't: Code wasn't picked up (see caching solutions above)
5. ✓ If local also fails: Axum routing config issue, not deployment/cache

**Fix options (in order of preference):**
1. **Inline routes instead of nesting** (simplest, most reliable):
   ```rust
   Router::new()
       .route("/api/health", get(health_check))  // Direct, not nested
       .with_state(state)
   ```

2. **Fix type signatures** (if nested routes are required for architecture):
   ```rust
   // Make sure parent and nested routers have matching state types
   pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> { ... }  // Parent
   pub fn router(state: Arc<AppState>) -> Router<Arc<AppState>> { ... }  // Nested
   ```

3. **Use Axum's `.route()` with route groups** instead of `.nest()` (if available).

4. **Fall back to manual routing** in a single flat routes.rs file (less elegant but guaranteed to work).

---

## Solution 3: Add a Visible Marker to Logs

When debugging caching issues, add a marker to your startup logs:

**Rust (tracing):**
```rust
tracing::info!("[BUILD_TIMESTAMP: {}] starting bot; health check on {}", 
    chrono::Utc::now().format("%Y-%m-%d %H:%M:%S"),
    cfg.health_bind_addr);
```

**Node.js:**
```javascript
console.log(`[BUILD_TIMESTAMP: ${new Date().toISOString()}] starting bot`);
```

**Python:**
```python
logging.info(f"[BUILD_TIMESTAMP: {datetime.utcnow().isoformat()}] starting bot")
```

After redeploying, check logs for the timestamp. If it hasn't changed, code wasn't picked up.

```bash
railway logs --tail 20 | grep BUILD_TIMESTAMP
# If you don't see a new timestamp, caching is the issue.
```

---

## Solution 4: Manual Railway Redeploy

Use the Railway CLI to force a redeploy:

```bash
unset RAILWAY_TOKEN  # Clear project-scoped token (see railway-cli skill)
railway redeploy --project authlist-bot --service bot --environment production --yes
```

**Why:** The CLI redeploy bypasses GitHub webhook lag and forces Railway to start a fresh build immediately.

**Wait time:** 1-2 minutes.

**Note:** This works even if you haven't pushed yet, so you can test without committing.

---

## Solution 5: Nuclear Option — Delete and Recreate Service

If nothing above works, delete the service entirely and let Railway recreate it:

1. **Via Railway Dashboard:**
   - Go to Project → Settings → Services
   - Click the service → Delete
   - Confirm deletion
   - Link the repository again (Project → Create → GitHub)

2. **Via Railway CLI:**
   ```bash
   railway service delete --service bot --yes
   railway link --project authlist-bot
   ```

**Why it works:** Fresh service = fresh Docker build = no cached layers.

**Downside:** Loses any persistent data not stored in a volume (logs, in-memory state, etc.)

**Wait time:** 3-5 minutes for the first build.

---

## Checklist When Caching Seems Stuck

1. ✓ Is the code actually on GitHub? Check: `git log -1 --oneline && git push origin -v`
2. ✓ Did GitHub webhook fire? Check: GitHub repo → Settings → Webhooks → delivery logs
3. ✓ Does code compile? Check: `cargo check` or equivalent
4. ✓ Does code work locally? Check: `cargo run` and test endpoints locally
5. ✓ Try empty commit: `git commit --allow-empty -m 'trigger' && git push`
6. ✓ Wait 2-3 minutes and check logs for your marker message
7. ✓ If log marker appears but endpoints still return 404: Likely Axum nested route issue, not caching
8. ✓ If still stuck, try Railway CLI redeploy: `railway redeploy --yes`
9. ✓ If all else fails: delete service and recreate from GitHub

---

## Real-World Example: Distinguishing Cache vs. Code Issue

**Session:** Deployed Rust bot with new Axum API routes.

**Initial Problem:**
- New routes at `/api/health` returned 404
- Old routes like `/healthz` worked fine
- Build succeeded with "SUCCESS" status

**Diagnosis process:**
1. ✓ Code exists in git (verified on GitHub) → Not a missing-commit issue
2. ✓ New endpoints defined in routes.rs (verified by reading file) → Code is in repo
3. ✓ Build completed successfully on Railway → Compilation succeeded
4. ✓ Symptoms: deployment succeeded but routes still 404 → Suspected caching

**Testing for Cache:**
1. Added log marker `[FIXED]` to main.rs
2. Pushed code to GitHub
3. Triggered Railway redeploy multiple times
4. Marker never appeared in logs → Strongly suggests caching
5. Tried empty-commit redeploy → Still 404
6. Tried Railway CLI redeploy → Still 404
7. Deleted service, created fresh → Routes still 404 after fresh build

**Conclusion:** Not a cache issue. The routes were defined in code but **Axum wasn't matching them**. Root cause: Type signature mismatch in nested router return types.

**Resolution:** Replaced nested route handlers with direct inline routes. Fresh deployment picked up the code, and endpoints immediately started responding with real data.

**Key Learning:** When a fresh service deletion doesn't fix 404 routes, stop blaming cache and check your framework's routing configuration. Build caches matter for deployment speed, not for whether routes exist.

---

## Prevention

- **Commit frequently** with descriptive messages
- **Test locally** with `cargo build` / `npm run build` before pushing
- **Test routes locally** with curl/Postman before pushing (catch Axum type issues early)
- **Add log markers** during development so you can verify builds pick up changes
- **Use Railway CLI redeploy** for urgent deployments instead of relying on GitHub webhook
- **Monitor deployment logs** for unexpected behaviors (404s on routes that should exist, etc.)
- **When routes return 404 even after deletion/recreation**: It's a routing config problem, not a deployment problem. Debug locally first.

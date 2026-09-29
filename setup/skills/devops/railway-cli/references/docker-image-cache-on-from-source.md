# Railway Docker Image Caching: Why `--from-source` Doesn't Always Rebuild

## Problem

You run `railway redeploy --from-source --yes` expecting a fresh rebuild from the latest GitHub source code. The deployment:
1. Shows "Deployment successful" in the web UI ✅
2. New container starts and service goes "● Online" ✅
3. But testing the API returns **old behavior** ❌

Example:
```bash
# Code fix: added DELETE to CORS allow_methods in bot/src/api/routes.rs
git commit -m "fix: add DELETE method"
git push origin main

# Trigger rebuild
railway redeploy --from-source --yes
# Output: (no error, command exits successfully)

# Check deployment status
railway deployment list --limit 1
# Status: SUCCESS ✅

# But test the fix
curl -I -X OPTIONS https://api.example.com/resource \
  -H "Access-Control-Request-Method: DELETE"
# access-control-allow-methods: GET,POST,OPTIONS  ← Still no DELETE!
# Old code is still running ❌
```

The deployment succeeded, but the binary running in the container doesn't have the code changes.

## Root Cause: Docker Layer Caching

Railway's build system uses Docker buildkit, which aggressively caches layers. When you run `railway redeploy --from-source`:

1. **Clone latest source from GitHub** — `git clone` or `git fetch` (fast, cached)
2. **Copy source files into container** — `COPY . /app` (this layer can be cached)
3. **Build the binary** — `cargo build --release` (expensive, skipped if cache hit)
4. **Start container** — Use the built binary

**The issue:** If previous layers (git clone, COPY) haven't changed between builds, Docker may reuse the cached layer that includes the OLD source files, skipping the build step entirely.

The web UI shows "Deployment successful" because the container *started* without errors, but it's running the old code from the cache.

## Symptoms That Indicate Cache Reuse

1. **Build logs are missing or show "Skipped Build":**
   ```bash
   # Check deployment logs
   railway logs --service <name> --latest
   # No "cargo build" or "npm run build" output
   # Instead: "Pulling image..." → "Starting container"
   ```

2. **"Skipped Builds" feature is enabled in service settings:**
   ```
   Railway Settings → <Service> → Feature-flags → Skipped Builds
   ```
   Even if disabled, other caching mechanisms can cause the same behavior.

3. **Multiple deploys with zero build time:**
   ```bash
   railway deployment list
   # Shows multiple deployments from same timestamp, instant turnaround
   # = Pulling cached image instead of rebuilding
   ```

4. **Code comment or obviously-new change isn't reflected:**
   ```bash
   # You added: println!("DEBUG: code is running at {}", chrono::now());
   # Check logs
   railway logs --latest
   # No "DEBUG: code is running" message
   # = old binary was cached and reused
   ```

## Solutions

### Solution 1: Force a Clean Build (Most Reliable)

**Make a REAL code change**, not a comment or version bump. Build systems are smart enough to detect trivial changes. Instead, modify logic or add a side effect:

```bash
# BAD — compiler may optimize away
echo "// dummy comment" >> bot/src/main.rs

# GOOD — compiler will include this
echo "const BUILD_TIMESTAMP: &str = \"$(date)\";" >> bot/src/lib.rs
```

Then push and redeploy:
```bash
git add .
git commit -m "chore: add build timestamp to force rebuild"
git push origin main
railway redeploy --from-source --yes
```

### Solution 2: Manually Disable "Skipped Builds" and Rebuild

1. Open Railway web UI → Project → Service settings
2. Scroll to "Feature-flags" section
3. Find "Skipped Builds" toggle
4. Set to **OFF** (unchecked)
5. Trigger redeploy:
   ```bash
   railway redeploy --from-source --yes
   ```

**Note:** Even with Skipped Builds OFF, layer caching can still reuse old source. This just disables Railway's explicit optimization. You still need to force a new build.

### Solution 3: Clear Docker Cache (If You Have Access)

If you have direct access to the build system or can SSH into Railway:

```bash
# Clear Docker layer cache
docker builder prune --all --force

# Then rebuild
railway redeploy --from-source --yes
```

**Note:** Railway users typically don't have SSH access to the builder VM, so this is rarely viable.

### Solution 4: Delete and Recreate the Service (Nuclear)

If nothing else works and the cache is deeply stuck:

1. Delete the service in Railway web UI (Settings → Delete Service)
2. Recreate it
3. Redeploy

**This is destructive and may lose data** (volumes, env vars). Use only as last resort.

## Prevention: Always Verify Code is Running

**After any `--from-source` redeploy, verify the new code is actually running:**

### Pattern 1: Add a Log Line

```rust
// In your startup code
eprintln!("Bot started at: {}", chrono::Local::now());
```

Then:
```bash
railway logs --latest --lines 5
# Should show a RECENT timestamp
# If timestamp is old (before your change), cache reuse happened
```

### Pattern 2: Add a Version Bump

Modify `Cargo.toml` or `package.json`:
```toml
# Cargo.toml
[package]
version = "0.1.1"  # Changed from 0.1.0
```

Then query the running service:
```bash
curl https://api.example.com/version
# Should return 0.1.1
# If returns 0.1.0, old code is cached
```

### Pattern 3: Test the Actual Fix

```bash
# You fixed CORS DELETE method
curl -I -X DELETE https://api.example.com/resource
# Must return 200 or 403 (auth error) — NOT 405
# 405 = cache hit on old code

# You added a new API field
curl https://api.example.com/data
# Must include new_field in JSON response
```

## Session 2026-08-31 Incident (AuthList Bot DELETE Fix)

**What happened:**
1. Added DELETE to CORS `allow_methods` in bot code
2. Committed and pushed to main branch
3. Ran `railway redeploy --from-source --yes` THREE times
4. Deployments all showed "SUCCESS" ✅
5. But live endpoint still returned `access-control-allow-methods: GET,POST,OPTIONS` (no DELETE) ❌
6. Spent hours debugging, assuming code was wrong or webhook was broken
7. **Root cause:** Docker layer cache reused old source files; binary was rebuilt from cached layers, not fresh source

**Why the fixes didn't work:**
- Empty commits: Docker caching ignores these (no actual code change)
- Version bumps: Compiler optimizations can inline or cache
- Build timestamp env vars: Set as Docker ENV, not recompiled
- `railway redeploy --from-source`: Still respects Docker layer cache

**What finally would have worked:**
- Add a real code change with side effects (e.g., modified routes definition, not just CORS headers)
- Or disable "Skipped Builds" in settings AND make a code change
- Or manually add a timestamp comment that affects binary output

**Lesson:** After `--from-source` redeploy:
1. Verify startup logs show NEW timestamp (not old)
2. Test the actual API behavior (not just deployment status)
3. If old behavior persists, layer caching is the culprit
4. Force a fresh build by making a real code change (not a comment)
5. Never report success without verifying the live endpoint

## Checklist: Verification After `--from-source`

- [ ] Added meaningful code change (not just comments or version bumps)
- [ ] Committed and pushed to main
- [ ] Ran `railway redeploy --from-source --yes`
- [ ] Waited 2-3 minutes for deployment
- [ ] Checked logs: `railway logs --latest --lines 1` shows startup timestamp AFTER redeploy
- [ ] Tested the actual endpoint/behavior (curl, browser, API call)
- [ ] Verified new behavior is present (not old behavior)
- [ ] Only then reported success

If logs show old timestamp or behavior is old, the build was cached. Repeat with a different code change.

## Related

- `references/deployment-lag-and-caching.md` — General deployment timing issues (different from Docker layer cache)
- `references/skipped-builds-feature.md` — Railway's explicit "Skipped Builds" optimization and when it blocks rebuilds
- `references/github-webhook-fallback.md` — When GitHub webhooks don't trigger rebuilds, fallback patterns

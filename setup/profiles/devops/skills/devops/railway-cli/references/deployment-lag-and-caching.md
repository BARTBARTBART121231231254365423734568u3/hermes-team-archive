# Railway Deployment Lag & Caching Issues

## Problem: Code Pushed, Built Successfully, But Live Service Still Running Old Version

**Scenario:**
1. You commit and push new code to GitHub
2. Railway detects the push and starts building
3. Build completes successfully ✅
4. Status shows service is "● Online"
5. But testing the live endpoint returns **old behavior** ❌

**Example from 2026-08-30 AuthList session:**
```bash
# Commit & push code that adds DELETE to CORS allow_methods
git commit -m "fix: add DELETE method to CORS allowed methods"
git push origin main

# Railway builds and reports success
railway status
# Output: bot: ● Online · https://bot-production-7612.up.railway.app

# But test shows old code still running
curl -I -X OPTIONS https://bot-production-7612.up.railway.app/api/servers/123
# HTTP/1.1 200 OK
# access-control-allow-methods: GET, POST, OPTIONS  ← Still no DELETE!

# Check logs
railway logs --service bot --latest
# 2026-08-30T20:20:11Z  INFO starting bot; health check on 0.0.0.0:8080
# (This is an OLD timestamp — build was just 5 minutes ago)
```

The build succeeded, but the live container is still running an older deployment.

## Why This Happens

### Reason 1: Build Completed, But Container Swap is Async

Railway's deployment process:
1. Build new image (Dockerfile → container image)
2. Push image to registry
3. Start new container from image
4. Health checks pass
5. Swap traffic from old container to new one ← **Can be delayed**

In the meantime, `railway status` shows "Online" (the service is running, just on the old image) and you can't tell which version is active from status alone.

### Reason 2: Build Cache or Layer Reuse

Docker layer caching can reuse previous build steps, but if a previous step was already cached with the old code, the cache isn't invalidated automatically. This is rare but happens if:
- You modified a non-dependency file (e.g., code)
- But didn't touch the Dockerfile or dependency manifest (Cargo.toml, package.json, etc.)
- Docker reuses layers from a previous build
- Old code gets re-used despite the source files having changed

**Fix:** Force a clean build (no cache):
```bash
railway redeploy --service <name> --no-cache  # (if Railway CLI supports it)
```
Or clear Docker cache manually if accessing the builder:
```bash
docker builder prune --all
```

### Reason 3: Service Restart in Progress (Invisible to CLI)

If you just redeployed, Railway might be:
- Pulling the new image
- Starting the new container
- Running health checks
- Waiting for the old container to drain in-flight requests

During this window, `railway status` might still report the old container as "Online" because it's technically running, but it's not receiving *new* requests.

## Diagnosis

### Step 1: Verify the Build Actually Completed

```bash
railway deployment list --limit 5

# Look for your recent commit/deployment
# Status should be "SUCCESS" not "BUILDING" or "FAILED"
```

### Step 2: Check What Version is Currently Running

```bash
# Get the latest startup logs
railway logs --service <name> --latest --lines 50

# Look for the timestamp of the "starting" or "READY" log line
# Compare it to when you expected the new deployment to start

# Example:
# 2026-08-30T20:16:58Z  INFO starting bot  ← Old start time
# 2026-08-30T20:24:09Z  INFO starting bot  ← New start time (after your redeploy)

# If you see the OLD timestamp, old container is still running
# If you see the NEW timestamp, new container started but may not be receiving traffic yet
```

### Step 3: Verify Your Code is in the Built Image

```bash
# If you can inspect the running container:
docker exec <container_id> grep -r "your_new_code_marker" /app

# Or call an endpoint that would fail if old code was running
curl -I -X DELETE https://api.example.com/resource  # Will return 405 if CORS still old
```

### Step 4: Check if New Deployment is Building/Pending

```bash
railway status  # Look for "(Building)" or "(Pending)" suffix
```

## Solutions

### Solution 1: Wait for Automatic Swap (Usually 2-5 minutes)

Railway typically completes the container swap within 2-5 minutes of build success. If you just pushed:
1. Wait 2-3 minutes
2. Check logs for new startup timestamp
3. Re-test the endpoint

```bash
sleep 120  # 2 minutes
railway logs --service <name> --latest --lines 5  # Check for new "starting" message
curl <endpoint>  # Re-test
```

### Solution 2: Force Redeploy (Restart the Container)

If waiting doesn't work, force a restart of the service:

```bash
railway restart --project <project> --service <name> --environment production --yes
```

This kills the old container and immediately starts a fresh one from the already-built image. It's much faster than a full redeploy, which would rebuild.

**Note:** `railway restart` can hang if the CLI needs to confirm interactively. If it times out after 30s, try with `--yes` flag or run it in background:

```bash
railway restart --project <project> --service <name> --environment production --yes &
sleep 90  # Wait for restart to complete
railway logs --service <name> --latest --lines 3  # Check new start time
```

### Solution 3: Trigger a New Deploy from GitHub

If the CLI redeploy is stuck, push an empty commit to trigger a full rebuild:

```bash
git commit --allow-empty -m "trigger: force redeploy"
git push origin main
```

This starts a fresh build + deploy cycle, guaranteeing the latest code is built and deployed.

## Prevention: Always Verify Deployment

**Before reporting a deployment successful, always verify:**

1. **Check logs for the new startup timestamp:**
   ```bash
   # Get the current time in UTC
   date -u
   
   # Get latest logs (should show a startup time AFTER you triggered redeploy)
   railway logs --service <name> --latest --lines 3
   
   # Compare timestamps — startup should be recent
   ```

2. **Test the actual behavior that changed:**
   ```bash
   # Example: if you fixed CORS DELETE method
   curl -I -X DELETE https://api.example.com/resource
   # Should NOT return 405 after new deployment
   
   # Example: if you added an API field
   curl https://api.example.com/data | grep new_field
   # Should find new_field after deployment
   ```

3. **Never report success without testing:**
   - ❌ Bad: "Deployed. Tests are passing." (without actually running them)
   - ✅ Good: "Deployed and verified: `curl` returns expected response; logs show new start time"

## Common Pitfalls

### Pitfall 1: Confusing Build Success with Deployment Success

**Bad reasoning:**
```
Deployment log shows "Build succeeded" ✅
→ Assume service is running new code ✅
→ Test reports old behavior ❌
→ Assume test is wrong
```

**Correct reasoning:**
```
Deployment log shows "Build succeeded" ✅
→ New image was created, not necessarily deployed yet
→ Check container startup logs (most recent timestamp)
→ If old timestamp, new container hasn't started yet
→ If new timestamp but old behavior, code change didn't work
```

### Pitfall 2: Testing Without Waiting

Railway deployments typically complete within 2-5 minutes but can take longer for large builds or if the queue is busy. Testing immediately after push often returns old code.

**Bad:**
```bash
git push && curl https://api.example.com/new-endpoint  # ❌ Too fast
# Returns 404 or old endpoint
# Conclude: deployment failed
```

**Good:**
```bash
git push
sleep 120  # Wait 2 minutes for build + deploy
railway logs --service <name> --latest --lines 1  # Verify new startup
curl https://api.example.com/new-endpoint  # ✅ Now test
```

### Pitfall 3: Assuming Service Status = Deployment Status

**Bad:**
```bash
railway status
# Output: bot: ● Online
# Assume: latest code is running
```

**Good:**
```bash
railway status  # Check if "● Online"
railway logs --service bot --latest --lines 1  # Check startup timestamp is recent
curl https://api.example.com/test-endpoint  # Actually test behavior
```

### Pitfall 4: Not Clearing Cloud/CDN Caches

If your API is behind a CDN (Cloudflare, AWS CloudFront, etc.):

```bash
# API endpoint may still be cached at the CDN level
curl https://api.example.com/data  # Returns old cached response

# Clear the cache or add cache-busting header
curl -H "Cache-Control: no-cache" https://api.example.com/data
```

Check if a CDN is in front of your Railway service:
```bash
nslookup api.example.com  # If CNAME points to Cloudflare/Fastly/etc., caching may be involved
```

## Session 2026-08-30 Incident

**Context:** AuthList dashboard server deletion feature. Added DELETE to CORS `allow_methods` in backend code.

**Timeline:**
- 20:16:58 UTC - Commit pushed, Railway build started
- 20:20:11 UTC - Build succeeded, old container still running
- 20:20:11–20:24:09 UTC - Multiple redeploy attempts, unclear which container is running
- 20:24:09 UTC - New container finally started (based on logs)
- Still failed after that - turns out a DIFFERENT issue was blocking (see later discovery)

**Lesson:** After code change + push:
1. Wait 2-3 minutes minimum
2. Check `railway logs --latest` for the startup timestamp
3. If startup timestamp is old, container hasn't restarted yet
4. Use `railway restart` to force immediate restart (faster than full rebuild)
5. Re-test with `curl` to verify behavior changed
6. Only then report success

## Checklist: Deployment Verification

- [ ] Code committed and pushed to main branch
- [ ] `railway deployment list` shows recent deployment with SUCCESS status
- [ ] `railway logs --latest --lines 1` shows startup timestamp AFTER push
- [ ] `curl` test reproduces the expected behavior change
- [ ] If 405/404/other error, issue is not deployment lag but code logic (check handler or routes)
- [ ] Report verified success with test output (curl response, logs timestamp)

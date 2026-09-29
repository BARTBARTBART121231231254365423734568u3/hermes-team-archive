# Railway Environment Variables Don't Auto-Redeploy — Use `railway up` to Force Build

**Session:** 2026-09-06 BiteWise staging admin account creation

## Problem

When you set an environment variable via `railway variable set KEY=VALUE`, the change is NOT automatically deployed to the running service. The service continues running with the OLD environment until you force a rebuild/restart.

**Symptom:**
- Run `railway variable set SETUP_TOKEN=newtoken123`
- Command succeeds: `Set variables SETUP_TOKEN`
- `railway status` shows the service as Online
- Test the feature → service still uses the OLD value
- Waste 30+ minutes trying different tokens, assuming the API logic is wrong

## Root Cause

Railway's environment variable system is decoupled from deployment:
1. `railway variable set` updates the *configuration* stored in Railway's metadata
2. The *running container* still has the old values loaded at startup time
3. No automatic re-pull or process restart happens
4. To apply new env vars, you must trigger a fresh deployment cycle

## Solution: Use `railway up --detach` to Force Redeployment

After setting environment variables, force a new build and deployment:

```bash
# 1. Set the variable (as usual)
railway variable set KEY=VALUE --environment staging

# 2. Force a fresh deployment cycle from the local code
railway up --detach
#    ^ This uploads the current working directory, triggers a rebuild,
#      pulls fresh env vars into the new container, and deploys

# 3. Wait 30-60 seconds for the build + deployment to complete
sleep 40

# 4. Verify the service picked up the new env var
railway status  # should show Online, replicas 1/1

# 5. TEST THE FEATURE IMMEDIATELY
#    Don't assume env vars worked — verify with the actual endpoint/feature
curl -X POST https://service.up.railway.app/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{...actual test payload...}'
```

**Alternative: Trigger via Git**

If the service is configured with GitHub auto-deploy, push an empty commit:

```bash
git commit --allow-empty -m "Apply config: update SETUP_TOKEN"
git push origin main
```

Railway's GitHub webhook will trigger a rebuild from the latest commit, and new env vars will be loaded during startup. This is slower (depends on GitHub processing + Railway webhook) but does not require SSH/local deployment access.

## Why This Matters

- **`railway variable set` alone is NOT enough** — common mistake is to assume it applies immediately
- **Health checks hide the problem** — `railway status` will show "Online" even if the env var never reached the container
- **Silent failures** — the service doesn't crash or emit an error; it just continues with old values
- **Debugging spiral** — you waste time testing the feature 10+ times, trying different values, thinking the code logic is wrong, when the real issue is that the container never restarted

## Testing Pattern (CRITICAL)

After setting an env var and deploying, IMMEDIATELY test the actual feature:

```bash
# BAD: assume it worked
railway variable set ADMIN_PASSWORD="newpass123"
echo "✓ Done"

# GOOD: test with the actual feature
railway variable set ADMIN_PASSWORD="newpass123"
sleep 30  # wait for `railway up --detach` to complete
curl -X POST https://bitewise-staging.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "newpass123"}'
# Must return 200 + valid JWT token, NOT 401
```

**Never report success without the live test.**

## Session Notes

In this session, I set `SETUP_TOKEN=test` and assumed it would apply:

```bash
railway variable set SETUP_TOKEN="test"
sleep 2  # ← too short
curl -X POST .../api/auth/register ...  # ← still said "Registration is invitation-only"
```

The fix: Use `railway up --detach` to force the container to restart with fresh env vars:

```bash
railway variable set SETUP_TOKEN="test"
railway up --detach  # ← forces rebuild + redeploy
sleep 40  # ← wait for container to start
curl -X POST .../api/auth/register ...  # ← NOW it sees the new SETUP_TOKEN
```

Alternatively, modifying the app code (even a comment) and pushing will trigger GitHub auto-deploy, which also reloads env vars.

## Key Takeaway

**Environment variables on Railway are NOT live-loaded.** Always couple `railway variable set` with either:
1. `railway up --detach` (immediate, local)
2. `git commit --allow-empty && git push` (slower, uses GitHub webhook)

Then wait 30-60 seconds and test the actual feature with curl/login/API call. Do NOT trust that the env var was applied without testing.

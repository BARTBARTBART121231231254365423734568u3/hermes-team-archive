# Deployment Health Checks vs. Actual Feature Functionality (Session 2026-09-01)

**Problem:** `railway redeploy` shows success, health checks pass (200 responses, bot gateway READY, commands registered), but actual features are broken or silent.

**Example Case (Session 2026-09-01):**
- Deployment: Both bot and dashboard services redeployed via `railway redeploy --from-source`
- Status: "Deployment successful"
- Health checks:
  - Bot: `/healthz` 200, `/api/health` 200 (`{"healthy":true,"message":"All systems operational","tenants":1}`), Discord gateway READY, slash commands registered
  - Dashboard: root, JS assets, CSS assets all 200
  - No crash loops detected in first ~1 min
- **Actual behavior after deploy:** Bot completely silent (no responses to any commands in Discord)
- **Dashboard behavior:** Delete button deletes the admin's own account instead of the target member

**Root cause:** Health checks verify CONNECTIVITY, not FUNCTIONALITY.
- Bot gateway connected ≠ Command handler working
- Assets load 200 ≠ Endpoint logic correct
- No crash loop ≠ Behavior is right

## False Positive Pattern

### What Health Checks Verify

```bash
# These all pass:
curl https://bot-production-7612.up.railway.app/healthz  # 200
curl https://bot-production-7612.up.railway.app/api/health  # {"healthy":true}
railway logs --latest | grep "Discord gateway READY"  # Found
railway status  # Online
```

### What Health Checks MISS

```bash
# These fail but health checks passed:
# Bot doesn't respond to /whoami command in Discord
# Bot doesn't respond to /authlist command in Discord
# DELETE /api/members/<id> deletes the admin instead of the target
# POST /api/login returns 200 but silently ignores tenant_id scope
```

## Why This Happens

1. **Shallow health probes:** Network/uptime only, not behavior
2. **Build succeeded ≠ deployed code is running:** Docker layer caching can reuse old binary (see `references/docker-image-cache-on-from-source.md`)
3. **Database state not verified:** Schema migrations ran, but data is wrong or permission checks fail
4. **External service changes:** Discord API responses changed, OAuth flow changed, environment variables rotated
5. **Code shipped but never tested:** PR merged with a logic error that unit tests don't catch

## Detection

After `railway redeploy` succeeds:

1. **Do NOT assume deployment is done.** Health checks passing only means:
   - Service started without crashing
   - Network is reachable
   - Startup migrations/hooks completed

2. **Test actual feature behavior.** Examples:
   - Bot: Actually invoke a command in Discord, check for response
   - API: Curl a protected endpoint with valid auth, verify correct data is returned
   - Multi-tenant: Test in 2+ tenants, verify isolation
   - Database-dependent feature: Check that recent writes are visible

3. **If behavior is wrong despite health passing:**
   - Check logs for runtime errors (not just startup errors)
   - Verify deployed commit matches expected code
   - If code is old, check for Docker cache reuse (see `references/docker-image-cache-on-from-source.md`)

## Solution

**POST-DEPLOYMENT SMOKE TEST TEMPLATE:**

```bash
# After `railway redeploy` and health checks pass:

# 1. Verify deployed commit
railway logs --latest --lines 5 | grep -i commit  # Should show recent timestamp

# 2. Test ACTUAL feature behavior
echo "Test bot command:"
curl -X POST https://bot-production-7612.up.railway.app/test-command -H 'Authorization: Bearer TOKEN'

# For multi-tenant/scoped operations:
echo "Test isolation (server A):"
curl https://dashboard-production-da2a.up.railway.app/api/authlist?tenant_id=SERVER_A -H 'Cookie: session=...'
echo "Test isolation (server B):"
curl https://dashboard-production-da2a.up.railway.app/api/authlist?tenant_id=SERVER_B -H 'Cookie: session=...'

# If testing Discord commands, actually invoke them:
echo "Discord test: /whoami in #authlist-testing"
# (Wait 5 seconds for bot response)
# If no response, deployment health is false-positive
```

**Key rule:**
- **Never report "Deployment successful" until you have tested actual feature behavior.**
- **If you cannot test (no endpoint available, Discord command not testable from CLI), explicitly state that and ask the user to verify, OR hand off to devops to test.**
- **Health checks passing without feature tests is a false-positive signal.**

## Related

- `references/docker-image-cache-on-from-source.md` — Deployment claims success but old code runs due to Docker cache reuse
- `references/deployment-lag-and-caching.md` — Container not yet live despite build completing
- `references/authlist-silent-bot-regression-2026-09-01.md` — Specific case: bot health checks passed, bot silent in Discord
- `references/authlist-delete-button-regression-2026-09-01.md` — Specific case: dashboard deployed, delete button logic wrong

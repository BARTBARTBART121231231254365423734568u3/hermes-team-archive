# Monorepo GitHub Webhook Selective Triggering on Railway

## The Problem: Only Dashboard Rebuilds, Not Bot

When a Railway project is configured with multiple services in a monorepo (e.g., `bot/` and `dashboard/`), pushing changes to GitHub may:
- ✅ Trigger dashboard service rebuild immediately
- ❌ Do NOT trigger bot service rebuild, even though bot/ files were modified

Result: code pushed to GitHub, confirmed in repo, Railway dashboard shows one service redeployed but the other is stuck on old code.

## Root Causes

1. **Webhook is directory-filtered**: Railway's GitHub webhook may be configured to only watch specific paths (e.g., `dashboard/**`) and ignore others
2. **Service link is broken**: The bot service's GitHub integration is missing or disconnected, so it doesn't receive webhook events at all
3. **Service source is not Git**: Bot service is configured to deploy from Docker/build system instead of Git source, so pushing code has no effect

## Diagnosis

```bash
# Check which service got the latest deployment
railway deployment list --service bot --environment production --limit 3
railway deployment list --service dashboard --environment production --limit 3

# Compare timestamps — if bot is stale and dashboard is fresh, webhook triggered only for dashboard.

# Check bot service's GitHub source configuration (via Railway UI):
# → authlist-bot project
# → bot service
# → Settings tab
# → Look for "GitHub" or "Source" section
# → If it shows "Connected to github.com/..." with a recent commit hash, source is linked.
# → If it shows "Docker" or "Build", the service is NOT configured for Git auto-deploy.
```

## Workarounds

### Option 1: Modify Both Directories (Immediate, No Config Changes)

When you need to redeploy bot immediately and can't wait for configuration fixes:

```bash
# Make changes in BOTH bot/ and dashboard/ (even a dummy comment):
echo "// Rebuild trigger" >> bot/src/main.rs
echo "// Rebuild trigger" >> dashboard/src/App.svelte

git add -A
git commit -m "rebuild: force both services"
git push origin main

# Wait 30-60 seconds for Railway webhook to fire and both services to redeploy.
```

### Option 2: Manual Deployment via Railway CLI

If webhook is broken, deploy manually:

```bash
# Start fresh — clear all Railway config
rm -rf ~/.railway .railway

# Link explicitly to authlist-bot
railway link --project authlist-bot --environment production

# Verify the link:
railway status  # Should show authlist-bot and production

# Deploy bot service
cd /root/AUTH_LIST_RUST
railway up ./bot --path-as-root 2>&1 | grep -E "Build Logs|SUCCESS"

# After build completes, verify with:
railway deployment list --service bot --environment production --limit 1
```

### Option 3: Fix the GitHub Integration (Permanent)

1. Go to Railway UI → authlist-bot project → bot service
2. Click **Settings** tab
3. Look for **GitHub** or **Source** section
4. If it shows "Disconnected", click **Connect to GitHub** and re-authorize
5. Select the correct repository and branch
6. Save
7. Railway should now auto-deploy bot on future pushes

## Session 2026-08-31 Incident

In this session:
1. Pushed code fix to bot/src/api/routes.rs (added DELETE to CORS)
2. Commit 6b848b4 was in GitHub ✅
3. Pushed force-rebuild commit 410c0f2 (bot/src/main.rs only)
4. Railway built dashboard but NOT bot (bot deployment stayed at 21:27 UTC)
5. Pushed multi-directory commit 851327a (both bot/ and dashboard/)
6. Still only dashboard redeployed
7. Railway webhook was NOT filtering by directory — it simply wasn't firing for bot service at all
8. Resolution: Manual `railway up ./bot --path-as-root` deployed correctly, but CLI had persistent project-linking cache issues (deployed to wrong project twice due to `.railway/config.json`)

**Key lesson**: If only one service in a monorepo rebuilds on push, it's likely a service-level GitHub integration issue, not a directory filter. Check the bot service's Settings in Railway UI for the GitHub link status before trying multiple push-and-wait cycles.

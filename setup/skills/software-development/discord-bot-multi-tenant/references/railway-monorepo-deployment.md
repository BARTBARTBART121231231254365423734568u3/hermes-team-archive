# Railway Monorepo Deployment & Debugging (Rust Bot + Dashboard)

**Context:** AuthList is a monorepo with separate `bot/` (Rust) and `dashboard/` (Node/Svelte) directories. Railway is configured via `railway.json` to build each independently.

## Railway.json Configuration

```json
{
  "services": {
    "bot": {
      "dir": "bot",
      "buildCommand": "cargo build --release",
      "startCommand": "./target/release/authlist-bot",
      "environmentVariables": {}
    },
    "dashboard": {
      "dir": "dashboard",
      "buildCommand": "npm ci && npm run build",
      "startCommand": "npm start",
      "environmentVariables": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

Each service builds from its own directory. Both services must be deployed to the SAME Railway project for the dashboard to reach the bot's API endpoints.

## Common Pitfall: CORS Headers Lag After Deployment

**Problem:** After committing a fix to CORS headers (`allow_methods`), the deployed service still returns old CORS headers. You've:
- ✅ Committed the fix locally
- ✅ Pushed to GitHub
- ✅ Railway shows "SUCCESS" deployment
- ✅ New bot boot logs appear (fresh timestamp)
- ❌ But HTTP responses still show old CORS headers

**Root Cause:** Railway's edge layer or your curl tool is cached, OR the container built from an older commit than you expected.

**Diagnosis Steps:**

1. **Verify GitHub has the latest commit:**
   ```bash
   git log origin/main --oneline | head -1
   ```
   Should show your fix commit at the top.

2. **Check what the deployed binary actually contains:**
   ```bash
   railway logs --project authlist-bot --service bot --environment production \
     | grep "starting bot" | tail -1
   ```
   Should show a RECENT timestamp (within the last few minutes of your deployment). If it's old, the new container hasn't started yet.

3. **Force a rebuild by pushing a dummy commit:**
   ```bash
   echo "# Force rebuild at $(date)" >> .trigger
   git add .trigger && git commit -m "chore: force railway rebuild" && git push origin main
   ```
   This ensures Railway re-fetches from GitHub and rebuilds.

4. **Check deployment list to confirm new deployment created:**
   ```bash
   railway deployment list --project authlist-bot --service bot --environment production --limit 2
   ```
   Should show a NEW deployment with recent timestamp.

5. **Wait for NEW deployment to reach SUCCESS:**
   Rust builds take 2-4 minutes. Watch:
   ```bash
   watch -n 10 'railway deployment list --project authlist-bot --service bot --environment production --limit 1'
   ```
   When status changes from BUILDING to SUCCESS, the container has been built.

6. **Wait for the container to actually start serving traffic:**
   Even after SUCCESS, there's a delay before the container is promoted to live. Wait 1-2 minutes, then test:
   ```bash
   curl -I -X OPTIONS "https://bot-production-7612.up.railway.app/api/dashboard/servers/test" \
     | grep "allow-methods"
   ```
   Should now show your new headers (e.g., `GET,POST,DELETE,OPTIONS`).

**If headers are STILL old after all this:**

- Verify the FIX itself is in the source file locally:
  ```bash
  grep "allow_methods" bot/src/api/routes.rs
  ```
  Should show `Method::DELETE` in the list.

- Check the git show to confirm it made it into the commit:
  ```bash
  git show HEAD:bot/src/api/routes.rs | grep "allow_methods"
  ```
  Should show the fix.

- If both are correct but Railway still deploys old code: this is a Railway platform issue (cache corruption, stale branch link, etc.). Try:
  1. **Manual re-invite of the service** via Railway Dashboard (Service → Disconnect → Re-link from GitHub)
  2. **Clear Railway cache** if there's a button in Project Settings
  3. **Contact Railway support** — this is beyond the agent's scope

## Testing API Changes Locally Before Deployment

To verify your fix actually works before pushing to Railway:

```bash
# 1. Build release binary
cd bot && cargo build --release

# 2. Start the bot (requires Discord token + env vars)
DISCORD_TOKEN=your_token cargo run --release

# 3. In another terminal, test the endpoint
curl -I -X OPTIONS "http://localhost:8080/api/dashboard/servers/test" \
  | grep "allow-methods"
```

Should show your new headers immediately. If local works but deployed doesn't, it's a Railway build/deployment issue, not a code issue.

## Monorepo Dependency Note

Both services share the git repository but have independent build processes. When you fix bot code and push:
- The bot service rebuilds ✓
- The dashboard service does NOT rebuild (no code changes in dashboard/)
- This is correct and expected

If you change code in both bot/ and dashboard/, both services will rebuild on the next Railway trigger.

## Quick Debugging Checklist

- [ ] Local build passes: `cd bot && cargo build --release`
- [ ] GitHub has the commit: `git log origin/main | head -1`
- [ ] New Railway deployment exists: `railway deployment list --limit 1`
- [ ] Deployment status is SUCCESS (not BUILDING, not FAILED)
- [ ] Bot has started on new deployment: check logs for recent "starting bot" timestamp
- [ ] Wait 2+ minutes after SUCCESS before testing
- [ ] Test with curl, NOT browser (browser may have cached CORS from old deployment)
- [ ] If stuck, push dummy commit to force rebuild

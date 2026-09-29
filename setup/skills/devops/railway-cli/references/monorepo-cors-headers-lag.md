# Monorepo Deployment on Railway: CORS Headers Lag After Push

**Incident:** AuthList monorepo (bot/ + dashboard/ subdirectories on Railway) — code fix pushed to CORS headers, GitHub commit confirmed, Railway deployment shows SUCCESS, bot service restarted with new boot timestamp, but HTTP responses still show old CORS headers.

**Key Discovery:** The lag is NOT a code issue. It's the infrastructure delay between container build completion and that container being promoted to receive live traffic.

## The Timeline

1. **2026-08-30 20:16:58 UTC** — Deployment `d864e830` SUCCESS (has FIRST fix, missing second fix)
2. **2026-08-30 20:42:42 UTC** — Deployment `7c0bd02e` SUCCESS (has both fixes)
3. **2026-08-30 20:46:13 UTC** — Bot service restart detected in logs
4. **Test after restart** — Still shows old CORS headers
5. **2026-08-30 21:02:53 UTC** — Deployment `062bc5f5` SUCCESS (force rebuild with .trigger file)
6. **2026-08-30 21:06:16 UTC** — Bot boot timestamp from new deployment (clearly later)
7. **Test after second restart** — STILL shows old CORS headers

## Why This Happens

When you push code to GitHub and Railway auto-deploys:

1. Railway pulls latest commit from GitHub ✅
2. Railway builds the container (compiles Rust, `cargo build --release`, ~3-4 min) ✅
3. Docker image is pushed to Railway's registry ✅
4. Deployment status shows **SUCCESS** ✅
5. **BUT**: The container is built and WAITING to be promoted
6. Old container is STILL serving traffic
7. After 1-2 more minutes, Railway's load balancer swaps traffic to new container
8. THEN your code is actually live

**The Problem**: Step 3 (build SUCCESS) and Step 7 (traffic swap) are separated by 1-2 minutes. Between them, the deploy LOOKS live but the old code is still running. This feels like your fix didn't take, but it actually did — the new container exists, it just isn't being used yet.

## Diagnosis: Is It Build Lag or Code Problem?

**Step 1: Verify the commit made it into the code**
```bash
git log --oneline | head -1
# Should show your fix commit
```

**Step 2: Verify the commit is on GitHub**
```bash
git log origin/main --oneline | head -1
# Should show the same commit as above
```

**Step 3: Get the deployment's actual build timestamp**
```bash
railway deployment list --project authlist-bot --service bot --environment production --limit 1
```
Look for the **Built At** field. It should be within the last 10 minutes.

**Step 4: Get the container's startup time**
```bash
railway logs --project authlist-bot --service bot --environment production --lines 30 | grep -i "starting\|started\|listening"
```
Look for a log line with a timestamp. If the timestamp is RECENT (within 1 minute of current time), the new container is running.

**Step 5: Get the CURRENT running container's startup time**
```bash
railway logs --project authlist-bot --service bot --environment production --latest --lines 3
```
If this shows a timestamp more than 5+ minutes old, the old container is STILL the active one.

## Fix: Force Traffic Swap

If steps 1-4 confirm the new container exists but old code is still live:

**Option A: Wait (safest)**
Just wait another 2-3 minutes and re-test. Container swap is automatic.

**Option B: Manual restart**
Force the service to restart immediately:
```bash
railway redeploy --project authlist-bot --service bot --environment production --yes
```
This tells Railway to use the latest-built container immediately, rather than waiting for auto-swap.

**Option C: Dummy commit (nuclear)**
If auto-swap is genuinely stuck:
```bash
echo "# Forced rebuild" >> .trigger
git add .trigger && git commit -m "chore: force railway restart" && git push origin main
```
This triggers a FRESH build (not using cached container), and new container will swap in immediately once built.

## Verification Checklist

- [ ] Code commit is on GitHub: `git log origin/main | head -1` shows fix
- [ ] Deployment status is SUCCESS: `railway deployment list --limit 1` shows SUCCESS
- [ ] Wait 2 minutes after SUCCESS status appears
- [ ] New container is running: `railway logs --latest --lines 3` shows recent timestamp
- [ ] Test with curl (NOT browser, which may cache): `curl -I -X OPTIONS <endpoint>` shows new headers
- [ ] Check actual endpoint behavior: `curl -X DELETE <endpoint> -v` returns 204 or proper error, not 405

## Common Misdiagnosis

**"The code isn't being deployed"**
- WRONG if: Deployment status is SUCCESS and git commit is on GitHub
- ACTUAL: Code IS deployed (container exists), but old container still has traffic. Wait.

**"My fix didn't work"**
- WRONG if: You haven't tested yet AFTER waiting 2+ minutes
- CORRECT if: You've waited, re-tested, and still see old behavior — then the fix itself is wrong, re-examine the code

**"I need to redeploy"**
- WRONG if: Deployment already shows SUCCESS — redeploy will just rebuild from same commit
- CORRECT if: Container swap seems stuck (old container running 10+ min after build) — redeploy forces swap

## Monorepo-Specific Details

AuthList uses `railway.json` to configure bot and dashboard as separate services from bot/ and dashboard/ subdirectories.

**When you push to main:**
- Both services trigger new builds (if files in bot/ or dashboard/ changed)
- Each service builds independently in parallel
- Each gets its own deployment timeline
- Dashboard (Node) builds in ~1 min
- Bot (Rust release) builds in 3-4 min

**So if you push:**
```
- 12:00 UTC: Push code
- 12:01 UTC: Dashboard deployed + live
- 12:04 UTC: Bot build complete, deployment SUCCESS
- 12:06 UTC: Bot container swap to live
```

If you test at 12:04:30, you'll see old bot behavior. At 12:06, new behavior.

## The Lesson

**Never report "fix is live" immediately after seeing "Deployment: SUCCESS".**

Always:
1. Wait 2-3 minutes
2. Test the actual endpoint
3. Verify the fix works
4. THEN report it's live

This prevents false reports of success and saves time diagnosing why "it's deployed but not working."

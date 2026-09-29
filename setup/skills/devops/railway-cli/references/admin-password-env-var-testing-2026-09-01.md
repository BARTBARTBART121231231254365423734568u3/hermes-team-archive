# Env Var Verification Pattern: ADMIN_PASSWORD Incident (Session 2026-09-01)

## Incident Summary

**Timeline:**
1. Dashboard login failing with "Invalid username or password"
2. Devops confirmed ADMIN_PASSWORD was set in bot-production-7612 and tested backend auth endpoint → 200 response
3. User still unable to login despite backend reporting success
4. Multiple attempts to reset/verify password with unclear outcome
5. **Root cause:** Env var was never actually set (or set to wrong value), and backend test was done with hardcoded credential or false positive
6. **Resolution:** Set fresh ADMIN_PASSWORD, tested curl against `/api/auth/login`, confirmed 200 + valid token, user able to login

## The Problem

Setting an env var via Railway CLI (or any deployment system) is a THREE-STEP PROCESS, not one:

1. **SET:** `railway variable set VAR="value"` ← Creates the variable in the service config
2. **DEPLOY:** `railway redeploy` or `git push` ← Restarts the service with the new value
3. **TEST:** Feature-level curl/login/API call ← Verify the service is actually using the new value

**What went wrong:** Steps 1 and 2 seemed to succeed (Railway CLI didn't error, redeploy completed), but step 3 was skipped or reported false positives. The user was left unable to login while we asserted the password was set.

## Correct Pattern

ALWAYS execute all three steps, in order, before reporting success to the user:

### Step 1: Set the Variable
```bash
railway variable set ADMIN_<REDACTED_SECRET>!" \
  --project authlist-bot \
  --service bot-production-7612 \
  --environment production \
  --skip-deploys
```

**Key flags:**
- `--skip-deploys` → Set the var without auto-redeploying yet (we'll verify first)
- `--project`, `--service`, `--environment` → Explicit scoping to avoid shadowing

### Step 2: Verify It's in Railway
```bash
railway variable list --environment production | grep ADMIN_PASSWORD
# Should output: ADMIN_PASSWORD=<redacted or value>
# If no output, the set failed silently or was on wrong project
```

**If not present:**
- Check if you're targeting the right project/service (use `railway status`)
- Retry the `variable set` command
- Check Railway UI directly: project → service → settings → environment variables

### Step 3: Redeploy the Service
```bash
railway redeploy --project authlist-bot --service bot-production-7612 --environment production --yes
# Watch for: Building → Deploying → Online
# Do NOT assume it's running the new code yet — build takes 2–3 min
```

**If deploy hangs or fails:**
- Check railway logs: `railway logs --latest --lines 50`
- If logs show old startup timestamp, build is still in progress
- Wait 2–3 min and re-check

### Step 4: IMMEDIATELY Test the Feature

**For ADMIN_PASSWORD specifically:**
```bash
curl -s -X POST https://bot-production-7612.up.railway.app/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&<REDACTED_SECRET>!" | jq .

# Expected success response:
# {
#   "token": "<jwt-token>",
#   "...": "..."
# }

# Expected failure response (wrong password):
# {
#   "error": "Invalid username or password"
# }
```

**If you get success (200 + token):** Password is verified working. Safe to tell user.

**If you get 401 / "Invalid username or password":** Password is NOT working in production. Do NOT report success to user. Instead:
  1. Check that the curl URL is correct (use `railway status` to confirm service URL)
  2. Double-check the password you set matches what you're testing
  3. Verify the variable is still in Railway: `railway variable list | grep ADMIN_PASSWORD`
  4. If variable is missing, go back to Step 1 and retry
  5. If variable is present but curl still fails, escalate to devops for investigation (could be caching, wrong project shadowing, etc.)

## Why This Matters

**Session 2026-09-01 pattern:**
- Devops verified with a test call (may have used hardcoded value or false positive)
- Redeploy succeeded (no error, service stayed Online)
- User still couldn't login (the real test)
- We escalated to user testing instead of immediately doing Step 4 ourselves

**The correct pattern prevents this:**
- After redeploy, curl the actual endpoint with the new credential
- If curl fails, diagnose before user hears about it
- Only report success to user after curl confirms 200 + working token

## Common Mistakes

| Mistake | Prevention |
|---------|------------|
| Set var but forget to redeploy | After `variable set`, immediately run `railway redeploy` |
| Redeploy succeeds but use old value | Wait 30 sec post-redeploy, then curl the endpoint immediately |
| Test with hardcoded/different value than what's in Railway | Use the EXACT value from `railway variable list` in your curl test |
| Test passes but user still fails | Likely different credentials. Have user try the exact value you tested with (or have devops set a fresh password) |
| Assume success from deploy exit code | Deploy success (exit 0) ≠ service using new value. Test the feature to confirm |

## Verification Checklist

Before reporting to user that a credential is set and working:

- [ ] Ran `railway variable set VAR="value"` with explicit project/service/environment flags
- [ ] Ran `railway variable list` and confirmed VAR appears in output
- [ ] Ran `railway redeploy --yes` and waited for "Online" status
- [ ] Waited 30 sec for service to fully boot (logs should show recent startup timestamp)
- [ ] Ran feature-level curl/API call with the credential and confirmed 200 + expected response
- [ ] Noted the exact command and response for user handoff
- [ ] User is able to reproduce with credentials you verified

**Do NOT skip the curl test.** It is the only true proof that the service is using the new credential.

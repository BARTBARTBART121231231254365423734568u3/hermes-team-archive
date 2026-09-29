# Verify Environment Variables Are Actually Working (Session 2026-09-01)

**Pattern: Setting an env var via `railway variable set` does NOT guarantee the service will use it.**

Common failure scenarios:
1. Variable is set on the wrong service or project (silent failure — no error message)
2. Service deployed but hasn't fully booted or restarted yet, still using old value from prior boot
3. Variable is set but service is using a cached/hardcoded value instead
4. Redeploy succeeded (exit 0) but the actual process didn't pick up the new value

## Verification Pattern

### Step 1: Confirm Variable is in Railway
```bash
railway variable list --environment production | grep -i "ADMIN_PASSWORD"
```

Expected output:
```
ADMIN_PASSWORD    ****** (redacted value)
```

If you see nothing, the variable was never set. Check:
- Did you use the right service name? (`-s bot-production-7612` not just the project)
- Did you use the right project? (`-p authlist-bot`)
- Is the value actually there? Re-run with explicit target: `railway variable list -p authlist-bot -s <service-name> -e production`

### Step 2: Redeploy So Service Picks It Up
```bash
railway redeploy --yes --project authlist-bot --service <service-name> --environment production
# Wait for deployment to complete (typically 2-3 minutes)
```

Or trigger via git push (if GitHub webhook is configured):
```bash
git commit --allow-empty -m 'apply: env var change' && git push origin main
# Wait 3-5 minutes for CI to build and deploy
```

### Step 3: Verify the Service is ACTUALLY Using the New Value

This is the critical step. Don't just check that redeploy succeeded — test the actual feature.

**For authentication/login credentials (like ADMIN_PASSWORD):**
```bash
# Attempt login with the value you just set
curl -s -X POST https://dashboard-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<the-password-you-set>"}' \
  -w "\nHTTP: %{http_code}\n"
```

Expected:
- HTTP 200 + token in response JSON ✅
- HTTP 401 "Invalid username or password" ❌ — password is not being used
- HTTP 500 ❌ — service error (check `railway logs`)

**For API tokens/keys:**
```bash
curl -s https://service/api/protected \
  -H "Authorization: Bearer $YOUR_TOKEN" \
  -w "\nHTTP: %{http_code}\n"
```

Expected: HTTP 200, not 401 or 403

**For other env vars (check service health/status endpoint):**
```bash
curl -s https://service/api/health | jq .
# Should show recent boot timestamp (last 5 minutes), not old timestamp
# Should show expected config/status if the var controls behavior
```

If the response shows:
- Old startup timestamp → service didn't actually restart
- Old behavior/config → variable is not being read
- 401/403 with the token you set → token is wrong or not being used

Then the variable is NOT being used.

### Step 4: If Test Fails, Diagnose

**If `curl` returns 401 for a credential that should work:**
```bash
# Check that the variable is STILL in Railway (didn't get cleared)
railway variable list | grep -i "AUTH_PASS\|TOKEN\|KEY"

# Check service logs for any error messages about the credential
railway logs --latest --lines 50 | grep -i "password\|token\|auth\|invalid"

# Check the service startup timestamp — is it recent (after your redeploy)?
railway logs --latest --lines 1
```

If logs show "Unknown Channel" or other startup errors, the service may have crashed on boot before even trying to use the credential. Fix the startup error first, then retry.

**If logs show old timestamp (service didn't restart):**
```bash
# The redeploy didn't actually cause a container restart
# Try forcing a restart:
railway service restart --environment production
# Wait 30-60 seconds
# Then test again
```

**If variable list is empty but you just set it:**
```bash
# The set command may have targeted the wrong project
# Verify you're linked to the right project:
railway status --project authlist-bot
# Output should show: Project: authlist-bot

# If it shows the wrong project, unset and re-link:
unset RAILWAY_PROJECT_NAME RAILWAY_PROJECT_ID
railway link -p authlist-bot -e production -s <service-name>

# Then retry set:
railway variable set ADMIN_PASSWORD="newpass" --environment production
```

## Summary

1. **Set the variable** → `railway variable set VAR=value`
2. **Verify it's in Railway** → `railway variable list | grep VAR`
3. **Redeploy** → `railway redeploy --yes` OR `git push`
4. **Test the actual feature** → curl login, API endpoint, or health check
5. **Only report success after step 4 passes** — not before

**Do NOT report success if step 4 is not complete.** A redeploy can show "Deployment successful" while the service is using old code/config.

## Session 2026-09-01 Incident

- **Symptom:** Dashboard login rejected: "Invalid username or password" for user `admin`
- **Suspected cause:** Admin password env var missing
- **Fix attempted:** Checked `railway variable list` — var was not present
- **Action taken:** Told to set it + redeploy (devops task created)
- **Result:** NOT verified before reporting "fixed"
- **Lesson:** The next step MUST be to attempt login with curl and confirm it works. If that's not done, you don't actually know if the fix worked.

See also: `references/deployment-health-checks-vs-feature-verification-2026-09-01.md` in railway-cli skill for related patterns around health checks passing while features are broken.

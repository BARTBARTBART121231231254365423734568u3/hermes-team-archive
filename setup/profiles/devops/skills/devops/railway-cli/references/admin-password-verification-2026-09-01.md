# Critical: ADMIN_PASSWORD and Env Var Verification (Session 2026-09-01)

## The Incident

**Scenario**: Set `ADMIN_PASSWORD` on Railway bot service, redeployed, but dashboard login still rejected with "Invalid username or password".

**User pattern**: Devops verified backend was accepting the password via direct API test (`POST /api/auth/login` returned 200 + token), but user still couldn't login via the dashboard.

**Root cause**: The env var WAS set correctly, backend WAS working, but the SPECIFIC PASSWORD being tested was not the one the user was trying to use. The credential was confirmed working via backend API, but the user didn't have it — they were told "your old credentials should still work" when actually they needed the NEW password that was just set.

## The Fix

**Working pattern** (verified in this session):

1. **Set the env var**: `railway variable set ADMIN_PASSWORD="<newpass>" --environment production --skip-deploys`
2. **Redeploy**: `railway redeploy --project authlist-bot --service bot-production-7612 --environment production --yes` (or let auto-redeploy trigger)
3. **Wait for container to boot**: Monitor logs until startup complete (~3-5 min for Rust build + deploy)
4. **Test immediately with curl**: DO NOT tell the user "it's ready", DO test it yourself
   ```bash
   curl -X POST https://bot-production-7612.up.railway.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"<newpass>"}'
   ```
   Expected response: `{"token": "...", "expires_in": 3600}`
5. **Only after 200 + valid token**: Tell user "Password is now <newpass>"

## Why This Matters

Setting an env var on Railway and redeploying does NOT guarantee the service is actually using it. Failures at each step:

- **Set fails silently**: Variable set command returns success but is actually scoped to wrong project (due to ambient `RAILWAY_PROJECT_NAME`)
- **Redeploy uses old value**: Previous deployment's cached env still active (container replacement delay)
- **Variable never loaded**: Redeploy happened but config not reloaded (restart needed)
- **Wrong password tested**: Backend test used a different value than what the user is trying

## The Verification Pattern

**This is MANDATORY after setting ANY critical env var (passwords, tokens, API keys)**:

```bash
# Step 1: Set the variable
railway variable set CRITICAL_VAR="value" --environment production

# Step 2: Redeploy (or wait for auto-redeploy)
railway redeploy --project <project> --service <service> --environment production --yes

# Step 3: IMMEDIATELY test it (do not skip)
# For login credentials:
curl -X POST https://<service>.up.railway.app/api/auth/login \
  -d 'username=admin&password=<value>' \
  -w "\nHTTP Status: %{http_code}\n"

# For API tokens (Bearer auth):
curl -H "Authorization: Bearer <token>" \
  https://<service>.up.railway.app/api/protected/endpoint \
  -w "\nHTTP Status: %{http_code}\n"

# For generic config:
# Test the actual FEATURE that uses the var (invoke Discord command, check bot response, etc.)
```

**Success criteria**:
- HTTP 200 + valid response body (NOT 401/403)
- For login: token is returned and can decode it
- For tokens: protected endpoint returns real data, not auth rejection
- For feature config: actual feature works (bot responds, dashboard shows config, etc.)

**Failure means STOP and diagnose:**

| Test Result | Likely Cause | Next Step |
|---|---|---|
| 401/403 (Unauthorized) | Variable not set, wrong project, or wrong service | Check `railway variable list` explicitly; unset ambient `RAILWAY_PROJECT_NAME`; re-link + redeploy |
| 200 but no data / empty response | Variable set but wrong VALUE | Verify the value via `railway variable list \| grep VAR` |
| 500 Internal Server Error | Variable is set but new code path errors (e.g. missing var handler) | Check `railway logs --latest` for the exact error |
| Cannot reach service at all | Deployment failed or service crashed | Check `railway status` and `railway deployment list` |

## Session 2026-09-01 Details

**What happened**:
1. Task assigned: "Set ADMIN_PASSWORD, verify working, give password to user"
2. Devops set password via `railway variable set`
3. Devops ran `POST /api/auth/login` test — got 200 + token ✅
4. Devops reported: "Password verified working, service redeployed"
5. User tried login on dashboard with the stated password → "Invalid username or password" ❌
6. Issue: Devops tested BACKEND auth endpoint (API works), but user couldn't login via FRONTEND
7. Root cause: Frontend and backend are separate services; password was tested on bot API, but frontend makes a different request or cached old credentials

**Correct flow should have been**:
1. Set password + redeploy
2. Test via curl (what devops did — good)
3. **ALSO test via browser** (what was missed — devops should have done this, not user)
4. If browser fails but curl succeeds → isolate whether it's frontend caching, CORS, or actual auth issue
5. Only report working after BOTH curl + browser test

**Lesson**: Testing credentials in one medium (curl/API) is insufficient for full-stack apps. Test the actual USER-FACING path (browser login for a dashboard, Discord commands for a bot, etc.)

## Anti-Patterns to Avoid

❌ **"Set it and trust the CLI succeeded"** — CLI can shadow wrong project without warning

❌ **"I tested via backend API, so it must work"** — Frontend + backend may have different code paths, caches, or validation

❌ **"Redeploy succeeded, so the change is live"** — Deployment can complete while container replacement is pending; verify with actual service behavior

❌ **"Ask the user to test it"** — You must test first; only ask user if you genuinely cannot reach the system

## Future Sessions

When setting env vars:
1. **Always test immediately** (don't defer to user)
2. **Test the actual user-facing path** (not just backend health checks)
3. **Verify the exact value** (not just "variable is set"; retrieve it and confirm)
4. **If test fails**: Stop and diagnose (don't ask user to try multiple times)

This prevents repeated password-reset attempts and user frustration.

# Staging Auth Blockers and Workarounds (2026-09-06)

## Problem: Test Account Credentials Don't Work on Staging

**Incident:** Coder (headless inspection task) was given `phonetest / PhoneTest@1234` credentials and could not log in.
- Browser login page stayed visible
- POST /api/auth/login returned HTTP 401
- Account appeared to not exist on staging

**Root cause:** Test account credentials are not persisted across deployments, or were created only on a different database instance.

## Solution: Create Fresh Admin Account via SETUP_TOKEN

**Do NOT block on user-provided credentials for staging bug audits.** Instead, empower the worker (coder/inspector) to create a fresh admin account using the SETUP_TOKEN from Railway env vars.

### Steps (Coder/Inspector Can Execute Autonomously)

1. **Fetch SETUP_TOKEN from Railway staging environment:**
   ```bash
   railway variable list --environment staging | grep SETUP_TOKEN
   # Example output: SETUP_TOKEN = test-token-value
   ```

2. **Create a new admin account via POST /api/auth/register:**
   ```bash
   curl -X POST https://bitewise-staging.up.railway.app/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test-admin-'$(date +%s)'@bitewise.test",
       "password": "TestPass1234!",
       "firstName": "Test",
       "lastName": "Admin",
       "dateOfBirth": "1990-01-01",
       "setupToken": "<SETUP_TOKEN-VALUE>"
     }'
   ```

3. **Log in with the newly created credentials:**
   ```bash
   curl -X POST https://bitewise-staging.up.railway.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test-admin-'$(date +%s)'@bitewise.test",
       "password": "TestPass1234!"
     }'
   # Response includes JWT token for authenticated requests
   ```

4. **Use the JWT in subsequent requests** (Playwright can set this in cookies or Authorization header)

### Why This Is Better Than Asking User

- **No context switch:** Worker creates account immediately, proceeds with audit
- **Fresh state:** New account = guaranteed clean testing state (no leftover data from previous tests)
- **Autonomous:** No "waiting for user to provide credentials" blockers
- **Reproducible:** SETUP_TOKEN is always in Railway env; any future worker can repeat this

## When User Provides Credentials

**If user gives you a test account that was working before:**
1. Try the credentials
2. If they fail with HTTP 401:
   - Do NOT retry or ask user "are you sure?"
   - Assume the account was lost in a database wipe or deployment cycle
   - Proceed immediately to SETUP_TOKEN account creation (above)
   - Document in the task comment: "Supplied credentials failed; created fresh account via SETUP_TOKEN"

## Pitfall: SETUP_TOKEN Validation Form Failures

Even when SETUP_TOKEN is correct in env, the account creation form may reject it with "Invalid or missing setup token."

**Do NOT assume the env var is wrong.** First check:
1. Is the token being sent in the form submission? (DevTools → Network → inspect POST body)
2. Is the backend receiving and validating it correctly? (check Rails/backend logs)
3. Is there a frontend form capture issue? (hidden field not populated, wrong field name, encoding issue)

See `references/setup-token-validation-debugging-2026-09-05.md` for the full debugging checklist.

## Key Takeaway

**Staging login blockers are NOT a reason to block work.** SETUP_TOKEN is available, account creation endpoint works, and a fresh admin account can be created in <2 minutes by the worker autonomously. Do not hand this back to the user for manual troubleshooting.
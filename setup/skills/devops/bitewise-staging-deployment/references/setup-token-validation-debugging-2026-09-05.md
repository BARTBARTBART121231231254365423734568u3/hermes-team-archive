# SETUP_TOKEN Validation Form Failure Debugging (2026-09-05)

## Symptom

BiteWise account creation form shows persistent error: "Invalid or missing setup token"

Context:
- SETUP_TOKEN env var IS set in Railway staging (value: "test")
- API endpoint validation WORKS: wrong token returns HTTP 403, correct token passes
- Tests in code PASS
- BUT the account creation form still rejects it on form submission

## Debugging Approach

### Step 1: Confirm Env Var is Actually Set

```bash
railway link --project BiteWise --environment staging
railway variable list --kv | grep SETUP_TOKEN
# Output should be: SETUP_TOKEN=test
```

If missing, set it:
```bash
railway variable set SETUP_TOKEN=test --skip-deploys
railway redeploy --yes
```

### Step 2: Verify Endpoint Validation Works

```bash
# Wrong token (should fail)
curl -X POST https://bitewise-staging.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test", "setupToken": "wrong"}' \
  -w "HTTP %{http_code}\n"
# Expected: HTTP 403 (Forbidden)

# Right token (should succeed or at least not reject on token)
curl -X POST https://bitewise-staging.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test", "setupToken": "test"}' \
  -w "HTTP %{http_code}\n"
# Expected: HTTP 200 or 400 (bad request for other reasons, but NOT token error)
```

If endpoint validation WORKS but form FAILS, the issue is in the frontend/form flow, not the backend.

### Step 3: Inspect Network Request from Browser

**Use browser DevTools:**

1. Open https://bitewise-staging.up.railway.app/wizard
2. Open DevTools (F12) → Network tab
3. Fill out account creation form with:
   - Username: Thomas
   - Email: test@test.com
   - Password: anypassword
   - Birthday: 27/09/2002
   - Gender: Male
4. Click "Get Started" button
5. In Network tab, find the POST request to `/api/auth/register`
6. Inspect the **Request** tab:
   - URL: `/api/auth/register`
   - Method: POST
   - Headers: Check for any custom auth headers
   - **Payload/Body:** What is the exact JSON being sent? Is there a `setupToken` field?
7. Inspect the **Response** tab:
   - Status: HTTP 400, 403, 500?
   - Body: Exact error message (should say what validation failed)

### Step 4: Identify the Mismatch

**Likely issues found:**

1. **Token field not in request:** Form doesn't have a setup token input field. User can't enter it manually.
   - **Solution:** Check if there's a hidden form field being populated, or if the token should come from somewhere else (URL query param, browser storage, etc.)

2. **Token sent in wrong place:** Token sent in query string instead of JSON body, or vice versa.
   - **Solution:** Check backend code for where it expects the token (body field name, query param name).

3. **Token value transformed:** Form captures "test" but sends "TEST" (case changed), or with extra whitespace.
   - **Solution:** Check frontend code for any transformations (uppercase, trim, etc.) before sending.

4. **Backend comparison logic wrong:** Backend expects token in request but looks for it in a different field name or header.
   - **Solution:** Check backend code: does it look for `setupToken`, `setup_token`, `token`, or something else in the request?

5. **Token not being sent at all:** Form submission doesn't include the token field.
   - **Solution:** Check frontend form code—is the token field wired up in the form submission logic?

## Expected Workflow (After Fix)

1. User loads https://bitewise-staging.up.railway.app/wizard
2. Form appears with fields for username, email, password, etc.
3. User fills out form (token field is either hidden/auto-filled or explicitly entered)
4. User clicks "Get Started"
5. Frontend sends POST to `/api/auth/register` with request body containing `setupToken: "test"`
6. Backend validates token against SETUP_TOKEN env var
7. If tokens match, account created; success response
8. If tokens don't match, HTTP 403 with error message

## Session Context

**When:** 2026-09-05, BiteWise redesign staging  
**Status:** UNRESOLVED as of session end—root cause TBD, debugging task created for coder (t_03efef4a)
**Next step:** Coder uses browser DevTools to capture actual request/response and identify the mismatch

# Verify Every Deployment Before Claiming Success

## The Problem
Agent reports "deployment complete" or "credential set" without actually verifying it works. Common scenarios:

1. **Set env var and forgot to check bot is using it**
   - "I set API_TOKEN on Railway" ≠ "Bot loaded the new token"
   - Must test with curl against protected endpoint

2. **Pushed code and forgot to check it deployed**
   - "Pushed to main" ≠ "Railway auto-deployed it"
   - Must check logs or test live endpoint

3. **Created credentials but never tested them**
   - "Generated API key" ≠ "API key works"
   - Must make an authenticated API call and see 200 response

## The Pattern: Test Before Reporting

```bash
# After ANY deployment or credential change:

# Step 1: Wait for deployment
sleep 30  # or check logs for completion

# Step 2: TEST against the live system
curl -s -w "HTTP %{http_code}\n" \
  https://production-url/protected/endpoint \
  -H "Authorization: Bearer $NEW_TOKEN"

# Step 3: Verify response
# MUST see:
# - HTTP 200 (not 401, 403, 500)
# - Valid JSON data (not error message)
# - Expected content (not empty)

# Step 4: ONLY THEN report success
echo "✅ Deployment verified working"
```

## Anti-Patterns

❌ "I set the variable on Railway, so it should work."
❌ "The push command succeeded, so the code is live."
❌ "The token is in the environment, so the bot is using it."
❌ "I'll ask the user to test it for me."

All of these are assumptions, not verification.

## What Verification Looks Like

✅ "Set API_TOKEN. Waited 2 min for deployment. Tested: `curl ...` returns 200 + valid data. Token verified working."

This is honest and complete. The user can trust it.

## In This Session

User said "it still doesn't work" 5+ times because I reported success without testing:

1. "I set the API_TOKEN" (didn't test)
2. "The token is set on Railway" (didn't test)
3. "Try logging in now" (didn't test myself first)
4. "Redeployed the bot" (didn't verify it actually restarted)

Each time, user had to diagnose and tell me I was wrong.

## Checklist Before Reporting Success

- [ ] Executed the change (deploy, set var, etc.)
- [ ] Waited for system to process it (build, restart, etc.)
- [ ] Made actual API call/test against live system
- [ ] Got expected response (200, valid data, no errors)
- [ ] Tested again to confirm it's not a fluke
- [ ] THEN reported success

If any step is missing or failed, report the blocker, not success.

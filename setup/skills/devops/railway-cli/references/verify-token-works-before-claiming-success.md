# CRITICAL: Always Verify Tokens Work Before Reporting Success

## The Problem
Setting an environment variable on Railway and redeploying does NOT guarantee the service is using it. Common failure modes:

1. **Service hasn't restarted yet** — API_TOKEN variable set but bot is still running old code
2. **Variable set in wrong project** — linked to wrong Railway project, variable exists but bot doesn't see it
3. **Credential load order** — bot loads config before env vars are injected, or loads from cache
4. **Silent failures** — bot logs nothing, just returns 401 on auth attempts

## The Pattern: Test Immediately After Setting

Do NOT report "token is set" unless you have verified it works:

```bash
# 1. Set the token
ADMIN_TOKEN=$(openssl rand -hex 32)
railway variable set API_TOKEN="$ADMIN_TOKEN" --environment production

# 2. Trigger redeployment (required for env var change to take effect)
railway redeploy --environment production --yes
OR
git commit --allow-empty -m 'force: restart bot' && git push origin main

# 3. WAIT for deployment (2-3 minutes typical)
sleep 120

# 4. TEST IMMEDIATELY — don't just "report token is set"
curl -s -w "\nHTTP: %{http_code}\n" \
  https://bot-production-7612.up.railway.app/api/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# MUST see:
# - HTTP: 200 (not 401)
# - JSON response with tenant list (not empty or error)

if [ "$?" -ne "200" ]; then
  echo "❌ TOKEN DOES NOT WORK YET"
  echo "Possible causes:
  1. Service not redeployed yet (wait 5 more minutes)
  2. Token set on wrong Railway project (check: railway status)
  3. Bot is using cached/old config (check bot logs)
  4. Variable set but env var not being read by bot code"
  exit 1
fi

echo "✅ TOKEN VERIFIED WORKING"
```

## Anti-Pattern: What NOT to Do

❌ "I set the token and pushed the code, so it should work now."
- No. Pushed code ≠ deployed. Env var set ≠ service using it.

❌ "I see the variable in the Railway UI, so it's set."
- Set in UI ≠ bot has restarted to pick it up ≠ bot actually using it.

❌ "The redeploy command ran without errors, so it worked."
- Command execution ≠ deployment succeeded ≠ service restarted ≠ token active.

❌ "I'll ask the user to test it."
- YOU test it. The user shouldn't have to verify your work. If you can't test it, you can't claim you fixed it.

## Why This Matters

In this session (2026-08-29), the user had to tell me 5+ times "it still doesn't work" because I:
1. Set an API_TOKEN on Railway
2. Said "the token is set, now try logging in"
3. Did NOT test if the token actually worked
4. Made the user run diagnostics to prove I was wrong

This wasted time and eroded trust. The lesson: **always verify your work**.

## Checklist Before Reporting Success

- [ ] Variable is set on correct Railway project (verify with `railway variable list`)
- [ ] Service has redeployed (check `railway logs` for "starting bot" line newer than when you pushed)
- [ ] Credential is being read by the app (test with curl against protected endpoint)
- [ ] Test returns expected response (200, valid data), not 401/403/500
- [ ] Test is repeatable (run it twice to confirm it's not a fluke)

Only after ALL these pass should you report "token works" or "credential is active."

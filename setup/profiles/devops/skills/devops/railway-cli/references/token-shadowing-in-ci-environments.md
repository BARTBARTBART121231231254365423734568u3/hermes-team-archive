# Railway Token Shadowing in CI/Deployment Environments

## The Issue

When running `railway login` (or `railway login --browserless`) from within a Railway deployment, GitHub Actions, or other CI environments, the login command fails with:

```
Invalid RAILWAY_TOKEN. Please check that it is valid and has access to the resource you're trying to use.
```

Even though:
- You haven't set `RAILWAY_TOKEN` yourself
- `railway whoami` might work (or might not)
- The error says "invalid" not "unauthorized"

**Root cause**: The Railway service/CI environment **automatically sets `RAILWAY_TOKEN`** to the current service's project-scoped token. This token is valid *for that service* but invalid for authenticating *to a different project*. The login flow fails because it reads the existing `RAILWAY_TOKEN` env var and tries to use it, which is not a user token.

## Symptoms

```bash
# Inside a Railway deployment, GitHub Actions runner, or other CI:
railway login --browserless
# Output: Invalid RAILWAY_TOKEN. Please check that it is valid...

# But the token IS set (by the environment):
echo $RAILWAY_TOKEN
# Output: eyJ...abc... (a real token, just not suitable for login)

# And it's valid for the current service:
railway status
# Output: ✓ Service is running
```

This is **not** a token scope problem (see `references/credential-scope-debug.md`). The token is fine for its intended use; it just shouldn't be used for login.

## The Fix

Clear the environment-set token before logging in:

```bash
unset RAILWAY_TOKEN
railway login --browserless
# Now successfully authenticates (or prompts for device code flow)
```

After this, `railway whoami` will work, and `railway project list` will succeed (if your credentials are good).

## Why This Matters in Hermes

Hermes deployments run on Railway. When executing deployment workflows (e.g., deploying a new bot/dashboard), the agent runs inside the Railway Hermes service. The environment automatically injects `RAILWAY_TOKEN` for the Hermes service itself. If the workflow tries to authenticate to a *different* Railway project (e.g., the bot/dashboard project), the shadowing issue occurs.

**Solution**: Always `unset RAILWAY_TOKEN` before `railway login` when running from within a Railway-deployed service.

Alternatively, if you have `RAILWAY_API_TOKEN` set (account-level token from Bitwarden Secrets Manager or elsewhere), the `unset` isn't needed — the login flow will detect and use it directly.

## Diagnostic Recipe

```bash
# 1. Check what tokens are set
env | grep -E '^RAILWAY_(API_)?TOKEN='

# 2. Try login as-is (will likely fail if inside Railway)
railway login --browserless 2>&1 | head -3

# 3. Unset the service token and retry
unset RAILWAY_TOKEN
railway login --browserless

# 4. Verify success
railway whoami
```

## Related

- `references/credential-scope-debug.md` — token scope issues (different problem)
- `rapid-code-deploy-cycle` skill — alternative deployment via git push (no Railway CLI needed)

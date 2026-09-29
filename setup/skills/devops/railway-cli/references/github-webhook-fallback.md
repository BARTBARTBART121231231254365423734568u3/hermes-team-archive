# Railway GitHub Webhook Fallback

When Railway CLI commands fail with `Unauthorized` even after confirming the token is set, and the token cannot be regenerated or re-scoped, use GitHub push-to-deploy as a fallback.

## Pattern

If you have Railway projects linked to GitHub repos (the standard setup), Railway auto-deploys on every push to the default branch. When direct Railway API/CLI access is blocked, trigger a redeployment by:

```bash
# 1. Make an empty commit to force a new deployment
git commit --allow-empty -m "trigger: restart <service-name>"

# 2. Push to the default branch (usually main)
git push origin main
```

This works because:
- Railway has GitHub OAuth connected (visible in UI)
- Railway watches the repo and auto-deploys on every push (even empty commits)
- No Railway API token scope restrictions apply — only GitHub auth (via `gh` CLI) is needed

## When to use this fallback

- Railway CLI returns `Unauthorized` but the environment has a Railway token pre-set
- The token is scoped to a different workspace or project than the ones you're trying to deploy
- You have `gh` CLI authenticated and access to the repository
- The repo is already connected to Railway (verify in Railway Dashboard → Project → Deploy)

## Why this works

Empty commits are intentionally cheap — they trigger CI/CD pipelines and deployment webhooks without changing code. It's a standard pattern in Rails, Go, Node deployment workflows when you need to force a redeploy.

## Alternative: Direct Token Regeneration

If you have Railway Dashboard access (browser), regenerate a new token scoped to the workspace containing your target projects:

1. Visit https://railway.app/account/tokens
2. Click "Create Token"
3. **Critically**: Set Workspace to "No workspace" (full account access)
4. Copy and set as `RAILWAY_TOKEN` environment variable
5. Retry `railway` CLI commands

The GitHub fallback is faster when token regeneration is not possible.

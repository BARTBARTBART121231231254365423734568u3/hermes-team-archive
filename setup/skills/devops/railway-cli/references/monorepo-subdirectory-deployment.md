# Railway CLI: Monorepo Subdirectory Deployment Pitfall & Fix

## The Problem

When deploying services from a monorepo (e.g., `bot/`, `dashboard/` subdirectories in the same repo), running `railway up` from the repository root **ignores the service's Root Directory setting** in `railway.json` and instead treats the entire repo root as the build context.

### Symptoms

- `railway up ./bot --path-as-root` fails with "Railpack could not determine how to build the app"
- `railway up` detects no Dockerfile, even though `bot/Dockerfile` exists
- Build context shows "uploading" multiple directories unrelated to the service
- "No buildable entrypoint found at repo root"

### Root Cause

`railway up` uploads the current working directory and everything below it. If you run `railway up` from the repo root, it uploads the ENTIRE repo (bot/, dashboard/, .git, etc.). The `--path-as-root` flag tells railpack "treat this archive root as the build context," but by then the archive already includes the entire repo.

The `railway.json` setting `dir: ./bot` is intended for Railway's **automated deployment via GitHub webhooks**, not for manual `railway up` invocations.

## The Fix

**Option 1: Change directory, then deploy (recommended)**

```bash
cd bot
railway up ./. --path-as-root --service bot --detach
```

This uploads **only** the `bot/` directory and its contents, setting that as the build context root.

**Option 2: Explicit path from repo root**

```bash
# From repo root
railway up ./bot --path-as-root --service bot --detach
```

This should work IF railpack correctly interprets `./bot` as the archive root. However, this is less reliable than `cd bot && railway up ./. --path-as-root ...`

## Session 2026-08-30: AuthList Deployment

AuthList is a monorepo with `bot/` and `dashboard/` services on the same Railway project.

**What worked:**
```bash
cd /root/AUTH_LIST_RUST/bot
railway up ./. --path-as-root --service bot --detach

cd /root/AUTH_LIST_RUST/dashboard
railway up ./. --path-as-root --service dashboard --detach
```

**What did NOT work:**
```bash
# From repo root — railpack couldn't find Dockerfile/buildable entrypoint
cd /root/AUTH_LIST_RUST
railway up ./bot --path-as-root --service bot --detach  # FAILS
```

## Workaround: If Stuck in the Repo Root

If you cannot change directories:

1. Ensure you have Railway CLI linked to the project: `railway link -p <project-name> -e production`
2. Use `railway redeploy` instead of `railway up` (redeploy re-triggers the GitHub webhook, assuming auto-deploy is on):
   ```bash
   railway redeploy --service bot --detach
   ```
3. Or, make an empty commit and push to GitHub to trigger auto-deploy (see `rapid-code-deploy-cycle` skill):
   ```bash
   git commit --allow-empty -m "trigger: restart"
   git push origin main
   ```

## Key Takeaway

For monorepos on Railway:
- **Always `cd` into the service subdirectory before `railway up`**
- Use `railway up ./. --path-as-root --service <name> --detach`
- If you can't `cd`, use `railway redeploy` or the git-push-based deployment cycle

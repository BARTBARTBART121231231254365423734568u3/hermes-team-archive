# Railway CLI Project Shadowing via Ambient Environment Variables

## The Issue

When running Railway CLI commands from within a Railway deployment (e.g., Hermes running on Railway), the environment is auto-populated with project-scoped variables:

```bash
env | grep RAILWAY_
# RAILWAY_PROJECT_NAME=worthy-healing
# RAILWAY_PROJECT_ID=
# RAILWAY_SERVICE_NAME=hermes-agent-railway
# RAILWAY_SERVICE_ID=
# RAILWAY_ENVIRONMENT=production
# RAILWAY_ENVIRONMENT_ID=...
# (and others)
```

Even though you:
1. Ran `railway link --project authlist-bot -e production -s bot`
2. Verified the link was created in `.railway/config.json` or `~/.railway/config.json`
3. See no error message

Every subsequent `railway` command **silently ignores the link and targets the ambient project** (`worthy-healing` in the example above).

```bash
railway status
# Output: Project: worthy-healing (WRONG — you linked authlist-bot!)
# Output: Service: hermes-agent-railway (WRONG — you specified bot!)
```

No error is raised. The commands execute successfully against the wrong project, leading to silent data corruption or deployment to the wrong service.

## Why It Happens

The Railway CLI reads environment variables in this priority order:

1. **`RAILWAY_PROJECT_NAME`** (if set) → uses this project, ignoring `-p` flags and `.railway/config.json`
2. **`RAILWAY_PROJECT_ID`** (if set) → uses this project ID
3. **`RAILWAY_SERVICE_NAME`** (if set) → uses this service, ignoring `-s` flags
4. **`.railway/config.json` (local link)** → fallback if no env vars are set
5. **`~/.railway/config.json` (global link)** → final fallback

In Railway deployments, the service automatically injects items (1), (2), (3) for its OWN project. These shadow any local or global config file.

**This is different from `RAILWAY_TOKEN` shadowing** (see `references/token-shadowing-in-ci-environments.md`) — that's an authentication issue. This is a **silent project targeting issue** with no error message.

## Symptoms

```bash
# You're trying to deploy bot-service in authlist-bot project
railway link --project authlist-bot --service bot
# Output: Project authlist-bot linked successfully! 🎉

# But then:
railway status
# Output: Project: worthy-healing
#         Service: hermes-agent-railway
# ← WRONG PROJECT, no error raised

# Or:
railway variable list
# Output: Variables for hermes-agent-railway, not bot

# Or:
railway service redeploy
# Redeployed... hermes-agent-railway (WRONG SERVICE)
```

## The Fix: Unset All Ambient Project Vars

```bash
# Clear all ambient project variables
unset RAILWAY_PROJECT_NAME
unset RAILWAY_PROJECT_ID
unset RAILWAY_SERVICE_NAME
unset RAILWAY_SERVICE_ID
unset RAILWAY_ENVIRONMENT_ID
unset RAILWAY_ENVIRONMENT

# Then re-link
railway link --project authlist-bot --service bot --environment production

# Verify
railway status
# Should now show: Project: authlist-bot, Service: bot, Environment: production
```

## Caveat: The Link Won't Persist Across Commands When Vars Are Unset

Unfortunately, unsetting the vars and relinking in a SINGLE shell session won't persist to the NEXT shell command if you unset inside a subshell or pipe:

```bash
# This WON'T work — unset happens in a subshell, doesn't affect the next line:
(unset RAILWAY_PROJECT_NAME; railway link --project authlist-bot) && railway status
# Second line still has RAILWAY_PROJECT_NAME set from the parent shell

# This WILL work — unset in the SAME shell, persists:
unset RAILWAY_PROJECT_NAME
railway link --project authlist-bot
railway status
```

If you're running multiple `railway` commands in a script or CI environment, include the `unset` statements ONCE at the top of the script, not before each command.

## Prevention: Scripting Pattern

If your deployment script must target a different Railway project than the one the Hermes service is running in:

```bash
#!/bin/bash

# STEP 1: Clear ambient vars ONCE at the start
unset RAILWAY_PROJECT_NAME \
      RAILWAY_PROJECT_ID \
      RAILWAY_SERVICE_NAME \
      RAILWAY_SERVICE_ID \
      RAILWAY_ENVIRONMENT_ID \
      RAILWAY_ENVIRONMENT \
      RAILWAY_ENVIRONMENT_NAME

# STEP 2: Re-link to the target project
railway link --project authlist-bot --service bot --environment production

# STEP 3: Verify (CRITICAL — don't skip this)
railway status 2>&1 | grep -E 'Project:|Service:|Environment:'
# Confirm output shows authlist-bot and bot

# STEP 4: Do your work
railway variable set MY_VAR=value
railway service redeploy --yes
```

## Session 2026-08-31 Incident (AuthList Bot DELETE Fix)

**What went wrong:**
1. Tried to deploy a CORS DELETE fix to authlist-bot bot service
2. Ran `railway link --project authlist-bot --service bot` multiple times
3. Every `railway status` and `railway service redeploy` command SILENTLY targeted `worthy-healing` (Hermes) instead
4. No error was raised; commands executed successfully against the WRONG project
5. Appeared that Railway's GitHub webhook was broken (because the fix wasn't deploying), but actually the CLI was targeting the wrong project all along
6. Spent hours trying API calls, web UI auth, version bumps, etc., when the real issue was **the ambient env vars were shadowing the link**

**Fix:** `unset RAILWAY_PROJECT_NAME` before relinking, and VERIFY the status output before proceeding.

**Lesson:** When `railway status` contradicts what you linked, assume the ambient vars are shadowing — don't diagnose further. Always add explicit env var clearing to multi-project scripts when running from a Railway-deployed context.

## Diagnostic Recipe

```bash
# 1. Check what ambient vars are set
echo "Ambient vars:"
env | grep -E 'RAILWAY_(PROJECT|SERVICE|ENVIRONMENT)' | sort

# 2. Check what the link says
echo "\nLinked config:"
cat .railway/config.json 2>/dev/null | grep -E 'project|service' || echo "No .railway link"
cat ~/.railway/config.json 2>/dev/null | grep -E 'project|service' || echo "No ~/.railway link"

# 3. Check what `railway status` reports (the actual truth)
echo "\nRailway CLI view:"
railway status 2>&1 | head -10

# If (1) and (3) match but not (2), ambient vars are shadowing the link.
```

## Related

- `references/token-shadowing-in-ci-environments.md` — `RAILWAY_TOKEN` shadowing (authentication issue, not targeting issue)
- `references/project-linking-issues.md` — `.railway/config.json` caching and multi-config pitfalls
- `references/monorepo-subdirectory-deployment.md` — Related: when using `railway up` with explicit `-p` flags to bypass linking

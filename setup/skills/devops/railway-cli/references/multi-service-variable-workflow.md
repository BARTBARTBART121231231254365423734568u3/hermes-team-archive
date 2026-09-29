# Multi-Service Variable Management on Railway

## Problem
When a Railway project has multiple services (e.g., bot + dashboard), setting environment variables can link to the wrong service or fail silently.

## Pattern: Correct Workflow

### Step 1: Link Correctly to the Specific Project + Environment
```bash
cd /path/to/repo
railway link -p PROJECT_NAME -e ENVIRONMENT_NAME
# Example: railway link -p authlist-bot -e production
```

**Verify** the link succeeded:
```bash
railway variable list
# Should show variables for the CORRECT project
# Look for project-specific vars (e.g., DISCORD_TOKEN, API_TOKEN, etc.)
```

If you see Hermes internal vars (RAILWAY_ENVIRONMENT, RAILWAY_PUBLIC_DOMAIN, etc.) but NOT your app's vars, you linked to the wrong project.

### Step 2: Set the Variable with Environment Flag
```bash
ADMIN_TOKEN=$(openssl rand -hex 32)
railway variable set API_TOKEN="$ADMIN_TOKEN" --environment production
```

**Verify** it was set:
```bash
railway variable list --environment production | grep API_TOKEN
# Should show the token (potentially truncated in display)
```

### Step 3: Trigger Redeployment
```bash
# Option A: Redeploy explicitly
railway redeploy --environment production --yes

# Option B: Let git-hook auto-deploy
# (if enabled on your Railway project)
git commit --allow-empty -m "trigger: bot restart with new API_TOKEN"
git push origin main
```

## Common Mistakes

### Mistake 1: Forget `-e` Flag
```bash
# WRONG: links globally or to random service
railway variable set API_TOKEN="..."

# RIGHT: explicitly specify environment
railway variable set API_TOKEN="..." --environment production
```

### Mistake 2: Link Without `-p` Flag in Multi-Project Repos
```bash
# In a monorepo or when you have multiple Railway projects:
# WRONG: `railway link` without args prompts interactively, often defaults to first project
railway link

# RIGHT: explicitly specify
railway link -p authlist-bot -e production
```

### Mistake 3: Assume Link State Persists Across Sessions
Don't rely on `~/.railway/config.json` linkage persisting if you clone the repo fresh or switch directories. Always re-link explicitly or verify with `railway variable list`.

## Testing the Token Works

After setting the token on Railway:

1. **Wait for deployment** (2–3 minutes)
2. **Check bot is using new token:**
   ```bash
   # Try to access protected endpoint
   curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     https://bot-production-7612.up.railway.app/api/tenants
   ```
   Should return 200 + tenant list, not 401 Unauthorized.

3. **Or check dashboard login:** Attempt login with the token. If it fails, token isn't set or bot isn't using it yet.

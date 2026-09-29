# Railway CLI Project Linking Pitfalls

## The Problem: `railway link` Ignores Your Flags

When working with multiple Railway projects, `railway link -p <project-name>` may:
1. Link to the WRONG project (different from what you specified)
2. Silently ignore your `-p` flag and default to a previous link
3. Cache old project info in `~/.railway/config.json` and keep using it despite clearing and re-running

## Why It Happens

The Railway CLI stores linked-project state in TWO places:
1. **`~/.railway/config.json`** — User's global Railway config (slower to clear, easy to miss)
2. **`.railway/config.json` in current directory** — Project-scoped config (takes precedence if present)

When both exist, the CLI prioritizes the local one. If you only cleared one, the other still has the old project ID.

## The Fix: Full Reset and Explicit Re-link

```bash
# 1. BLOW IT ALL AWAY
rm -rf ~/.railway
rm -rf .railway

# 2. VERIFY nothing is cached
ls -la ~/.railway 2>&1 | grep -i "no such" || echo "⚠️ Config still exists!"
ls -la .railway 2>&1 | grep -i "no such" || echo "⚠️ .railway dir still exists!"

# 3. Use INTERACTIVE mode first to confirm which project you're targeting
railway link
# Follow prompts CAREFULLY — it will ask you to select:
# - Workspace
# - Project
# - Environment
# VERIFY you selected the RIGHT ONE before confirming

# 4. VERIFY the link worked
railway status
# Output should show your target project, not some other one
```

## Alternative: Explicit Project ID in Commands

Instead of relying on `railway link`, use explicit flags on EVERY command when in multi-project repos:

```bash
# DON'T do this (ambiguous when multiple projects exist):
railway variable list

# DO this (explicit):
railway variable list --project authlist-bot --environment production

# Or if the ID/slug is simpler:
railway variable list -p authlist-bot -e production
```

Note: Some subcommands (like `railway status`) require you to have linked first. For those, interactive `railway link` is unavoidable, so use the reset pattern above.

## Debugging: How to Tell Which Project You're Actually Linked To

```bash
# Check what config.json says
cat ~/.railway/config.json | grep -E '"project|"name' | head -10

# Check what `railway status` reports (the source of truth)
railway status 2>&1 | grep -E 'Project:|Environment:'

# If they don't match, the local .railway/config.json is shadowing the global one
cat .railway/config.json 2>/dev/null | grep -E 'project|service' || echo "No local config"
```

## Session 2026-08-29 Incident

In this session, I:
1. Set `railway link -p authlist-bot` multiple times
2. But `railway variable list` kept showing variables from `worthy-healing` (a different project)
3. The fix was to check `~/.railway/config.json` directly and see it DID contain `authlist-bot` project ID
4. But `railway status` and `railway variable list` still reported `worthy-healing`
5. Root cause: OLD `~/.railway/config.json` entry for `worthy-healing` was cached at a different priority

**The lesson**: When `railway status` contradicts what you expect, it's the source of truth. Don't trust that `railway link -p X` worked — verify with `railway status` immediately after.

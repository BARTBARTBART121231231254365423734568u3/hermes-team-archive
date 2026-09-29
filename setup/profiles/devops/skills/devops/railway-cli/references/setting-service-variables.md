# Setting Environment Variables on Railway Services

## Problem

After linking to a Railway project/service, you may need to SET or UPDATE environment variables (secrets, tokens, config). The CLI command for this is **`railway variable set`**, but it has important linking and scoping requirements.

## Linking Requirements

Before you can set a variable, the CLI must know which service you're targeting. There are three ways:

### Option 1: Link a Service (Recommended)

```bash
railway link
# Prompts for workspace, project, environment
# Then prompts for service
# After this, all `railway variable` commands target that service

railway variable set MY_VAR="my_value"
```

### Option 2: Link via Flags (Non-interactive)

If automation is needed:

```bash
railway service bot  # Link the 'bot' service in the current project
railway variable set API_TOKEN="secret-value"
```

### Option 3: Direct Service Targeting (Rare)

Some agents try to pass service flags directly:

```bash
# DOES NOT WORK — railway-cli doesn't accept --service in variable subcommands
railway variable set API_TOKEN="value" --service bot  # ❌ Error: unexpected argument '--service'
```

**Workaround**: Link the service first, then set variables.

## Common Pitfalls

### Pitfall 1: "Service 'bot' not found" After Linking

You may see this when trying to re-link to a specific service after a general `railway link`:

```bash
railway link                    # General link to project (succeeds)
railway service bot            # Try to link to 'bot' service specifically
# Error: Service "bot" not found.
```

**Why**: After `railway link`, the CLI remembers the current environment but not a specific service. Trying to link to a service name that doesn't exist or isn't in that project fails.

**Fix**:
1. Verify the service exists: `railway service list`
2. If it exists, use the exact name from the list
3. If it's a different project, re-link: `railway link` and select the correct project

### Pitfall 2: Variable Set with No Service Linked

```bash
railway variable set API_TOKEN="value"
# Error: Service not linked. Please link a service first.
```

**Fix**: Run `railway link` before any `variable set` command.

### Pitfall 3: Variables Masked in Output

When you list variables, Railway masks secrets with asterisks by default:

```bash
railway variable list
# Output:
# API_TOKEN       *****
# DATABASE_URL    *****
```

To reveal a specific variable, use the Railway UI or try the `--raw` flag (if available in your version).

## Verification

After setting a variable, Railway should auto-redeploy the service. Check:

```bash
railway status                 # Shows deployment in progress
railway logs                   # View live logs to confirm new value is loaded
```

If the variable doesn't appear to take effect within 30 seconds, the service may still be deploying. Wait and check logs again.

## Timeout or Connection Issues

If `railway variable set` times out or fails with network errors:

1. Verify `RAILWAY_API_TOKEN` is still valid (token can expire)
2. Check Railway status page: https://railway.app/status
3. Try `railway whoami` — if it fails, re-authenticate with `railway login --browserless`
4. Re-link the service and retry

## References

- `references/credential-scope-debug.md` — Fixing "Not Authorized" token errors
- `references/bitwarden-secrets-integration.md` — Fetching `RAILWAY_API_TOKEN` from shared secrets vault

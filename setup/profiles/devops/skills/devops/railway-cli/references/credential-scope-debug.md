# Railway Token Scope Debugging

When `railway` commands return `Not Authorized` or `Unauthorized`, the token exists
but lacks the right scope. This is the #1 cause of "Railway isn't working" reports.

## Symptoms

- `railway whoami` → `Unauthorized. Please check that your RAILWAY_TOKEN is valid...`
- `railway project list` → same error
- `railway api 'query { me { id name email } }'` → `{ "errors": [{ "message": "Not Authorized" }] }`
- `railway login --browserless` → `Invalid RAILWAY_TOKEN`

Even though `echo $RAILWAY_TOKEN` shows a value. Token *exists* ≠ token *works*.

## Root cause

Railway token creation UI defaults to **Workspace: "My Projects"** (or the most
recently-used workspace). That scope:

- Cannot list projects in other workspaces you own
- Cannot call `me { ... }` GraphQL query at all
- Returns `Not Authorized` on the majority of CLI commands

## Diagnostic recipe

```bash
# 1. Confirm token is set and check length (real tokens are 60+ chars; 36-char ones are usually broken)
echo "len=${#RAILWAY_TOKEN}"

# 2. Try a no-side-effect GraphQL probe
railway api 'query { me { id name email } }' 2>&1

# 3. If "Not Authorized" → token scope is wrong, NOT the token value
# 4. If "Invalid RAILWAY_TOKEN" → token value itself is bad (revoked, truncated, wrong env var name)
```

## Fix (in order of speed)

1. **Regenerate token at railway.app → Account → Tokens** with Workspace = **"No workspace"**.
   Paste it back into `RAILWAY_TOKEN` env var. Usually fixes it in 30 seconds.
2. **Browser auth fallback**: if you can run `railway login` interactively on a machine
   with a browser, do it there, then copy the resulting `RAILWAY_API_TOKEN` to this box.
3. **As a last resort**, `unset RAILWAY_TOKEN && railway login --browserless` — uses any
   cached session in the env if present.

## What NOT to do

- Don't keep retrying different CLI flags — the token is the problem, not the command.
- Don't uninstall and reinstall `railway` — same broken token will still be there.
- Don't claim "I don't have Railway access" until you've at least run `railway whoami`
  with the existing token. The user often has it preconfigured; missing it is a probe
  failure, not an access failure.

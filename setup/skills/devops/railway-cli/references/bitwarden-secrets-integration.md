# Railway + Bitwarden Secrets Manager Integration

This setup uses **Bitwarden Secrets Manager (`bws` CLI)** to store and rotate the account-level `RAILWAY_API_TOKEN` (distinct from project-scoped `RAILWAY_TOKEN`).

## Context

- **Location**: Stored in Bitwarden Secrets Manager vault (not personal Bitwarden password manager)
- **Tool**: `bws` CLI (Bitwarden Secrets Manager client), NOT `bw` (personal password manager CLI)
- **Environment**: Only available in certain contexts (e.g., deployment VMs, CI runners); dev machines may not have it
- **Pattern**: Used across multi-project deployments to rotate secrets without hardcoding tokens

## Fetching RAILWAY_API_TOKEN from Bitwarden

If `RAILWAY_API_TOKEN` is not set in the current shell:

```bash
# 1. Check if bws is installed
which bws || echo "bws not found"

# 2. List available secrets (requires existing auth)
bws secret list

# 3. Fetch the Railway API token by secret ID (user will know the ID)
export RAILWAY_API_TOKEN="$(bws secret get <secret-id> --raw)"

# 4. Verify it works
railway whoami
```

## When RAILWAY_API_TOKEN is Not Available

If `bws` is not installed or not authenticated in the current session:

1. **On a shared/deployment machine**: The token is stored in the vault but requires `bws` auth. Ask the project owner for the token value directly, or access it through the Bitwarden web vault if you have permission.

2. **Locally in development**: Use `railway login --browserless` (interactive browser-based auth) or create a separate scoped token in the Railway UI (Account → Tokens) and store it locally in `~/.railway/config.json` or as `RAILWAY_API_TOKEN`.

3. **Never commit tokens to git**: All Railway tokens (whether from vault or manually created) belong in `.gitignore`, environment variables, or config files marked `mode: 600`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `command not found: bws` | Bitwarden Secrets Manager CLI not installed | Install via `npm install -g @bitwarden/cli`, or fetch token from web vault directly |
| `bws secret get` returns empty | Secret ID doesn't exist or auth token expired | Double-check secret ID; re-run `bws auth` or use web vault |
| `railway whoami` still says `Unauthorized` after fetching from Bitwarden | Token exists but has wrong scope | Token scope is the issue, not the source. See `references/credential-scope-debug.md` |

## Key Difference: bws vs bw

- **`bws`** (Bitwarden **Secrets** Manager): Machine-to-machine API access, stores deployment secrets like Railway tokens. No personal password manager data.
- **`bw`** (Bitwarden personal **password manager** CLI): Manages personal vault (passwords, bookmarks, notes). Different tool, different auth, different data.

Never confuse them or try to use `bw login` when `bws` is needed.

---
title: Railway CLI Operations
name: railway-cli
description: Query and manage Railway projects via CLI.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when querying, listing, or managing Railway projects and services via terminal — account access, project enumeration, deployments, status checks.
metadata:
  hermes:
    tags: ["railway", "devops", "cli", "deployment", "authentication"]
    related_skills: ["github-repo-management"]
---

# Railway CLI Operations

Programmatic access to Railway (railway.app) account, projects, services, and deployments via the Railway CLI.

## When to Use

- Querying account projects, services, or deployment status from terminal
- Automating Railway project discovery in CI/CD or agent workflows
- Debugging deployment issues, checking logs, or service health
- Linking/managing Railway services programmatically

## Installation

```bash
npm install -g @railway/cli
```

## Authentication

Railway CLI supports two authentication patterns:

### Pattern 1: Existing Session (Recommended if available)
If a valid `RAILWAY_API_TOKEN` environment variable already exists, `railway login --browserless` will detect and use it:

```bash
railway login --browserless
# Output: "RAILWAY_API_TOKEN found"
# Output: "Logged in as <email> 👋"
```

### Pattern 2: Generate New API Token
If no existing session, create a token in the Railway UI (Account → Tokens):
1. Click "Create Token"
2. **CRITICAL**: Ensure **Workspace** is set to **"No workspace"** (full account access), NOT "My Projects" or a specific workspace
3. Copy the generated token
4. Store it as `RAILWAY_API_TOKEN` environment variable or in `~/.railway/config.json`

⚠️ **Pitfall**: Tokens scoped to "My Projects" will fail with `Not Authorized` errors on most queries. Token scope is the primary blocker.

## Common Commands

### List all projects
```bash
railway project list
```

### Show project status (must be linked)
```bash
railway status
```

### Get project details via GraphQL API
```bash
railway api 'query { projects(first: 50) { edges { node { id name environments { name } } } } }'
```

### List services in current project
```bash
railway service list
```

### View deployment logs
```bash
railway logs
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Not Authorized` on queries | Token is scoped to "My Projects" or other limited workspace | Regenerate token with "No workspace" scope |
| `Invalid RAILWAY_TOKEN` | Environment variable set but stale/revoked | `unset RAILWAY_TOKEN` and try `railway login --browserless` |
| `Unable to parse config file` | Corrupted `~/.railway/config.json` | `rm -rf ~/.railway && railway login --browserless` |

## Key Learnings

- **API tokens vs. sessions**: The Railway CLI prefers finding existing authenticated sessions via `RAILWAY_API_TOKEN` env var. If that fails, manually-generated tokens often have scope restrictions baked in at creation time.
- **Scope is non-obvious**: The token creation UI defaults to "My Projects" which is severely restricted. Full account access requires explicit "No workspace" selection.
- **Fallback to browserless login**: When token auth fails, `railway login --browserless` often succeeds if a prior session was cached in the environment.

## References

- Railway CLI docs: https://docs.railway.app/guides/cli
- GraphQL API: https://railway.app/docs/reference/public-api
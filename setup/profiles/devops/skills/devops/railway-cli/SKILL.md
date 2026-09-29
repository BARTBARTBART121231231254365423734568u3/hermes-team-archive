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

## Capability-Probe Checklist (do this BEFORE claiming "I can't access Railway")

Always run these probes first. A working `railway` install + scoped token is often preconfigured on the box:

```bash
# 1. Is the CLI installed? (don't trust which alone — also check ~/.railway/bin and npm globals)
which railway || ls -la ~/.railway/bin/railway 2>/dev/null || echo "not found"

# 2. Is RAILWAY_TOKEN / RAILWAY_API_TOKEN set?
env | grep -E '^RAILWAY_(TOKEN|API_TOKEN)=' | sed 's/=.*/=<set>/'

# 3. Is there a session/config in ~/.railway?
ls -la ~/.railway/ 2>/dev/null

# 4. If found, try `railway whoami` — if it returns email, you're good.
#    If it returns "Unauthorized" or "Not Authorized", see Troubleshooting.
```

⚠️ **Pitfall**: Declaring "the Railway CLI isn't installed" after only running `which railway` is a known failure mode. The CLI is often installed to `~/.railway/bin/` (not on default PATH) or via npm global, and `RAILWAY_TOKEN` is frequently pre-set in the sandbox environment. Always run the full checklist before reporting a missing capability.

⚠️ **Deployment guards are mandatory for mutations.** If a target helper cannot represent a multi-environment project, do not bypass it with raw `railway up`, `redeploy`, variable mutation, or deployment commands; repair/port the guard or hand the blocker to devops while preserving manifest and exact-target validation. Read-only discovery must carry explicit project/environment/service identifiers with target read-back before its output is trusted.

On the local Linux Hermes host, `railway` may be absent from PATH even while the installed CLI exists at `/opt/railway/railway`. Use the guarded wrapper at `~/Hermes Workspace/projects/hermes-agent-railway/scripts/railway_guard.py` through `python3`: `status --project <id> --environment <id> --json` for read-only target/deployment/domain identity, and `deployment list --project <id> --environment <id> --service <id> --limit 2 --json` for the live revision and rollback pointer. For any deploy, use only `deploy-verified <reviewed-manifest> --commit <full-sha> [--apply]` from the verified repository. Its dry-run requires remote manifest branch HEAD equal to that SHA; a local reviewed worktree alone cannot pass. Do not bypass the wrapper just because the `railway` executable is not on PATH, and do not push an auto-deploy branch before checking flags/configuration and recording rollback.

⚠️ **Multi-project setups — two distinct tokens**: Be aware of the distinction:
- **`RAILWAY_API_TOKEN`** — Account-level token (needed for project enumeration, cross-project queries, `railway list`). Often stored in Bitwarden Secrets Manager in shared/deployment contexts. If missing, consult `references/bitwarden-secrets-integration.md`.
- **`RAILWAY_TOKEN`** — Project-scoped token (only works within a linked project, set automatically by `railway link`). This is what shows in `railway status` output and is NOT sufficient for `railway project list` or cross-project work. **CRITICAL PITFALL**: In Railway deployments or CI environments, the service automatically sets `RAILWAY_TOKEN` to its own project-scoped token. This token **shadows and blocks** `railway login` flows. If `railway login --browserless` fails with "Invalid RAILWAY_TOKEN" even when you haven't manually set it, clear it first: `unset RAILWAY_TOKEN`.

If `railway list` or cross-project commands fail with "Unauthorized", you likely have only the project-scoped token. Fetch the account-level one instead.

## Installation

```bash
npm install -g @railway/cli
# or, if npm global not writable:
mkdir -p ~/.railway/bin && npm install --prefix ~/.railway @railway/cli
# then add to PATH for the session:
export PATH="$HOME/.railway/bin:$NODE_modules_bin:$PATH"
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

### Query project domains directly via curl (bypasses CLI link/project-context issues entirely)

When you need a service's public domain (to curl-verify reachability, for example) and don't want to fight `railway link`/ambient-var shadowing, hit the GraphQL API directly with the account token — no CLI state involved:

```bash
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"query($id:String!){ project(id:$id) { id name environments { edges { node { id name serviceInstances { edges { node { serviceId domains { serviceDomains { domain } customDomains { domain } } } } } } } } } }","variables":{"id":"<PROJECT_ID>"}}'
```

⚠️ **Pitfall**: `domains` is NOT a field on `Service` — querying `project.services.edges.node.domains` fails with `Cannot query field "domains" on type "Service"`. Domains live under `project.environments.edges.node.serviceInstances.edges.node.domains` instead (a service's domain is per-environment, since staging/production of the same service have different domains). Use `me { projects }` or a bare top-level `projects(first:N)` query to first discover project IDs if unknown — note plain `projects` at top level returns an empty edge list for a personal (non-team) account; use `me { projects { edges { node { id name } } } }` instead.

### List services in current project
```bash
railway service list
```

### View deployment logs
```bash
railway logs
```

### Set environment variables and apply them

⚠️ **CRITICAL**: Setting an env var with `railway variable set KEY=VAL` does NOT automatically redeploy the service. The running container continues with the OLD values until you force a rebuild.

```bash
# Set the variable (in Railway's metadata)
railway variable set SETUP_TOKEN="newtoken123" --environment staging

# Force a rebuild + redeploy to apply the new env var
railway up --detach

# Wait for container startup
sleep 40

# IMMEDIATELY test the feature to verify the env var was applied
curl -X POST https://service-staging.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "...", "setupToken": "newtoken123"}'
```

See `references/environment-variables-do-not-auto-redeploy-2026-09-06.md` for full diagnostic and why this matters.

## Release-Branch Gate: Verify Before Declaring a Release Deployable

A healthy Railway service and a verified release-candidate branch do **not** mean the release will deploy. Before waiting on Railway, identify the service's configured GitHub deployment branch and compare it to the release ref.

1. Confirm the exact release-candidate commit exists at `origin/<release-branch>`.
2. Determine the GitHub branch Railway watches (often `main`) from the service source/deployment configuration.
3. If the RC is not on that branch, promote it through the normal Git workflow: fetch first, fast-forward when safe, otherwise use a reviewed merge; never force-push or discard newer deployment-branch work.
4. Verify `origin/<deployment-branch>` contains the intended RC SHA with `git ls-remote` before observing Railway.
5. Only then follow deployment status/logs and perform live verification.

For a service rename requested alongside deployment, rename the **existing** service in place using Railway's supported update path. Verify its service ID, source repository, volume/domain bindings, and HTTP health are unchanged before resuming deployment. Do not recreate a service merely to change its display name.

See `references/release-branch-gates-and-safe-service-renames.md` for a compact handoff/checklist.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Not Authorized` on queries | Token is scoped to "My Projects" or other limited workspace | Regenerate token with "No workspace" scope |
| `Invalid RAILWAY_TOKEN` | Environment variable set but stale/revoked | `unset RAILWAY_TOKEN` and try `railway login --browserless` |
| `Unable to parse config file` | Corrupted `~/.railway/config.json` | `rm -rf ~/.railway && railway login --browserless` |
| `Unauthorized` on all commands but token is set | Token is workspace-scoped or project-restricted and cannot be changed | Use GitHub webhook fallback: `git commit --allow-empty -m 'trigger: restart' && git push origin main` (see `references/github-webhook-fallback.md`) |
| `railway variable list` shows wrong project variables | `railway link` defaulted to wrong project; multiple projects available | Use `-p <project_name>` flag explicitly: `railway link -p authlist-bot -e production` |
| Token set but still "No service linked" | After `railway link`, need to specify `-e` (environment) | Command: `railway variable set KEY=VAL -e production` not just `railway variable set KEY=VAL` |
| `railway status` shows the WRONG project even after `railway link` | Ambient env vars (`RAILWAY_PROJECT_ID`, `RAILWAY_ENVIRONMENT_ID`, `RAILWAY_ENVIRONMENT`, `RAILWAY_SERVICE_ID`, `RAILWAY_SERVICE_NAME`, **`RAILWAY_PROJECT_NAME`**) are already set in the shell — e.g. because the agent itself is running inside a Railway deployment — and the CLI reads those in preference to the `~/.railway/config.json` link. **CRITICAL: No error is raised; commands execute silently against the wrong project.** See `references/ambient-env-var-project-shadowing.md` for full diagnosis. | (1) Unset all: `unset RAILWAY_PROJECT_NAME RAILWAY_PROJECT_ID RAILWAY_SERVICE_NAME RAILWAY_SERVICE_ID RAILWAY_ENVIRONMENT_ID RAILWAY_ENVIRONMENT`. (2) Re-link: `railway link -p <target> -e <env> -s <svc>`. (3) VERIFY: `railway status` must show correct target before proceeding. |
| Environment query returns "not found" but you're certain the environment exists (or the user says it's been used before) | DO NOT assume the environment needs to be created. Ask the user directly: "Railway says staging env doesn't exist. Have you deployed to staging before, or is this a new environment we need to set up?" If it's genuinely new infrastructure, confirm with the user and create it in the Railway dashboard. If the user says it DOES exist, use `railway link --project <name> --environment <target>` explicitly with the environment name as a flag (not relying on CLI auto-detection). Session 2026-09-05: Assumed staging was missing without asking Thomas → four devops protocol violations → user corrected "we've done this multiple times" → actually, staging environment had never been created before (new workflow), but devops couldn't report the blocker. Lesson: Ask the user first; don't assume infrastructure state. | Ask the user what the environment name/config is, or delegate with context: "Environment query unclear; I know prior deployments succeeded. Need you to check Railway dashboard + API directly for actual blocker (not just recreate infrastructure)." |
| Deployment task hits repeated protocol violations (clean exit rc=0 without kanban_complete/kanban_block) across 3+ retries | **ALWAYS** a genuine blocker that devops encountered but couldn't report (missing Railway environment, unmerged feature branches, merge conflicts, missing branch). NOT a worker bug. See `references/devops-protocol-violations-on-deployment-tasks-2026-09-05.md`. | (1) Identify the blocker: Check if target environment exists, if all branches are merged, if the branch exists locally/remote. (2) Fix the blocker directly: Create missing environment in Railway dashboard, resolve merge conflicts via coder, push missing branch. (3) Create a FRESH devops task with full context: "Blocker fixed: staging environment now created. Proceeding with deploy." Do NOT retry the same task; always create fresh after fixing the underlying blocker. Session 2026-09-05: 11 devops protocol violations across 4 tasks before discovering staging environment didn't exist + 6 route branches unmerged. Fix: User created env, Coder merged branches, fresh deploy task succeeded. Timeline: `references/devops-protocol-violations-on-deployment-tasks-2026-09-05.md`. |

| `railway redeploy --from-source --yes` succeeds but live API still shows OLD behavior | Docker layer caching is reusing source files from a previous build, skipping the actual build step. The container starts ("Deployment successful") but runs old code. See `references/docker-image-cache-on-from-source.md`. | (1) Verify cache reuse: `railway logs --latest --lines 1` — if startup timestamp is old (before redeploy), new code never built. (2) Make a REAL code change (not comment or version bump): `echo 'const BUILD_TS: &str = \"$(date)\";' >> src/lib.rs`, commit, push. (3) Redeploy: `railway redeploy --from-source --yes`. (4) Wait 2-3 min, verify startup timestamp is new with `railway logs --latest --lines 1`. (5) Test actual endpoint behavior with curl — if old behavior persists, repeat step 2 with a different code change. |
| `railway up` from monorepo root deploys to WRONG project even after fresh @railway/cli install and explicit `railway link --project authlist-bot` | `.railway/config.json` caches the old project link from a prior session and is NOT cleared by `rm ~/.railway`. The local `.railway/` persists across sessions in the repo dir. `railway up` reads `.railway/config.json` (repo-local) instead of `~/.railway/config.json` (user-global), so the wrong project is used. | MANDATORY: `rm -rf .railway ~/.railway` BEFORE any `railway link` or `railway up`. Then verify with `railway status` AFTER linking (do not assume the link worked). If `railway status` still shows wrong project, the issue is deeper — use explicit `-p/--project` flags on every command or seek local `.railway/` in ancestor dirs. |
| `railway up` from repo root fails: "Railpack could not determine how to build" / no Root Directory honored, even though service has Dockerfile or build config | Running `railway up` from a MONOREPO root uploads the entire repo as build context, completely bypassing the service's Root Directory setting from `railway.json` — railpack can't find a Dockerfile/buildable entrypoint at the repo root. This happens even if the service specifies `dir: ./bot` or similar in config. | Deploy the service's subdirectory as the archive root: `cd bot && railway up ./. --path-as-root --service bot --detach` from repo root, OR use full flags: `railway up ./bot --path-as-root --service bot --detach`. The `--path-as-root` flag is critical — it treats the archive root as the build context, not the uploaded directory alone. |
| `railway up`/`railway redeploy` fails with `Railpack could not determine how to build the app` even though the service has a Dockerfile/subdir build config | Running `railway up` from the monorepo ROOT uploads the whole repo as the build context, bypassing the service's configured Root Directory / `dir` setting from `railway.json` — railpack then can't find a buildable entrypoint at the repo root. | Deploy the SERVICE'S subdirectory as the archive root: `cd <service_dir> && railway up ./. --path-as-root --service <name> --detach`, or run `railway up <service_dir> --path-as-root --service <name>` from the repo root. Do NOT rely on `railway.json`'s `dir` field being honored by `railway up`. |
| `railway status` shows `Deploy failed` after `railway up`/`redeploy`, but you can't tell why | `railway logs` with no flags often replays STALE/cached logs from a prior deployment, not the failing one. | Get the actual failing deployment's logs explicitly: `railway logs --service <name> --latest --lines 150`. If that shows the BUILD succeeded (image pushed) but the service still shows failed/502, the crash is at container STARTUP, not build — check for a stack trace or `Error:` line right after `Starting Container`, not in the build section. |
| Build succeeded and deployed, but live endpoint still shows OLD behavior (old CORS headers, old API response, etc.) | Container replacement is pending or delayed: build completed but new container hasn't yet fully started and taken traffic, or old container still running. This looks like a code problem but is actually a deployment timing issue. | (1) Check that build actually completed: `railway deployment list --limit 2` should show new deployment with SUCCESS status. (2) Verify new container has started: `railway logs --service <name> --latest --lines 3` should show a startup log with a RECENT timestamp (within 1 min of your push). (3) If old timestamp, new container hasn't started yet — wait 2-3 more min and re-test. (4) If new timestamp but old behavior persists, the code change didn't actually work (check handler/CORS config). See `references/deployment-lag-and-caching.md` for full diagnostic. |
| Container crash-loops immediately after a deploy that otherwise built fine (curl to the service returns 502, `railway status` shows `Deploy failed`) | The build succeeded but the process panics/exits on startup — common causes: a migration/schema check that now rejects the deployed code (see e.g. sqlx migration-checksum pitfall in a language-specific skill), a newly-required env var that isn't set, or a startup DB query against a table/column that doesn't exist yet. | Read runtime logs (`railway logs --service <name> --latest`) for the exact panic/error line right after `Starting Container` — do not guess from the build log, which will look clean. Fix the root cause, rebuild+retest LOCALLY first, then redeploy and re-verify with a live curl + fresh `--latest` logs before considering it fixed. |

**Special case**: Running from within a Railway deployment or CI environment?  
If `railway login` fails with "Invalid RAILWAY_TOKEN" even though the token is set by the environment, see `references/token-shadowing-in-ci-environments.md` for the fix (`unset RAILWAY_TOKEN` before login).

## CRITICAL: Investigation Escalation Rule (Reinforced Session 2026-08-31)

**When diagnosing Railway/deployment issues, hand off to devops IMMEDIATELY on any sign of multi-step complexity.** A cheap model (Haiku) lacks live system visibility and the reasoning power to quickly pinpoint infrastructure problems. This is not an option—it is a HARD RULE.

**DO NOT investigate yourself beyond:**
- 1 read-only probe to understand the state (`railway status`, `git log`, `curl endpoint`)
- 1 verification attempt (e.g., one `railway logs` fetch)

**If either probe shows ambiguity or requires multi-step diagnosis, STOP and hand off immediately.** Examples of "hand off now":
- First `railway status` shows wrong project (even after linking) → unset env vars and link again ONCE; if still wrong, hand off
- `railway logs` shows a cryptic error or migration issue → hand off
- Redeployment seems to succeed but live behavior is old → hand off (could be caching, timing, or state mismatch)
- About to try SSH, restart container, or any advanced troubleshooting → hand off FIRST

**DO NOT:**
- Try 2+ different diagnostic commands to "narrow it down"
- Attempt workarounds (editing configs, creating fallback patterns, inventing API calls)
- Continue troubleshooting while uncertain about the actual root cause
- Ask yourself "maybe if I try one more thing" — that's the start of a spiral

**Correct pattern:**
1. Run 1 read-only probe (`railway status` or `railway logs --latest --lines 20`)
2. State clearly what you found and what's UNCLEAR
3. Hand off IMMEDIATELY (do not delay): 
   ```
   kanban_create(
     assignee="devops",
     title="<short, specific title>",
     body="**What I found:** <state>\n\n**What I tried:** <commands>\n\n**What's unclear:** <what blocks diagnosis>\n\n**Context:** <repo, service, error message, user action that triggered this>"
   )
   ```
4. Report to user: "Handed off to devops for investigation. They'll SSH in and check the database/logs/state. Will report back."
5. STOP. Do not continue investigating.

**Why this rule exists:**
- Sonnet-tier devops has access to SSH, database, live logs, deployment history
- Cheap model spiraling through hypotheses is expensive (token waste) and usually wrong
- Infrastructure problems almost always need live system access (not code inspection)
- A specialist solves in 1 attempt what a generalist spends 30 minutes guessing at

**Session 2026-08-31 incident (FINAL OUTCOME):**
- Symptom: `/setsteamid` succeeds but `/authlist` empty; user appears in `/departed.csv`
- Bot deployment c4a4ca0d is healthy on commit 6dd308d
- Database migration 0009 DID run; schema is correct
- Data WAS written correctly to the right tenant
- Root cause: member's `is_active=false` because Discord user doesn't hold configured tracked role
- Fix: Assign the Discord role to the user (external, not code)
- **Agent mistake:** Tried to restart bot after 1 log check, user corrected → "should be handed out to a agent instead"
- **Correct action:** One `railway logs` → "can't inspect DB without SSH" → hand off → devops SSH'd, checked schema, found is_active=false, identified role mismatch in 10 min
- **Token cost of wrong approach:** ~5 tool calls, user correction, timeout, retry loop
- **Token cost of correct approach:** 1 kanban_create, 1 message to user

See `references/investigation-escalation-incident-2026-08-31.md` for the complete incident timeline and why this rule prevents wasted effort.

## Key Learnings

- **API tokens vs. sessions**: The Railway CLI prefers finding existing authenticated sessions via `RAILWAY_API_TOKEN` env var. If that fails, manually-generated tokens often have scope restrictions baked in at creation time.
- **Scope is non-obvious**: The token creation UI defaults to "My Projects" which is severely restricted. Full account access requires explicit "No workspace" selection.
- **Fallback to browserless login**: When token auth fails, `railway login --browserless` often succeeds if a prior session was cached in the environment.
- **Multi-service on Railway with static hostnames**: Services deployed to Railway get stable, predictable URLs (e.g., `service-production-xyz.up.railway.app`). Use these URLs in inter-service communication rather than environment variables or service discovery. Frontend can use hostname detection to route to the correct backend service at runtime.

- **CRITICAL: `railway status` is the source of truth** — When running Railway CLI inside a Railway deployment (e.g., Hermes on Railway) while targeting a DIFFERENT project, ambient environment variables (`RAILWAY_PROJECT_NAME`, `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_NAME`, etc.) **silently shadow the `.railway/config.json` link with NO ERROR MESSAGE**. Every command executes successfully against the WRONG project. **Always verify `railway status` immediately after linking; if it shows the wrong target, unset the ambient vars and re-link.** See `references/ambient-env-var-project-shadowing.md`. **Session 2026-08-31 Incident:** Spent hours diagnosing a "broken GitHub webhook" on authlist-bot when the actual issue was silent project shadowing — the CLI was targeting `worthy-healing` instead. Fix: `unset RAILWAY_PROJECT_NAME`.

- **CRITICAL: Always verify credentials work before claiming success** — Setting a variable on Railway and redeploying does NOT guarantee the service is using it. See `references/verify-token-works-before-claiming-success.md` for the testing pattern. TL;DR: after setting a credential, test it immediately with curl against a protected endpoint. Only report success after receiving 200 + valid response. **Never ask the user to test or verify your work** — you must verify it yourself. If you cannot test it (no tools available, system unreachable), then say so explicitly and ask the user. But do not report success without testing.
  
  **Session 2026-08-29 Incident:** I set admin API token on Railway, claimed success without testing, and made the user test it 5+ times. Root cause: hardcoded wrong token in dashboard source while Railway had the correct one. A 30-second curl test would have caught this. The user: "i dont know why you just dont test these things urself." **Lesson embedded: Always test credentials with curl immediately after setting. Do not ask the user. See `references/verify-token-works-before-claiming-success.md` for the exact test pattern.**

- **Data isolation bugs are NOT deployment issues** — A per-server SaaS or multi-tenant system leaking data across tenants (authlist showing entries from OTHER Discord servers when `/setsteamid` is run) is a DATABASE SCHEMA or QUERY BUG, not a Railway/deployment problem. The fix requires a database migration (composite primary keys, tenant-scoped queries), not redeploying. When debugging SaaS data leaks: (1) Confirm the bug is real (test in 2+ tenant contexts). (2) Check if the database schema has tenant isolation (composite keys, indexes, FK constraints). (3) Verify all queries filter by tenant_id at the query level, not application level. (4) If schema is wrong, hand to coder for migration. Do NOT assume deployment or configuration. **Session 2026-08-31 Incident:** Debugged a 403 Steam API error for 1+ hour (root cause: invalid API key), which distracted from the REAL bug: authlist data wasn't isolated per Discord server due to a database PRIMARY KEY that only had `(discord_id)` instead of `(tenant_id, discord_id)`. The Steam error was a red herring; the schema was the blocker. A fresh coder handoff with "same Discord user in two servers sees different authlist entries — check DB schema" solves it immediately.

- **CRITICAL: When root cause is unclear or multi-step debugging needed, hand off to devops immediately.** Do not keep iterating with different commands/theories. A single cheap model (Haiku) trying to debug live infrastructure will spiral through hypotheses and waste time. Escalate with full context after first sign of complexity — deployment failures, cross-service routing issues, caching/timing problems where you need live log inspection. **Session 2026-08-31 Incident:** Debugged a 403 Forbidden Steam API error for 1+ hour when root cause was simply an invalid API key in the env var. The fix required getting the correct credential from the user, not investigation. Lesson: when a fix requires real-world context (a credential, a decision, external state), ask the user rather than spiraling through diagnostics. When fixing infrastructure, hand off. See "Investigation Escalation Rule" section.

- **CRITICAL: Setting env vars is not enough — you MUST verify the actual live service is using them.** A common failure pattern: (1) Set env var on Railway service, (2) Believe it's set, (3) Redeploy succeeds (exits 0, shows "Online"), (4) Actually test the feature — it fails because the service is still using the old/empty value. The gap is usually: the deployment happened but before the service had fully booted, or the variable was set on the wrong service/project. See `references/verify-token-works-before-claiming-success.md` for the exact verification pattern (test with curl/login/feature immediately after redeploy, don't just check that redeploy succeeded). **Session 2026-09-01 Incident:** ADMIN_PASSWORD was set via CLI but dashboard login still failed with "Invalid username or password". Root cause: credential was either never actually set in the environment, set to the wrong project, or set but never tested live. Backend confirmation (`railway variable list`) showed the variable missing or empty. Fix: (1) Verify the variable exists in Railway: `railway variable list | grep ADMIN_PASSWORD` — if not present, set it: `railway variable set ADMIN_PASSWORD="<value>" --environment production`. (2) Redeploy: either `railway redeploy --yes` or push code. (3) **IMMEDIATELY TEST**: `curl -X POST https://<service>.up.railway.app/api/auth/login -d 'username=admin&password=<value>'` — must return 200 + valid token, NOT 401. (4) Only THEN report to user "credential verified working". DO NOT report success after setting + redeploying alone. The feature test is mandatory before claiming success. **Session anti-pattern:** Repeated setting of ADMIN_PASSWORD and asking user to test, when the real fix was to curl the login endpoint immediately after setting and verify it returned 200.

- **CRITICAL: Docker layer caching on `--from-source` redeploy** — After pushing code changes, `railway redeploy --from-source --yes` can show "Deployment successful" while running OLD code due to Docker layer reuse. The container starts fine but the binary was built from cached source files, not fresh. Symptom: logs show old startup timestamp (before your push), live API returns old behavior. Fix: Make a REAL code change (not comments/version bumps), verify startup timestamp is AFTER your redeploy, test actual endpoint. See `references/docker-image-cache-on-from-source.md` for full diagnosis and incident analysis. **Session 2026-08-31 Incident:** AuthList DELETE CORS fix deployed successfully 3x but API still rejected DELETE — cached binary was months old. Debugging cost 2+ hours before realizing deployment success ≠ code freshness.

| Setting env var with `railway variable set KEY=VAL` succeeds but service still uses old value | Container is still running with the env vars it loaded at startup. Setting a variable in Railway's metadata does NOT restart the container or reload values. | Use `railway up --detach` to force a rebuild/redeploy, which will pull fresh env vars on startup. Wait 40-60 seconds for the container to start, then TEST the feature immediately (e.g., `curl` the endpoint, attempt login, trigger the feature that uses that env var). See `references/environment-variables-do-not-auto-redeploy-2026-09-06.md`. |
| Deployment succeeds (status Online, `--from-source` completes, no crash loop) but live feature is broken or silent (bot doesn't respond to commands, API returns wrong behavior, delete removes wrong record) | Shallow health checks pass (connectivity) but actual feature behavior fails. Most common causes: (1) Docker layer cache reused old binary despite `--from-source`, (2) Code shipped with logic error, (3) Database state wrong or isolation missing, (4) External service state changed. | Test ACTUAL feature behavior after deployment: curl endpoints, invoke Discord commands, test multi-tenant isolation. Do NOT trust health checks alone. If behavior is wrong and committed code looks right, check log startup timestamp (Docker cache symptom). See `references/deployment-health-checks-vs-feature-verification-2026-09-01.md`. |
| `ADMIN_PASSWORD` or critical env var is unset in production, blocking login or feature access | Variable was never set at deployment time, or set to the wrong project/service, or set but service didn't restart. See `references/verify-token-works-before-claiming-success.md` — setting an env var is only the first step; you must redeploy/restart and then TEST the actual change. | (1) Check current value: `railway variable list` and filter/grep for the var name. (2) If unset, set it: `railway variable set VAR_NAME="value" --environment production`. (3) Redeploy: either `railway redeploy --yes` or push a commit (`git commit --allow-empty -m 'apply config' && git push`). (4) Verify live: test the actual feature/endpoint that uses this var with curl. For login credentials, attempt login and check if it succeeds or still fails. Do NOT report success without step 4. Session 2026-09-01: ADMIN_PASSWORD was missing from bot-production-7612, blocking dashboard admin login. Fix required: set the variable + redeploy + test login with curl. |

| Guarded `deployment redeploy --from-source` succeeds (SUCCESS status, container healthy) but still deploys the OLD branch/commit even after the user changed the service's Source branch in the Railway dashboard | `redeploy --from-source` re-triggers a build from whatever source the service is CURRENTLY configured for at the platform level — it does not re-read a just-changed dashboard setting reliably, and a dashboard branch edit does not always propagate to the exact environment/service you're deploying (multi-environment projects are especially prone to this: confirm you edited the SAME project id / environment id / service id that the deploy targets, not a sibling environment). Guarded CLI tooling intentionally refuses to mutate the source-branch config itself (that's a human-authorized platform setting, not a code change). | (1) Merge/cherry-pick the fix onto whichever branch the service is ACTUALLY building from right now (check via the deployment's reported source branch after a redeploy, not just the dashboard) — this ships the fix immediately without fighting the platform. (2) In parallel, ask the user to confirm they edited the exact project/environment/service the deploy targets (paste the three IDs), since Railway dashboards for multi-environment projects make it easy to edit the wrong one. (3) After ANY branch-source change (dashboard or otherwise), don't trust it until a fresh redeploy's reported deployment metadata shows the new branch AND the live commit SHA matches — verify both, not just deployment status=SUCCESS. Session 2026-09-08: BiteWise service kept redeploying from `bitewise/staging` at a stale commit through two guarded redeploys after the user reported switching dashboard source to `main`; fix that actually shipped the change was merging the fix branch directly into whatever branch Railway was observed to be building (staging), rather than waiting on the dashboard edit to take effect. |

## References

- Railway CLI docs: https://docs.railway.app/guides/cli
- `references/multi-tenant-data-isolation-pitfalls.md` — Data isolation bugs in multi-tenant systems: why they happen, how to diagnose, and how to fix. Includes AuthList session 2026-08-31 case study (schema migration + query updates + test coverage).
- GraphQL API: https://railway.app/docs/reference/public-api
- `references/credential-scope-debug.md` — full diagnostic for "Not Authorized" token errors
- `references/setting-service-variables.md` — Setting/updating environment variables on linked services (requires `railway link` first; covers linking pitfalls)
- `references/multi-service-variable-workflow.md` — Complete workflow for setting bot environment variables in multi-service projects, linking to correct project, and verifying deployment (UPDATED: session 2026-08-29, added section on testing token immediately)
- `references/verify-token-works-before-claiming-success.md` — Testing credentials immediately after setting (REINFORCED: session 2026-09-01, added critical env var pattern)
- `references/verify-env-var-before-claiming-success.md` — **CRITICAL**: Setting an env var via CLI is not enough; you MUST test the actual feature. Session 2026-09-01: ADMIN_PASSWORD was set but never verified working, leading to repeated login failures and user frustration. Pattern: set → verify in railway list → redeploy → test with curl/login. Do not report success after redeploy alone.
- `references/docker-image-cache-on-from-source.md` — **CRITICAL**: `railway redeploy --from-source` can reuse Docker layer cache and NOT rebuild, causing the binary to be old despite fresh source. Symptoms: deployment shows SUCCESS but live API returns old behavior, logs show old startup timestamp. Solution: make a REAL code change (not comments), verify startup timestamp is recent, test actual endpoint. Session 2026-08-31 incident: AuthList DELETE CORS fix deployed successfully but API still rejected DELETE due to Docker cache reuse. (NEW: session 2026-08-31)
- `references/project-linking-issues.md` — Diagnosing and fixing `railway link` when it ignores flags or links to the wrong project; CLI project-linking cache issues (REINFORCED: session 2026-08-29, added root cause analysis)
- `references/bitwarden-secrets-integration.md` — fetching `RAILWAY_API_TOKEN` from Bitwarden Secrets Manager (multi-project setups)
- `references/monorepo-subdirectory-deployment.md` — Deploying subdirectories in monorepos: why `railway.json` dir is ignored by `railway up`, and the `--path-as-root` + subdirectory pattern that works (NEW: session 2026-08-30, verified on AuthList project)
- `references/deployment-lag-and-caching.md` — Why code is pushed but service still runs old version: build success vs. deployment completion, container swap delays, diagnosis via logs & timestamps, force restart pattern, verification checklist. CRITICAL: Always verify deployment before reporting success (check logs timestamp, test actual endpoint behavior). (UPDATED: session 2026-08-30, added AuthList incident where CORS DELETE fix was delayed by container swap timing — appeared to be code issue but was infrastructure lag; added verification checklist)
- `references/monorepo-cors-headers-lag.md` — SPECIFIC incident: Monorepo (bot/ + dashboard/) on Railway, code fix pushed + GitHub confirmed + Railway SUCCESS status, but HTTP responses still show old CORS headers. Root cause: container built successfully but not yet promoted to live traffic. Diagnosis checklist: verify commit/build/container startup times to distinguish build lag from code bugs. Wait 2-3 min before testing, or use railway redeploy to force swap. (NEW: session 2026-08-30)
- `references/monorepo-github-webhook-selective-trigger.md` — GitHub webhook on Railway does NOT auto-trigger bot service rebuilds when bot/ files change in monorepo; only triggers dashboard. Root cause: webhook may be filtered to specific directory or service name. Workaround: manually modify files in BOTH bot/ AND dashboard/ directories to trigger both, or use `railway up` with explicit subdirectory. (NEW: session 2026-08-31)
- `references/deployment-health-checks-vs-feature-verification-2026-09-01.md` — **CRITICAL**: `railway redeploy` can show "Deployment successful" and pass all health checks (200 responses, gateway READY, no crash loop) while actual features are broken or silent. Health checks verify connectivity, not behavior. Test actual feature behavior (invoke commands, curl endpoints, test isolation) after every deploy. Session 2026-09-01 incident: AuthList bot deployed successfully but was completely silent to Discord commands; dashboard deployed but delete button deleted wrong record. (NEW: session 2026-09-01)
- `references/railway-environment-setup-staging-deployment-2026-09-06.md` — **CRITICAL**: When creating staging environment, duplicating from production does NOT automatically update the service's git source branch — service remains on `main` by default. Must manually update service Settings → Source to point at feature branch (e.g., `bitewise/staging`). Devops deployments will silently run old code if branch linkage is wrong. Always verify `railway status | grep branch` BEFORE creating devops task. Also: empty-state UIs hide actual page layouts — always seed test data before user review. Session 2026-09-06 incident: Staging environment created but service still pointed at `main` → multiple devops protocol violations → fixed by updating source to `bitewise/staging`. (NEW: session 2026-09-06)
- `references/ambient-env-var-project-shadowing.md` — **CRITICAL**: When Railway CLI runs inside a Railway deployment (Hermes on Railway), ambient env vars (`RAILWAY_PROJECT_NAME`, etc.) silently shadow `.railway/config.json` with NO ERROR, executing commands against WRONG project. Includes diagnosis recipe, fix pattern (unset + re-link + verify), and session 2026-08-31 incident (silent shadowing misdiagnosed as broken webhook). (NEW: session 2026-08-31)
- `references/github-webhook-fallback.md` — fallback deployment pattern when Railway token has limited scope
- `scripts/railway-probe.sh` — automated capability probe (run before claiming no Railway access)
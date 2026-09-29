---
title: Rapid Code-to-Deploy Cycle
name: rapid-code-deploy-cycle
description: Deploy Railway via git push when CLI is scoped.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when deploying code to Railway by pushing to GitHub (fallback when Railway CLI token has workspace scope restrictions).
metadata:
  hermes:
    tags: ["railway", "devops", "git", "deployment"]
    related_skills: ["railway-cli", "github-pr-workflow"]
---

# Rapid Code-to-Deploy Cycle

When you need to modify code and deploy to Railway-hosted projects, and you have GitHub push access but limited/restricted Railway API token scope, use the git-push-based deployment cycle instead of the Railway CLI.

## When to Use

- Railway project is linked to a GitHub repository with auto-deploy enabled
- Your Railway token has limited workspace scope (cannot access all projects)
- You have `gh` CLI access and are authenticated to GitHub
- You need to rapidly iterate: code → commit → deploy without CLI friction
- Typical scenarios: bot shutdowns, lifecycle code changes, quick feature toggles

## The Workflow

### 1. Make Code Changes

Use your file tools (`write_file`, `patch`) to modify code:

```bash
# Example: add bot shutdown logic to a Discord.js bot
# (Use patch or write_file to modify src/index.ts)
```

### 2. Commit Locally

```bash
cd /path/to/repo
git add -A
git commit -m "<conventional commit message>"
```

Commit message should be descriptive but concise:
- `chore: bot leaves all servers on startup and shuts down` ✓
- `fix: resolve auth token scope issue` ✓
- `trigger: restart service` — for empty-commit redeploys (see below)

### 3. Push to Default Branch

```bash
git push origin main  # or 'master', whatever the default is
```

**That's it.** Railway will detect the push and automatically trigger a new deployment.

## Force Redeploy with Empty Commit

When you need to redeploy without code changes (e.g., after a failed deployment or to pick up env var changes):

```bash
git commit --allow-empty -m "trigger: restart <service-name>"
git push origin main
```

Empty commits are lightweight and standard in CI/CD pipelines. They cost nothing but trigger webhooks.

## Greenfield Single-Service Monorepo (API Serves Web)

For a new pnpm TypeScript monorepo (`apps/web` Vite + `apps/api` Fastify) that must go to GitHub empty-repo → Railway single service without CLI scope fights:

1. Ship a root multi-stage `Dockerfile` (base → deps → builder → runner): install with `pnpm install --frozen-lockfile`, build with `pnpm build`, run `pnpm --filter @<name>/api start` with `PORT` from the platform. The API serves `apps/web/dist` via static middleware with an SPA fallback (exclude `/health` and `/api/*` from the fallback) — this avoids relying on Railpack to detect a buildable entrypoint at the monorepo root. Resolve the web-dist path from the COMPILED output location, not the source tree: from `apps/api/dist/` the bundle is `../../web/dist`, one level deeper than it looks from `src/` — compute it with `__dirname` at runtime and assert it exists at boot (or log a clear warning). A green build does not prove the container boots: boot the built `dist/` locally with `PORT` set and curl `/health` plus one real route before pushing.
2. Ship `railway.json` with the Dockerfile builder and a restart policy; keep `DATABASE_URL`/`PORT` out of the repo (document them in `.env.example` and README).
3. Keep the verify-before-push gate: run `pnpm install` then `pnpm verify` (lint + typecheck + tests + build) and push to `main` only on green. A green push is the deploy trigger via the GitHub webhook — never claim Railway is live from `git push` alone; match the deployment to the remote SHA and curl `/health` plus one real route before calling it delivered.
4. Prepare Railway config but do not deploy publicly without explicit scope approval — for a user-owned new repo, hand over "New Project → Deploy from GitHub → pick repo" and let the user connect it.

Pitfall: relying on Railpack auto-detection at a pnpm monorepo root fails with no buildable entrypoint — the Dockerfile single-service shape exists to remove that inference, because the platform builds the declared image instead of guessing the workspace layout.

## Multi-Repo Patterns

When modifying multiple projects in one workflow:

```bash
# 1. Make changes to repo A
cd /root/projects/repo-a
git add -A
git commit -m "chore: update service X"
git push origin main

# 2. Make changes to repo B
cd /root/projects/repo-b
git add -A
git commit -m "chore: update service Y"
git push origin main

# 3. Verify both deployed (check Railway dashboard or logs)
```

Both deployments will start in parallel. Use Railway Dashboard or `railway logs` (if you do have CLI access) to monitor status.

## Failure Recovery

If a deployment fails:

1. **Check logs** — via Railway Dashboard or `railway logs --service <service-name>`
2. **Fix the code** — use your file tools to correct the error
3. **Commit and push again** — the same workflow will retry
4. **Escalate if code is correct** — if logs show no code errors, the failure may be environmental (missing secrets, service dependencies)

## Why Not Use Railway CLI Directly?

The Railway CLI is powerful but requires a properly-scoped API token:
- Tokens generated in the UI often default to "My Projects" (workspace-scoped)
- Workspace-scoped tokens cannot access projects in other workspaces or teams
- Regenerating tokens requires UI access to https://railway.app/account/tokens
- **Solution**: git push → GitHub webhook → Railway auto-deploy requires only GitHub auth, which is easier to verify and debug

See `railway-cli` skill for token troubleshooting if you want to use Railway CLI instead.

## Git Config Prerequisite

Ensure git identity is configured (one-time per session):

```bash
git config --global user.email "<your-email>"
git config --global user.name "<your-name>"
```

If not set, commits will fail with "Author identity unknown". Use any sensible identity (your actual email, your name, or a bot identifier).

## Verification

After pushing, verify the full deployment chain rather than treating a successful `git push` or a healthy endpoint as proof of the requested code being live:

1. **Check GitHub's actual branch tip**: fetch `origin/main` and confirm the requested commit SHA exists there. A local SHA in a handoff can be stale, rewritten, or simply wrong.
2. **Target the exact Railway service**: in a multi-service repository, verify the service name and configured root directory before reading deployments. A healthy dashboard deployment does not prove the bot service deployed (and vice versa).
3. **Match deployment to commit**: confirm Railway's active deployment reports the same remote commit SHA, and that its status is running/online.
4. **Check service logs**: use targeted logs for the exact service to confirm a clean build/start, not just a generic project-level status.
5. **Verify the requested live behavior, not merely the build artifact**: hit the real endpoint or execute a bounded behavior check. For frontend-only changes, first confirm the production asset/bundle hash or content matches the build containing the change, **then validate the rendered behavior in the relevant viewport, route, and state**. Responsive navigation, auth-gated shells, editor-route exceptions, CSS breakpoints, and installed-PWA update timing can all make a byte-identical bundle appear "old" to a real mobile user.
6. **For mobile/PWA releases, use a device-aware check**: validate the intended phone viewport (including standalone PWA where feasible), the authenticated/normal-app route conditions that mount the UI, and the service-worker update path. Asset equality is necessary evidence, not sufficient proof that a user sees the redesign.
7. **When the platform CLI is unavailable, curl is sufficient live evidence**: `/health` ok, plus the live JS bundle filename matching the fresh build and containing a new unique string from the change (download + grep — hash alone does not prove the new code is served). A health-gated startup (the app reports healthy only after migrations succeed) additionally proves startup migrations ran without needing deploy-log access.

See `references/deployment-evidence-chain.md` for a concise evidence checklist and common false positives. See `references/mobile-pwa-release-verification.md` for the rendered-mobile/PWA verification checklist.

## Performance Notes

- **Push-to-deploy latency**: Usually 30-90 seconds from push to live (depends on build time)
- **Parallel deployments**: Multiple repos push in parallel; deployments start independently
- **No manual Railway CLI wait**: You don't need to poll `railway status` — the webhook does the work

## Pitfall: Railway Caching Can Hide Fresh Deployments

**The Issue**: You push code to GitHub, Railway detects the push and starts a build, but the deployed binary doesn't include your changes. This happens when:
- Docker image cache is stale (old compiled binary reused)
- Git clone is cached (old commit SHA checked out)
- Build artifact cache isn't invalidated (old dependencies used)

**Recognition**: New code doesn't appear in logs or behavior, even though:
- Build completed with "SUCCESS" status
- Bot/service is online and responding
- Health check passes
- You added a test marker in code (e.g., "[FIXED]") but it doesn't appear in logs

**Fix**: Force a complete rebuild by:

1. **Empty-commit redeploy** (usually sufficient):
   ```bash
   git commit --allow-empty -m "trigger: force clean rebuild"
   git push origin main
   ```

2. **If that fails**, wait ~2-3 minutes and retry — Railway's webhook may have lag.

3. **If issue persists**, the problem is not caching — it's that your code has a compilation error. Check:
   ```bash
   cd /path/to/repo
   cargo check  # or equivalent build check for your language
   ```
   If code doesn't compile locally, it won't deploy. Fix compile errors first.

4. **Nuclear option** (last resort): Delete the service in Railway Dashboard and recreate it from scratch. This pulls fresh from GitHub and builds from nothing.

**Why it happens**: Railway's Docker build layer caching is designed to speed up deployments, but aggressive caching can hide stale artifacts. The git clone is also cached at the Docker build stage, so even multiple pushes might use the same clone if the Dockerfile doesn't invalidate the cache.

**Verification**: Add a visible marker to logs when testing caching:
```rust
// In bot/src/main.rs or equivalent entry point
tracing::info!("[BUILD_ID: {}] starting bot", env!("CARGO_PKG_VERSION"));
// or
tracing::info!("[TIMESTAMP: {}] starting bot", chrono::Utc::now());
```

If that marker doesn't appear after a rebuild, your code definitely wasn't picked up.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Push succeeds but no deployment starts | GitHub webhook not connected to Railway project | Verify in Railway Dashboard → Project → Settings → Integrations |
| Deployment starts but fails | Code error or missing env vars | Check Railway Deployments tab for logs; fix code, commit, and push again |
| Deployment fails with 'Railpack could not determine how to build the app' | Watched branch holds no buildable app yet (docs/scaffolding only) — expected first-deploy state, not a defect | Do NOT fix-and-push or empty-commit; identical contents fail identically until the app ships — see 'Empty-branch failure' below |
| Deployment succeeds but changes don't appear | Railway Docker/git cache is stale | `git commit --allow-empty -m 'trigger: force clean rebuild' && git push` or delete + recreate service |
| "Author identity unknown" on commit | Git identity not configured | `git config --global user.email "..." && git config --global user.name "..."` |
| Push (incl. empty-commit) starts no deployment within ~2 min | Dead webhook path, not stale cache | Fall back to `railway up --service <svc> --detach` from the repo root, then fix the webhook in dashboard Settings → Integrations; do not keep pushing empty commits |
| `railway up` says 'No linked project found' despite a prior link | Project link is directory-scoped (stored per working directory) | Run `railway link -p <project> -e <env> -s <svc>` from the repo directory first, confirm with `railway status`, then `up` |
| User enabled auto-deploy in the dashboard | Toggles have silently not taken effect before | Verify with a trigger push: a new deployment id must appear in `deployment list`, then curl `/health` — only then call the pipeline working |

## Empty-Branch Failure (No Buildable App Yet)

When a Railway service is freshly linked to a repo whose watched branch contains no buildable app yet (docs, specs, or scaffolding only — no `package.json`, `Dockerfile`, or other entrypoint), the first auto-deploy fails with `Railpack could not determine how to build the app`. Treat this as an expected state, not an incident: read the logs once to confirm the cause, record it, and take no recovery action — neither a code fix nor an empty-commit redeploy changes the outcome, because Railpack infers the builder from branch contents and identical contents fail identically.

While the app is not release-ready, keep all worker branches off the watched branch: merging to it IS the deploy trigger via the GitHub webhook, so branch-only pushes (review first, merge on release approval) prevent unrequested public deployments.

## Staging Environment Alongside Production

When the user wants approved work validated on staging without touching production, use branch-per-env: production service tracks `main`, staging service tracks a `staging` branch. Merging to `main` IS the production deploy trigger, so approved-but-unreleased work lands on `staging` first and production stays pinned until explicit release approval.

```bash
railway environment new staging
railway add --database postgres            # --service naming does NOT apply to plugin databases:
                                           # Railway auto-names it (e.g. Postgres-Ab12) — read the real
                                           # name from `service list` before referencing it
railway add --repo <owner>/<repo> --service <app>-staging
railway service source connect --repo <owner>/<repo> --branch staging --service <app>-staging
railway variable set 'DATABASE_URL=${{<DbService>.DATABASE_URL}}' --service <app>-staging
railway domain --service <app>-staging
```

Verify staging like production: new deployment id, `/health` 200, migration log lines in deploy logs. Keep design-iteration pushes on `staging`; forward to `main` only on release approval.

## References

- `references/railway-docker-cache-workarounds.md` — detailed troubleshooting for stale Docker cache issues (code pushed but not deployed)
- `references/railway-multi-service-coordination.md` — coordinating multiple services (Discord bot + dashboard + database) on a single Railway project
- `railway-cli` skill — direct Railway API access (requires good token scope)
- `github-pr-workflow` skill — GitHub PR workflow if you want to gate changes with CI
- Railway auto-deploy docs: https://docs.railway.app/deployment/github

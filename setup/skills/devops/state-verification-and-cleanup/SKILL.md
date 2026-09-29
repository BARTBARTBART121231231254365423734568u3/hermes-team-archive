---
title: State Verification and Cleanup Workflow
name: state-verification-and-cleanup
description: Maintain repo state, verify each step, never assume success.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when deploying, setting credentials, linking services, correcting project/workspace registration, or making infrastructure changes that require verification.
metadata:
  hermes:
    tags: ["devops", "verification", "state-management", "workflow", "debugging"]
    related_skills: ["railway-cli", "github-pr-workflow"]
---

# State Verification and Cleanup Workflow

A class of infrastructure tasks — deployments, credential management, configuration updates — fail silently or unexpectedly when you:
1. **Lose context** — cloning repos repeatedly, not keeping a working tree around
2. **Don't verify each step** — assume a command worked because it returned exit 0, without testing the actual outcome
3. **Ask the user to verify your work** — reporting "it should work" and making the user test whether you're right
4. **Guess at tool behavior** — trying different CLI flags without reading output or checking where your current state really is

## When to Use

- Deploying to Railway, AWS, or any cloud platform with environment variables
- Setting credentials, tokens, or secrets anywhere
- Linking repos or services to external platforms
- Making changes that require subsequent services to restart
- Any task where "I pushed the code" ≠ "it's live" ≠ "it's using the new config"

## Core Rules

### 1. Keep Your Working Tree Persistent

**Anti-pattern**: Cloning a fresh repo copy for every operation.
```bash
# ❌ WRONG:
cd /root && git clone https://github.com/user/project.git
# ... do work ...
# repo disappears when the session ends or context resets
```

**Pattern**: Clone once at the start of a session and keep it around for all operations.
```bash
# ✅ RIGHT:
cd /root && if [ ! -d project ]; then git clone ...; fi
cd /root/project
# ... all work happens here ...
# repo persists across multiple tool calls and sessions
```

**Why**: Losing your repo directory means you lose context (current branch, git history, uncommitted changes). You'll re-clone, which can pull stale code if the push didn't succeed, and you waste time re-reading files.

### 2. Check Current State BEFORE Acting

Every operation should start with a state probe, not an assumption.

```bash
# BEFORE you set a credential:
echo "Current state:"
env | grep -E 'API_TOKEN|RAILWAY' | head -10
ls -la ~/.railway/ 2>/dev/null | head -5

# BEFORE you claim the bot is using a token:
curl -s https://bot-production.up.railway.app/api/protected \
  -H "Authorization: Bearer $TOKEN" -w "\nHTTP: %{http_code}\n"
# Must be 200, not 401

# BEFORE you deploy:
git status  # Verify no uncommitted changes, or that you're on the right branch
railway status  # Verify you're linked to the RIGHT project
```

Before creating implementation worktrees, prove that the configured project baseline is the intended remote and production lineage:

```bash
hermes project list
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git merge-base --is-ancestor <production-sha> HEAD
git log --all --decorate --oneline --graph -20
```

If local `main` differs from the intended remote or production SHA, do not let a project-linked task silently inherit local `main`. Create an explicit worktree from the verified remote revision, verify its `HEAD`, and route the task to that exact directory. Compare the actual target files at both revisions before coding; a worktree can be syntactically healthy while containing an older navigation, settings, or release architecture.

**Why**: A huge portion of failures come from wrong assumptions about where things are configured. Checking state takes 10 seconds and prevents 10 minutes of debugging; proving ancestry before dispatch prevents entire worker/review/deploy chains from operating on the wrong application state.

### 3. Verify Each Step Produces an Observable Outcome

Never assume a command worked because it didn't return an error.

```bash
# ❌ WRONG:
railway variable set API_TOKEN="$TOKEN"
echo "Token set!"
# You don't know if it actually succeeded or was set on the wrong project

# ✅ RIGHT:
railway variable set API_TOKEN="$TOKEN"
sleep 2  # Give the API time to persist
railway variable list | grep -q API_TOKEN || { echo "FAILED: Token not found"; exit 1; }
echo "✅ Token verified in Railway config"

# Then deploy
railway redeploy --yes
sleep 120  # Redeployment takes time

# Then TEST the actual outcome
curl -s https://bot.up.railway.app/api/tenants \
  -H "Authorization: Bearer $TOKEN" -w "\nHTTP: %{http_code}\n" > /tmp/test.txt
grep -q 'HTTP: 200' /tmp/test.txt || { echo "FAILED: Token does not work"; exit 1; }
echo "✅ Token verified WORKING in live service"
```

**Pattern for credentials specifically**: See `railway-cli` skill → `references/verify-token-works-before-claiming-success.md`.

**Why**: This session spent an hour on an invalid token because I set it but never tested if it actually worked. The user had to tell me 5 times it didn't work.

### 4. CRITICAL: Verify Against the Actual Source of Truth, Not Local Files

**Major error pattern from session 2026-08-31:**

When diagnosing whether code is deployed or if a feature exists, ALWAYS verify against the actual remote source (GitHub, production logs, deployed API response), NEVER assume local files match the remote.

```bash
# ❌ WRONG:
cd /root/AUTH_LIST_RUST
grep -r "DELETE" bot/src/api/routes.rs
echo "✅ DELETE is in the code!"
# You have checked LOCAL files. But the user's GitHub repo might have:
# - Old code (local is newer)
# - Different code (local is from a different branch or old clone)
# - No feature at all (local files were never pushed)

# ✅ RIGHT:
# Check the ACTUAL remote that matters (GitHub repo, production API, live deployment)
curl -s https://api.github.com/repos/user/project/contents/bot/src/api/routes.rs?ref=main | \
  grep -q 'DELETE' && echo "✅ DELETE is in GitHub main" || echo "❌ NOT in GitHub"

# Or if it's a deployed service:
curl -s https://bot-production.up.railway.app/api/servers \
  -X OPTIONS -H "Access-Control-Request-Method: DELETE" -w "\n" | \
  grep -i 'access-control-allow-methods' | grep -q DELETE && \
  echo "✅ Service accepts DELETE" || echo "❌ Service does not accept DELETE"
```

**Why**: This session, I checked local `/root/AUTH_LIST_RUST/bot/src/api/dashboard.rs` and claimed the feature was built and committed, but the user showed me a screenshot proving it doesn't exist in the actual GitHub repo. I had looked at files from a different machine, old local uncommitted changes, or a completely different project — without verifying against the actual source.

**Recovery pattern**:
1. If the feature should exist: check the actual GitHub remote (`git show origin/main:path/to/file | grep feature` OR curl the GitHub raw content)
2. If it's a deployment issue: test the actual live API (curl the deployed endpoint and check response headers/behavior)
3. If checking code existence: NEVER stop at local files — always verify the remote first
4. When confused, ask: "What is the source of truth for this check?" (local code? GitHub? deployed API?) and verify THAT source

## CRITICAL: Infrastructure Verification ≠ Visual Verification for UI Redesigns

**Session 2026-09-04 hard lesson**: A UI redesign or major frontend feature release can pass every infrastructure check and still serve the old layout to end users.

**The trap**:
- Railway deployment status: SUCCESS ✅
- Deployed artifact hashes match source: verified ✅
- Service-worker manifest and assets: HTTP 200 ✅
- All infrastructure gates clear ✅
- **User opens app on phone:** old layout, no redesign ❌

**Why it happens**: The source tree integration was incomplete, the build produced a stale artifact, route-level conditions prevent rendering, or CSS breakpoints hide the component at the user's actual viewport.

**Fix (immediate)**:
1. **Render-verify against production in a mobile viewport using headless/background tooling by default.** Never open, focus, navigate, or duplicate tabs in the user's visible browser unless the user explicitly asks to watch; verification must not interrupt their desktop.
2. **Compare actual production HTML to source at the deployed commit SHA** (curl the live index vs git show).
3. **Check if the compiled bundle includes the redesign component** (curl app bundle + grep for key strings).
4. **Test at the actual phone viewport dimensions** and capture a background/headless screenshot as evidence; use a physical foreground device only when explicitly authorized or when no equivalent check exists.
5. **Reuse one isolated browser context for all required routes** and close only the pages/context the verification created; opening one visible tab per route is intrusive and unnecessary.
6. **If redesign is missing**: source integration incomplete (re-integrate + redeploy) OR build produced stale artifact (force clean rebuild).

**Pattern for any major frontend release**: Deploy → **immediately render-verify in the target viewport, invisibly by default** → only then report done. Do not ask users to verify; use background browser automation, curl, DevTools, and bundles without disturbing the user's active browser session.

See `references/mobile-pwa-release-verification.md` for full render-verification checklist for PWA deployments.

## Verification Tool Output Against Expected Behavior

When a tool behaves oddly or you're unsure, READ the output, don't guess.

```bash
# ❌ WRONG:
railway link -p authlist-bot
# ... and then blindly assume it linked to authlist-bot

# ✅ RIGHT:
railway link -p authlist-bot
railway status 2>&1 | grep -i "Project:"
# Output: Project: authlist-bot ✅
# or      Project: worthy-healing ❌ (WRONG PROJECT! Retry)
```

**Why**: In this session, `railway link -p authlist-bot` silently linked to `worthy-healing` instead. The only way to catch this was to check `railway status` output. The `-p` flag was ignored due to cached config, but the command "succeeded" with exit 0.

## Correcting Tool-Managed Project or Workspace Paths

Treat a project registry as external state, not as a text file to edit blindly:

1. Read the live record first (`hermes project show <slug>` or the equivalent tool-specific inspect command).
2. Read the relevant subcommand help before mutating (`hermes project add-folder --help`, `remove-folder --help`, `set-primary --help`) so the update uses the supported registry API.
3. Add the canonical existing folder and mark it primary in one operation when supported:
   ```bash
   hermes project add-folder <slug> 'C:/absolute/path/to/repo' --primary
   ```
4. Read the live record back with `hermes project show <slug>` and verify both the primary path and folder list. Do not infer registry state from exit code alone.
5. Update any durable team/project record that repeats the path, including deployment-manifest references, so discovery and documentation do not disagree.

**Pitfall:** Interpret each field by its label before deleting it. An indented legacy-looking string may be a folder label or annotation rather than a second registered folder; trying to remove it as a path can fail while the actual registry is already correct.

## Debugging Checklist for "It Should Work But Doesn't"

When a step should have worked but the next step fails:

1. **Check where state is actually stored**
   ```bash
   # For credentials:
   env | grep -i token
   cat ~/.config_file | grep -i token
   
   # For repo links:
   git remote -v
   cat ./.project/config | grep -i linked
   railway status  # Shows actual linked project
   ```

2. **Check if service restarted**
   ```bash
   # For deployment-based changes:
   service_logs | grep -E 'starting|initialized|ready' | tail -1
   # Timestamp should be recent (last 2 minutes), not hours ago
   ```

3. **Check if the change is actually being used**
   ```bash
   # For tokens:
   curl -s https://service/protected -H "Auth: Bearer $TOKEN" -w "\nHTTP: %{http_code}\n"
   # Must be 200, not 401/403
   
   # For config changes:
   curl -s https://service/health | grep -i "token\|config"
   # Should show new value or timestamp
   ```

4. **Check logs for actual errors**
   ```bash
   railway logs 2>&1 | grep -i "error\|failed" | tail -20
   # Often shows the real problem (file not found, parse error, etc.)
   ```

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong | Fix |
|---|---|---|
| "I set the variable, so it should work now" | Setting ≠ deployment ≠ service using it ≠ tested | Test with curl immediately after |
| "The command didn't error, so it worked" | Commands return 0 even when they silently fail (wrong project, cached config, etc.) | Verify output explicitly, not just exit code |
| "I'll ask the user to test if it works" | You can test it. The user shouldn't have to verify your work. | Always test credentials/deployments yourself before reporting success |
| "I cloned the repo fresh for this task" | Fresh clone = lost context, stale code, re-reading files | Keep one persistent working tree per project |
| "I tried command A, it didn't work, so I tried command B" without checking output | Debugging blind = spinning wheels. You don't know WHY A failed. | Read and understand the error message before trying alternatives |
| "The tool must be broken" | Almost never true. Usually the tool is working, but not for your current state. | Check: Is the credential scope right? Is the project linked? Did the service restart? |

## Workflow Template

For any deployment or credential operation:

```bash
set -e  # Exit on error

# 1. STATE CHECK
echo "=== CURRENT STATE ==="
railway status 2>&1 | head -5
env | grep -E 'TOKEN|API' | sed 's/=.*/=<redacted>/'

# 2. OPERATION
echo "=== APPLYING CHANGE ==="
railway variable set KEY="$VALUE" --environment production
echo "Variable set via CLI"

# 3. VERIFY PERSISTENCE
echo "=== VERIFYING PERSISTENCE ==="
railway variable list | grep -q KEY || { echo "FAILED: Variable not in list"; exit 1; }
echo "✅ Variable persisted to Railway config"

# 4. TRIGGER DEPLOYMENT
echo "=== DEPLOYING ==="
git commit --allow-empty -m 'force: apply env change' && git push origin main
echo "Pushed. Waiting for deployment..."
sleep 120

# 5. VERIFY LIVE BEHAVIOR
echo "=== TESTING LIVE SERVICE ==="
TEST_RESULT=$(curl -s https://service/protected -H "Authorization: Bearer $VALUE")
echo "$TEST_RESULT" | grep -q 'success' || { echo "FAILED: Service not using new value"; exit 1; }
echo "✅ Service verified using new credential"

echo ""
echo "=== SUCCESS ==="
echo "Credential is live and working."
```

## Hermes Model and Dispatcher Changes

1. Inventory each profile default, provider, credential fallback order, and the live routing policy before editing. Verify candidate model IDs with a real provider request; a plausible tier name is not proof of availability. Preserve independent-account fallback order and explicit task pins.
2. Apply profile defaults separately from dispatcher routing. For a fresh unpinned worker, compare the run-linked `model_routing` event with the responding session's `session_meta.model` and provider; a successful smoke response alone can come from the profile default while the routing hook never ran. Report LOW/HARD as policy-only if only MEDIUM received an end-to-end probe.
3. Before a gateway-hosted dispatcher patch, check active workers, back up target files and configuration privately, and determine whether the operator process is inside the gateway service cgroup. For a scheduled backup prerequisite, inspect the job's resolved data root and the *archive*, not just the scheduler's `ok`: assert that the manifest names the live database and configuration, validate copied SQLite databases with `PRAGMA integrity_check`, and prove an isolated restore. A successful archive of an empty or obsolete data root is not a backup. Perform the controlled stop/install/start from an independent process outside that cgroup; an embedded worker cannot safely stop its own parent service. On a systemd user host, first prove a separate transient operator unit can launch with `systemd-run --user --wait --collect --pipe --unit <preflight-name> /usr/bin/true`; check its cgroup separately from the gateway's before entrusting it with a bounded, fail-closed restart. Preserve all drain, backup, exact-revision, rollback, and approval checks in the external operator—never fake a human TTY or treat a successful preflight as a successful restart. Before launching a drain-waiting operator, inspect the gateway cgroup and classify persistent idle session kernels separately from active workers; a literal zero-child condition may never become true while idle tool kernels remain. Check every Kanban board layout used by the runtime, not only top-level database files, or a drain and snapshot can miss running work. Do not set an outer subprocess timeout that can kill a restart operator mid-change before its rollback handler runs. After launch, inspect the operator's progress and exact wait condition promptly; a running unit proves only that it is alive, not that a restart has begun. If a drain wait stalls, compare the live gateway cgroup with Kanban's running tasks and classify each child by parent, command, and wait state before changing the predicate—idle session kernels and productive workers require different handling. Never launch a second restart operator while the first can still mutate state; first prove the predecessor is finished or enforce a fail-closed predecessor gate, then read the operator's result artifact before reporting progress. If activation is deferred until the scheduled backup, have the independent operator recheck that exact run and artifact at wake time and fail closed if absent; a timer by itself is not evidence of a safe restart. Confirm inactive before applying, restore service on failure, then check live status and a fresh worker response. When the user has explicitly authorized execution and is frustrated by repeated attempts, avoid a string of preparatory status updates: either carry the external operator through live verification or state the single actual blocker without suggesting readiness. Do not equate gateway health with messaging transport delivery.
4. When a reviewed installer or patch lives in a separate repository from the authoritative project, distinguish deployment-local code from Git ancestry. Do not force a cherry-pick to manufacture ancestry or declare the project worktree stale solely because it lacks the patch commit. Continue isolated source work from its verified base, and explicitly require later source-to-runtime integration to preserve the live hook and repeat the routing smoke.

## SSH Migration Access: Match Account and Key Explicitly

Before dispatching a server migration, prove the exact login tuple independently:

1. Verify the server host fingerprint out of band, then record it in `known_hosts`.
2. Treat Linux usernames as case-sensitive; obtain the actual account name rather than inferring it from a person's name.
3. Inventory local public keys and pair each public key with its matching private-key filename. A key comment such as `windows-pc` is only a label, not the filename SSH will automatically select.
4. Test the intended tuple explicitly so agent/default-key behavior cannot mask a mismatch:
   ```bash
   ssh -i /path/to/private_key -o IdentitiesOnly=yes -o BatchMode=yes user@host 'id; printf "HOME=%s\n" "$HOME"; sudo -n true'
   ```
5. Only after that probe succeeds, inventory OS, architecture, disk, required tools, and privilege level, then release the migration worker.

**Pitfall:** Do not rotate keys or repeatedly rewrite `authorized_keys` when authentication fails until you have tested every documented account/key pairing explicitly—the correct key may already be installed for a different case-sensitive account.

Never paste private keys, passwords, or secret values into chat or task metadata. Public keys and fingerprints are safe to exchange, but keep secret transfer in an authenticated channel.

## Status Reporting During an In-Flight Deploy

When a user asks for a status update while a worker or deployment is still running, report the **highest verified stage** only. Separate completed facts from pending gates; do not collapse them into “fixed.” A heartbeat proves only that the worker process is alive; inspect destination artifacts, logs, or external state before claiming transfer or implementation progress. If no artifact exists yet, say plainly that preparation is active but execution has not started.

Use this sequence for code-to-production work:

1. **Implementation:** changed locally or committed.
2. **Source control:** pushed, PR merged, or otherwise present in the intended remote branch.
3. **Automated checks:** name the test/build command and its real result.
4. **Deployment:** queued, building, failed, or live — include an ID only when returned by the platform.
5. **Production verification:** confirm the exact live behavior or log evidence required by the task.

A good concise update looks like:

> Code is committed and pushed. `cargo test` passed (60 tests). Railway deployment `<id>` is building. The remaining gate is production log verification that OAuth checks the tenant’s configured guild; it is not ready for a user retry yet.

Do not say “fixed,” “ready,” or ask the user to retry until stage 5 is complete. Conversely, do not bury tangible progress behind vague phrasing such as “the agent is working”: tell the user exactly what has landed and what is still being verified.

## CRITICAL: Database Cleanup Tasks Must Be Handed Off to Devops

**Session 2026-09-02 correction**: When discovering stale or corrupted data in a production database, DO NOT attempt to write your own fix script or Rust binary. This is devops work.

**Why**: You lack direct database access in production containers, lack installed database tools (sqlite3, psql), and lack the ability to verify fixes immediately. Devops has all of these — let them do it. The handoff saves 2,000+ tokens and 30+ minutes of failed attempts.

**Pattern**:
```python
# When you find stale data:
kanban_create(
  title="Clear stale X from member record",
  assignee="devops",
  body="Member discord_id=ABC has field_name='stale_value' but should be NULL/default. Update and verify."
)

# When you find one anomaly:
kanban_create(
  title="Audit database for more instances of stale X",
  assignee="devops",
  body="One member had stale steam_id64. Query the entire members table. Are there more? Report counts."
)
```

Do NOT assume isolation. Always request an audit when data quality issues appear.

See: `references/database-cleanup-handoff-patterns.md` (Session 2026-09-02 detailed example with token cost analysis).

## References

- `references/database-cleanup-handoff-patterns.md` — Handoff patterns for data cleanup; when NOT to build fixes yourself
- `references/multi-agent-coordination-production-fixes.md` — Multi-agent coordination under production pressure
- `railway-cli` skill → `references/verify-token-works-before-claiming-success.md` — Testing credentials immediately after setting
- `railway-cli` skill → `references/project-linking-issues.md` — Diagnosing `railway link` when it links to the wrong project

## CRITICAL Session 2026-08-31: Verifying Against Local Files is Unreliable

This session, I spent 2+ hours "diagnosing" a Railway build cache issue for the AuthList bot's DELETE endpoint. My evidence:
- Checked local `/root/AUTH_LIST_RUST/bot/src/api/dashboard.rs` — found DELETE handler
- Checked local `bot/src/api/routes.rs` — found `.allow_methods([..., DELETE, ...])` 
- Claimed the feature was implemented, committed, and in GitHub
- Blamed Railway for not rebuilding the code

The user showed me a screenshot from another AI session that had already tried and failed this same diagnosis. That session ALSO checked local files and reported the feature was built. It wasn't.

**The actual truth**: The DELETE feature was never actually built or committed to the repo. The local files on THIS machine (a different machine than the user's) contained code that doesn't exist in the user's GitHub repo.

**Lesson**: When diagnosing "why isn't this deployed", NEVER stop at checking local files. Local files can be:
- Old (from a prior failed checkout)
- From a different branch
- From a different machine entirely
- Uncommitted local changes
- From a completely different project

Always verify the ACTUAL source of truth:
- For code: `git show origin/<branch>:path/to/file` or curl the GitHub raw URL
- For deployment: test the actual live endpoint with curl (HTTP status, response headers, behavior)
- For builds: check the actual build logs from the CI/deployment service, not local build attempts

This is now a first-class verification rule in this skill, embedded in Section 4 above.

## Key Learning from Session 2026-08-29

In one session working on a Discord bot deployment, I:
1. Set a credential and told the user "it should work now"
2. The user said "it still doesn't work"
3. I made them test my work 5 times before I tested it myself
4. When I finally tested, it didn't work because the credential was set on the wrong Railway project
5. The root cause was that `railway link -p authlist-bot` silently linked to `worthy-healing` instead
6. I only caught it by reading `railway status` output, which I should have done immediately

**The lesson**: You have the tools to verify your work. Use them BEFORE you tell the user anything "should" work. This saves time, prevents frustration, and catches bugs early.

The user's explicit feedback: "i dont know why you just dont test these things urself". This became the core philosophy of this skill — **assume nothing, verify everything**. Never ask the user to test your work; you have curl, logs, and APIs. Use them.

## Pitfall: Editing an Already-Applied Migration File Breaks Every Deployment

sqlx (and most migration frameworks — Flyway, golang-migrate, Django in strict mode) checksum each applied migration by its exact file content. If a migration has already run against the production DB and you edit that file afterward — even a **comment-only change**, even fixing a typo — every existing deployment's checksum check fails and the process refuses to boot:

```
Error: migration N was previously applied but has been modified
```

This looks like an unrelated crash (502, container restart loop) and is easy to misdiagnose as a code bug in the surrounding feature, when the actual diff is cosmetic.

**Rule**: never touch a migration file that has already shipped, for ANY reason, including comments. If a column's documentation is stale, either:
- Leave the comment as-is (harmless drift), or
- Add a NEW migration file with an `ALTER TABLE ... COMMENT` if the DB supports it, or a fresh no-op migration with a code comment explaining the correction (SQLite has no column-comment ALTER — in that case just leave it).

**Recognition**: if a deploy that touched a `migrations/` directory suddenly crash-loops right after boot with a schema/checksum-sounding error, `git diff` the migrations directory specifically first — before looking anywhere else — and revert any edit to an already-applied file.

**Recovery**: revert the migration file to its exact previous content (`git show <last-good-commit>:path/to/migration.sql > path/to/migration.sql`), rebuild, retest, redeploy. Do not try to "fix forward" by editing the migration again — that's the same mistake repeated.

## Pitfall: Verifying Backend Success Without Testing End-User Path

**Session 2026-09-01 example**:
- Devops reported: "ADMIN_PASSWORD is set and verified working. POST /api/auth/login returns HTTP 200 with a valid token."
- User reported: "I'm getting 'Invalid username or password' when I try to login."
- Agent assumed: Devops was right (backend API works), user is entering wrong password, proceed to debug user input.
- Reality: The PASSWORD WAS WRONG. Devops tested with the wrong password string, or the password they tested with differs from what's set in production, or there's environment variable shadowing.

**Rule**: When testing a credential:
1. Set the credential via the tool
2. Verify it persisted: read it back from the service config (e.g. `railway variable list | grep ADMIN_PASSWORD`)
3. **Confirm the service has restarted** (deployed the new var; check logs or redeploy status)
4. Test with the EXACT string you set (not a copy-paste that might have whitespace differences)
5. Test from an end-user perspective if possible (actually log in, not just API status)

**What went wrong here**:
- Devops set `ADMIN_PASSWORD="newpass"`
- Devops tested `curl ... -H "Authorization: Bearer newpass"` — might not match how the frontend sends it
- Frontend uses a form POST to `/api/auth/login` with body `{"username":"admin","password":"newpass"}`
- These are subtly different (Bearer vs form body, URL encoding, header parsing differences)
- Devops never tested the actual frontend login path that the user uses

**Fix**: After setting any credential, test it via the ACTUAL client path:
- For a password: try logging in with the frontend (or `curl -X POST ... -d '{"username":"admin","password":"...'}`)
- For an API token: call a protected endpoint exactly as the client app would
- For a webhook secret: send a real webhook request and check logs

Do not just test generic API access — test the exact flow the user will use.

## Pitfall: Kanban Worker Crash-Loops (rc=0, No Terminal Call) — Verify the Workspace Before Respawning Again

A dispatched worker can do the CORRECT work and still "fail" purely on the reporting side: it exits cleanly (rc=0) without calling `kanban_complete`/`kanban_block`/`kanban_request_review`. The dispatcher logs this as a protocol violation and respawns. If this repeats 3-4x on the same task, do NOT keep blindly respawning a 5th time — that burns tokens for zero new progress, since the same worker profile tends to repeat the same behavior.

**Correct recovery** (as coordinator):
1. `cd` into the task's actual workspace and inspect it directly (`git status`, `git diff --stat`, `git log`). The finished work is very often sitting there uncommitted — the worker did the job, it just never reported.
2. Independently verify: run the project's real build/test command yourself (e.g. `npm run build`, the repo's own regression script) against what's in the workspace.
3. If it verifies clean, finish the task yourself — commit, push, and call `kanban_complete` with metadata noting the crash-loop and that you (the coordinator) independently verified and closed it out. Do not fabricate verification; only close it if you actually ran the checks and they passed.
4. If the workspace is empty/incomplete, inspect startup logs and task configuration before replacing it. Verify the assigned profile can load every forced skill, the workspace path exists, and the workspace `HEAD` is the intended remote/production ancestor. A fresh task on an unverified project default can faithfully repeat the same failure or edit the wrong codebase.
5. After two empty-workspace crashes, stop automatic replacement chains. Either take over the already-defined narrow work in a verified exact-base worktree and run the checks yourself, or surface a capability blocker. Do not create another implementation/review/deploy tree merely to retry process startup.

This turns a pure-reporting failure into a same-turn resolution instead of a multi-hour respawn loop.

### Verify Dispatch Prerequisites Before Diagnosing a Worker Crash

Before creating a routed task with forced skills, verify every requested skill is available to the assigned profile. An unknown forced skill can terminate the process before task execution begins, which the dispatcher may surface only as a dead PID.

For an immediate worker exit:
1. Inspect the task's startup stderr/log before respawning; classify startup-argument failure separately from implementation failure.
2. Remove or replace unavailable forced skills, then create one clean recovery run with the same exact task contract.
3. Distinguish four independent states in status reports: profile/gateway available, task worker alive, code integrated, and code deployed. Never use evidence from one layer to claim another.
4. If a recovery worker produces a verified remote release candidate, stop duplicate local verification processes and advance the existing artifact to review rather than rebuilding it again.

## Pitfall: Batching Many Parallel Kanban Writes Can Wedge the Tool Layer

Firing off 10+ `kanban_block`/`kanban_create`/`kanban_show` calls in one parallel batch (e.g. bulk-closing a stale task cluster) has been observed to overload the board's plugin callback and wedge the ENTIRE tool layer — not just kanban, but terminal and other tools too — for an extended period, sometimes only clearing after the underlying process/container is restarted by the user.

**Rule**: when cleaning up more than ~5 stale tasks at once, batch writes in small groups (3-4 at a time) with a pause, rather than one giant parallel call. If a call starts erroring with "can't start new thread" or "pre_tool_call plugin callback timed out", STOP issuing more kanban calls immediately — retrying identical calls into a wedged backend does not help and wastes turns. Report the outage honestly, and confirm recovery with one cheap probe (e.g. `terminal("echo test")`) before resuming board operations, rather than assuming a fix.

## Pitfall: Deployment Guards Refusing Source-Config Mutations Are a Hard Wall, Not a Bug

A guarded deploy tool (e.g. `railway deploy-verified ... --apply`) may successfully redeploy the correct commit and confirm production is healthy, yet still leave a cosmetic platform-metadata field wrong (e.g. Railway's stored "source branch" label staying on an old branch name after a `redeploy --from-source`, because that call preserves the service's configured source and only guarded config-mutation calls could change it, which the guard intentionally blocks). Do not try to force this through terminal/CLI workarounds — changing a deploy target's source configuration is exactly the kind of mutation the guard exists to gate to a human. Report it as a known cosmetic gap requiring a manual dashboard change, not as a failure to keep retrying.

## Pattern: Merging Multiple Parallel PRs That Touch the Same Files

When several independent branches (e.g. security fix, code-quality pass, design fix from different specialist agents) are all based on an older commit and all touch overlapping files, merge them serially with a full verify between each — don't batch-merge and hope:

1. Merge/rebase branch A onto current main, resolve conflicts by understanding BOTH sides' intent (not blindly taking "ours" or "theirs") — read the surrounding function to see which version is structurally correct post-merge.
2. Full build + full test suite (not just `cargo check` — actually run `cargo test` / `npm run build`, since compile success doesn't catch behavior regressions in merged logic).
3. Push, merge to main, deploy, verify live (health check + a real functional request), THEN move to branch B — never merge B before A is confirmed live and healthy.
4. Rebase B onto the now-updated main (it will likely conflict with A's changes to the same files) and repeat the same verify cycle.

This catches cross-branch integration bugs (e.g. two branches independently touching the same match arm) before they reach production, and keeps the failure surface to one branch at a time if something breaks.

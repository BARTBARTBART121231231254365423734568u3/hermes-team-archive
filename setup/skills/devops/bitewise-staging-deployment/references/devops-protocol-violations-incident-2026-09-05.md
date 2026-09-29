# Devops Protocol Violations: Incident Analysis & Workarounds

**Session:** 2026-09-05 BiteWise Staging & Production Deployment  
**Pattern:** Devops tasks exiting cleanly (rc=0) without calling kanban_complete or kanban_block — protocol violation occurs 2+ times on the same task or recurring task, causing silent failures in Infrastructure operations.

## Symptoms

- Devops task shows status `running` or `ready`, then suddenly transitions to blocked with no explanation
- Task output shows: `worker exited cleanly (rc=0) without calling kanban_complete or kanban_block — protocol violation`
- Multiple retry attempts (3-5 runs) all hit the same pattern
- Actual work (deployment, environment variable setting) may have partially succeeded despite the crash
- Manual verification confirms the deployment completed despite the protocol violation

## Root Causes Identified (2026-09-05)

### 1. Git Source Branch Mismatch (PRIMARY — 2 incidents)

**Scenario:** Staging service in Railway is linked to the wrong git branch (e.g., `main` instead of `bitewise/staging`).

**Behavior:**
- Devops attempts to redeploy
- Railway builds and deploys the service
- But deployment is of the WRONG branch (old code)
- Devops likely detects mismatch and exits, but kanban_complete not called
- Multiple retries hit the same mismatch

**Fix:**
```bash
# Manual verification
railway status --project BiteWise --environment staging | grep -i "branch\|source"
# If output shows main or incorrect branch, STOP and fix before deploying

# Correct the branch in Railway dashboard or via API
# Then create a FRESH devops task (don't retry the old one)
```

**Prevention:** Before creating devops deployment task, verify the service is linked to the correct branch:
```bash
railway status --project <project> --environment <env> | grep -i source
```

### 2. Environment Variable Missing or Misconfigured (SECONDARY — 2 incidents)

**Scenario:** Task requires an environment variable (e.g., SETUP_TOKEN) that's not set, has wrong format, or has a value mismatch.

**Behavior:**
- Devops attempts deployment
- Environmental checks fail (missing var, validation error)
- Devops exits cleanly (found the blocker, but doesn't report it explicitly)
- Retry attempts all fail on the same blocker

**Fix:**
```bash
# Check current env var
railway variable list --environment staging | grep SETUP_TOKEN

# Set or correct it
railway variable set SETUP_TOKEN=test --environment staging

# Redeploy
railway redeploy --yes
```

**Prevention:** Always verify environment variables are set BEFORE creating devops deployment task:
```bash
railway variable list --environment <env> | grep -E "SETUP_TOKEN|DATABASE_URL|..."
```

### 3. Dispatcher Livelock (TERTIARY — seen when multiple quick retries)

**Scenario:** Devops task hits protocol violation, gets requeued. User or orchestrator immediately creates a new task (or retries old one). Dispatcher is still processing the prior run.

**Behavior:**
- New devops task sits in `ready` indefinitely, never picked up
- Devops dispatch queue appears stuck
- Creating priority 100 "pickup signal" task helps, but not guaranteed

**Fix:**
- Don't retry the same failing task (protocol violation = stale task)
- Create a FRESH devops task with full context
- Use priority 100
- If still not picked up after 2+ minutes, create a "pickup signal" card

## Workaround Pattern (Proven 2026-09-05)

When devops protocol violations occur:

### Step 1: Identify Root Cause Manually

```bash
# Environment setup check
railway status --project BiteWise --environment staging
# Verify:
#   - Environment is staging, not production
#   - Service is Online
#   - Git source branch matches expected
#   - Recent deployment timestamp is recent (not stale)

# Environment variable check
railway variable list --environment staging | grep -i "setup_token|database|api_url"

# Deployment logs check
railway logs --latest --lines 50 | grep -i error
```

### Step 2: Fix the Infrastructure Issue

Common fixes:

**Wrong git branch:**
```bash
# Update service source in Railway dashboard:
# Project → Service → Settings → Source → Branch → select bitewise/staging
# Or via API/CLI if available
```

**Missing or wrong env var:**
```bash
railway variable set SETUP_TOKEN=test --environment staging
railway redeploy --yes
```

**Service pointing to wrong source:**
```bash
railway redeploy --yes  # May re-detect correct branch on re-deploy
```

### Step 3: Create Fresh Devops Task (Don't Retry Old One)

The old task is now in protocol-violation deadlock. Create a NEW task:

```
Title: [RETRY] Deploy BiteWise redesign to staging (infrastructure fixed)
Assignee: devops
Priority: 100
Body:
  Infrastructure issue resolved:
  - [X] Staging git source corrected to bitewise/staging
  - [X] SETUP_TOKEN env var set to test
  - [X] Service points to correct branch
  
  Task: Deploy bitewise/staging to Railway staging environment
  ...[rest of body]
```

### Step 4: If New Task Still Sits in Ready

Create an explicit "pickup signal" task:

```
Title: URGENT: Pick up deployment task [ID]
Assignee: devops
Priority: 100
Body: Deployment task is ready. Pick it up NOW.
```

This acts as a dispatcher nudge and often forces devops into the work queue.

## Manual Verification Workflow (Proven 2026-09-05)

When you suspect devops work may have succeeded despite the protocol violation:

```bash
# Check if deployment actually happened
curl -s https://bitewise-staging.up.railway.app/api/health
# If returns 200, API is online — deployment likely succeeded

# Check deployment timestamp in Railway
railway status --project BiteWise --environment staging | grep -i "deployment\|timestamp"

# Verify the service is running the correct branch
railway logs --latest --lines 10 | grep -i "cloning\|checkout\|bitewise/staging"
```

If work actually completed:

```bash
kanban_complete --task_id <devops_task_id> --summary "Devops task completed despite protocol violation. Verified: API online, deployment timestamp recent, correct branch deployed."
```

## Prevention Checklist

Before creating ANY devops deployment task:

- [ ] Target environment exists in Railway (e.g., staging, production)
- [ ] Target environment has a service linked
- [ ] Service has volumes/persistence configured (if needed)
- [ ] Required environment variables are set: `railway variable list --environment <env>`
- [ ] Git branch to be deployed exists and is pushed: `git branch -a | grep <branch>`
- [ ] Service source is linked to correct git branch (verify in Railway dashboard)
- [ ] No prior devops task for this same operation in blocked/protocol-violation state

## Timeline: Session 2026-09-05

1. **t_cdbe123e** (deploy to staging) — protocol violation after missing environment
2. **t_3e69cd79** (deploy to staging) — protocol violation, environment was created but missing from task context
3. **t_a85e70c8** (deploy to staging) — SUCCESS after coder merged branches
4. **t_1e93f7ac, t_0e85a07f** (cleanup, env var setup) — mixed success/protocol violations
5. **t_c544166d** (SETUP_TOKEN fix) — devops verified env var set, but form still failed
6. **t_ac3c313a** (database debugging) — protocol violation, but work was actually done (database fine)
7. **t_6c42f713** (API debugging) — protocol violation, but diagnosis was correct (backend OK)
8. **t_02f3864b** (frontend API_URL config) — coder found root cause (not frontend, backend issue)

Pattern emerges: Devops protocol violations are common when infrastructure has blockers, but work often completes despite the crash. Manual verification is always required.

## Related Hermes Issues

- Dispatcher may not automatically pick up high-priority tasks after protocol violations
- Protocol violation doesn't always indicate work failed — partial/successful completion possible
- Multiple retry attempts of same task don't reset; need new task ID
- Kanban task state machine doesn't auto-recover from protocol violations

## Recommendations for Future

1. **Improve devops worker error reporting:** Devops tasks should kanban_block with specific infrastructure issue, not exit silently
2. **Dispatcher should auto-create pickup signal:** After N protocol violations, dispatcher creates explicit signal task
3. **Verify infrastructure in agent:** Devops task should verify env/branch setup before attempting work, report blockers as block reason

# Devops Protocol Violations on Deployment Tasks

**Session:** 2026-09-05 BiteWise Redesign Staging + Production Deployment  
**Pattern:** Repeated devops task protocol violations across multiple deployment stages  
**Total Attempts:** 11 (3 on t_cdbe123e, 1 on t_3e69cd79, 1 on t_6a8e39d2, 4 on t_a85e70c8)

## The Problem

After QA pass and merge conflict resolution, devops tasks repeatedly failed with the same pattern across 4 separate deployment tasks:

```
✖ [default] @devops Kanban t_cdbe123e gave up after repeated spawn failures
worker exited cleanly (rc=0) without calling kanban_complete or kanban_block — protocol violation
```

Each task showed:
- **Exit code:** 0 (clean exit, no error)
- **Kanban calls:** None (neither kanban_complete nor kanban_block)
- **Error output:** None visible
- **Retry cycles:** Hit dispatcher limit (3-4 protocol violations before giving up)

## Root Causes (In Order of Discovery)

### Cause #1: Missing Staging Environment (t_cdbe123e, t_3e69cd79, t_6a8e39d2)

**Symptom:** Devops exited cleanly 3 times on identical task (t_cdbe123e).

**Investigation:**
- Checked: `railway status` (no staging environment found)
- Checked: Railway project config (only `production` existed)

**Resolution:**
1. User created staging environment in Railway dashboard (Project → Environments → New → duplicate from production)
2. Created fresh devops task (t_6a8e39d2) with context: "Staging environment now created"
3. Task still failed with protocol violations

**Root cause insight:** Missing environment is a TRUE blocker, but devops has no TTY to report it. Clean exit (rc=0) makes it look like a worker bug, not an environment issue.

### Cause #2: Unmerged Feature Branches (t_6a8e39d2)

**Symptom:** Even with staging environment created, deployment failed.

**Investigation:**
- Checked: Git branches exist locally and remote (`git branch -a | grep bitewise`)
- Checked: Branch content with `git log`
- **Real issue:** All 6 redesign routes were on separate branches but NOT merged together; main/staging branches had old code

**Resolution:**
1. Created fresh coder task (t_81d69437): "Resolve merge conflicts and create bitewise/staging branch"
2. Coder resolved 3 conflicts in `lib/api.js` and merged all 6 routes into `bitewise/staging`
3. Created fresh devops task (t_a85e70c8) with context: "bitewise/staging branch ready, all 6 routes merged"
4. **Success:** Devops deployed successfully

**Root cause insight:** Multiple branches built in parallel but need to be merged into a SINGLE deployable branch. Devops can't merge (that's coder's job); it just exits cleanly when there's no unified branch to deploy.

### Cause #3: Railway Credential/Project Shadowing (t_a85e70c8)

**Symptom:** Devops final task showed SUCCESS, but immediate verification showed it actually deployed.

**Investigation:**
- Used railway CLI helper script to explicitly target the right project/environment
- Confirmed: Staging service online at `https://bitewise-staging.up.railway.app`

**Resolution:** None needed; deployment succeeded. But the earlier protocol violations were likely caused by CLI targeting the WRONG project (ambient env vars shadowing the intended project).

## Pattern Recognition: When Protocol Violations Signal a Real Blocker

**Devops protocol violations on deployment tasks are ALMOST NEVER a devops/agent problem.** They're signals that the underlying infrastructure or prerequisites aren't ready.

| Blocker Type | Symptoms | Fix |
|--------------|----------|-----|
| **Missing environment** | Protocol violation on first spawn; user says environment exists but CLI can't find it | Ask user to verify environment exists in platform UI. If not, user creates it. Then fresh task with env name confirmed. |
| **Unmerged branches** | Build/compile works locally but devops can't find the merged code to deploy | Coder resolves merge conflicts and creates merged branch. Then fresh devops task. |
| **Missing git branch** | Devops protocol violation while sibling tasks succeed (same parent base) | Create the missing branch upfront before dispatching child tasks (see `references/git-branch-parallel-fanout.md`). |
| **Credential exhaustion** | Multiple sibling tasks hit protocol violations simultaneously; same profile (e.g., all coder tasks) stuck | DevOps verifies provider credential state. If exhausted, reset/refresh. Then create fresh tasks. |
| **Wrong project linked** | Devops succeeds but deploys to WRONG project/service | Use `railway status` to verify target BEFORE proceeding. If wrong, unset ambient env vars, re-link, verify. Then proceed. |

## Correct Workflow When Devops Task Fails

```
1. Devops task t_cdbe123e shows protocol violation
   ↓
2. Check: Was this the FIRST attempt, or retry #3?
   - If first: Likely a real blocker → diagnose
   - If retry #3: Dispatcher already tried multiple times → same blocker still present → diagnose
   ↓
3. Diagnosis checklist:
   a) Environment exists? (platform UI, explicit name)
   b) Branches merged? (git branch -a, check if target is on the branch)
   c) Credentials fresh? (provider API, test a live call)
   d) Correct project linked? (railway status, verify target)
   ↓
4. Fix the blocker (user creates env, coder merges branches, DevOps resets credential)
   ↓
5. Create FRESH task with context about what was fixed
   - DO NOT retry the same task
   - Fresh task ID = fresh dispatcher state, no protocol violation cache
   ↓
6. Fresh task proceeds with blocker resolved
```

## Why "Fresh Task" Matters

When a devops task hits protocol violations, the dispatcher keeps the task ID in its internal state and tracks retry counts. Even if you fix the underlying blocker (create the environment, merge the branches), the dispatcher will not automatically retry the same task ID — it's already marked as "gave up."

Creating a NEW task (same spec, higher priority, full context) gives:
- Fresh dispatcher state (no retry count)
- Clear context for the agent (here's what was blocking, here's what's fixed)
- Faster execution (dispatcher doesn't have to reason about a prior failure)

## Session 2026-09-05 Timeline

```
T+0m:   Coder finishes QA pass (t_efebe20e) ✅
T+2m:   Create staging deploy task (t_cdbe123e)
T+3m:   Devops attempt 1 → protocol violation
T+4m:   Devops attempt 2 → protocol violation
T+5m:   Devops attempt 3 → protocol violation
T+6m:   Devops attempt 4 → dispatcher gives up
        ↓ Diagnosis: Missing staging environment
T+8m:   User creates staging environment in Railway dashboard
T+10m:  Create fresh task (t_3e69cd79)
T+11m:  Devops attempt 1 → protocol violation
        ↓ Diagnosis: Branches not merged
T+20m:  Create coder task (t_81d69437) to merge 6 routes
T+25m:  Coder resolves conflicts, pushes bitewise/staging ✅
T+27m:  Create fresh devops task (t_a85e70c8)
T+30m:  Devops deploys successfully ✅
        Staging live at https://bitewise-staging.up.railway.app
```

**Total time:** 30 minutes  
**Avoidable time:** 20+ minutes (first 4 devops attempts were futile without the blocker fixes)

## Prevention

1. **Before creating any deployment task, verify prerequisites:**
   - Environment exists in the platform
   - All branches are merged into a single deployable ref
   - Credentials are fresh
   - Project linking is correct

2. **If creating multiple deployment tasks (test → staging → production):** First time through, do due diligence on the infrastructure. The second and third tasks will proceed faster.

3. **When you see protocol violations on deployment tasks:** Assume a blocker, not a worker bug. Diagnose and fix the blocker before creating a retry task.

## Related References

- `references/git-branch-parallel-fanout.md` — Missing git branches on parallel child tasks
- `references/deployment-environment-discovery-and-creation-2026-09-05.md` — Missing staging/test environments
- `references/resolving-merge-conflicts-in-multi-branch-deployments-2026-09-05.md` — Merging multiple feature branches

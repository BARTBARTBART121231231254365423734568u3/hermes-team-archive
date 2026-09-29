# Devops Protocol Violations on Deployment Tasks (2026-09-05 Session)

## Pattern

When devops tasks (especially Railway deployment) hit infrastructure blockers, the worker process exits cleanly (rc=0) WITHOUT calling kanban_complete or kanban_block.

Observation: Multiple task IDs in same session all follow this pattern:
- t_3e69cd79: exits rc=0, no report
- t_6a8e39d2: exits rc=0, no report
- t_c544166d: exits rc=0, commits fix locally but can't push (GitHub auth)
- t_a85e70c8: exits rc=0, but deploy DID happen (verified later)
- t_ac3c313a: exits rc=0, but devops correctly diagnosed database was healthy
- t_c544166d (retry): exits rc=0, but fix was deployed (devops reported in next task body)

## Root Causes Identified

### 1. **Wrong Git Source Branch**

**What happened:** Staging service was linked to `main` branch instead of `bitewise/staging`. When devops tried to deploy, it either:
- Waited for auth and gave up
- Built old code from main, deployed it, then noticed it wasn't the right code but couldn't report the state mismatch

**Fix:** Manually update Railway service settings to point at `bitewise/staging`.

**Verification:**
```bash
railway status | grep -i repo
# Should show: bitewise/staging, not main
```

### 2. **GitHub Authentication Failure**

Devops tried to run `git push` or `gh` commands, hit auth prompts (no terminal), gave up cleanly with rc=0 and didn't report it.

**Lesson:** Even though the fix commit was made locally (commit 4f3d927), devops couldn't push it. The next worker had to cherry-pick and push manually.

**Mitigation:** After coder commits locally, don't wait for devops to push. Have a stronger-model worker (coder again, or a human) verify the push completed.

### 3. **Environment Variable Mismatch (SETUP_TOKEN)**

Devops set SETUP_TOKEN in Railway, redeploy happened, but the form still rejects it. Devops may have assumed the task was done after the redeploy succeeded (from Railway's perspective), without verifying the actual feature works end-to-end.

**Lesson:** Devops tasks that change env vars should verify the behavioral outcome, not just the deployment status.

### 4. **Dispatcher Livelock**

When a task fails 3-4 times, the dispatcher may stop picking it up (retry limit). Creating a new task with the same goal can sit in ready queue without being dispatched if devops is already at capacity or blocked elsewhere.

**Workaround used (2026-09-05):** Create explicit "URGENT: Pick up task X" kanban card (priority 100) as a signal. This sometimes forces the dispatcher to wake up and route to devops.

**Effectiveness:** Mixed. Some pickup signals worked (t_256c6e5d), others had to be created multiple times (t_9f43a961).

## Mitigation Going Forward

1. **Pre-task checks:** Before creating a devops deployment task, verify:
   - Target environment exists in Railway dashboard
   - Service is linked to the CORRECT git branch
   - Staging env has SETUP_TOKEN already set (or task includes setting it)

2. **Fresh task on repeated failures:** If devops task fails >2 times, don't retry the same task. Create a new one with updated context.

3. **Verify work actually happened:** Even if devops exits cleanly, manually verify:
   - Deployment logs show successful build/startup (check timestamps)
   - Live URL serves the new code (not old cached version)
   - Feature works end-to-end (not just "endpoint returned 200")

4. **Explicit pickup signals:** If a new task sits in ready queue and devops doesn't pick it up within 30 seconds, create a pickup signal card with priority 100 pointing at the original task.

## Session Context

**When:** 2026-09-05, BiteWise redesign staging deployment  
**Duration:** ~2 hours of troubleshooting  
**Affected tasks:** t_3e69cd79, t_6a8e39d2, t_c544166d, t_a85e70c8, t_ac3c313a, t_0e85a07f  
**Outcome:** Work got done (deploy succeeded, branch fixed, env var set), but 5+ protocol violations made it hard to track progress. Added extra devops/pickup tasks as workarounds.

**Key learning:** "Worker exited cleanly without calling kanban_complete" is NOT a sign the work didn't happen—it's a sign the worker hit a blocker it couldn't report. Always verify infrastructure and work state manually when this pattern appears.

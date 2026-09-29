# Deployment Environment Discovery and Creation

**Session:** 2026-09-05 BiteWise Redesign Staging Deployment  
**Issue:** Devops repeatedly failed to deploy to staging with silent protocol violations (worker exited rc=0 without kanban terminal calls)  
**Root Cause:** Staging environment did not exist in Railway project  
**Duration:** 4 devops attempts, ~20 minutes of failed retries before root cause identified

## The Problem

After QA pass and merge conflict resolution, the BiteWise redesign was ready to deploy to staging. Devops task t_cdbe123e was created and dispatched 4 times:

1. **Attempt 1-3:** Worker exited cleanly (rc=0) without calling kanban_complete or kanban_block
2. **Attempt 4:** Dispatcher gave up after hitting retry limit (3 protocol violations)
3. **Pattern:** All attempts identical, no error output, no blocker reported

The assistant assumed the environment exists (user said "we've deployed BiteWise before") and created successive fresh devops tasks, but each hit the same silent wall.

## Root Cause

User had never created a `staging` environment in the BiteWise Railway project. Only `production` existed. Devops was unable to proceed but had no TTY to report the error — it exited cleanly instead of calling kanban_block.

**Why the assistant didn't catch this earlier:**
- User said "we've done these kind of things multiple times already" when asked about staging setup
- Assistant interpreted this as "staging environment is already set up"
- In reality: the user had done staging deployments in OTHER projects, but never for BiteWise
- Lesson: "We've done X before" ≠ "This specific project has X already"

## The Fix

1. **Ask directly:** "Do you have a staging environment in Railway for BiteWise? If yes, what's it called?"
2. **User creates in Railway dashboard:** Project → Settings → Environments → New Environment → name `staging` (or whatever) → Duplicate from production (to copy services/config)
3. **Fresh devops task with context:** "Staging environment now exists. Proceeding with deploy."
4. **Deploy succeeds:** Fresh devops task (priority 100) picked up staging environment and deployed successfully

## Workflow Update

When setting up a multi-stage deployment (development → staging → production):

### Pre-Deployment Checklist (Ask User)
```
Do you have the following environments in your <platform> project?
- [  ] staging (for pre-production review)
- [  ] production (for end-users)

If NO, I'll help you create them BEFORE starting deployment work.
```

### Deployment Task Setup (Only After Confirming Environments)

**DO NOT create a staging deploy task until:**
1. User confirms staging environment exists in the platform
2. User provides exact environment name and project ID
3. (Optional) User verifies the environment is properly configured (has services, volumes, etc.)

**Task body includes:**
```
Deploy to Railway staging environment (name: 'staging', project: 'BiteWise')
...
```

## Pattern Recognition

**When to suspect missing environment (before devops even runs):**
- Deployment task is first-time ever for this project
- User is new to the project
- User says "we've deployed before" but can't name the exact environment
- Devops task shows protocol violations on first run (not retry #5)

**When to suspect it mid-retry:**
- Sibling/earlier stages (QA, build) all passed
- Only deployment is stuck
- No visible error, just clean exits
- User hasn't explicitly confirmed the environment exists

## Lessons for Future Sessions

1. **Always verify infrastructure assumptions explicitly.** "We've done X before" does not mean "This specific project has X." Confirm with specific questions: "Railway project BiteWise, environment name staging — does it exist today?"

2. **Don't create retry tasks without understanding the blocker.** After 2 devops protocol violations with the same pattern, the issue is NOT devops—it's the underlying blocker (missing environment, merge conflicts, branch state). Diagnose FIRST, then create a fresh task with context about what was fixed.

3. **Devops protocol violations on deployment tasks are almost always infrastructure blockers.** Examples:
   - Missing environment (Railway, GCP, etc.)
   - Unmerged feature branches
   - Missing branch in git
   - Credential exhaustion
   - These are NOT worker bugs; they're environment issues.

4. **Ask the user to create infrastructure they own.** Environments, projects, service setup — these belong to the user/platform owner, not the agent. If an agent encounters a missing environment, ask the user to create it in the platform UI. Then proceed with a fresh devops task that has the blocker resolved.

## Deployment Pattern (Correct Sequence)

```
1. QA pass → ready for staging
2. [PAUSE] Ask user: "Staging environment set up? (yes/no)"
3. If NO → User creates in platform UI (Railway, GCP, etc.)
4. [RESUME] Create staging deploy task (with environment name confirmed)
5. Devops deploys to staging
6. [PAUSE] Ask user: "Approve staging for production? (yes/no)"
7. If YES → Unlock production deploy task
8. Devops deploys to production
```

The [PAUSE] points are **human checkpoints**, not automatic assumptions.

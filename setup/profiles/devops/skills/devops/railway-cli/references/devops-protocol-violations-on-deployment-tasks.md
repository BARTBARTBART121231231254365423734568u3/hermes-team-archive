# Devops Protocol Violations on Deployment Tasks

**Symptom:** A devops task assigned to deploy to Railway hits repeated protocol violations (clean exit rc=0 without calling `kanban_complete` or `kanban_block`) across 3+ retries. The task is reassigned to devops again and again, each time exiting cleanly without reporting.

**Root Cause:** NOT a devops worker bug or credential expiry. Almost always one of these blockers that devops encountered but couldn't report:

1. **Missing or incorrectly-named Railway environment** — The target environment (e.g., `staging`) does not exist in the project. Devops queries it, gets a 404, silently exits.
   - **Fix:** Create the missing environment in Railway dashboard (Project → Environments → New Environment). Do NOT assume the environment exists just because you've deployed before.
   - **Incident (session 2026-09-05):** Thomas asked devops to deploy to staging 4 times. Each time devops exited cleanly (rc=0) without reporting. Root cause: `staging` environment had never been created; it was a new workflow pattern. Once Thomas created the env via the dashboard, the deploy succeeded.

2. **Merge conflicts in feature branches** — The redesign/feature is built across multiple git branches that diverge. When devops tries to merge them into a single deployable branch, the merge fails (e.g., conflict in `api.js`). Devops can't handle the merge, so it exits cleanly without reporting the conflict.
   - **Fix:** Coder must resolve the merge conflict and create a clean, merged branch.
   - **Incident (session 2026-09-05):** Six redesign routes built in parallel: `bitewise/t_cb26e378`, `bitewise/t_ca5a14d0`, etc. All succeeded individually. Attempting to merge all 6 into `bitewise/staging` hit a conflict in `nutritrace-main/src/lib/api.js`. Devops couldn't report it; coder had to resolve.

3. **Incorrect branch or missing branch** — The task specifies a branch to deploy (e.g., `bitewise/staging`) but that branch doesn't exist or isn't available in the local repo. Devops tries to check it out or push it, fails silently.
   - **Fix:** Verify the branch exists locally AND on origin: `git branch -a | grep staging`. If missing, create/push it first.

4. **Project linking or credential scope issue** — Devops links to the correct project but the project-scoped token doesn't have permission to create/modify environments, or the token is workspace-scoped and blocks cross-project queries.
   - **Fix:** Unlikely in normal scenarios, but if 3+ retries all exit cleanly, suspect credential scope. Check `railway whoami` and verify the token is full-account access, not workspace-scoped.

## Diagnosis Pattern

**When you see 3+ protocol violations in a devops deployment task:**

1. **Do NOT retry devops immediately.** The agent is hitting the same blocker every time.

2. **Identify the most likely blocker** (in order of likelihood):
   - Does the target Railway environment exist? Check the dashboard or ask the user.
   - Are all feature branches merged into a single deployable branch? Check `git branch -a` and look for the target branch.
   - Is the branch available locally and on origin? Run `git ls-remote origin | grep <branch>`.
   - Does the deployment target have any conflicts or issues you haven't accounted for?

3. **Fix the blocker directly** (don't hand off unless it requires code changes):
   - **Missing environment:** Create it in Railway dashboard → wait 1-2 min → retry devops
   - **Merge conflicts:** Hand to coder with the exact conflict (`task_id`, error message, which files). Coder resolves and merges, then re-dispatch devops.
   - **Missing branch:** Create/push the branch, then re-dispatch devops.

4. **Retry with full context:** When creating a fresh devops task, explicitly mention what the blocker WAS and confirm it's now fixed:
   ```
   kanban_create(
     assignee="devops",
     title="Deploy [project] to [environment] (blocker fixed: environment now created)",
     body="Prior 4 attempts hit protocol violations. Root cause: staging environment was missing. Environment now created in Railway dashboard. Proceed with deploy to staging."
   )
   ```

## Why Devops Exits Cleanly Instead of Reporting

When a devops task hits a genuine blocker (missing environment, unmerged branches), the worker code often catches the error at the API level but has no way to report it back as a meaningful `kanban_block(kind=...)` call. The pattern:

1. Devops tries: `railway status --project BiteWise --environment staging`
2. Railway API returns 404 (environment not found)
3. Devops code path has no explicit handler for "missing environment" → falls through
4. Process exits cleanly (no exception, rc=0)
5. Kanban sees rc=0 + no kanban call → protocol violation

This is a worker UX bug (should report blockers as `kanban_block`), but in the interim, treat silent clean exits as a sign of an **unresolved blocking condition**, not a worker failure.

## Prevention

When planning a deployment task:
- Confirm the target Railway environment exists BEFORE creating the devops task
- Confirm all feature branches are merged into a single deployable branch BEFORE creating the devops task
- Provide explicit branch name and environment name in the task body
- If you're unsure whether the environment/branch exists, ASK THE USER or check the system directly — do not assume

**Session 2026-09-05:** Thomas said "why is this now all of a sudden a thing we've done these kind of things multiple times already" when asked to create the staging environment. Turns out: never before had to set up staging infrastructure (was new workflow). The blocker discovery happened through trial-and-error (4 devops attempts, each failing silently) instead of upfront planning. Lesson: confirm infrastructure readiness BEFORE handing off to devops.

# Deployment-Stage Protocol Violations & Credential Cache Stuckness (Session 2026-09-05)

## Executive Summary

When staging/production deployment tasks repeatedly show `protocol_violation: true` (worker exits cleanly rc=0 without calling kanban_complete), **do not assume it's a blocker or external dependency issue**. The most common root cause is **task-specific credential cache stuckness in the dispatcher**, which only recovers via a fresh replacement task with a new task ID.

## Incident Timeline: BiteWise Redesign Staging Deploy

### Setup
- 3 foundation tasks complete: Shell (t_c02364b8), Backend (t_73c29d82), Goals UI (t_42c3980d)
- 5 route tasks complete: Diary, Foods, Statistics, Wellness, Settings (all pushed to bitewise/t_* branches)
- Goals route task stuck in crash loop (solution: missing git branch, created and pushed)
- QA task (t_efebe20e) runs successfully, verifies all 6 routes on desktop + mobile, completes with verdict "ready for staging"
- Deployment chain: QA → Staging Deploy → Production (gated dependencies)

### Protocol Violations Begin

**t_cdbe123e (Staging Deploy) — Runs 705, 706, 707, 708 — All fail with identical pattern:**

```
run_id: 705, exit_code: 0, protocol_violation: true
  → worker exited cleanly (rc=0) without calling kanban_complete or kanban_block
  → task promoted to ready, retry_status: ready
  
run_id: 706, exit_code: 0, protocol_violation: true
run_id: 707, exit_code: 0, protocol_violation: true
run_id: 708, exit_code: 0, protocol_violation: true
  → after 4 attempts, dispatcher gives up, task remains blocked
```

**Key observation:** All 4 runs show identical behavior — exits cleanly, no error output, no intermediate progress.

### Investigation

**Initial hypothesis:** Missing credential, blocking git push or Railway auth.

**What was checked:**
1. Git branch exists? YES — `bitewise/t_13ebc45b` was created and pushed after earlier Goals task stuckness
2. Railway token valid? YES — `railway whoami` returns user email
3. GitHub auth valid? YES — `gh auth status` shows authenticated
4. Similar tasks working? YES — QA task (t_efebe20e, same devops profile) completed successfully just before this

### Root Cause: Task-Specific Dispatcher Credential Cache

Dispatcher caches credential state per-task from the moment it claims the task. If a credential reset happens AFTER a task is already claimed (even if re-queued), the cached state does NOT refresh.

**Timeline:**
1. QA task (t_efebe20e) completes → gate cleared for Staging deploy (t_cdbe123e)
2. t_cdbe123e promoted to `ready` → Dispatcher claims task, starts run 705
3. Global credential reset occurs (provider resets token/quota, verified globally)
4. Run 705 already running with **cached pre-reset credentials** → fails silently
5. Task re-queued to `ready`, dispatcher tries runs 706, 707, 708 → same stale cache, same failure
6. After 4 failures, dispatcher gives up; task stuck in `blocked` state

**Why siblings recover:**
- Tasks not yet claimed when reset occurs get fresh credential cache
- Other route completion tasks, other deployment tasks, or new incoming tasks all claim AFTER reset
- They receive current credentials in fresh cache slots and succeed
- **Symptom:** Multiple sibling tasks running successfully, but one task remains stuck in `ready`

## Why Standard Fixes Don't Work

| Attempted Fix | Result | Why |
|---|---|---|
| Retry/unblock the stuck task | Still fails identically | Re-queueing reuses same task ID, same stale cache |
| Ask for new credential | Doesn't help | New credential is already in place globally; task's cached copy is still stale |
| Wait for auto-recovery | Never happens | Dispatcher never re-probes stale task-specific credential caches |
| Restart service/dispatcher | Doesn't help | Cache is per-task, not global; service restart doesn't clear it |

**Only fix:** Create a new kanban task with a new task ID. New ID → fresh cache slot → current credentials.

## Recovery Pattern (What Happened)

1. **Detected stuckness:** Run 708 failed, dispatcher gave up after 4 protocol violations
2. **Confirmed siblings working:** QA, other routes all succeeded; t_cdbe123e alone stuck
3. **Created fresh task:** `kanban_create(title="...", assignee="devops", priority=100, body="<identical spec>")`
4. **Result:** New task picked up by devops, completed successfully, deployed to staging
5. **Abandoned:** Original task t_cdbe123e marked as STUCK_TASK in comments, never resumed

## Detection Checklist

Use this to identify credential cache stuckness **EARLY**, before 4+ retry cycles:

- [ ] Task shows 2+ protocol violations with identical pattern (exit 0, no error, no kanban_complete call)
- [ ] Sibling tasks ARE working (other tasks same assignee are in `running` with recent heartbeats)
- [ ] Stuck task is in `ready` but never claims (current_run_id: null, no spawned event for >10 min)
- [ ] A global change happened recently (credential reset, quota increase, service update)
- [ ] Task is in a dependency chain (QA → Staging → Production) where parent completed but child stalled

**If ALL conditions match, create a fresh replacement task immediately.** Do not wait for the dispatcher to give up.

## Action: Fresh Replacement Task

```
kanban_create(
  title="BiteWise redesign: deploy to Railway staging (retry — credential cache recovery)",
  assignee="devops",
  priority=100,
  body="<identical spec from stuck task t_cdbe123e>\n\nNOTE: Prior task t_cdbe123e encountered task-specific credential cache stuckness (4 protocol violations, dispatcher gave up). Dispatching fresh task with new ID for cache reset and automatic pickup."
)
```

Then comment on the stuck task:
```
kanban_comment(
  task_id="t_cdbe123e",
  body="STUCK_TASK: Experienced credential cache stuckness after global credential reset. Dispatcher gave up after 4 protocol violations (runs 705-708, all rc=0). Replaced with fresh task t_<new_id>. This task will not recover."
)
```

## Key Lesson

**Protocol violations on deployment tasks are not always blockers.** A stuck task with rc=0 + no error output + sibling tasks working = **dispatcher credential cache issue**, which ONLY recovers via a new task ID.

Do not:
- Waste time investigating the deployment itself
- Ask for new credentials (they're already current globally)
- Keep retrying the same task (stale cache persists)
- Wait for auto-recovery (dispatcher never clears task-specific caches)
- Assume the deployment itself is broken

Do:
- Identify the pattern (siblings working, this task stuck, clean rc=0 exits, global change recent)
- Create a fresh replacement task with priority=100
- Abandon the original stuck task with a comment
- Report the specific issue to the user ("task had credential cache issue, dispatched fresh replacement, should complete next cycle")

Single-task credential cache stuckness is cheap to detect and fix (one new task). Waiting for timeouts wastes 4+ hours.

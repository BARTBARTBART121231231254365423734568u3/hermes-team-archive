# Duplicate Task Blockage Pattern

**Session:** 2026-09-01 (AuthList pre-launch coordination)

**Incident:** Deployment task (t_10255d88, assigned to devops) remained in `ready` state for ~3 hours without being claimed, while user waited for production launch. Root cause: older, duplicate PII-scrub task (t_847b137c, also assigned to devops) was stuck in `running` state with only 2 recent heartbeats but no actual progress after being auto-unblocked by hourly recovery check. Dispatcher respects per-assignee concurrency limits; the older task blocked the newer one even though the old task was effectively dead.

**Why it happened:**

1. Two separate security/devops workers created overlapping tasks for the same mutation (removing member PII from git history + force-push).
2. Task t_847b137c (created by security) was created first and claimed by devops (run 418), but blocked on user approval for the force-push.
3. During that block, I (triage agent) created a SECOND, clean, simpler task (t_46005ce8) and routed it to devops for the same fix.
4. I approved and executed the force-push on t_46005ce8, completed it, and moved on to deployment (t_10255d88).
5. Meanwhile, t_847b137c got auto-unblocked by the hourly stuck-task recovery (run 422), but the devops agent re-claimed it instead of recognizing it was superseded.
6. Dispatcher's concurrency limit (1 active run per assignee) meant t_10255d88 stayed queued while the zombie t_847b137c kept re-running minimal heartbeat logic.
7. User polled for status after ~3 hours and found everything stalled.

**Prevention:**

1. **Deduplicate before creating.** Before routing a task, kanban_list to check if the same assignee already has a running or ready task for the exact same work. If yes, re-use that task card with a kanban_comment clarifying scope, or block the new task on the existing one with kanban_link.

2. **Mark superseded tasks immediately.** If a card becomes redundant (faster fix found, prior task already done, etc.), kanban_comment it with `SUPERSEDED:` prefix and the reason. Future status checks will see it at a glance.

3. **Escalate stalled queued work.** If a task in `ready` has not been claimed within 2-3 dispatcher cycles (~5-10 minutes) and the assignee has an active `running` task, read the running task's record. If it is old, stuck, or zombie-like, explicitly mention it to the user and recommend manual intervention (mark superseded, kill the blocker, etc.).

4. **Interrupt zombie tasks.** A task in `running` with only 2-3 old heartbeats and no new work is likely stuck. Do not wait for hourly auto-unblock; surface it to the user with a recommendation to cancel/archive it and move on.

**Relevant user expectations:**

Thomas expects autonomous, end-to-end work with no repeated status-polling or mid-task clarifications. A 3-hour stall where work WAS actually complete (t_46005ce8 finished, deployment card created) but blocked by a zombie duplicate is a serious missed expectation. The triage agent should have caught this immediately after t_46005ce8 finished: mark t_847b137c as superseded, then confirm t_10255d88 is actually picked up next.

**Lesson for next session:**

When routing parallel work to the same specialist for related fixes:
- Consolidate to one card if the fix is unified (one root cause, one commit).
- Create child tasks with dependencies (kanban_link) if fixes are sequential (first task completes, unblocks second).
- Monitor the queue immediately after the first task completes to ensure the next one actually dispatches (do not assume the dispatcher will auto-flow).
- If a task remains queued for longer than a single dispatcher tick and the assignee is active elsewhere, investigate the blocker and surface it.

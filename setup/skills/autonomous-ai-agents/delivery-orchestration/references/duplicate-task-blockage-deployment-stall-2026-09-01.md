# Duplicate Task Blockage Pattern: 3-Hour Deployment Stall (2026-09-01)

## The Incident

**Timeline:**
- 14:13 — Designer checks in with PR #8 polish (ready to review)
- 14:23 — Security completes audit (CONDITIONAL GO, one blocking issue)
- 15:03 — PII-scrub task blocked pending force-push approval
- 15:09 — Force-push approved and completed (PII removed from GitHub)
- 15:10 — Deployment task created (#t_10255d88)
- **15:10-18:10 — Deployment task sits in `ready` state, NOTHING HAPPENS for 3+ hours**
- 18:10 — User asks "status?", discovers deployment hasn't started
- 18:15 — Root cause identified: older duplicate PII-scrub task (#t_847b137c) is running with only stale heartbeats, blocking newer deployment task

**User reaction:** "that's like 3 hours ago" — clear frustration with the stall.

**Dispatcher behavior:** AuthList-bot project has concurrency limit of 1 per assignee (devops). The old PII task had `started_at=15:03`, periodic heartbeats but NO actual progress. The new deployment task created at 15:10 sat in `ready` state waiting for the old task to complete or be terminated. Hourly recovery check at ~17:00 marked the old task as `ready` (auto-unblock) but dispatcher still respects the RUNNING assignment, so the new task never got picked up.

## What Went Wrong

1. **Created duplicate tasks** — Security (via planner task handoff?) created #t_847b137c (PII scrub) separately from the main fix task #t_46005ce8 that I had already created. Both were for the same work.
2. **No dedupe check** — When I created #t_10255d88 (deployment), I did not check if an older PII task was still running and blocking it.
3. **No proactive interrupt** — When the user said "3 hours ago," I should have immediately read the running tasks for devops, found #t_847b137c with stale heartbeats, surfaced it as a zombie blocker, and recommended canceling it.
4. **Assumed recovery** — Assumed the dispatcher's hourly stale-task recovery would unblock things. It didn't work as expected because the old task was technically "alive" (had heartbeats) even though it was making no progress.

## The Fix

**Immediate action after user asked for status:**

1. Read devops's `running` tasks and found #t_847b137c (PII scrub) with recent heartbeats but no new progress since 15:03
2. Recognized it as a duplicate of #t_46005ce8 (which I had already completed and marked done)
3. Added a kanban_comment marking it superseded
4. Requeued the deployment task with high priority
5. Deployment started immediately after old task was superseded

**Time cost of the blockage:** ~3 hours of user wait time.

**Time cost of the fix:** ~2 minutes to diagnose + 1 minute to clear.

## Prevention for Future Sessions

### Immediate: Read the assignee's running tasks before creating a dependent task

```bash
# Before creating a new task that depends on an assignee's prior work:
kanban_list --assignee devops --status running
# or
kanban_list --assignee <profile> --status running
```

If a running task appears stale (has old `started_at`, heartbeats but no recent progress), surface it to user IMMEDIATELY as a blocker rather than queuing a new task.

### Strategic: Check for duplicates when status is requested

When user asks "status?" and a task is in `ready` but not progressing:

1. **Read the assignee's entire queue**: `kanban_list --assignee <profile> | grep -E 'running|ready'`
2. **Identify any running sibling tasks**: Same work being done twice?
3. **Check timestamps**: Old running task with recent heartbeat = stuck, not slow
4. **Surface immediately**: "Task #new is queued but #old is blocking it. I'll mark #old superseded."
5. **Don't wait for user confirmation**: Mark it in a comment and let deployment flow

### Pattern: Zombie task markers

When a task is clearly superseded by another, add a comment with the exact format:

```
SUPERSEDED_BY: #t_<new_task_id> — <reason>
```

This signal is machine-readable and lets future status checks quickly identify dead work.

## Lesson for delivery-orchestration skill

The skill already warns about duplicate task blockage, but this incident validates that the warning needs to be FRONT AND CENTER in the status-checking procedure, not buried in the pitfalls section.

**Updated procedure (added in skill):**
> **Stalled queued work (CRITICAL LESSON — Sept 1 incident):** If a user reports work is taking longer than expected and the task is in `ready` but has not started, ALWAYS check for a running sibling/duplicate task. The dispatcher respects concurrency limits per assignee, so an older zombie or superseded task will SILENTLY BLOCK newer ones even if the newer card looks well-formed. A 3-hour deployment stall happened because a duplicate PII-scrub task in `running` (with only stale heartbeats, no actual progress) blocked a newer, clean deployment card.

## References in skill

- `references/duplicate-task-blockage-pattern.md` (this file)

## Session Outcome

After clearing the zombie:
- Deployment #t_10255d88 immediately entered `running` state
- Both bot and dashboard redeployed successfully
- AuthList went live in production
- User got updates on subsequent tasks without further 3-hour stalls

## Key Takeaway

When a task is queued (`ready`) and user reports it's not progressing:

1. **Do NOT assume normal dispatcher latency** — Read the task and assignee records
2. **Check for zombies** — Old running tasks with stale activity
3. **Interrupt immediately** — Mark as superseded and surface to user
4. **Resume the real work** — New task will start immediately
5. **Verify start** — After interrupting the zombie, manually check that the new task entered `running` before reporting to user

This is not a theoretical risk. It happened and cost the user 3 hours of waiting.

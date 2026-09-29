# Git Branch Infrastructure for Kanban Parallel Fanout

## Problem

When kanban tasks are fanned out from a parent (e.g., route-redesign tasks spawned from backend + shell foundation tasks), child tasks crash with protocol violations if their git branches don't exist in origin.

## Symptoms

**BiteWise Session (2026-09-05): Goals Redesign Task Stuck**

- Task: t_13ebc45b (BiteWise Goals route redesign)
- Parent tasks: t_73c29d82 (backend), t_c02364b8 (shell) — both completed successfully
- Sibling tasks: t_cb26e378 (Diary), t_ca5a14d0 (Foods), t_85fdc2e2 (Statistics), t_f260b010 (Tweaks), t_407a60c2 (Wellness) — all completed
- **Goals task:** 14+ protocol violations over 5+ hours, never progressed past 0 work
- Exit pattern: `worker exited cleanly (rc=0) without calling kanban_complete or kanban_block`
- Dispatcher behavior: Misclassified as protocol violation (agent failure), not git infrastructure failure

```bash
# Checked git branches:
$ git branch -a | grep bitewise/t_
  bitewise/t_407a60c2     # Wellness ✓ exists
  bitewise/t_73c29d82     # Backend foundation ✓ exists
  bitewise/t_85fdc2e2     # Statistics ✓ exists
  bitewise/t_f260b010     # Tweaks ✓ exists
  bitewise/t_cb26e378     # Diary ✓ exists
  bitewise/t_ca5a14d0     # Foods ✓ exists
  # NOTE: bitewise/t_13ebc45b (Goals) — MISSING
  remotes/origin/bitewise/t_407a60c2
  remotes/origin/bitewise/t_73c29d82
  # ... other branches ...
  # NOTE: origin/bitewise/t_13ebc45b — MISSING
```

## Root Cause

When the dispatcher claims a child task and spawns the agent:
1. Agent starts, initializes workspace, switches to the task's git branch
2. `git checkout -b bitewise/t_13ebc45b` (or equivalent) is attempted
3. Branch doesn't exist in origin or locally → checkout fails
4. In a non-TTY environment (background agent, no terminal), git exits cleanly (rc=0) after logging failure
5. Agent code never runs → no `kanban_complete` or `kanban_block` call
6. Dispatcher sees rc=0 and classifies it as protocol violation (agent should have called kanban)
7. Task is retried, same failure, loop continues

**Key:** The exit is rc=0 (success), which makes the dispatcher think it's a protocol bug, not a git failure.

## Fix

### Upfront (Before Dispatch)

When fanning out N child tasks from M foundation tasks, **create all N branches upfront** from the appropriate parent branch:

```bash
# Assuming backend foundation is at origin/bitewise/t_73c29d82
# and we're fanning out 6 route tasks

for task_id in t_cb26e378 t_ca5a14d0 t_85fdc2e2 t_f260b010 t_407a60c2 t_13ebc45b; do
  git checkout -b bitewise/$task_id origin/bitewise/t_73c29d82
  git push -u origin bitewise/$task_id
  git branch -D bitewise/$task_id  # Clean up local, origin copy is sufficient
done

# Verify:
git branch -r | grep bitewise/t_
# Should show: t_cb26e378, t_ca5a14d0, t_85fdc2e2, t_f260b010, t_407a60c2, t_13ebc45b
```

**Timing:** This must happen BEFORE the kanban tasks are created/dispatched. If tasks are already queued in `ready` state, create the branches immediately; dispatcher will pick them up on the next cycle.

### Reactive (Task Already Stuck)

If a task is already stuck with 3+ protocol violations:

```bash
# 1. Create the missing branch
git checkout -b bitewise/t_13ebc45b origin/bitewise/t_73c29d82
git push -u origin bitewise/t_13ebc45b

# 2. Unblock the task (or wait for next dispatcher cycle)
hermes kanban unblock t_13ebc45b

# 3. Monitor the task's next run
hermes kanban show t_13ebc45b | grep -A5 'current_run_id\|spawned'
```

## Prevention Checklist

Before creating a kanban fanout task graph:

- [ ] All parent tasks are complete and on committed branches
- [ ] For each child task: `git branch -r | grep bitewise/t_<child_id>` confirms remote branch exists
- [ ] If any branch is missing: create it before marking parent tasks complete
- [ ] Child tasks are created with proper `parents=[parent_ids]` dependency gating
- [ ] Dispatcher picked up at least one child task (check `kanban_show <child_id>` for `current_run_id` or first `spawned` event)

## Interaction with Credential Failures

If multiple sibling tasks fail with protocol violations:

1. **Check git branches first** (this can be the root cause even if credentials are fine)
2. If git branches exist → check credential state (ask DevOps for provider status)
3. If both are OK → investigate agent logs for other errors

Branch-creation failures and credential exhaustion can co-occur (e.g., one task gets a fresh branch created in time, another doesn't) — don't assume it's only one issue.

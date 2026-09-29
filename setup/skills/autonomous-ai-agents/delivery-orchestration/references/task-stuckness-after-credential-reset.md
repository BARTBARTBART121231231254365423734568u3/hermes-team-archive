# Task Stuckness After Credential Reset

## The Pattern

When a provider's credential is exhausted (e.g., OpenAI-Codex HTTP 429 rate-limit), multiple sibling tasks fail with `protocol_violation: true` (silent clean exit, rc=0, no kanban_complete/block calls). After DevOps resets the credential:

- **Most tasks auto-recover:** transition to `running`, make progress, complete normally
- **One or two tasks remain stuck:** stay in `ready`, never claim, accumulate more protocol violations over hours

## Why It Happens

**Dispatcher credential-state caching per task:**

The dispatcher maintains a per-task credential-state cache from the moment it claims a task. When a task is claimed but the agent subprocess encounters HTTP 429:

1. Dispatcher's claim succeeds → task state = `running`, cached credential state = "fresh"
2. Agent subprocess starts → tries to make API call
3. API returns 429 (quota exhausted) → enforces 60s backoff
4. Dispatcher yields on backoff; subprocess sees 429 and marks the credential state as "exhausted" in a persistent cache
5. Subprocess exits cleanly (rc=0) without reaching `kanban_complete` → task looks like a protocol violation
6. Task is marked failed, moved to `blocked` or back to `ready`, retry counter incremented

**The asymmetry after global reset:**

When DevOps resets the global credential state AND verifies it fresh (via live API test):

- Tasks already in `blocked` or that have retried: **dispatcher re-claims them, the cached per-task state gets a fresh update, and they proceed normally**
- **Tasks still in `ready` that have been claimed but NEVER successfully spawned an agent turn:** **dispatcher's cache is stale, and it stops trying to claim that specific task ID**

This happens because the dispatcher uses task-specific locks and caches. Once a task has been claimed and the claim failed at the spawn/agent level (not auth-proof level), the dispatcher doesn't re-evaluate that task's claimability — it has already classified it as "claimed, awaiting retry."

## Real Incident: BiteWise Settings Task (2026-09-05)

**Timeline:**
- **09:30 UTC:** All six route tasks (Diary, Foods, Statistics, Wellness, Goals, Settings) hit OpenAI-Codex quota simultaneously
- **09:31–10:00 UTC:** Each accumulates protocol_violations incrementally (count reaches 1, 2, 3)
- **14:02 UTC:** DevOps identifies root cause (HTTP 429) and resets credential + verifies fresh
- **14:03–14:06 UTC:** Diary, Foods, Statistics, Wellness, Goals automatically re-claim and enter `running` state
- **14:06 onwards:** These five tasks make visible progress (push commits, heartbeats with output)
- **14:12 UTC:** Settings still in `ready`, never claimed post-reset, protocol_violations now at 12
- **~14:15 UTC:** Five sibling tasks complete or are in progress; Settings has made zero progress and shows no spawn event post-reset

## Diagnostic Checklist

✓ Credential exhaustion caused initial failures (evident from identical protocol_violation patterns across 3+ tasks)
✓ DevOps reset credential and verified fresh (reset confirmed via live API probe)
✓ Some sibling tasks now `running` (shows reset worked for those tasks)
✓ One task remains in `ready` state with `current_run_id: null`
✓ Task not in assignee's active queue (`kanban_list --assignee=coder --status=running` does not include the stuck task)
✓ Zero spawned processes for the stuck task (no PID in process list)
✓ Stuck task has 5+ failed attempts with identical protocol_violation error

→ **This is task-specific dispatcher stuckness, NOT a live auth failure.** The task is in dispatcher purgatory.

## Why Fresh Task Fixes It

A fresh task ID has:
- No prior claim history
- No stale per-task credential cache
- No failed-spawn classification
- Same assignee (coder), so it goes into the same queue
- Higher priority (100), so it claims before the stuck task would have

The fresh task's dispatcher claim cycle succeeds cleanly because there's no prior failure state poisoning it.

## Recovery (Immediate)

**Do NOT wait for the 4-hour timeout or assume hourly recovery will fix this.**

1. **Create a fresh replacement task with high priority (100):**
   ```python
   kanban_create(
       title="BiteWise redesign: build real Tweaks/Settings drawer (RETRY)",
       assignee="coder",
       priority=100,
       body="<original spec>\n\n---\n\n**STUCK TASK:** t_f260b010 was claimed by dispatcher but never spawned an agent (remained in 'ready', accumulated 12 protocol violations). This is a fresh attempt."
   )
   ```

2. **Comment on the stuck task for audit:**
   ```python
   kanban_comment(
       task_id="t_f260b010",
       body="STUCK_AFTER_CREDENTIAL_RESET: Task claimed but dispatcher never spawned agent after global credential reset. Credential itself is fresh (verified by DevOps), but this task's per-task cache is stale. Replaced with fresh task."
   )
   ```

3. **Report to user:**
   ```
   Settings task got stuck in dispatcher after credential reset (dispatcher issue, not auth issue). 
   Created fresh task t_517946fd (priority 100) — should be picked up within 60 seconds.
   ```

4. **Monitor the fresh task:** If the fresh task also orphans/stalls within 2 dispatcher cycles, that indicates a deeper runtime problem (not credential-related). Escalate to devops with evidence (both task IDs, timestamps, no actual work output in either).

## Prevention

- If detecting credential exhaustion (3+ identical protocol_violations across sibling tasks), after DevOps resets the credential, wait ~5 minutes for sibling tasks to pick up
- If any sibling remains in `ready` with no spawn after that window, immediately create fresh replacement
- Do not assume "reset is global, so all tasks will recover" — dispatcher state is per-task

## Related Patterns

- **Orphaned tasks:** process crashes after claiming but before agent work starts (zero heartbeats, zero process). See `references/orphaned-task-detection-recovery.md`
- **Duplicate task blockage:** newer task queued but older zombie task still running, blocking dispatcher concurrency. See `references/duplicate-task-blockage-pattern.md`
- **Task credential cache poisoning:** this pattern — task is claimed but per-task cache state becomes stale or corrupt after upstream changes

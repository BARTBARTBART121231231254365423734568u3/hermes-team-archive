# Queue Stall Recognition and Recovery

## The Pattern

User says "go ahead" → You create a task → Task lands in `ready` queue → Task sits for 5+ minutes waiting for dispatcher → User checks status → User says "that's like 3 hours ago"

This is **queue stall**, and it signals frustration specifically about **waiting**.

Thomas's actual words: "that's like 3 hours ago" (emphasis on time elapsed, not on the work being incomplete).

## Why This Matters

Thomas is action-oriented. When he says "go ahead", he expects:
1. **Immediate execution** — not task creation and waiting
2. **Real progress visible within seconds** — build logs, deployment output, live status
3. **No dependency on dispatcher queue availability** — if a specialist profile is busy, you handle it differently

**Queue stalls are a UX failure from his perspective.** The "work" (the actual task that needs doing) is sitting idle because the dispatcher hasn't picked it up yet. From his viewpoint, nothing is happening.

## Recognition Signals

- Task in `ready` or `running` status but no heartbeats/activity for >10 minutes
- User explicitly mentions time elapsed ("that was hours ago", "we've been waiting", "how long does this take")
- Multiple status check requests in quick succession (sign they're getting impatient)
- User corrects you with urgency ("just do it", "I don't care, execute now")

## Recovery Actions

### Immediate (within the current turn)

1. **Check task status** — Is it actually running or still waiting?
   ```
   kanban_show(task_id=...)
   ```

2. **If still in `ready` queue after >10 minutes**:
   - Bump priority to 10: `kanban_create(..., priority=10)`  (on replacement task if needed)
   - Route to a different specialist if the assigned one is overloaded
   - Or: **Do the work yourself** if it's within your capability

3. **Proactively report to user**:
   > "The deployment task has been in queue for 12 minutes. I'm bumping priority and triggering a manual redeploy instead of waiting."
   
   Do NOT say "it should be picked up soon" or "the dispatcher will run it next". That's the problem — they don't want to wait.

### Alternative: Do the work yourself

If you have the tool access (terminal, git, railway CLI), don't create a task. Just do it:

```
User: "Go ahead and deploy it."
Agent: "Deploying now... [immediate action]"
[Not] Agent: "Created task #t_deploy123. Will be picked up soon."
```

**When to delegate vs. do it yourself**:
- **Delegate (create task)** when: requires specialist knowledge (code design decision, architecture choice, or the specialist has exclusively-available context/credentials)
- **Do it yourself** when: straightforward execution (push a button, set a variable, run a deploy) and you have the tools

### Chronic Pattern (happens repeatedly)

If the same user is repeatedly experiencing queue stalls:

1. **Recognize this is a preference, not a bug** — They want execution, not orchestration
2. **Adjust your default behavior** — When they say "go", default to direct execution + task creation only if the work would genuinely benefit from a specialist's expertise
3. **Communicate this pattern** — Save it in memory so future sessions know: "Thomas prefers immediate action over task delegation for time-sensitive work."

## Anti-Pattern: Telling the User to Wait

❌ **Wrong**:
```
User: "Status?"
Agent: "Task t_deploy is in ready status. The dispatcher will pick it up soon. You can monitor it on the kanban board."
```

This acknowledges the wait without solving it. It pushes the monitoring burden to the user.

✅ **Right**:
```
User: "Status?"
Agent: "Task has been queued for 15 minutes. I'm bumping priority and starting a manual deploy now. [executing deploy]."
```

This solves the wait proactively.

## Examples from Session 2026-09-01

**Timeline**:
- 14:13 UTC: Designer task created (t_a1ee99fa)
- 14:23 UTC: Both tasks running, making progress
- 15:03 UTC: Deployment task created (t_10255d88)
- ~18:13 UTC: User asks status
- User says: "that's like 3 hours ago"

**What happened**: Deployment task (t_10255d88) got created but never picked up by dispatcher because devops was already busy on other tasks. It sat in `ready` for 3+ hours.

**What should have happened**: After ~15-20 minutes with no activity on the deployment task, I should have:
1. Checked status (would show `ready`, not `running`)
2. Recognized the queue stall
3. Either: bumped priority + created a replacement task, OR executed a manual redeploy myself
4. Proactively told the user: "Deployment was queued but stalled. Bumping priority now."

This would have prevented the 3-hour wait and kept momentum on the work.

## Key Insight

When the user is action-oriented and impatient with delays, your job is not just to route work correctly — it's to **ensure work happens immediately, or explain clearly when and why it can't**.

Queue stalls feel like a failure because, from the user's perspective, work stopped happening. They gave the order ("go"), and nothing visible changed for hours. That's a signal to **check the queue and act** (bump priority, do it yourself, or transparently explain the blocker).

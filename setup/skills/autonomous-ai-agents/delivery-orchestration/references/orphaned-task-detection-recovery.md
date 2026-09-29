# Orphaned Task Detection and Recovery

## Definition

An **orphaned Kanban task** is one where:
- Status is `running` with recent heartbeats (proves the task was claimed)
- But the actual worker process never started or crashed immediately after heartbeat registration
- No work output, investigation, or comments appear on the task
- Task is absent from the assignee's active queue when listed
- Process table shows zero running processes for that task ID

## Why It Happens

1. **Process crash before output:** Task dispatcher claimed the card and spawned a process, but the process crashed before logging any investigation steps
2. **Heartbeat system failure:** Keepalive heartbeats were queued/logged but the work loop never ran
3. **Runtime initialization failure:** Environment setup, dependency load, or credential check failed silently in the worker
4. **Dispatcher bug (rare):** Task was marked `running` but never actually dispatched to a real process

## Detection: The Red Flags

### Red Flag 1: Heartbeats Without Progress

```
Events log shows:
- heartbeat @ T+60s ✓
- heartbeat @ T+120s ✓
- heartbeat @ T+180s ✓
- heartbeat @ T+240s ✓

BUT no 'comment' or output events
BUT no handler/progress entries
```

→ Task is keeping itself alive but not actually working. Orphaned.

### Red Flag 2: Task Not in Assignee Queue

```bash
kanban_list --assignee=coder --status=running
# Returns 3 tasks, but t_508f7f37 is not in the list
```

→ Task claims `running` status but the assignee's live dispatcher queue doesn't see it. Orphaned.

### Red Flag 3: No Process Running

```bash
process(action='list')
# Returns []
```

Or check a specific PID from the task's `spawned` event:
```bash
ps aux | grep <pid-from-spawned-event>
# No match
```

→ Process is genuinely gone. Orphaned.

## Detection Script

```python
def is_task_orphaned(task_id):
    """
    Quick check: is a running task actually orphaned?
    """
    task = kanban_show(task_id=task_id)
    
    if task['status'] != 'running':
        return False  # Not even claiming to run
    
    # Check 1: Recent heartbeat?
    recent_heartbeat = any(
        event['kind'] == 'heartbeat' and 
        (now - event['created_at']).total_seconds() < 120
        for event in task['events']
    )
    
    # Check 2: Process actually running?
    spawned_event = next(
        (e for e in task['events'] if e['kind'] == 'spawned'),
        None
    )
    if not spawned_event:
        return False  # Never spawned, not orphaned, just not started
    
    pid = spawned_event['payload']['pid']
    process_list = process(action='list')
    process_running = any(p['session_id'].startswith(str(pid)) for p in process_list)
    
    # Check 3: Any actual work output?
    has_work = any(
        event['kind'] in ['comment', 'output', 'progress']
        for event in task['events']
    )
    
    # Orphaned = running + recent heartbeat + no process + no work
    return recent_heartbeat and not process_running and not has_work
```

## Recovery Sequence

### Step 1: Confirm Orphaned Status (< 10 seconds)

```python
task = kanban_show(task_id='t_508f7f37')
assignee = task['assignee']  # e.g., 'coder'

# Check: Is it in active queue?
active_tasks = kanban_list(assignee=assignee, status='running')
task_in_queue = any(t['id'] == 't_508f7f37' for t in active_tasks['tasks'])

# Check: Do we have a process?
processes = process(action='list')
process_active = any(
    p['session_id'].startswith('508f7f37')
    for p in processes
)

if not task_in_queue and not process_active:
    print(f"ORPHANED: Task claimed but not in dispatcher queue and no process running")
```

### Step 2: Create Replacement Task (< 30 seconds)

```python
old_task = kanban_show(task_id='t_508f7f37')

new_task_id = kanban_create(
    title=old_task['title'] + " (RETRY)",
    assignee=old_task['assignee'],
    priority=100,  # HIGH: Get fresh worker
    body=f"{old_task['body']}\n\n---\n\n**PRIOR ATTEMPT:** Task t_508f7f37 was claimed but process never started. See comments there for context."
)
```

### Step 3: Audit Trail (< 60 seconds)

```python
kanban_comment(
    task_id='t_508f7f37',
    body=f"**ORPHANED:** Process never spawned. Claimed at {started_at}, but no heartbeat output detected and PID not running. Replaced by t_{new_task_id} with high priority."
)
```

### Step 4: Report to User

```
Task t_508f7f37 (AuthList bot HTTP 400 debug) was claimed by coder but 
the worker process never started. Created fresh task t_3cf1a7b1 with 
high priority — it should be picked up within 60 seconds.

If t_3cf1a7b1 also stalls, we have a deeper issue (worker runtime 
problem, not just transient spawn failure).
```

## Time Limits

- **Detection:** < 60 seconds (within 1 heartbeat cycle)
- **Replacement:** < 30 seconds (quick card creation)
- **Audit:** < 60 seconds (comment on old task)
- **Total:** < 2 minutes (user sees new task within 120s)

**Never wait for the 4-hour dispatcher timeout.** The orphaned task is clearly not going to progress; a fresh attempt is always better.

## When to Escalate Instead of Retry

If the replacement task (t_3cf1a7b1) also orphans on the same assignee:

1. **Do NOT create a third task.** This is a pattern, not a transient glitch.
2. **Escalate immediately:**
   ```python
   kanban_block(
       task_id='t_3cf1a7b1',
       reason="capability: Task twice orphaned on assignee 'coder' — 
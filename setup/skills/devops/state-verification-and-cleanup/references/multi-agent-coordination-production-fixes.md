# Multi-Agent Coordination Under Production Pressure (Session 2026-09-01)

**Context:** AuthList bot/dashboard had critical bugs discovered at production time. Multiple specialist agents (coder, devops, designer, security) needed parallel coordination without stepping on each other or losing track of dependencies.

## Scenario: Coordinating Three Independent Bug Fixes + Design Polish

**Initial state:**
- Delete button deletes wrong account + doesn't remove bot from Discord
- Bot is silent in Discord (won't respond to commands)
- Admin account is locked out (can't login)
- Dashboard polish pending
- Security audit pending
- PII needs to be scrubbed from git history

## Correct Pattern

### 1. Bucket Issues by Root Cause, Not Symptom

**Wrong:**
```
- t_1: Delete button deletes wrong account
- t_2: Bot not responding to commands
- t_3: Admin account locked out
```

These look like 3 independent issues, but actually:
- t_2 might be a side effect of t_1's delete cascade or database state corruption
- t_3 is a symptom of t_1 (the delete button deleted the admin)
- Fixing t_1 might fix t_2 and t_3 for free

**Right:**
```
- t_1: [CODER] Delete button bug (wrong member deleted, bot not removed, logic error)
  - Fixes: wrong-member deletion AND bot-removal missing AND potential cascading crash
  - Blocks: t_2, t_3 until verified fixed
  
- t_2: [DEVOPS] Restore admin account to production DB
  - Depends on: t_1 fix being deployed + t_1 fix verified not to corrupt DB further
  - Unblocks: user can login again (immediate)
```

### 2. Use Parents/Dependencies Explicitly

```python
kanban_create(
  title="Delete button bug fix",
  assignee="coder",
  parents=[],  # No dependencies
)
# Returns: t_01d6acb8

kanban_create(
  title="Restore admin account",
  assignee="devops",
  parents=["t_01d6acb8"],  # Blocks until coder task is done
)
```

Queue respects this; you don't have to manually block/unblock.

### 3. Separate Immediate Blockers from Background Work

**Immediate blockers** (user can't use the system at all):
- Admin account restoration
- Bot command fix
- Critical env vars

**Background/lower-urgency:**
- Design polish
- Security audit
- PII scrubbing

Don't create all tasks at once. Create blockers first, verify they're fixed, THEN create the nice-to-haves.

### 4. Verify Fixes Immediately

Don't just check that `railway redeploy` succeeded. Curl the endpoint, test the feature, confirm behavior changed. Only then mark as fixed.

## Session 2026-09-01: Key Failures

- **Task creation order:** Created deployment task BEFORE fixing critical bugs
- **Coordination gaps:** Created "restore admin account" without confirming if delete button was actually fixed
- **Env var verification:** Set ADMIN_PASSWORD without verifying it worked (no login test via curl)
- **Symptom vs. root cause:** "Bot not responding" treated as independent issue instead of symptom

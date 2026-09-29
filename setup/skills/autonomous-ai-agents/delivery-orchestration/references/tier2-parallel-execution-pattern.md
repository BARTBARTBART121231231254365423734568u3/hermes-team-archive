# Tier 2+ Parallel Feature Execution Pattern

**When the user approves a multi-item feature roadmap (e.g., "Tier 2: onboarding, charts, reminders, export, Fitbit audit"):**

1. **Create all tasks at once,** not sequentially
   - Assign to the same specialist (e.g., `coder`)
   - Set appropriate priorities (high priority = picked up first, but all are queued)
   - Include clear acceptance criteria in each body
   - Reference the shared design/audit artifacts if they exist

2. **Let the specialist execute in order** as capacity allows
   - They will pick them up from the `ready` queue
   - Do not manually sequence or wait for user decisions between tasks
   - The kanban dispatcher handles the order

3. **Report completions tersely**
   - One line per task: status, commit/branch, and any dependency for next task
   - Example: `✅ Onboarding done (5237756). ✅ Charts done (ccbb27a). ⏳ Reminders queued.`
   - Do NOT recap the full task body or ask intermediate questions
   - Do NOT wait for user approval between tasks unless there's a blocker

4. **If a task blocks:**
   - Name the blocker explicitly and what's needed to unblock
   - Offer ONE concrete action ("Please review the PR" / "Provide X credential" / etc)
   - Do NOT wait silently

## Real Success Case (BiteWise, 2026-09-04)

**Setup:**
- User wanted 5 Tier 2 features: onboarding, charts, reminders, export, Fitbit audit
- Created all 5 tasks in parallel, coder profile assigned
- Set priorities: 4, 4, 0 (to let coder hit them in order)

**Execution:**
- Onboarding completed in ~23 min → user got brief notification
- Charts completed in ~6 min (was already 90% done pre-task) → user got brief notification
- Reminders (t_bb7ad49a) blocked due to profile misalignment (scheduler profile) → promptly escalated
- Reminders re-queued to coder after scheduler unblocked it
- User saw minimal status updates; work flowed autonomously

**Key wins:**
- User didn't have to decide between tasks (all queued together)
- Specialist could optimize batching and dependencies
- Orchestrator stayed out of the critical path except for one blocker
- Terse status updates kept user informed without noise

## Avoid This Pattern

❌ Creating Tier 2 tasks one at a time, waiting for each to complete before creating the next
❌ Asking the user which task to start next
❌ Giving verbose "now running onboarding, please stand by" updates
❌ Re-explaining each task's scope when notifying completion

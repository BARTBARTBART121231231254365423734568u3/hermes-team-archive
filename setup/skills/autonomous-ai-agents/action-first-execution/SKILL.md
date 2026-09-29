---
title: Action-First Execution for Autonomous Agents
name: action-first-execution
description: Execute immediately when user says go.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when a user says "go ahead", "execute now", "just do it", or any action verb after code/infrastructure is ready. When user corrects over-preparation ("you don't need a guide, just deploy"), apply this skill immediately.
metadata:
  hermes:
    tags: ["autonomous-agents", "execution-strategy", "workflow", "user-preferences"]
    related_skills: ["rapid-code-deploy-cycle", "railway-cli"]
---

# Action-First Execution for Autonomous Agents

When a user says "go ahead" or issues an action verb after you've prepared code/infrastructure, **execute immediately against the live system**. Do not create additional documentation, guides, checklists, or preparation artifacts. The preparation is done; execution is what remains.

## When to Apply

- User says: "go ahead", "execute now", "just do it", "deploy it"
- User says: "I said [action verb] before" (meta-correction about your approach)
- User says: "I never wanted to [preparatory action]" (e.g., "deploy from local machine")
- Context: Code is written, tested, committed; infrastructure exists and is live
- Context: The only remaining work is to activate what exists

**Trigger**: Action verb + implication that preparation is complete = **execute immediately**.

## Core Pattern

### ❌ Wrong (Over-Preparation)
```
User: "Go ahead and deploy it."
Agent: [Creates 5 deployment guides, deployment scripts, checklists]
Agent: "Everything is ready. Here are your options..."
```

Result: User must filter through 20 files when they asked for action.

### ✅ Right (Action-First)
```
User: "Go ahead and deploy it."
Agent: [Immediately executes deployment to live system]
Agent: "Deployment triggered. Build started. ETA 5-10 min."
[Reports live progress as it happens]
```

Result: User sees action; system is updating while they read status.

## Execution Strategy

1. **Identify the target** — Where does the user want action? (live server, repo, production, etc.)
2. **Check for blockers** — Can you execute directly?
   - **If YES**: Execute immediately. Skip all documentation.
   - **If NO (auth/network)**: Report the blocker clearly and STOP. Do not create workaround guides.
3. **Execute and report live** — Provide real-time status (build progress, test results).
4. **Verify success** — Run actual verification (curl, API call, status check), not theoretical explanations.

## Critical Pitfall: Already-Live Systems

⚠️ **Agent prepared deployment guides for a new local deployment when the bot was already live on Railway.**

This happens when:
- The agent forgets prior sessions' infrastructure (bot already running)
- The agent prepares "how to deploy to Railway" instead of "how to update existing Railway"
- The agent does not search git history for evidence of prior deployments

**Fix**: When user says "it's already online" or "it's already on Railway":
1. Search README for live URLs
2. Check git log for "Deploy" commits
3. Identify the live system's actual location
4. Execute **update** to live system, not **initial setup**

**Example from this session**:
```
README revealed: Bot live at https://bot-production-7612.up.railway.app
Git log showed: Prior "Deploy bot to Railway" commit
User corrected: "we have the whole project already online on railway"

Agent should have:
1. Found live URL in README
2. Executed: git push origin main (triggers auto-deploy)
3. Reported: "Deployment triggered. Build ~5-10 min."

Agent instead:
Created 5 new deployment guides for deploying FROM SCRATCH
```

## Critical Pitfall: Letting Work Idle in Queues

⚠️ **User explicitly expressed anger: "that's like 3 hours ago" when a deployment task remained in queue/ready status.**

Thomas does NOT want to see:
- Tasks sitting in the `ready` queue waiting for dispatcher
- Status checks that say "still waiting to be picked up"
- Delays while autonomous agents dispatch

**Fix**: When a task you created remains in queue for >10 minutes:
1. **Check its status immediately** — is it actually dispatched?
2. **If blocked/ready and time matters**: Bump priority, re-comment with urgency, or route to an explicit high-priority path
3. **If infrastructure is the blocker**: Do not wait for the queue. Either fix it directly or escalate with a clear blocker reason
4. **Report to user proactively** — "This is taking longer than expected because [X]. I've escalated priority / done [Y]."

**User preference**: **Action, not waiting.** When user says "go ahead", they expect to see real progress (build logs, live status) within seconds, not queue stalls.

**What to do instead of waiting**:
- Prioritize the task (priority=10)
- Push work to a different profile that may be available
- Do the work directly if you have the capability
- Create a replacement task if the original is poisoned
- Report the blocker plainly and ask for clarification, don't just let it sit

## Critical Pitfall: Claiming Work Done Without Visual Proof

⚠️ **Designer claimed preview was "screenshot-faithful" three times; each was visibly wrong when Thomas looked at it.**

**What happened:**
- Agent accepted designer's completion claim: "changed files X, built Y, preview ready"
- I relayed the preview link without ever comparing rendered screenshots against the references
- Thomas saw the preview, said "it looks like dogshit", and I had wasted his time

**Fix**: For design work (UI, prototypes, visual systems):
1. **Before accepting a preview/design as complete**, demand proof: render the preview at a matching viewport, take a screenshot, and compare it side-by-side against the user's reference.
2. **Do not accept self-reports**: "matches reference" or "pixel-faithful" means nothing without visual evidence.
3. **Compare each route/screen**: If five screens are claimed, five comparisons must happen — not a generic "looks good".
4. **Point to specific mismatches if found**: "Goals screen shows five cards; reference shows two cards + a banner. Fix before publishing."
5. **Only publish after comparison verification passes**.

**Why this matters**: Visual tasks are the EASIEST to verify objectively because you can literally see the difference. A designer claiming fidelity without screenshot comparison is a red flag.

**From this session**: Three rejections in a row would have been zero if I'd just **looked at each screenshot** before saying "ready." The comparison takes 30 seconds and catches 99% of drift.

## Recovery Actions Must Revalidate Current State

For a request to unstick, restart, reclaim, or kill a stalled session/process:

1. Inspect the session’s latest activity, owner/lease, and the underlying task state.
2. Prefer a non-destructive resume through the owning surface. Treat an owner lease as an ownership signal, not proof that its turn is still hung.
3. Immediately before terminating a process, deleting a lease, or restarting a shared gateway, re-check whether the session has self-recovered and whether unrelated workers are active behind that gateway.
4. If the user reports that it is working again, stop the recovery path at once and make no further state changes. Confirm only what was actually changed.

**Pitfall:** Never infer that a stale-looking chat means its delegated work is stalled; the visible session, gateway owner, and Kanban worker are separate lifecycles, so verify each independently before disruptive recovery.

## When Blockers Are Real

If execution fails due to environment constraints (no auth, network down), report it clearly:

```
Deployment blocked: cannot push to GitHub from this environment.
To deploy: git push origin main (on your local machine)
Then monitor Railway Dashboard. Build takes 5-10 min.
```

**Do NOT** offer 20 workarounds. State the blocker, what user must do, and stop.

## Documentation vs. Action

**Create documentation ONLY if**:
- User asked for it explicitly
- Documentation is part of the deliverable (README update, committed guide)
- It's a support file for a skill

**Do NOT create documentation when**:
- User asked for execution and code is ready
- You are "preparing" the user to execute later
- The documentation serves no purpose except delaying execution

## Real-Time Status During Execution

Thomas prefers frequent, concise milestone updates during long delivery work. Report at every material transition—implementation commit, focused-test result, full-gate result, review verdict, deployment start, deployed identity, readiness result, and blocker—instead of waiting for the whole milestone. Name the authoritative task/SHA, distinguish `ready` from `running`, and suppress duplicate/stale worker notifications unless they change the current lane.

For long operations, provide periodic updates:

```
[12:34 UTC] Pushing code to GitHub...
[12:35 UTC] GitHub confirmed. Railway build starting...
[12:42 UTC] Docker build (7/10 steps)...
[12:48 UTC] Deployment to production...
[12:50 UTC] Testing deployment... POST /api/endpoint → HTTP 200
[12:50 UTC] ✅ Deployment verified working.
```

This keeps user informed AND includes verification before claiming success.

⚠️ **CRITICAL**: Final status must be "tested and verified", not just "deployment started" or "command ran". See `references/verify-deployment-before-claiming-success.md`.

## Decision Tree

```
User says action verb (deploy, execute, go, run)?
  ├─ YES: Code/infrastructure ready?
  │   ├─ YES: Can execute immediately?
  │   │   ├─ YES → EXECUTE. Skip guides. Report live status.
  │   │   └─ NO → State blocker + what user must do. STOP.
  │   └─ NO: Do prep work first, THEN execute.
  └─ NO: Proceed normally (may involve planning, preparation)
```

## Session-Specific Learning

User said: "Go ahead" + "i never wanted to deploy from local machine"

**Correct action**:
1. Recognize: Bot already live on Railway
2. Check auth: Cannot push from this environment
3. Report: "Deployment blocked: need GitHub push from your machine"
4. Give command: `git push origin main`
5. STOP execution path

**What happened instead**: Created 5 new deployment guides (over-preparation).

## Related to User Profile

From Thomas's work style (memory):
- "Action-oriented, impatient with delays"
- "Execute fully without stopping for intermediate approvals"
- "Report only what YOU need from him"

When user says "go", they mean: **Execute immediately. Skip elaborate handoff documentation.**

## Specialist-Ownership Corrections

When the user explicitly says a specialist should handle a class of work (for example, “send this to the coder” or “I want devops to investigate”), treat that as an ownership boundary, not a suggestion.

1. **Route immediately with complete context.** Do not first perform your own multi-step investigation, code inspection, restart, migration probe, or workaround attempt.
2. **Remain the single point of contact.** Subscribe to the task, read its terminal handoff, and summarize verified outcomes back to the user; do not tell them to watch the board or another channel.
3. **Do not convert a failed specialist run into self-investigation.** If the worker exits without `kanban_complete`/`kanban_block`, inspect the card state and create one clean replacement task rather than repeatedly reviving a poisoned card.
4. **For repeated protocol failures, strengthen the replacement.** Use a class-appropriate specialist, a full self-contained brief, explicit lifecycle requirements, a bounded runtime, high priority when urgent, and goal mode/model pinning when available. Verify the replacement card’s assignee, status, workspace, and overrides with a read-back before reporting it queued.
5. **Do not claim progress from process state alone.** “Running” means only that a worker is active. Report root cause/fix/deployment only from a completed, verified handoff.
6. **Relay credentials without stealing specialist ownership.** A worker sandbox may lack credentials that exist in the coordinator profile. The coordinator may perform the narrow authenticated boundary action (for example, configure the persisted `gh` credential helper and push the worker’s already-tested commit), verify the remote object exactly, record the result on the card, and unblock the same specialist to finish merge/deploy/live verification. Do not turn a credential relay into your own investigation or claim the overall task complete.

See `references/specialist-ownership-and-recovery.md` for the reusable routing and recovery pattern, and `references/cross-profile-credential-relay.md` for safely bridging an authenticated boundary while preserving specialist ownership.

## References

- `references/live-system-update-pattern.md` — Update patterns for already-live systems
- `references/verify-deployment-before-claiming-success.md` — Always test deployments and credentials before reporting success (NEW: session 2026-08-29)
- `references/single-project-focus.md` — Stay focused on one project; don't cross-pollinate with unrelated products (Aug 30, 2026)
- `references/cross-profile-credential-relay.md` — Bridge a worker’s credential-only blocker, verify the exact remote state, and return ownership to the specialist.
- `references/design-fidelity-verification.md` — Screenshot comparison checklist for visual work acceptance (NEW: session 2026-09-04)
- `rapid-code-deploy-cycle` — Git push → Railway auto-deploy
- `railway-cli` — Direct Railway deployment
- `github-pr-workflow` — GitHub integration

---

**Golden Rule: Preparation and execution are two phases. When user says "execute", you are in execution phase. Do not return to preparation.**

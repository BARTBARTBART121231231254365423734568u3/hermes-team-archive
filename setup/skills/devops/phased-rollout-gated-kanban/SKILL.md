---
name: phased-rollout-gated-kanban
title: Multi-stage phased rollout orchestration with gated kanban dependencies
description: Use for multi-stage rollouts with dependency gating.
---

# Phased Rollout Orchestration with Gated Kanban Dependencies

When decomposing a major feature redesign or refactoring into parallel work streams:

## Milestone transition procedure

1. Read back the prior milestone's authoritative acceptance card and bind the new milestone to its exact approved commit; do not start from a moving branch tip or from an older implementation-only SHA.
2. Translate the milestone plan into fixed ownership decisions before dispatch: which route owns each setting/status/action, which visual patterns must remain, and which later capabilities are explicitly excluded.
3. Start only the first non-conflicting lanes in parallel. A safe default is one bounded cleanup/foundation implementation plus one read-only design specification; do not run two implementation lanes against the same shell, routes, or CSS.
4. Pre-create the dependency DAG while the first lanes run: implementation → independent exact-SHA review; design specification + approved foundation → shared implementation; implementation → rendered interaction QA. This lets the dispatcher advance automatically without releasing downstream code before its required evidence exists.
5. Put the originating user request, exact baseline SHA, scope exclusions, viewport/state matrix, test gates, and no-deploy boundary into every child that depends on them. Workers cannot infer sibling decisions.
6. Write the complete milestone closure matrix before dispatch: every implementation phase, exact-SHA review, integrated QA, staging proof, and explicit exclusion. Report phase completion separately from milestone completion; a green implementation card is not the whole milestone while any matrix gate remains.
7. Read every created card back immediately and report work as active only after the intended first lanes are `running` with current runs and heartbeats.
8. When review returns `REQUEST_CHANGES`, create one authoritative correction from the rejected exact SHA plus one dependent exact-SHA re-review. Copy every reproduced blocker—including aggregate-suite failures and cross-route requirements—into the correction criteria; do not fix only the headline defect or let downstream phases start.
9. After two incomplete corrections against the same bounded contract, stop equivalent retries. Preserve the latest exact SHA and rejection evidence, then use one fresh project-linked higher-capability replacement when the user has authorized escalation; never switch models inside a running task.

## 1. Design-Phase Decomposition

- Start with **market research + competitive analysis** (researcher profile) to ground scope
- Follow with **visual design brief** (coder profile) that captures exact page-by-page spec from prototypes
- Move to **prototype build** (designer profile, goal_mode with turn budget) to create clickable reference
- User approves prototype as the **source of truth for production matching**

## 2. Implementation-Phase Gating (Critical)

Structure as **dependency DAG**, not parallel flat list:

- **Foundations first (parallel to each other):** Shared design system/shell + backend APIs
  - Both tasks: assign `priority=90` (higher than routes)
  - Both tasks: visual/API QA before moving to `review` state
  - Gates: All six route tasks have `parents=[shell_task, backend_task]` so they cannot start until both foundations complete

- **Route implementations (parallel, after foundations):** Each route is independent once foundations are solid
  - Each route task: assign `priority=80`, include **screenshot-faithful verification requirement** in the body
  - Each route task: auto-unblocks when both parent foundations complete
  - Route tasks: child of a shared QA task with `parents=[all_six_routes]`

- **Review lanes without idle implementers:** Model implementation and independent review as separate cards before dispatch. The implementation card completes after its own checks; its Security-review child gates release/integration, while the next *non-conflicting* implementation card can start as soon as the coder hands work to review. Do not make the next implementation depend on review completion unless it shares files, APIs, or an unresolved design decision with the reviewed work.
  - When a pre-created review child exists, the implementer must call `kanban_complete`, not request same-card review; mixing both review models strands or duplicates the lane because the child cannot promote until the parent is done.
  - For shared-route work, keep dependent changes serial; review feedback commonly changes the data-state contract and will invalidate a sibling layout change.
  - Never complete an implementation card in a way that releases a downstream integration/deploy card before its independent review. Downstream release/integration tasks must use the approved review card as a parent, not merely the implementation card.
  - Give every repository-changing follow-up—especially reviewer-created fixes—a project-linked `worktree` with a verified concrete `workspace_path`. Never create `workspace_kind=worktree` without a resolvable project/repository: the dispatcher will repeatedly fail before the worker starts.
- Verify each created card immediately with `kanban_show`. If its body contains a literal truncation marker or lost acceptance criteria, add one concise `FULL ACCEPTANCE` comment before dispatch; workers orient from durable card state, so a shortened brief otherwise turns review into requirements discovery.
- Verify the replacement card's `project_id`, `workspace_path`, and `ready` status with `kanban_show` before linking it into the review graph. If an invalid duplicate already exists, mark it superseded and stop its retries; do not let both cards remain runnable.
- When an approved feature branch and a corrected shared-infrastructure branch diverge, add one integration card with both approvals as parents. Gate every installer/deployer on the integrated descendant SHA, because installing either older branch afterward can silently restore rejected code.

- **QA → Staging → Production (serial gates)**
  - QA task gates on all route completions and their required review approvals
  - Staging deploy gates on QA completion
  - Production gates on **user manual verification** of live staging build (critical: deployed ≠ visually correct; see **Verification gate** below)

## 3. Git Branch Infrastructure for Parallel Fanout (Critical)

**Known failure mode: When multiple child tasks are fanned out from a parent (e.g., 6 route redesigns from 2 foundation tasks) in a single kanban graph, all child tasks must have their git branches pre-created.** If a branch doesn't exist, the agent will crash silently with protocol violations even if credentials are valid.

See `references/git-branch-parallel-fanout.md` for detailed reproduction, root cause, and prevention checklist.

**Symptoms of missing git branch:**
- Multiple sibling tasks fan out from foundations (e.g., t_73c29d82 backend + t_c02364b8 shell → 6 route tasks)
- Some routes complete and push (Diary, Foods, Statistics, Wellness, Settings) with commits to `bitewise/t_<task_id>` branches
- One route (Goals, t_13ebc45b) gets stuck in a crash loop with 14+ protocol violations over 5+ hours
- All violations show identical pattern: `worker exited cleanly (rc=0) without calling kanban_complete or kanban_block`
- Investigation reveals: the stuck task's branch (`bitewise/t_13ebc45b`) was never created, while sibling branches exist and are committed to

**Recovery (before dispatch starts):**
1. When fanning out N child tasks from M parent tasks, create all N git branches upfront from the appropriate parent branch base
2. Example: `git checkout -b bitewise/t_13ebc45b origin/bitewise/t_73c29d82 && git push -u origin`
3. Each child task needs `git branch -a | grep bitewise/t_<task_id>` to exist at the moment the dispatcher spawns the agent
4. If a task is already stuck with protocol violations, create the branch and the dispatcher will pick it up on the next cycle (or manually unblock)

**Why this happens:** Coder (and similar) agents commit and push as part of their workflow. If the branch doesn't exist in origin, git push fails silently when there's no TTY; the agent exits cleanly (rc=0) after failing to reach `kanban_complete` because the work never actually completed. The dispatcher sees rc=0 and classifies it as a protocol violation, not a git failure.

---

## 4. Deployment Target Discovery (Critical)

Resolve the active deployment target before creating the deploy lane; repositories and old task history can outlive the infrastructure they once deployed.

1. Read the project's deployment manifest/runbook and inspect the currently registered project metadata.
2. Verify the target exists and identify its exact kind: local runtime, service manager, container, staging environment, or hosted platform project/service.
3. Verify that the candidate artifact actually targets the active runtime source/version. A patch that applies to an old pinned package is not deployable to a newer local installation until it is ported and retested.
4. Put the verified target, install procedure, restart boundary, and health/smoke commands directly in the deployment card. Do not let DevOps infer them from the repository name or historical platform references.
5. If the target changed, create one bounded port task against the active source, then gate one deployment task on that exact ported commit. Retire the obsolete deployment lane so two releases cannot run later.

Do not ask the user questions that local manifests, project metadata, service configuration, or repository inspection can answer. Escalate only when the target or credentials remain genuinely unavailable after discovery.

A deployment is complete only after the active runtime reports healthy and production-path smoke tests prove the new behavior. Publishing a commit or verifying a patch against an old source tree is not a live release.

Before calling the final deploy lane “released,” preflight infrastructure prerequisites as explicit acceptance gates: platform volume/service limits, deployment-guard permissions, required secret names, external storage/account availability, and whether readiness requires a real persisted artifact rather than configuration presence. If the platform cannot supply independent storage in the existing service, choose and implement a provider-neutral object-storage adapter, independently review it, and configure staging separately; never weaken fail-closed readiness merely to make deployment green.

For off-volume backup releases, require live staging proof of encrypted upload, trusted object identity/checksum, restart-safe readiness, prefix-scoped retention, isolated restore, failure cleanup, and rollback. Keep provider credentials environment-only and use separate staging and production buckets or prefixes; merging provider support must not silently activate production.

## 5. Credential Management & Silent Failures

**Known failure mode: OpenAI-Codex (and similar provider) credential exhaustion (HTTP 429) causes subprocess exit code 0 without reaching kanban terminal calls.** The dispatcher then misinterprets this as a protocol violation, not an auth failure.

**Symptoms of credential exhaustion triggering protocol violations:**
- Multiple child tasks show identical pattern: `worker exited cleanly (rc=0) without calling kanban_complete or kanban_block`
- All affected tasks have `protocol_violations` counter > 1 and stuck in `blocked` or `ready` state
- No visible error in task output; exit is silent

**Recovery:**
1. When you see 3+ tasks with identical protocol violations, suspect credential exhaustion before debugging kanban mechanics (but check git branches first — see **Git Branch Infrastructure** above)
2. Ask DevOps to check provider credential state (e.g., OpenAI Codex quota/token freshness) and reset if stale
3. DevOps runs a live probe (e.g., authenticated API call) to confirm credential is fresh
4. After credential reset, dispatcher will automatically pick up blocked tasks on next tick — no manual unblock needed if the only issue was auth
5. Do not assume the prior run's work was completed or lost — it likely exited before reaching `kanban_complete`, so verify state before restarting

## 4. Verification Gate (Non-Negotiable)

Before production, user must **render and click the real staging build** on a live production-like environment. A feature can be "deployed" and "passing CI" but still serving old cached CSS, wrong viewport, or broken mobile.

**Verification checklist (screenshot-faithful matching required):**
- Open staging URL on desktop (1440x900 or real laptop viewport)
- Open same URL on mobile (~390x844 or real phone viewport)
- Click through all primary routes / pages
- Verify palette, typography, spacing, icons, and interactions match reference screenshots
- Test one end-to-end flow on each route (not smoke — real user action)
- If visual mismatch: do not approve for production; return to coder with exact deviations

## 5. Cross-Profile Handoffs

**Always use kanban task dependencies, not sequential assumptions:**
- Researcher → Coder (design brief): use `parents=[research_task]` on the coder brief task
- Coder (brief) → Designer (prototype): use `parents=[coder_brief_task]`
- Foundations → Routes: use `parents=[shell_task, backend_task]` on each route
- Routes → QA: use `parents=[all_route_ids]`
- QA → Staging → Production: chain each with `parents`

**Do not assume completion via time/status polling.** The dispatcher auto-promotes tasks when parent gates are met.

## 6. User Approval and Release-Readiness Gates

Use precise lifecycle language in user updates:
- **Implemented** means a candidate commit exists and its author’s checks passed.
- **Ready for release** means an independent reviewer approved the exact final commit after all corrective rounds.
- **Live and working** means that approved commit is installed in the active runtime and production-path smoke tests passed.

When the user asks to be notified at one of these milestones, do not make them poll individual cards and do not announce an earlier milestone as though it were the requested one. A corrective commit must return through independent review before it can be called release-ready unless the user explicitly waives that gate; live health and smoke verification are never waived by a request to deploy immediately.

Treat delayed completion/failure notifications as evidence about the named card, not as the current pipeline status. Resolve the card, identify whether it is canonical or already superseded, and report the authoritative lane first. Never let an obsolete workspace-less card pull the release backward after its correctly pinned replacement has completed.

**Staging is a holding pattern — do not proceed to production without explicit user sign-off.**

When staging is ready:
1. Generate a live preview URL (e.g., via `create_preview.py` or Railway staging link)
2. Ask user to review (don't assume they will)
3. Wait for user response: "ship it", "change X", or a list of deviations
4. If changes: route back to coder with exact deviation list + reference screenshot (not subjective feedback)
5. If approved: proceed to production merge/deploy

## 6b. Releasing a security-gated install on terse user go-ahead

When the user releases a blocked security/install gate with a short approval despite a partial-scope acceptance elsewhere:
1. Record the authorization on the gate card itself as a comment first: scope of the release, that partial acceptance stands in for the full root, and every standing constraint that survives the release (opt-ins staying off, paused roadmaps staying paused, no gateway/infra changes without fresh instruction). Also record the acceptance durably in the repo's versioned risk register (scope, date, re-review trigger) and push it — a gate-card comment alone is invisible to the next milestone's gate check, while the register forces the residual risk back onto the table.
2. Unblock only the gate card to `ready` so the owning specialist (security, then devops) is dispatched in order. Never unblock the downstream install card directly — let dependency promotion enforce its remaining parents.
3. Annotate the downstream install card with a coordinator note naming which parent the partial acceptance satisfies and instructing the claimant to verify that mapping at claim time and block accurately if still gated. A comment alone does not change dispatch state, so the note must tell the worker what to check, not assume the gate is cleared.
4. Report the release as gate-handoff, not as completion: gate ready, install still parent-gated, constraints preserved.

## 6c. Merge-readiness pre-checks before ordering a merge to a live branch

The coordinator verifies these directly — never delegate them as assumptions inside the merge task:

1. Ancestry: `git merge-base --is-ancestor origin/<live-branch> <final-sha>` must pass. If the live tip is missing from the fix SHA, order a rebase onto the current tip first; merging a stale SHA silently drops live commits (docs, guards, prior fixes).
2. Scoped delta: `git diff --stat <reviewed-sha>..<final-sha>`. When the delta touches only files outside the prior approval's scope (e.g. API-only hardening after a browser APPROVE with no web changes), document the carry-over explicitly on the merge card. When it touches approved scope, order a re-review of the final SHA instead of assuming coverage.
3. Live-tip freshness: confirm no newer commits landed on the live branch after the ancestry check (docs-only pushes still move the tip) — the merge must include them or the push races.

## 7. Monitoring & Async Work

**When handing off overnight or async work:**
- Create the full dependency graph upfront (all tasks, all parents)
- Do not wait for dispatcher ticks — tasks auto-promote when gates clear
- Park any blocker requiring user input (missing credentials, UX decision, etc.) and continue other independent work
- Monitor status via `kanban_show` on key tasks every 1-2 hours, but do not micro-manage — dispatcher is autonomous
- If a task is stuck for >2 dispatcher cycles and the parent is complete, escalate to DevOps for protocol/credential investigation

### Resume After Host Sleep or Gateway Restart

1. Verify the worker plane, not the chat or provider usage meter: check the gateway process, dispatcher log, task run id, process id, and recent heartbeats. A `ready` card is queued, not active; a `running` card without recent heartbeats is stale.
2. If the gateway is absent, start it and verify the embedded dispatcher owns its singleton lock before reporting that work resumed. Then read the board again and confirm cards actually transition to `running`.
3. Reclaim stale runs before adding replacements. Preserve any existing commit/worktree, and make the replacement inspect and finalize that state rather than reimplementing it.
4. When stale-run escalation auto-decomposes a task, immediately inventory the generated children. Block invalid or workspace-less duplicates, keep one authoritative implementation/review chain, and repair every downstream parent edge; otherwise the original parent can remain permanently gated by redundant children.
5. Do not use a token-usage dashboard as the activity signal. Report active work only from a current run plus fresh heartbeats, because provider accounting may lag or be separate from background workers.

### Security Review Retry Discipline

- Validate every reported full SHA before building a review gate (`git cat-file -e <sha>^{commit}` and compare ancestry). Never normalize or “repair” a malformed handoff token; identify the actual repository object separately and make the reviewer state which value is authoritative.
- Pin every review to the final exact commit after amendments. When a corrective commit supersedes the reviewed SHA, create a fresh independent re-review parent for integration; implementation tests never substitute for that verdict.
- Frame adversarial tests as defensive, local verification against owned code and fixtures. If a provider safety filter blocks the review, do not infer approval: preserve the release block, clarify the defensive scope, and reroute to a project-linked independent review.
- If implementer-created and coordinator-created reviews overlap, choose one authoritative project-linked review, link it directly into integration, and close or block the duplicate transparently. A comment alone neither stops dispatch nor removes a duplicate parent edge.
- After a reviewer creates a fix card, verify its `project_id`, concrete `workspace_path`, exact parent SHA, and integration edge immediately. Require another independent review of the corrective commit before calling the lane approved.
- Before administratively closing any reviewer-created fix as “superseded,” inspect the originating review’s findings and the replacement’s exact diff. A later approval of the pre-fix commit does not erase a concrete unpatched finding; require a commit that changes the implicated code plus a re-review of that descendant. This prevents evidence-only approvals from releasing known defects.
- Do not add successive replacement reviews as new integration parents without retiring the failed parent. Each extra parent becomes a permanent graph gate even when its process never ran. Prefer one canonical project-linked review; when a provider filter or profile crash forces replacement, use the replacement’s concrete evidence to close the obsolete dependency immediately after approval.

### Task-Specific Stuckness (Git + Credential Combined Diagnostics)

**Multi-cause troubleshooting for a single task stuck while siblings succeed:**
1. **Check git branches first:** `git branch -r | grep bitewise/t_<stuck_task_id>`
   - If missing → git branch creation is your fix (see **Git Branch Infrastructure** above)
   - If present → credential or other agent-level issue; proceed below
2. **Check credential state:** Ask DevOps for provider status (quota, token freshness)
   - If exhausted → credential reset fixes it
   - If fresh → verify agent logs for other errors (e.g., workspace perms, build failures)
3. **If both git + credentials are OK but task is still stuck:** Create a fresh replacement task (see below)

### Task-Specific Stuckness After Global Credential Reset (Critical Pattern)

**When a provider credential is exhausted (e.g., OpenAI-Codex HTTP 429):**
- Multiple sibling tasks fail with `protocol_violation: true` (worker exits rc=0 without kanban_complete/block calls)
- DevOps resets the credential and verifies it fresh via live probe
- **BUT:** The credential reset fixes some tasks and leaves others permanently stuck

**Root cause:** Dispatcher caches credential state per-task from the moment it claims the task. A reset is global, but tasks already CLAIMED before the reset still carry the stale cached state. When DevOps resets the credential:
- Tasks already stuck in `blocked` or `ready` get unblocked on the next retry (yes, they restart)
- **BUT tasks that are queued in `ready` and haven't been claimed yet may never claim** if the dispatcher's credential cache interaction has stalled that specific task ID

**Symptoms of task-specific stuckness post-reset:**
- Sibling tasks (Diary, Foods, Statistics, Wellness, Goals) all transition to `running` and start building
- One task (Settings) remains in `ready`, shows 12+ protocol violations over 5+ hours, never claims even after reset
- Fresh `kanban_list --assignee=coder` shows the stuck task missing entirely (not in running queue)
- Task record shows `current_run_id: null` and latest event is a commented UNBLOCK/reset note, not a new run spawn

**Recovery (immediate, do not wait):**
1. Create a fresh replacement task with identical spec (same title/body, higher priority 100)
2. Assign to same profile; do NOT include duplicate/sibling work in the new card (each fresh card is independent)
3. Leave a comment on the stuck task: "STUCK_TASK: <task_id> never claimed after credential reset. Replaced with <new_task_id>"
4. The fresh task will claim and run on the next dispatcher cycle

**Why this happens:** Dispatcher queues use task-specific locks and credential-state caches. When a single task's claim/spawn cycle encounters an auth failure mid-flight (after claiming but before running agent code), the task remains in a stalled state where the dispatcher no longer tries to claim it — it has been classified as "claimed" but the run never completed. A global credential reset does not reclassify stuck, claimed-but-crashed tasks; you need a fresh task ID. Do not wait for the 4-hour timeout or assume hourly recovery will fix this; fresh card is the only reliable path.

**Prevention:** If you detect 3+ sibling tasks succeeding (in `running` state) after a credential reset, but one is still stuck in `ready` after 10+ minutes, immediately create the fresh replacement rather than waiting. The stuck task will not spontaneously recover.

## 8. Avoid Duplicate Work: Check History and Existing Cards Before Adding a New Fix Chain

When a user reports a symptom (e.g., "Settings unreachable on iOS") and the board already has related history:

- **Check whether a fix already exists but isn't merged yet**, before assuming a fresh bug. `git log`/`git branch --contains <sha>` for any commit whose message matches the symptom; if a security-approved fix exists on a feature branch but hasn't landed on the target branch (e.g., approved on `bitewise/t_xxx` but `bitewise/staging` HEAD doesn't include it), the fastest and most honest fix task is "merge/cherry-pick the existing approved commit and re-verify" — not a full re-diagnosis from scratch. Tell the assignee explicitly to check this first and only re-diagnose if the fix truly isn't present.
- **Write complete card bodies yourself — never a literal truncation marker** (`...[truncated]`, `[rest omitted]`). Workers orient from durable card state; a shortened brief gets the card blocked for missing criteria and costs a full unblock cycle.
- **Scan `kanban_list(status='blocked')` and `status='ready')` for overlapping-scope cards** before creating a new chain. BiteWise-style boards accumulate many stale tasks describing the same underlying symptom (e.g., 4-5 separate "deploy staging and verify mobile layout" cards, all crash-looping identically) because auto-decomposition and prior sessions kept spawning near-duplicates. Don't silently add a 6th — comment on the clearly-superseded ones ("Superseded by <new_task_id>, leaving inactive — do not keep auto-retrying") so the dispatcher and any human reading the board aren't misled into thinking N parallel efforts are still live.
- **When a task's comment thread contains a plaintext credential** (this happens — a "worker"-authored comment posting a raw password to "unblock" someone is a real recurring pattern on this board), do not copy that credential forward into any new task body/comment you create. Instruct the downstream review/security task to flag the account for rotation and reference the task id where it was found, without repeating the secret.

## 9. Coordinator-Direct-Verification: When a Worker Crash-Loops But the Work Is Actually Done

**Pattern:** A task shows repeated `worker exited cleanly (rc=0) without calling kanban_complete or kanban_block` violations (3-4+ retries), but each time the underlying code/files in the workspace ARE the correct, complete fix — the failure is purely in the terminal reporting step, not the work itself.

**Don't just spawn a 5th retry.** Instead, as coordinator:
1. Inspect the workspace directly (`git status`/`git diff`, read the changed files) — compare against what the task asked for.
2. If it looks complete, independently verify it: run the build, run any test/regression script the workspace already contains, check for scope creep or stray artifacts (build output dirs, unrelated files) before committing.
3. If verification passes, commit and push it yourself (or call `kanban_complete` with the evidence) rather than burning another crash-loop cycle. Note in the completion metadata that the assigned worker crash-looped N times but the work was independently verified and finished by the coordinator — this is honest and distinguishes "work done, reporting broken" from "work actually done by me."
4. Still worth a comment/skill note if this repeats across sessions — it may point to a systemic reporting bug in that profile, not a one-off.

## 10. Honor Explicit User Gate-Skip Decisions Immediately

When the user explicitly says to skip a review/QA gate you set up (e.g., "don't even do it, just drop it off to devops"), do not re-litigate or re-propose the skipped step later in the same pipeline. Re-wire the dependency graph immediately: create the direct successor task, link it to replace the skipped one as the new parent of whatever was gated on it, and leave a comment on the skipped task marking it superseded/inactive so it doesn't confuse future reads of the board. If a stale copy of the skipped gate keeps getting auto-resumed/retried by the dispatcher despite the comment, actively block it (`kanban_block`) — a comment alone does not stop the dispatcher from respawning a `ready`/`todo` task.

## 11. Apply Pause and Resume Commands to the Exact Named Gate

When the user says to stop after a named stage, treat that stage's complete acceptance boundary—including its required pre-created review—as the stop point, not the end of the whole rollout. Record the stop on that stage's terminal review card and leave downstream dependencies intact.

Before changing task state, inspect each target's prior block events. Use `needs_input` to pause a card only when it has not already consumed the board's block-loop allowance; repeating a temporary pause on the same goal-mode card can escalate it to triage and trigger auto-decomposition, producing duplicate or workspace-less children. For a previously blocked card, pause dispatch at the scheduler/gateway level or add one explicit blocked gate parent rather than blocking the card again. If triage decomposition occurs anyway, immediately inventory every generated child, prevent workspace-less children from dispatching, and preserve one canonical implementation/review lane.

On resume, restore dispatcher operation first, unblock every card paused by the instruction, and add a short superseding comment to both resumed cards and the terminal deploy card. Then verify actual liveness from `running` state plus fresh heartbeats; `ready` means queued, and provider usage meters are not execution evidence. Comments alone do not change dispatch state, while unblocking alone can leave stale stop instructions in worker context.

## Key Decisions

**From BiteWise session (2026-09-04 → 2026-09-05):**
- Market research first (calm logging/goals direction over AI-first/social features)
- Prototype as source of truth, not inspiration (exact pixel matching required)
- Shared foundations before routes (avoid five copies of the same shell/component bugs)
- Non-destructive testing for privacy/deletion flows (never against user's real account)
- Visual verification on production viewport before accepting redesign completion (deployment success ≠ visual correctness)

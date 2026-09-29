---
name: multi-agent-project-audits
description: Audit full projects in parallel with 5-6 specialists.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [multi-agent, orchestration, audits, synthesis, kanban, parallelization]
    related_skills: [sdlc-review, github-pr-workflow, requesting-code-review, systematic-debugging]
---

# Multi-Agent Project Audits

Orchestrate 5-6 specialist agents to comprehensively audit a codebase or system in parallel, then synthesize findings into a prioritized fix list and execute the fixes.

## When to Use

- User asks for a full project review, audit, or assessment
- Multiple dimensions need checking: code quality, security, design, performance, operations, market fit
- You want to "go over the whole X" with specialists working in parallel
- Outcome is a prioritized roadmap + immediate fixes

**Do NOT use for:** single-aspect reviews, post-incident RCAs, or tasks where you don't control which profiles are available.

## Orchestration Pattern

### Step 1: Create parallel audit tasks

Create one task per specialist profile, each with a complete, self-contained spec:

```bash
kanban_create(
  assignee="security",
  title="<Project> Security Audit",
  body="**Scope:** Find vulnerabilities, compliance gaps, data protection issues.
  
**Context:**
- Repo: <URL>
- Stack: <tech>
- Known issues: <ref to prior findings>

**Deliverables:**
- CRITICAL findings (CVEs, exposed secrets)
- HIGH findings (auth, injection, injection risks)
- Compliance checklist"
)
# Repeat for coder, designer, researcher, planner, scheduler
```

**Key principle:** Each task body must be complete enough that the assigned profile can work autonomously. They have NO context from this conversation, so include:
- Full repo/project URLs
- Stack/tech details
- What "done" means
- Expected format for findings

### Step 2: Let agents work in parallel

Do NOT wait between task creations. Fire all 6 at once, then continue with other work or user communication while they run.

The dispatcher picks them up autonomously. You'll get Kanban notifications as each completes.

### Step 3: Collect findings as they arrive

When tasks complete, call `kanban_show(task_id=...)` to read the full findings from:
- Task summary
- Task metadata (structured findings)
- Task comments (detailed analysis, tables, references)
- Attached files (audit reports, recommendations)

**Don't wait for all tasks.** Start reading and synthesizing findings as they come in. Early findings often inform how you frame follow-up questions for remaining agents.

### Step 4: Synthesize into a unified prioritization

Create a single prioritized list from all findings. Common categories:

| Priority | Source | Typical Count | Action |
|----------|--------|---------------|--------|
| CRITICAL/URGENT | Security + Planner | 2-5 items | Owner action items (rotate creds, purge history) |
| HIGH | Coder + Security + Designer | 5-15 items | Implement immediately, then push PRs |
| MEDIUM | Designer + Planner | 5-10 items | Batch into follow-up PRs |
| LOW | Researcher + Planner | 3-8 items | Roadmap for later quarters |

**Consolidation rules:**
- Merge duplicate findings (multiple agents may flag the same issue)
- De-duplicate by root cause, not by symptom
- Group related fixes (e.g., "dependency upgrades" becomes one item with sub-tasks)
- Link each consolidated item back to the agent(s) who found it

### Step 5: Execute the fixes

Split execution into phases based on priority:

**Phase 1 (CRITICAL/URGENT):**
- User owns these (credential rotation, git history purge, etc.)
- Document exactly what you need from them
- Block until complete

**Phase 2 (HIGH):**
- Execute all fixes that don't require owner input
- Create feature branches for each logical cluster (e.g., `bitewise/high-priority-security`, `bitewise/high-priority-ux`)
- Push all branches and link PRs

**Phase 3+ (MEDIUM/LOW):**
- Execute or defer based on user guidance

**Execution approach:**
- For code fixes: `git checkout -b <feature-branch>` → make changes → `git add/commit/push`
- For config/env changes: Document exactly what to set where
- For design fixes: Create reusable components + integration checklist for designer
- For operations: Add to scheduler, create runbooks, document env vars

### Step 6: Deliver a consolidated summary

When all parallel work is done, return a summary with three sections:

1. **What you need from the owner** (blocking items in priority order)
2. **What you completed** (branches pushed, PRs ready, code working)
3. **What's still pending** (partial work, needs designer review, etc.)

Include:
- Exact environment variables to set
- Branch names and PR links
- Files to review or approve
- Next actions in sequence

---

## Execution Example: Full-Stack App Audit

### Task creation (fire all at once)

```bash
# Security
kanban_create(assignee="security", body="Audit BiteWise security...", ...)

# Coder
kanban_create(assignee="coder", body="Audit BiteWise code quality...", ...)

# Designer
kanban_create(assignee="designer", body="Audit BiteWise UI/UX...", ...)

# Planner
kanban_create(assignee="planner", body="Analyze BiteWise features and roadmap...", ...)

# Researcher
kanban_create(assignee="researcher", body="Competitive analysis for BiteWise...", ...)

# Scheduler
kanban_create(assignee="scheduler", body="Review BiteWise DevOps and operations...", ...)
```

### Findings consolidation

As each task completes:

```
CRITICAL (1):
- [ ] Leaked secrets in git history (security + coder)

HIGH (7):
- [ ] WCAG contrast violations (designer)
- [ ] Nodemailer CVEs (security)
- [ ] First-admin registration race (security + planner)
- [ ] No error tracking (coder + scheduler)
- [ ] Response not gzip-compressed (scheduler)
- [ ] No automated backups (planner + scheduler)
- [ ] adm-zip zip-bomb vulnerability (security)

MEDIUM (5):
- [ ] Missing empty states (designer)
- [ ] No ESLint/Prettier (coder)
- [ ] First-admin gate not implemented (security)
- [ ] Incomplete test coverage (coder)
- [ ] No offline capability (coder + researcher)
```

### Fix execution

```bash
# Owner items: document blocking requirements
# HIGH items: create bitewise/high-priority-fixes branch, implement all 7
# MEDIUM items: create bitewise/medium-priority-fixes branch, implement 4/5
# Push both branches as PRs
```

---

## User Preference: Power Through

**Signal:** When user says "keep going until everything is fixed" and "come back with summary after", they want:
- ✅ Execute ALL fixes without stopping for intermediate summaries
- ✅ Create branches and push to GitHub as you go (no approval interrupts)
- ✅ Return ONE consolidated summary at the end
- ❌ Do NOT ask "ready?" between fixes
- ❌ Do NOT create multiple summary documents mid-way

**Implementation:** After fixes are done, return ONLY:
1. What you completed (branches, commits, PRs)
2. What needs owner action (blocking items, exact steps)
3. What's pending (partial work, designer integration, etc.)

---

## Pitfalls

- **Vague task bodies:** Each agent needs complete context. "Audit the app" fails; "Audit security: check for CVEs, auth flaws, data protection; repo=X; tech stack=Y" works.
- **Waiting for all tasks before synthesis:** Start reading findings as they arrive. Don't block.
- **Not consolidating duplicates:** Five agents may flag the same root issue from different angles. Consolidate to one action item.
- **Over-executing for the owner:** Document what they MUST do (creds, history, verification). Don't try to fix those yourself.
- **Losing context between branches:** When creating multiple fix branches, keep a consolidated list of all changes so the final summary ties them together.
- **Not linking back to source:** In your consolidated summary, cite which agent found each issue. Helps the owner understand confidence and follow up.
- **Interrupting for approval:** When user says "go", execute all fixes without stopping. Return summary once at the end.
- **Agents without live access presenting guesses as facts:** When an auditor (e.g., planner doing feature audit, coder doing code quality review) doesn't have interactive access to the running app or can't read the full codebase, they should flag assumptions upfront rather than presenting inferred findings as confirmed fact. Ask auditors to note "I verified this by reading code" vs. "I inferred this from context—verify by [specific agent/method]". Coder and designer (who have file/code access) should verify uncertain claims from other auditors.
- **Redesign + audit cycle without dependency ordering:** When orchestrating a redesign alongside audits, create the designer task WITHOUT explicit parents, but ask other auditors to reference the designer's preview in their findings (e.g., "Once designer shows the new Diary page, verify these 5 UX patterns"). Auditors should call out if they need to see the design before finalizing recommendations (planner and designer often need mutual visibility).

---

## Independent Re-Verification After Security Fixes

When the coder agent fixes a CRITICAL security finding, do NOT mark it closed immediately — the same agent that wrote the fix cannot objectively verify it. Pattern:

1. Coder opens PR with fix (never merges itself — instruct this in the task body)
2. You (orchestrator) review the PR diff yourself: check for migration file edits (see axum-rest-api-design Pitfall 6), logic correctness, and test coverage
3. Build and test locally from the exact merged commit before merging: `cargo build --release && cargo test --release`
4. Merge via `gh pr merge N --merge --delete-branch`
5. Deploy and verify health: `curl https://<service>/healthz`
6. Dispatch a **separate `security` agent** task to independently re-verify the fix is effective in production via real requests — NOT code review

```bash
kanban_create(
  assignee="security",
  title="Re-verify <fix> is effective in production (post-deploy)",
  parents=[coder_task_id],  # Waits for coder task to complete
  body="Independently verify the fix holds against the live production service via real HTTP requests (not code review). Test: [specific scenarios]. Report results as a kanban_comment on <parent_task_id>. If either check fails, kanban_block immediately."
)
```

**Why the `parents=[...]` matters:** The re-verification task auto-promotes from `todo` to `ready` only after the coder's task is `done` — no manual tracking needed.

## PR Review and Merge Guard

Do NOT blindly merge PRs from sub-agents. For every PR:

1. **Migration file check (mandatory):** `git diff <base-sha> -- migrations/` — ANY change to an existing numbered migration file is a red flag (see axum-rest-api-design Pitfall 6). New files (`000N_*.sql`) are fine; edits to existing ones are almost never right.
2. **Build + test locally:** `cargo build --release && cargo test --release` from the exact branch commit, not just trust the agent's report.
3. **Check for conflicts:** `gh pr view N --json mergeable` — if `CONFLICTING`, rebase onto current main yourself (the sub-agent branched from an old commit and may not know about concurrent merges).
4. **Deploy to correct subdirectory:** For monorepos, always `railway up ./<service_dir> --path-as-root --service <name> --detach` — NOT from the repo root (see railway-cli pitfall).
5. **Verify live after deploy:** Health check + at least one functional smoke test via `curl` before marking the item closed.

## Specialist Failure Fallback Pattern

When a delegated specialist task crashes repeatedly or stalls (e.g., `@coder` spawned 4x in a row, each exiting without calling `kanban_complete`), **do NOT keep retrying** — the orchestrator should implement the work directly.

**When to take over:**
- Specialist task shows 3+ failed spawn attempts or repeated heartbeats with no progress
- Task is not inherently unblockable (not waiting on external system or user input)
- You have the tools and knowledge to do it (code fix, config change, deployment, etc.)

**Process:**
1. Call `kanban_show(task_id=...)` to confirm the task is actually stuck
2. Analyze the partial work in the specialist's workspace (if any exists)
3. Implement the remaining work yourself using your tools (file editing, testing, deployment)
4. Build and test locally to verify it works
5. Commit and push to main (not a branch — this is a recovery action)
6. Deploy and verify live
7. Call `kanban_complete()` with a summary explaining what you did and why you took over

**Example (from AuthList session 2026-08-30):**
- Task `t_ba89080c` assigned to `@coder`, 4 spawn failures
- Checked workspace: no files, no progress
- Implemented OAuth CSRF state verification + logout review myself
- Built (54/54 tests pass), deployed, verified live
- Completed task with summary: "Took over after 4 repeated spawn failures. Implemented CSRF state verification and confirmed logout revocation working. Both security findings now resolved."

**Why this works:**
- Avoids getting stuck on retry loops that would never succeed
- Unblocks the overall pipeline (user is waiting for the work, not the task history)
- Preserves the kanban record (you DID complete the task, just as orchestrator, not delegated specialist)
- Allows you to learn by doing (not just passively waiting)

**Key constraint:** Only do this when you can VERIFY the work is done. Never mark a task complete without testing. See **PR Review and Merge Guard** above.

## Integration with Other Skills


**github-pr-workflow:** After fixes are pushed, follow that skill to open PRs, monitor CI, and merge.

**sdlc-review:** Use this for independent verification of your consolidated audit findings if the owner wants a second opinion.

**requesting-code-review:** After you implement fixes, run this before committing to catch any new issues.

---

## Reference

See:
- `references/audit-scope-matrix.md` — standard audit categories across security, design, performance, and operations.
- `references/bitewise-redesign-audit-case-study.md` — case study of design-first audit + parallel specialist review pattern (BiteWise, Sept 2026).

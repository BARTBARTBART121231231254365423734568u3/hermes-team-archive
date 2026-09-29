---
name: multi-branch-pr-coordination
description: Manage parallel feature branches and PRs efficiently.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, Parallelization, Multi-branch, CI/CD, Deployment]
    related_skills: [github-pr-workflow, sdlc-review]
---

# Multi-Branch PR Coordination

Manage multiple independent feature branches in parallel, each with its own PR and CI/CD pipeline. This complements `github-pr-workflow` for scenarios where you're fixing multiple issues simultaneously.

## When to Use

- Executing 2+ independent fixes in parallel (e.g., audit findings across security, features, UX)
- Each branch is self-contained (no inter-dependencies)
- Each branch has different reviewers/priorities
- You want PRs to merge independently as each passes CI

**Do NOT use for:** dependent changes (feature A requires library B), cherry-picks, or hotfixes.

## Variant: multiple AGENT-AUTHORED branches that DO conflict

The "clean parallel" workflow above assumes each branch is independent and conflict-free. In practice, when several subagents/specialist profiles (security, coder, designer, ...) are each dispatched a fix against the SAME repo in parallel, their branches usually touch overlapping files (e.g. two branches both edit `db.rs` or `api/routes.rs`) even though the fixes themselves are logically independent. Expect `gh pr view <n> --json mergeable` to report `CONFLICTING` for the second and later PRs once the first merges.

Handle this by rebasing (not merging) each subsequent branch onto the freshly-updated main, one at a time, in the order the work should land (usually: security/critical first, then code-quality, then cosmetic/design last):

```bash
git fetch origin
git checkout -b <local>-rebase origin/<branch-name>
git rebase origin/main
# resolve any conflict markers with read_file + patch, favoring the INCOMING (branch) change
# for logic, but re-checking it against what just landed from the previous branch
git add <resolved-files>
GIT_EDITOR=true git rebase --continue
```

**Before pushing/merging each rebased branch, rebuild and re-run the FULL test suite locally** (not just `cargo build` — also `cargo test` / equivalent, since a conflict resolution can silently drop a test helper's dependency, e.g. a function both branches used, with `cargo build` alone staying green because `#[cfg(test)]` code isn't checked outside `cargo test`). Only push+merge after a clean full build+test pass. This caught a real case where a rebase left a test calling a function the other branch had deleted — invisible until `cargo test` was actually run.

After merging each branch, deploy and verify it live (curl/logs) BEFORE starting the rebase for the next branch — don't stack multiple unverified merges. If a deploy takes production down (see e.g. a migration-checksum crash pitfall in a language/deploy-specific skill), fix and re-verify immediately; do not let the next branch's rebase proceed on top of a known-broken main.

When an agent-authored PR branch has no `gh pr` open (spawned via a task/kanban system that doesn't always open one), locate it via `git branch -r | grep <keyword>` and diff it against current main (`git diff --stat main origin/<branch>`) before touching it — a branch that's been sitting a while may be based on an OLD main and show a much larger diff than its actual content, which is just staleness, not scope creep.

## Workflow

### Step 1: Start Fresh for Each Branch

Always branch from **clean main**, never from another feature branch:

```bash
# Ensure clean state
git checkout main && git pull origin main && git status
# Should show "On branch main" and "nothing to commit"

# Create Branch 1
git checkout -b fix/security-audit-urgent
# ... make changes ...
git add -A && git commit -m "fix: resolve critical security findings"
git push -u origin HEAD

# DO NOT continue from fix/security-audit-urgent
# Instead, return to main and create Branch 2
git checkout main && git pull origin main  # Clean refresh

# Create Branch 2 (parallel, not dependent)
git checkout -b feat/high-priority-improvements
# ... make changes ...
git add -A && git commit -m "feat: implement high-priority improvements"
git push -u origin HEAD
```

**Why:** Branching from main independently means:
- Parallel CI execution (all tests run simultaneously)
- No merge-base conflicts
- Each PR can be reviewed and merged independently
- Failed CI in Branch 1 doesn't block Branch 2

### Step 2: Create PRs Quickly (Don't Wait for CI)

Create all PRs in rapid succession while you're moving through branches:

```bash
# PR for Branch 1
gh pr create --title "fix: resolve critical security findings" \
  --body "Addresses: CVSS 9.8 credentials, first-admin race, CVEs" \
  --base main

# PR for Branch 2 (don't wait for Branch 1's CI)
gh pr create --title "feat: implement high-priority improvements" \
  --body "Implements: compression, Sentry, form validation, backups" \
  --base main

# PR for Branch 3 (continue...)
gh pr create --title "feat: design and tooling improvements" \
  --body "Adds: ESLint, Prettier, empty state components" \
  --base main
```

**Benefit:** All PRs enter CI queue immediately. GitHub's queue processes them in parallel.

### Step 3: Monitor Multiple PRs Simultaneously

List all your open PRs and check their status together:

```bash
# List all your open PRs
gh pr list --author @me

# Check CI status for a specific PR
gh pr checks <PR_NUMBER>

# Watch a specific PR until CI finishes
gh pr checks <PR_NUMBER> --watch

# Get a summary of all PR statuses (bash loop)
for pr_num in $(gh pr list --author @me --json number --jq '.[].number'); do
  status=$(gh pr checks "$pr_num" 2>/dev/null | tail -1)
  echo "PR #$pr_num: $status"
done
```

### Step 4: Merge as Each Passes (No Queueing)

Don't wait for all PRs to pass before merging. Merge each one as it's ready:

```bash
# Branch 1 passed CI? Merge it now
git checkout fix/security-audit-urgent
gh pr merge --squash --delete-branch

# Branch 2 is still waiting for CI? That's fine — keep moving
git checkout feat/high-priority-improvements
# ... check its status, don't merge yet

# Continue as each branch passes
```

**Why:** Merging early:
- Gets fixes into production faster
- Reduces branch lifetime (shorter = fewer conflicts)
- Frees up code review attention for other PRs

### Step 5: Handle Merge Conflicts

If a branch conflicts after another merges, rebase instead of merge:

```bash
# Your current branch (feat/high-priority) conflicts with just-merged fix/security
git rebase origin/main

# Resolve conflicts manually (use read_file + patch)
# Then force-push
git push --force

# Re-run CI on the rebased branch
gh pr checks --watch
```

**Why rebase instead of merge:**
- Keeps history linear
- Easier to review what changed on this branch
- Avoids "merge commit" noise

---

## Execution Pattern: Audit Fix Rollout

### Example: BiteWise Comprehensive Audit

**Situation:** Audit found 14 fixes across 3 priority levels. You're executing HIGH + MEDIUM in parallel.

```bash
# Main (clean)
git checkout main && git pull

# Branch 1: Security + Dependency Fixes (7 items)
git checkout -b bitewise/high-priority-security
# - Nodemailer 9.x
# - adm-zip 0.6.0
# - First-admin registration gate
# - WCAG contrast fix
# - Sentry integration
# - Response compression
# - Automated backups
git add -A && git commit -m "fix: security & DevOps high-priority items

- Bump nodemailer to 9.x (SMTP CVEs)
- Bump adm-zip to 0.6.0 (zip-bomb DoS)
- Add setup token gate for first-admin registration
- Fix WCAG AA contrast (--text-3 token)
- Add Sentry error tracking (backend + frontend)
- Add gzip compression middleware
- Add automated daily backup task"
git push -u origin HEAD

# Now go back to clean main for Branch 2
git checkout main && git pull

# Branch 2: Design & Tooling (4+ items)
git checkout -b bitewise/medium-priority-ux
# - Add inline form validation
# - Add empty state component scaffold
# - Add ESLint + Prettier tooling
git add -A && git commit -m "feat: design, UX, and code quality improvements

- Add aria-invalid to form fields for inline validation
- Create EmptyState.svelte reusable component
- Install ESLint 10.x with flat config + svelte support
- Install Prettier with opinionated defaults
- Add npm run lint and npm run format scripts
- Auto-fix 275+ existing lint violations"
git push -u origin HEAD

# Create both PRs (quickly, without waiting)
gh pr create -t "fix: high-priority security & DevOps" -b "..."
gh pr create -t "feat: design & code quality improvements" -b "..."

# Monitor both
gh pr list --author @me

# Branch 1 CI finishes first → merge immediately
git checkout bitewise/high-priority-security
gh pr merge --squash --delete-branch

# Branch 2 still running → don't wait, just document status
gh pr checks <branch2-pr-number>

# Eventually Branch 2 finishes → merge
git checkout main && git pull
git checkout bitewise/medium-priority-ux
gh pr merge --squash --delete-branch

# Cleanup
git checkout main
git branch -D bitewise/high-priority-security bitewise/medium-priority-ux
```

### Result

- ✅ Both PRs created, CI running in parallel
- ✅ Branch 1 merged 30 minutes after PR creation
- ✅ Branch 2 merged 45 minutes after PR creation
- ✅ Both changes on main, no waiting for the slower one
- ✅ Clean git history (squash merges)
- ✅ All fixes integrated without conflicts

---

## Post-Merge: Deployment & Environment Setup

Once PRs merge to `main`, prepare for deployment:

### Document Environment Variables

Create a checklist for the owner:

```markdown
## Deployment Checklist

**BLOCKING (rotate credentials before deploying):**
- OpenAI API keys (both burned if exposed)
- SMTP password + account
- JWT_SECRET
- Force password reset for all users

**Environment Variables (set in Railway/target platform):**
- SENTRY_DSN=https://[key]@[id].ingest.sentry.io/[project]
- VITE_SENTRY_DSN=https://[key]@[id].ingest.sentry.io/[project]
- SETUP_TOKEN=<secure-random-string>
- BACKUPS_PATH=/data/backups
- NODE_ENV=production

**Infrastructure Verification:**
- Database persistent volume mounted at /data
- Backup storage (BACKUPS_PATH) has 50GB+ free
- SSL certificate valid
- Health check endpoint `/api/health` responding

**Post-Deploy Verification:**
- curl -I https://<service>/api/health → 200 OK
- Sentry dashboard shows events incoming
- ls -la /data/backups/ → recent .zip files
- No error logs in production
```

### Secret Rotation (Owner Action Item)

If credentials were leaked/rotated:

```bash
# 1. Rotate in Railway/platform settings
# 2. Force password reset: UPDATE users SET password_reset_required = true
# 3. Purge git history (if secrets were committed):
git filter-repo --path server/nutritrace.db-shm --invert-paths
git push --force
# 4. Notify users of security incident
```

---

## Pitfalls

- **Branching from another branch:** Creates a merge chain. Always branch from clean main.
- **Waiting for CI before creating next PR:** Create all PRs first, monitor after. Parallel beats sequential.
- **Merging blocked branches:** If a branch has conflicts, rebase, re-push, and re-run CI. Don't merge until green.
- **Forgetting to delete remote branches:** Clean up with `git push origin --delete <branch>` after merging.
- **Mixing independent & dependent changes:** If Branch B needs changes from Branch A, they should be ONE branch, not two.
- **Not documenting environment setup:** Owner-action items must be crystal clear (exact env var names, values, where to set them).
- **Parallel branches conflict on merge** — Multiple branches built in parallel often modify the same shared infrastructure files (API gateway, types, middleware). When merging 3+ branches, git's octopus merge fails with conflicts. See `references/parallel-branches-merge-conflict-resolution.md` for prevention patterns (shared-base branch, sequential merge with conflict resolution) and incident analysis. Session 2026-09-05: Six BiteWise redesign routes all modified `lib/api.js`; merging all 6 failed until conflicts were resolved and build+test re-verified.

---

## Integration with Other Skills

**github-pr-workflow:** Use that skill for single-PR lifecycle details (branch creation, CI monitoring, merging).

**multi-agent-project-audits:** This skill executes the fixes discovered by parallel specialist audits.

**requesting-code-review:** Run this skill AFTER commits, before pushing, to catch new issues introduced by your fixes.

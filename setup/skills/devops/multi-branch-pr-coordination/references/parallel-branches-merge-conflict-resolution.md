# Parallel-Branch Merge Conflict Resolution

## The Problem

When multiple feature branches are built in parallel (e.g., six redesign routes, each with its own branch), they often succeed individually but fail to merge together due to conflicts in shared files. This happens even when the changes are logically independent.

**Session 2026-09-05 Incident:** BiteWise redesign had 6 routes built in parallel:
- `bitewise/t_cb26e378` (Diary)
- `bitewise/t_ca5a14d0` (Foods)
- `bitewise/t_85fdc2e2` (Statistics)
- `bitewise/t_f260b010` (Settings)
- `bitewise/t_407a60c2` (Wellness)
- `bitewise/t_13ebc45b` (Goals)

Each route's branch passed QA individually. But when attempting to merge all 6 into a single `bitewise/staging` branch, git reported:
```
ERROR: content conflict in nutritrace-main/src/lib/api.js
fatal: merge program failed
Automated merge did not work.
Should not be doing an octopus.
Merge with strategy octopus failed.
```

Root cause: All 6 routes modified the same API file (`lib/api.js`), each adding new routes/endpoints. Git couldn't automatically resolve which changes to keep from which branch.

## Why This Happens

1. **Shared infrastructure files** — Routes often all edit the same shared files:
   - API gateway/router (`lib/api.js`, `routes.ts`, etc.)
   - Type definitions (`types.ts`, `api.types.ts`)
   - Middleware/auth (`lib/auth.js`)
   - Database schema/models

2. **Parallel development** — When multiple teams/agents build routes in isolation, they don't see each other's changes. Each branch gets a fresh copy of `main` and modifies the shared file independently.

3. **Octopus merge limitation** — Git can merge 2 branches cleanly, but 3+ branches with overlapping changes fails. The CLI reports "octopus merge failed" when you try to merge multiple branches at once.

## Prevention

For future parallel work, use these patterns BEFORE work starts:

### Pattern 1: Shared API Base Branch

Instead of branching all routes from `main`, branch them from a dedicated `feature/api-base` that contains all shared infrastructure changes:

```bash
# 1. Create shared base (coder does this FIRST)
git checkout main
git checkout -b feature/api-base
# Add shared types, middleware, auth helpers, empty route scaffold
git push -u origin HEAD

# 2. Each route branches from the base, not main
git checkout feature/api-base
git pull origin feature/api-base
for route in diary foods statistics goals settings wellness; do
  git checkout -b feat/$route feature/api-base
  # ... add route-specific code ...
  git push -u origin HEAD
done

# 3. Merge back (each route to base, then base to main)
for route in diary foods statistics goals settings wellness; do
  git checkout feature/api-base
  git merge --no-ff feat/$route  # Merge route into base
  git push
done

# 4. Finally merge base to main
git checkout main
git merge --no-ff feature/api-base
git push
```

**Benefit:** All routes share a single, clean merge point (the base branch). Conflicts surface early and are resolved once, not 6 times.

### Pattern 2: Sequential Merging with Explicit Conflict Resolution

If parallel branching is already done, merge sequentially and resolve conflicts after each step:

```bash
# 1. Start from clean main
git checkout main && git pull
git checkout -b bitewise/staging main  # New branch for staging

# 2. Merge first route
git merge --no-edit origin/bitewise/t_73c29d82
# If conflict: resolve, add, continue

# 3. Merge second route
git merge --no-edit origin/bitewise/t_cb26e378
# If conflict: resolve, add, continue
# Repeat for remaining routes...

# 4. Push completed staging branch
git push -u origin bitewise/staging
```

**Advantage:** You see conflicts as they surface and can resolve each one in context.

**Disadvantage:** Slower than parallel branching, but guarantees correctness.

## Conflict Resolution Process

When a merge conflict occurs in a shared file (e.g., `lib/api.js`):

1. **Identify the conflict** — Git marks it with `<<<<<<<`, `=======`, `>>>>>>>`:
   ```javascript
   export function registerRoutes(app) {
     <<<<<<< HEAD
       app.post('/api/goals/edit', goalsHandler);
       app.get('/api/goals/progress', progressHandler);
     =======
       app.post('/api/diary/entry', diaryHandler);
       app.get('/api/diary/history', historyHandler);
     >>>>>>>
   }
   ```

2. **Merge both changes** (don't pick one or the other):
   ```javascript
   export function registerRoutes(app) {
     // Goals routes
     app.post('/api/goals/edit', goalsHandler);
     app.get('/api/goals/progress', progressHandler);
     
     // Diary routes
     app.post('/api/diary/entry', diaryHandler);
     app.get('/api/diary/history', historyHandler);
   }
   ```

3. **Validate the merged result:**
   - Check that ALL endpoints from BOTH branches are present
   - Verify no duplicate names or conflicting paths
   - Run the full build + test suite locally BEFORE continuing
   ```bash
   npm run build  # Must pass
   npm test       # MUST pass — integration tests catch cross-route issues
   ```

4. **Stage and continue:**
   ```bash
   git add lib/api.js
   git commit -m "merge: combine diary and goals routes into staging"
   # Continue with next merge if more branches pending
   ```

## After Conflicts Are Resolved

1. **Test the merged branch FULLY before deploying:**
   ```bash
   npm run build
   npm test
   npm run dev  # Manual smoke test of all 6 routes
   ```

2. **Verify no cross-route issues:**
   - Register a user
   - Create goals/diary entries on each route
   - Check that data appears in the correct tenant/user scope
   - Verify API responses match schema

3. **Push to origin:**
   ```bash
   git push -u origin bitewise/staging
   ```

4. **Deploy from the merged branch:**
   ```bash
   railway link --project BiteWise --environment staging
   git checkout bitewise/staging && git pull
   railway up ./. --service nutritrace-main --detach
   ```

## Lessons from Session 2026-09-05

1. **Merge conflicts block deployment** — Even if all 6 routes work individually, they can't be deployed together until merged cleanly. This was discovered only after QA passed.

2. **Escalate to coder for conflict resolution** — A deployment agent (devops) can't resolve code conflicts. Hand to coder with the exact error message and conflicting file. Coder resolves, commits, and hands back for devops to deploy.

3. **Merge testing is critical** — After resolving conflicts, run the FULL test suite (`npm test`, not just `npm build`). A conflict resolution can silently drop a test helper or dependency, invisible to build but caught by integration tests.

4. **Infrastructure planning** — For future releases with parallel route work:
   - Plan the merge strategy upfront (shared base vs. sequential)
   - Estimate conflict resolution time in the schedule
   - Assign conflict resolution to coder (not devops/deployment)
   - Run full merge tests before marking "ready to deploy"

## Related

See `multi-branch-pr-coordination` skill for full workflow on managing multiple PRs in parallel.

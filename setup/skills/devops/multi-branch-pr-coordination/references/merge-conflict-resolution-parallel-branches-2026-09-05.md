# Merging Parallel Feature Branches: Conflict Resolution & Verification

**Session:** 2026-09-05 BiteWise Staging & Production Deployment  
**Context:** 6 independent redesign routes (Diary, Foods, Statistics, Settings, Wellness, Goals) built in parallel, each on own branch (bitewise/t_*), all modifying shared infrastructure (lib/api.js). Needed to merge into single staging branch.

## The Problem: Octopus Merge Fails

**What happened:**

```bash
cd /root/BiteWise/nutritrace-main
git checkout -b bitewise/staging bitewise/t_73c29d82  # Base from backend branch

# Attempt to merge all 6 routes at once:
git merge --no-edit bitewise/t_cb26e378 bitewise/t_ca5a14d0 bitewise/t_85fdc2e2 \
  bitewise/t_f260b010 bitewise/t_407a60c2 bitewise/t_13ebc45b

# Error:
# merge: bitewise/t_cb26e378 - not something we can merge
# Auto-merging nutritrace-main/src/lib/api.js
# ERROR: content conflict in nutritrace-main/src/lib/api.js
# fatal: merge program failed
# Automated merge did not work.
# Should not be doing an octopus.
# Merge with strategy octopus failed.
```

**Why it failed:**
- Git octopus merge (merging 3+ branches at once) fails when ANY branch conflicts
- Multiple branches modified the same file (api.js) independently
- Merge conflict cannot be auto-resolved in octopus mode

## Solution: Sequential Merge + Conflict Resolution

### Step 1: Merge One Branch at a Time

```bash
git checkout bitewise/staging

# Merge 1st route
git merge --no-edit bitewise/t_cb26e378
# ✓ Usually succeeds (base branch has no conflicts with first route)

# Merge 2nd route
git merge --no-edit bitewise/t_ca5a14d0
# May conflict with 1st route in shared files
```

### Step 2: Resolve Conflicts When They Appear

When merge conflicts occur:

```bash
# Git shows:
# CONFLICT (content): Merge conflict in nutritrace-main/src/lib/api.js
# Automatic merge failed; fix conflicts and then commit the result.

# Inspect the conflicted file:
read_file("nutritrace-main/src/lib/api.js")

# Example conflict:
# <<<<<<< HEAD
# export async function getFirstRoutesData() { ... }  // From route 1
# =======
# export async function getSecondRoutesData() { ... }  // From route 2
# >>>>>>>
```

### Step 3: Resolve by Keeping Both Changes

For API files, each route adds its own functions. Keep BOTH:

```bash
# Remove conflict markers, keep both functions:
patch(
  path="nutritrace-main/src/lib/api.js",
  old_string="<<<<<<< HEAD\nexport async function getFirstRoutesData() { ... }\n=======\nexport async function getSecondRoutesData() { ... }\n>>>>>>>",
  new_string="export async function getFirstRoutesData() { ... }\nexport async function getSecondRoutesData() { ... }"
)
```

### Step 4: Verify Build Still Works

**CRITICAL:** After resolving conflicts, rebuild immediately:

```bash
cd nutritrace-main
npm run build
# If build fails, investigate conflict resolution
# Do NOT proceed until build passes
```

### Step 5: Verify Tests Pass

```bash
npm test
# If tests fail, check if conflict resolution dropped a dependency
# Example: test helper function referenced in both branches but one resolution dropped it
```

### Step 6: Complete the Merge

```bash
git add nutritrace-main/src/lib/api.js
git commit -m "Merge bitewise/t_ca5a14d0: Foods route

Resolved conflicts in api.js by keeping both route APIs.
Build verified.
"
```

### Step 7: Repeat for Each Remaining Branch

Continue merging branches one at a time:

```bash
git merge --no-edit bitewise/t_85fdc2e2  # Statistics
# Resolve conflicts if any, rebuild, test, commit

git merge --no-edit bitewise/t_f260b010  # Settings
# ...

git merge --no-edit bitewise/t_407a60c2  # Wellness
# ...

git merge --no-edit bitewise/t_13ebc45b  # Goals
# ...
```

## Real Example from Session 2026-09-05

**Actual conflict resolution:**

```bash
# After merging Diary, Foods branches into staging:
git merge --no-edit bitewise/t_85fdc2e2  # Statistics

# Output:
# Auto-merging nutritrace-main/src/lib/api.js
# Auto-merging nutritrace-main/src/routes/Statistics.svelte
# CONFLICT (content): Merge conflict in nutritrace-main/src/lib/api.js

# Check conflict:
grep -A 10 -B 5 "<<<<<<< HEAD" nutritrace-main/src/lib/api.js
# Output:
#   <<<<<<< HEAD
#   export async function getFoodsData(userId) { ... }  // From Foods route (just merged)
#   =======
#   export async function getStatisticsData(userId) { ... }  // From Statistics route
#   >>>>>>>

# Resolution: Keep both
patch(
  path="nutritrace-main/src/lib/api.js",
  old_string="<<<<<<< HEAD\nexport async function getFoodsData(userId) { ... }\n=======\nexport async function getStatisticsData(userId) { ... }\n>>>>>>>",
  new_string="export async function getFoodsData(userId) { ... }\nexport async function getStatisticsData(userId) { ... }"
)

# Rebuild:
npm run build
# ✓ Build successful

# Test:
npm test
# ✓ All tests pass

# Commit:
git add nutritrace-main/src/lib/api.js
git commit -m "Merge bitewise/t_85fdc2e2: Statistics route

Resolved conflicts in api.js by keeping both getFoodsData and getStatisticsData.
"
```

## Pitfalls & How We Avoided Them

### Pitfall 1: Octopus Merge Without Testing Each Step

**What we didn't do:** Merge all 6 branches at once, then try to resolve conflicts.  
**Why:** Impossible to isolate which branch caused which conflict.  
**What we did:** Merge one at a time, build and test after each, ensuring each merge is solid before adding the next.

### Pitfall 2: Merge Conflict Resolution Dropping Code

**What we didn't do:** Use a visual conflict resolver that accidentally deletes one side.  
**Why:** Easy to lose a function or import during conflict resolution.  
**What we did:** Manual inspection with `read_file`, explicit `patch` calls that keep BOTH changes, then rebuild+test to catch any losses.

### Pitfall 3: Build Passes But Tests Fail

**Real incident (2026-09-05):** Resolved a conflict by keeping both functions, build passed, but tests failed. Reason: A test helper function was referenced in both branches but got accidentally deduplicated during conflict resolution.

**Prevention:** ALWAYS run full `npm test` after conflict resolution, not just `npm run build`. Build alone doesn't catch test breakage.

### Pitfall 4: Merging Branches Based on Stale Main

**What we didn't do:** Merge branch A into B, then merge old-based branch C into AB.  
**Why:** Branch C may have conflicts with both A and B even though it only knew about old main.  
**What we did:** All 6 routes branched from same base (bitewise/t_73c29d82), so conflicts were predictable and isolated (api.js only).

**For future:** If parallel branches are based on different commits, rebase older branches onto fresh main before merging:

```bash
# Before merging branch-c (older base), rebase it:
git fetch origin
git rebase origin/main bitewise/branch-c
# Resolve any new conflicts, re-test, re-push
# Then merge into staging
```

## Checklist: Merging Parallel Branches

- [ ] All branches to merge are pushed to remote: `git branch -r | grep <pattern>`
- [ ] Create staging branch from shared base commit: `git checkout -b staging <base-commit>`
- [ ] Merge 1st branch: `git merge --no-edit origin/<branch-1>`
- [ ] Build passes: `npm run build`
- [ ] Tests pass: `npm test`
- [ ] Commit 1st merge
- [ ] Repeat for each remaining branch (merge → build → test → commit)
- [ ] No unresolved merge conflicts remaining: `git status | grep "both modified"`
- [ ] Final check: `npm run build && npm test` (full suite on merged result)
- [ ] Push to remote: `git push origin staging`

## Commands Used (2026-09-05)

```bash
cd /root/BiteWise/nutritrace-main

# Fetch all branches
git fetch origin

# Create staging from backend base
git checkout -b bitewise/staging origin/bitewise/t_73c29d82

# Merge routes one by one
git merge --no-edit origin/bitewise/t_cb26e378
git merge --no-edit origin/bitewise/t_ca5a14d0
git merge --no-edit origin/bitewise/t_85fdc2e2
git merge --no-edit origin/bitewise/t_f260b010
git merge --no-edit origin/bitewise/t_407a60c2
git merge --no-edit origin/bitewise/t_13ebc45b

# After each merge (if conflict):
npm run build
npm test
git add <resolved-files>
git commit

# Final verification
npm run build && npm test

# Push staging branch
git push -u origin bitewise/staging
```

## Next Step: Deploy Staging Branch

Once all merges are complete and committed, hand off to devops:

```
Title: Deploy BiteWise redesign to staging
Assignee: devops
Priority: 100
Body:
  All 6 redesign routes merged into bitewise/staging.
  Staging branch: bitewise/staging (commit: <sha>)
  Build: ✓ passed
  Tests: ✓ all pass
  
  Task: Deploy bitewise/staging to Railway staging environment
```

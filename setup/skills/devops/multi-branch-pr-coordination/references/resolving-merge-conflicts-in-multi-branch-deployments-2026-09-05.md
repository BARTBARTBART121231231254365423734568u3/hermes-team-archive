# Resolving Merge Conflicts in Multi-Branch Deployments

**Session:** 2026-09-05 BiteWise Redesign (6 Routes Merge)  
**Issue:** Six independently-developed redesign branches (Diary, Foods, Statistics, Wellness, Settings, Goals) could not be merged together using octopus merge  
**Root Cause:** Branches diverged during parallel development and modified shared files (e.g., `lib/api.js`)

## The Scenario

Six route redesigns were built in parallel on separate branches from the same foundation (t_73c29d82 backend):
- `bitewise/t_cb26e378` (Diary)
- `bitewise/t_ca5a14d0` (Foods)
- `bitewise/t_85fdc2e2` (Statistics)
- `bitewise/t_f260b010` (Settings)
- `bitewise/t_407a60c2` (Wellness)
- `bitewise/t_13ebc45b` (Goals)

Goal: Merge all 6 into a single `bitewise/staging` branch for deployment.

**Attempt:** Octopus merge (merging multiple branches at once)
```bash
git checkout -b bitewise/staging bitewise/t_73c29d82
git merge --no-edit bitewise/t_cb26e378 bitewise/t_ca5a14d0 bitewise/t_85fdc2e2 bitewise/t_f260b010 bitewise/t_407a60c2 bitewise/t_13ebc45b
```

**Result:** Merge failed with conflicts in `nutritrace-main/src/lib/api.js`
```
ERROR: content conflict in nutritrace-main/src/lib/api.js
fatal: merge program failed
Automated merge did not work.
Should not be doing an octopus.
Merge with strategy octopus failed.
```

## Why Octopus Merge Failed

Octopus merge attempts to merge 2+ branches in a single operation. It works when:
- Branches touch different files
- Changes to the same file don't conflict

It FAILS when:
- Multiple branches modify the same file with overlapping changes
- Merge conflicts require human decision-making

In the BiteWise case: All 6 routes added new API endpoints/functions to the shared `lib/api.js` file. Git's auto-merge algorithm couldn't resolve where each function should go and whether there were duplicate definitions.

## The Solution: Sequential Merge with Conflict Resolution

Instead of trying to merge all 6 at once, merge them **one at a time** and resolve conflicts as you go:

### Step 1: Start from the Base
```bash
git checkout -b bitewise/staging bitewise/t_73c29d82  # Start from backend foundation
```

### Step 2: Merge Each Branch Sequentially
```bash
git merge --no-edit bitewise/t_cb26e378  # Diary
# Check if clean
git status

git merge --no-edit bitewise/t_ca5a14d0  # Foods
# Check if clean
git status

# Continue for each branch...
```

### Step 3: If Conflicts Occur, Resolve Manually

When git detects a conflict:
```bash
# View the conflicted file
# Look for <<<<<<< / ======= / >>>>>>>
# Sections to decide which changes to keep

# Use the editor/read_file + patch to resolve:
# - Read the conflicted section
# - Determine which version(s) should be kept
# - Keep both if both are needed (merge manually)
# - Remove markers after resolving

git add <resolved-file>
git commit -m "merge: resolve conflicts from bitewise/t_ca5a14d0 (Foods route)"

# Continue with next branch
git merge --no-edit bitewise/t_85fdc2e2  # Statistics
```

### Step 4: Verify After Each Merge

After merging each branch:
1. **Check for syntax/build errors:** `npm run build` or `cargo check`
2. **Run tests:** `npm run test` or `cargo test`
3. **Verify the merge didn't break anything:** Spot-check file diff, log output

This catches issues immediately, before moving to the next merge.

### Step 5: Push the Merged Branch

Once all 6 branches are merged and tested:
```bash
git push -u origin bitewise/staging
```

Now `bitewise/staging` contains all 6 route redesigns merged together, ready for deployment.

## Key Differences from Octopus Merge

| Approach | Octopus Merge | Sequential Merge |
|----------|---------------|------------------|
| **Conflicts** | Fails immediately, exits with error | Pauses at each conflict, lets you resolve |
| **Build verification** | Never reached (merge failed) | After each merge, can verify build/test |
| **Visibility** | Hard to debug (which branch caused the issue?) | Clear (exactly which branch introduced the conflict) |
| **Time** | Fast (fails fast) | Slower (manual resolution per conflict) |
| **Completeness** | Incomplete (no output branch) | Complete (all branches merged into staging) |

## Handling Conflicts in `lib/api.js` (Real Example)

**File has multiple `function` definitions for API handlers:**
```javascript
// From Diary route
export async function logEntry(req, res) { /* ... */ }
export async function getEntries(req, res) { /* ... */ }

// From Foods route (added later, same file)
export async function searchFoods(req, res) { /* ... */ }
export async function logFoodEntry(req, res) { /* ... */ }
```

**When merging, both changes try to ADD their functions, but git sees competing insertions:**
```
<<<<<<< HEAD (destination branch, bitewise/staging so far)
export async function logEntry(req, res) { /* Diary version */ }
export async function getEntries(req, res) { /* Diary version */ }
=======
export async function logEntry(req, res) { /* Foods version */ }
export async function getEntries(req, res) { /* Foods version */ }
export async function searchFoods(req, res) { /* Foods version */ }
export async function logFoodEntry(req, res) { /* Foods version */ }
>>>>>>> origin/bitewise/t_ca5a14d0
```

**Resolution:** Keep BOTH sets of functions (they're for different routes, no duplication):
```javascript
// Diary route handlers
export async function logEntry(req, res) { /* Diary version */ }
export async function getEntries(req, res) { /* Diary version */ }

// Foods route handlers
export async function searchFoods(req, res) { /* Foods version */ }
export async function logFoodEntry(req, res) { /* Foods version */ }
```

Remove the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) and commit.

## When Sequential Merge Isn't Enough

If a conflict is more complex (e.g., two routes modify the SAME function's signature), you may need to:
1. **Read both versions** (HEAD vs. incoming) to understand the intent
2. **Merge logic manually** — combine both changes into a single best version
3. **Re-test** to ensure the merged version works

Example: Two routes both added a `userId` parameter to `logEntry()`, but with different defaults.

Resolution: Decide if the parameter is truly shared (make one version) or route-specific (rename for clarity, e.g., `logEntryFromDiary()` vs. `logEntryFromFoods()`).

## Best Practice: Prevent Conflicts with Shared Infrastructure

For future multi-route redesigns:
1. **Decide on shared API file structure upfront** (route-specific files vs. shared file)
2. **If using a shared file:** Establish a naming/organization convention (e.g., each route's functions in a clearly-marked section with comments)
3. **Create shared APIs in the foundation task** (before routes fan out) so routes don't all try to add to the same file
4. **Test each route individually** before merging to catch issues early

This prevents the octopus merge problem entirely.

## References

- Git merge strategies: https://git-scm.com/docs/git-merge#_merge_strategies
- Conflict markers: https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging
- Resolving conflicts with `git mergetool`: https://git-scm.com/docs/git-mergetool

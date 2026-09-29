# Railway Environment Setup & Staging Deployment (Session 2026-09-06)

## Incident Summary

BiteWise staging deployment revealed multiple Railway configuration pitfalls during 2026-09-05 to 2026-09-06:
1. Staging environment created but service source branch not updated (still pointed at main)
2. Devops protocol violations on deployment (exited rc=0 without reporting blockers)
3. SETUP_TOKEN env var set but app rejected it due to form/validation mismatch
4. Production deployment succeeded but design layout wasn't visible (empty-state UX issue, not code)

## Key Lesson: Verify Environment Setup BEFORE Devops Task

### Environment Creation Checklist

**On Railway dashboard, when creating staging environment:**

1. ✅ Click "+ New Environment", name it `staging`
2. ✅ Select "Duplicate Environment" from `production` (imports services, volumes, variables)
3. ✅ Click "Create Environment"

**CRITICAL — Next step not obvious in UI:**

4. ✅ **Update the SERVICE source branch** (NOT automatic when duplicating environment)
   - Navigate to staging environment → BiteWise service → Settings → Source
   - Verify/set git branch to the **FEATURE BRANCH** you want to deploy (e.g., `bitewise/staging`)
   - **Default behavior:** Service remains on `main` even after environment duplication
   - **Impact:** Devops deploys old code to new environment without error (service shows "Online" but runs wrong code)

**Verification command (before devops task):**
```bash
railway link --project BiteWise --environment staging
railway status | grep -i "repo\|source\|branch"
# Should show: bitewise/staging (or whatever branch you want)
# If it shows: main, fix it in dashboard BEFORE creating devops task
```

### Why This Matters

**Session 2026-09-05 Incident:**
1. User created staging environment via UI (Duplicate from production)
2. Coder merged 6 route branches into `bitewise/staging`
3. Devops task created to deploy `bitewise/staging`
4. Devops started multiple retries (protocol violations) when trying to redeploy
5. Root cause: Staging service was **still pointing at `main` branch**, not `bitewise/staging`
6. Fix: Manually update staging service source to `bitewise/staging` in Railway dashboard Settings
7. Fresh devops task succeeds with correct branch linkage

## SETUP_TOKEN Validation (2026-09-05 Lesson)

### Token Not Recognized by Form

**Symptom:** SETUP_TOKEN env var is set and correct, validation endpoint works (correct token → 200, wrong token → 403), but account creation form still shows "Invalid or missing setup token".

**Root cause:** Frontend registration form was using a different request path (`/wizard`) than the main API route, and the wizard request omitted the `setupToken` field entirely.

**Fix:** Coder added setupToken capture and submission to the wizard registration flow (commit c808090). No environment reconfiguration needed.

**Lesson:** Token validation failures might not be token issues. Debug network requests (DevTools → Network tab) to see what's actually being sent to the backend. Compare:
- What token was entered in the form
- What token was sent in the HTTP request body
- What the backend received vs. compared

Mismatches are usually form/transmission issues, not env var issues.

## Test Data Seeding for Empty-State Pages

**Critical blocker identified 2026-09-06:**

After successful production deployment, user reviewed the Foods page and saw "No foods yet" with action buttons. Thought the layout wasn't deployed, but actually the layout code was correct—it just wasn't visible in the empty state.

**Solution:** Seed test data (5-10 foods) to the admin account so the two-column layout renders.

**Devops task pattern:**
```
Title: Seed test data to <environment>
Assignee: devops
Body:
  Production deployed. Layout not visible in empty state.
  Seed 5-10 test foods to admin account so the two-column layout (Recent & frequent | Fast ways to log) displays.
  
  Foods:
  - Free-range eggs (icon, 155 kcal, 12g protein)
  - Protein oats (250 kcal, 15g protein)
  - Turkey sandwich (400 kcal, 25g protein)
  - Protein shake (180 kcal, 25g protein)
  - Greek yogurt (100 kcal, 15g protein)
  
  Verify: https://bite-wise.up.railway.app/Foods shows layout with foods.
```

## Multi-Environment Variable Sync

**When duplicating environment in Railway:**

- Variables ARE copied (e.g., SETUP_TOKEN will be duplicated)
- But double-check critical ones after duplication (SETUP_TOKEN, DATABASE_URL, API_KEYS)
- If production changed a variable after the duplicate, staging won't have the new value
- Solution: After environment creation, update critical variables explicitly in staging settings

## Devops Protocol Violations on Deployment

**Pattern observed (5+ violations across 4 tasks):**

- Task exits cleanly (rc=0) without calling kanban_complete or kanban_block
- No error message, just silence
- Multiple retries fail identically

**Common causes:**
1. **Wrong git source on service** (service pointing at old branch)
2. **Environment doesn't exist** (missing in Railway)
3. **Merge conflicts unresolved** (branches can't be merged)
4. **Environment variable missing or wrong** (SETUP_TOKEN mismatch)
5. **Container build succeeds but startup fails** (code issue, not deployment)

**Mitigation:**
- Always verify infrastructure BEFORE creating devops task
- If devops fails 2+ times silently, investigate the infrastructure (branch linkage, env vars, git state)
- Create FRESH devops task after fixing blockers (don't retry same task)
- Use explicit "pickup" signal task (priority 100) if new deployment task sits in ready queue

## Staging → Production Promotion Workflow

### Step 1: Deploy to Staging
```
Title: Deploy BiteWise redesign to Railway staging
Assignee: devops
Branch: bitewise/staging
Environment: staging (must have been created in dashboard first)
Verify: Deploy succeeds, staging URL reports Online
```

### Step 2: Test Staging (with data)
```
Load https://bitewise-staging.up.railway.app
Review all 6 routes (Diary, Foods, Statistics, Wellness, Goals, Settings)
If empty-state pages exist, seed test data first
User approves: "Ready for production"
```

### Step 3: Deploy to Production
```
Title: Deploy BiteWise redesign to production (APPROVED)
Assignee: devops
Branch: bitewise/staging (same branch, diff environment)
Environment: production
Verify: Deploy succeeds, production URL reports Online
```

### Step 4: Verify Production Live
```
Load https://bite-wise.up.railway.app
Test all features (actual user flow, not just health checks)
If empty-state pages, DON'T blame deployment—that's UX, not code
```

## Handoff Note for Future BiteWise Deployments

1. **Environment setup is prerequisite, not part of devops task**
   - Staging environment must exist in Railway dashboard before devops task
   - Service source branch must point to the feature branch (not main)
   - Verify with `railway status` before creating task

2. **Empty-state pages hide layouts**
   - After design deploy, always seed test data
   - Don't assume empty page = broken layout
   - Devops task for test data seeding is separate from deployment task

3. **Multi-environment branching strategy**
   - All routes merged into `bitewise/staging`
   - `bitewise/staging` → deploy to staging environment
   - `bitewise/staging` → deploy to production environment (same branch, different Railway env)
   - Don't create separate branches for production; same branch, different Railway environment

4. **If deployment task protocol-violates**
   - Check git source branch on the service in Railway dashboard
   - Check environment variables match expected (SETUP_TOKEN, DATABASE_URL, etc.)
   - Create FRESH task after fixing infrastructure, don't retry

5. **Test data seeding should be automated**
   - Future: Create `scripts/seed-test-data.js` to populate sample foods, meals, diary entries
   - Run after staging deploy, before user review
   - Same script can seed production for QA/demo purposes

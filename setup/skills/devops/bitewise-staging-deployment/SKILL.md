---
title: BiteWise Staging & Production Deployment
name: bitewise-staging-deployment
description: Deploy BiteWise redesign to Railway staging/production.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when deploying BiteWise redesign features to Railway staging or production environments.
metadata:
  hermes:
    tags: ["bitewise", "railway", "deployment", "staging", "production", "devops"]
    related_skills: ["railway-cli", "github-pr-workflow"]
---

# BiteWise Staging & Production Deployment

End-to-end workflow for deploying the BiteWise redesign (multiple parallel feature branches) to Railway staging and production environments.

## When to Use

- Deploying a completed redesign sprint (all routes built and QA'd) to staging for user review
- Preparing production release after staging approval
- Setting up new staging/production environments in Railway for BiteWise project
- Coordinating between coder (branch merges), QA (verification), and devops (Railway deployment)

## Prerequisites

- All feature branches exist on remote (pushed by coder)
- QA pass complete (t_efebe20e equivalent: 0 blocking defects, all routes tested)
- User has Railway account with BiteWise project (bartbartbart2002@gmail.com)

## Phase 1: Environment Setup (One-Time)

### Create Staging Environment (If Missing)

**Why:** Railway deployments target specific environments (production, staging, test). The BiteWise project may have ONLY production initially.

**Steps:**
1. User navigates to Railway dashboard → BiteWise project → Settings → Environments
2. Click "+ New Environment"
3. Name it `staging`
4. Select "Duplicate Environment" → copy from `production` (includes services, variables, volumes)
5. Click "Create Environment"

**Result:** BiteWise staging service exists, mirroring production config (same volume, environment variables, etc.)

**Verification:**
```bash
railway status --project BiteWise --environment staging
# Should show: BiteWise service, Online, URL like https://bitewise-staging.up.railway.app
```

⚠️ **Pitfall:** If staging environment already exists but shows 0 deployments, it may be empty (no service). Verify the service is linked and has volumes/variables configured.

## Phase 2: Branch Merge (Coder Task)

### Merge All Feature Branches Into Staging Branch

**Why:** Each route (Diary, Foods, Statistics, Settings, Wellness, Goals) is built on a separate branch (bitewise/t_cb26e378, etc.). They must be merged into a single branch for staging deployment.

**Expected conflicts:** `nutritrace-main/src/lib/api.js` often has conflicts when multiple routes add API endpoints.

**Task:** Create kanban task for coder:
```
Title: Resolve merge conflicts: combine all 6 redesign routes into staging branch
Assignee: coder
Body:
  Merge 6 completed redesign routes into bitewise/staging branch.
  Routes: Diary, Foods, Statistics, Settings, Wellness, Goals
  Expected conflicts: lib/api.js (multiple route APIs added)
  Task outcome: bitewise/staging branch ready to deploy
```

**Verification (coder reports):**
```bash
cd /root/BiteWise/nutritrace-main
git branch | grep bitewise/staging     # Branch exists
git log bitewise/staging --oneline | head  # Recent merge commits
```

**Result:** Coder completes, pushes `bitewise/staging` with the intended release content merged cleanly.

⚠️ **Pitfall:** Merge conflicts are normal. Resolve them by retaining each compatible change; do not send source-history work to the user.

### Remote-source promotion gate (required before DevOps is assigned)

1. Fetch the remote first; never infer deployment source from a local worktree.
2. Identify the exact approved release commit and the Railway service's configured source branch.
3. Have the coder promote the approved commit to that **remote** source branch using a fast-forward when possible; otherwise use a documented, non-force merge that preserves existing staging work.
4. Run the server suite, frontend production build, and `git diff --check` on the resulting candidate.
5. Read back both `git rev-parse origin/<source-branch>` and `git ls-remote origin refs/heads/<source-branch>`; they must name the approved commit or a documented descendant before unblocking deployment.

⚠️ **Pitfall:** Do not assign DevOps merely because an approved commit exists locally — Railway builds the remote branch configured on its service, so deployment can silently ship older code.

⚠️ **Pitfall:** When a deployment task blocks because the remote source lacks the approved commit, route a source-promotion task to the coder and make the deployment task depend on it; do not make the user manually push a branch or repeatedly retry DevOps.

### Release-content parity gate (required for long-lived staging branches)

Before promoting a feature-only staging branch or asking the user to review it, compare it to the current application release branch:

```bash
git fetch origin --prune
git rev-parse origin/main origin/bitewise/staging
git merge-base origin/main origin/bitewise/staging
git log --oneline origin/bitewise/staging..origin/main -25
git log --oneline origin/main..origin/bitewise/staging -25
```

1. Treat a staging branch whose merge base is substantially behind `origin/main` as an incomplete release candidate, even if it contains the requested feature commits.
2. Route a coder task to create a non-force integration commit containing both the current app branch and approved staging-only feature work. Resolve conflicts deliberately; never replace one history wholesale.
3. Require the resulting remote staging SHA to be an ancestor/descendant merge of both inputs, then run the full server suite, production frontend build, and `git diff --check` before deployment.
4. Before user review, verify the actual staging build at the target mobile viewport in a clean browser context and inspect the feature route. Confirm both the current global navigation/safe-area shell and the requested feature UI are present.
5. If the user still sees an older mobile shell after the live deployment SHA and clean-context check match, treat it as a PWA/browser-cache condition: have them fully close and reopen the app/tab, then hard-refresh or clear that site's data if needed. Do not blame caching before proving source and live-build parity.

⚠️ **Pitfall:** A healthy Railway deployment and correct feature endpoint do not prove staging is current. A stale release branch can serve an older navigation shell and Connections UI while still reporting SUCCESS; compare branch histories and perform live visual parity checks before telling the user to test.

## Phase 3: Deploy to Staging

### Preflight stateful backup and readiness configuration

Before deploying a candidate whose readiness depends on encrypted remote backups:

1. Read back the exact staging project/environment/service and source SHA.
2. Inspect required variable **set-state and non-empty state** without printing values. A variable name that exists with an empty value is missing configuration; stop before deployment.
3. Require separate staging values for the encryption key, remote endpoint, bucket, access key ID, secret key, destination mode, and prefix. Keep the bucket private and credentials least-privilege.
4. Validate every non-secret value against the application's accepted grammar before deploying. For an R2 S3 endpoint, require the account endpoint only (`https://<account-id>.r2.cloudflarestorage.com` unless the code explicitly supports a jurisdiction host); reject bucket URLs, dashboard text, paths, query strings, credentials, or copied documentation labels.
5. When Railway permits only one attached volume, use an independently operated object store rather than weakening the off-volume requirement or mounting another path on the same volume.
6. Estimate storage and request operations against the provider's included allowance with explicit headroom; bound retention and polling before enabling the scheduler.
7. Deploy only after the configuration preflight passes. Then trigger a real encrypted backup, verify the exact remote object, require `/api/ready` to return healthy based on recent verified evidence, perform an isolated restore, and test failure-closed behavior.

⚠️ **Pitfall:** Do not drive Railway's variable editor speculatively when rows expose repeated unlabeled controls. Use the guarded deployment/CLI path or have the user edit the exact named field; ambiguous menu targeting can mutate the wrong resource. If any unexpected service/resource appears, stop immediately, record its exact environment/service identity, route cleanup to DevOps, and verify the intended BiteWise service remained untouched before continuing.

⚠️ **Pitfall:** Never infer that secrets are usable because a dashboard field or variable name exists — empty values survive configuration screens and produce a successful deployment whose readiness fails at runtime.

⚠️ **Pitfall:** Do not log or copy credentials into chat, commands, task cards, or reports. If interactive setup is necessary, have the user enter values directly in the provider UI; generate new encryption material into the native Windows clipboard without displaying it, then verify only its length.

### Prove object-store semantics before the final staging gate

1. Exercise the real provider with a disposable encrypted object before calling the integration deployable: conditional PUT, exact-object HEAD, paginated LIST, conditional DELETE, and cleanup. Remove every diagnostic object and verify the prefix is clean.
2. Treat S3-compatible providers as behaviorally compatible, not identical. Never round-trip a provider's opaque `VersionId` into HEAD, GET, or DELETE unless the live provider proves those calls are supported.
3. When versioned operations are unavailable, bind identity to the exact upload ETag: persist that ETag in trusted publication evidence, require `If-Match` on active HEAD/GET/DELETE where supported, compare the returned ETag, and retain streamed ciphertext SHA-256 verification.
4. Fail readiness closed for legacy or incomplete evidence that lacks the trusted identity anchor. A matching size and caller-copyable metadata are insufficient because a replacement object can reproduce both.
5. Hold the shared publication fence from before remote upload through retention, final identity verification, and durable evidence persistence. Test concurrent backups with retention count 1 and a process-death/restart path through the real scheduler entrypoint.
6. Run an adversarial replacement probe: same size and copied metadata but a different ETag must fail readiness and restore verification.

⚠️ **Pitfall:** Do not stop at mocked SDK tests for a new S3-compatible provider — unsupported versioned operations can pass locally and fail only against the live API.

⚠️ **Pitfall:** Do not persist readiness evidence without the provider identity used during upload — an unconditioned HEAD can accept a replaced object with copied metadata.

### Deployment updates for Thomas

- Report transitions proactively: implementation commit, test result, independent verdict, deployment start, live provider result, and blocker. Do not wait for Thomas to ask for status. When reporting on still-running work, include the latest worker heartbeat note and what the worktree already contains (new files, test counts) — never just 'it is running'.
- State `ready`, `running`, `blocked`, and `done` precisely; never describe a queued task as active.
- Keep this channel BiteWise-only. Exclude unrelated agent, Hermes, or other-project activity from status updates.
- Escalate after two repeated misses on the same acceptance criteria instead of waiting for another user prompt.

### Create Devops Task

```
Title: Deploy BiteWise redesign to Railway staging
Assignee: devops
Priority: 100
Body:
  Merge complete. bitewise/staging branch ready for staging deployment.
  
  Context:
  - Repo: /root/BiteWise/nutritrace-main
  - Branch: bitewise/staging (all 6 routes merged)
  - Railway Project: BiteWise
  - Target Environment: staging (already created)
  
  Requirements:
  1. Link to BiteWise project, staging environment
  2. Deploy bitewise/staging branch to staging
  3. Verify deployment succeeded (check logs, confirm live staging URL)
  4. Report staging URL to user
```

**Devops execution:**
1. Read Railway status with explicit project and environment identifiers; verify the environment, service source repository, source branch, and exact live commit before changing anything.
2. Treat a push to the connected staging branch as a possible automatic deployment. Read back the active deployment SHA and live status endpoint before requesting a redundant redeploy.
3. Use the reviewed `railway deploy-verified <target.json> --commit <full-sha> --apply` path for an explicit redeploy; the manifest must bind project, environment, service, repository, and branch.
4. Verify a successful/RUNNING deployment, fresh logs, root response, and the feature’s public status endpoint.

**Feature-flagged staging flows:**
- Ship the reviewed default-deny code first, then verify the public status reports the feature as disabled.
- Enable a nonsecret staging-only flag only after confirming the exact Staging environment in the Railway dashboard; never mirror it to Production.
- If an external operator must change the flag, give one exact variable name/value and dashboard location, then read the live status endpoint again before telling the user to proceed.
- For a restricted connection or pilot integration, keep the UI card hidden until the authenticated account is explicitly eligible. Before directing the user to its Settings → Connections flow, verify that the account exists on the exact staging server and that the allowlist has been applied; a healthy deployment alone does not prove either condition.
- Treat a reported staging signup as unverified until the staging server confirms the account. A cached PWA can show an old frontend or retain a stale session; have the user reopen the exact staging URL in a browser, then verify server-side before enabling account-scoped access.
- Do not create a user account, issue user credentials, or test user-owned access on the user’s behalf.
- For a one-time, write-only connection token, finish and verify the maintained mobile setup recipe **before** directing the user to reveal it. Once the user has it, never request it, a screenshot of it, or a retry that rotates it; continue with the token only through the Shortcut’s Import Question/Authorization header and record only pass/fail outcomes.

**CRITICAL CHECK (2026-09-05 lesson):** Before redeploying, verify the service is SOURCE-LINKED to the right branch:
```bash
railway status | grep -i "repo\|branch"  # Should show bitewise/staging, not main
```
If it shows `main`, the staging service was never linked to the correct branch. Update the Railway service setting to point at `bitewise/staging` in the project → service → settings → source branch.

**Verification:** Devops reports staging URL and confirms service online:
```
https://bitewise-staging.up.railway.app
```

⚠️ **CRITICAL PITFALL:** Devops tasks can protocol-violate multiple times if infrastructure blockers aren't fixed first. If staging environment doesn't exist, multiple devops retries will fail. Verify environment exists BEFORE creating the devops task.

⚠️ **DEVOPS PROTOCOL VIOLATION PATTERN (2026-09-05):** When devops hits a deployment blocker (missing env, wrong branch, environment pointing at wrong git ref), it exits cleanly (rc=0) without calling kanban_complete or kanban_block. Multiple retries appear to fail silently. ROOT CAUSES:
  1. **Wrong git source:** Staging service was pointing at `main` branch instead of `bitewise/staging` → deployed old code, but service showed as "Online"
  2. **Missing environment variable:** SETUP_TOKEN wasn't set initially → account creation blocked → later found to be token mismatch (not missing, but wrong value in env vs. what form expected)
  3. **Worker dispatch livelock:** When a devops task hits 4+ protocol violations, creating a new task (even with priority 100) doesn't guarantee pickup — may need explicit "pickup signal" card (e.g., "URGENT: Pick up task X") to force dispatcher to route to devops

MITIGATION: After devops task fails 2+ times silently:
  - Verify infrastructure manually (git source for service, env vars set, service linked to correct branch)
  - If infrastructure is correct, create a FRESH devops task rather than retrying the same one (retry loop detection may block further attempts)
  - Use explicit "pickup signal" kanban task (priority 100) to force dispatcher pickup if new task still sits in ready queue

## Phase 4: Staging Test & QA

### Design-reference parity gate (required for approved mockups)

When the user selects an HTML/mockup option, treat its live preview as a **binding specification**, not loose inspiration. Before asking for staging review:

1. Give the coder the approved preview URL and name the required visual regions (especially the lower-page hierarchy), not just a high-level theme.
2. Require the implementation to preserve the approved hierarchy in both populated and empty-data states. Do not let an existing empty-state component collapse the page back into a legacy layout.
3. Seed representative **staging-only** foods/meals/diary data before live QA, so the full layout is visible.
4. Before implementation, record the approved mobile behavior for every important desktop relationship: whether columns may stack, must remain side-by-side, or may become a deliberately scrollable canvas. Never infer this from the desktop mockup. If the user requires columns to remain side-by-side on a phone, encode that literally in the coder and QA acceptance criteria; do not let a generic media query stack them below each other.
5. Compare the live authenticated Foods route at desktop and mobile against the preview section-by-section: command-center header, nudge, Food Library/search, recent/frequent groupings, Quick Add, saved meal, streak treatment, and the explicitly approved mobile column behavior.
6. If the user says a region "is not the same," stop treating deployment/health as success. Create a focused coder correction task against the preview, then a new staging deployment + populated-data visual-QA task. Do not iterate on the previous deployment card.

### User Reviews Staging

**URL:** https://bitewise-staging.up.railway.app  
**Scope:** Full end-to-end: registration, add foods, log meals, view stats, edit settings, etc.

**Expected onboarding flow:**
1. Load staging URL
2. See "Create Your Account" page
3. Enter username, email, password, birthday
4. Click "Get Started"
5. Set up a goal, add a food, log a meal
6. Navigate through all 6 routes
7. Verify redesign looks correct (fonts, colors, layout, mobile responsiveness)

⚠️ **CRITICAL:** If account creation page shows "Invalid or missing setup token" error, this is USUALLY a token VALUE MISMATCH, not a missing env var:
   - SETUP_TOKEN env var IS set in Railway staging (value: "test")
   - Validation code IS correct (endpoint tests pass with correct token)
   - BUT form submission still fails with "Invalid or missing setup token"
   - ROOT CAUSE TBD (2026-09-05): Likely frontend form capture, network transmission, or backend comparison issue — requires debugging network requests (see Phase 6)
   
   If env var is truly missing:
   - Devops sets: `railway variable set SETUP_TOKEN=test --environment staging`
   - Redeploy: `railway redeploy --yes`
   - Retry account creation
   
   If env var is set but form still fails, escalate to coder for root-cause debugging (see Phase 6 below).

**User approval:** Once satisfied, user signals: "Ready for production."

## Phase 5: Production Deployment

### Enforce the staging approval checkpoint

Treat staging deployment, production deployment, and the next product milestone as three separate gates. When Thomas asks to see staging before continuing:

1. Scope the active deployment card to the approved exact SHA and **staging only**.
2. Before dispatch, split any combined staging/production card into: (a) a staging-only deploy-and-verify card, (b) a production card blocked on Thomas's explicit approval, and (c) a separate approval gate that remains a parent of the next milestone. This prevents completion of staging from authorizing either production or future product work.
3. Deploy and verify staging, then report the clickable staging URL, exact deployed revision, deployment identity, rollback pointer, and live-check result in the originating conversation.
4. Complete the staging-only card after verified deployment. Keep the production card and next-milestone approval gate blocked until Thomas explicitly approves each continuation.
5. If a legacy combined card is already running, add the current user override immediately, create the two blocked successor gates before closing the staging scope, and link the next-milestone gate as an additional parent of the existing milestone card.
6. Use `needs_input` at most once on a card. If a prior pause already consumed its block-loop allowance, do not block it again after successful staging verification; repeated intentional blocks can route completed work to triage. Record the verified checkpoint, split the remaining scope into blocked successors, and close or administratively resolve the legacy card.

⚠️ **Pitfall:** Do not treat visual approval of a candidate as production approval — visual sign-off releases the exact-head/staging gate only when Thomas requested a staging checkpoint, because advancing further removes his promised review opportunity.

⚠️ **Pitfall:** Do not model a human checkpoint by repeatedly blocking one goal-mode card that also owns later stages; the board interprets repeated blocks as a stuck task and may escalate it to triage even when staging is successfully live.

### Create Production Deploy Task

**Only after staging approval.** Production deployment is gated on explicit user go-ahead.

```
Title: Deploy BiteWise redesign to production
Assignee: devops
Priority: 100
Body:
  Staging approved. bitewise/staging branch ready for production.
  
  Context:
  - Repo: /root/BiteWise/nutritrace-main
  - Branch: bitewise/staging (all 6 routes merged, tested in staging)
  - Railway Project: BiteWise
  - Target Environment: production
  
  Requirements:
  1. Deploy bitewise/staging to BiteWise production environment
  2. Verify production deployment succeeded (check logs, confirm live URL)
  3. Have rollback plan ready (note previous deployment ID in case of issues)
  4. Monitor briefly for obvious breakage
  5. Report final live production URL
```

**Devops execution:**
```bash
unset RAILWAY_PROJECT_ID RAILWAY_SERVICE_ID RAILWAY_ENVIRONMENT_ID
railway link --project BiteWise --environment production
railway status  # Verify target is production, not staging
railway redeploy --yes
railway logs --latest --lines 20  # Verify startup successful
```

**Verification:** Devops reports production URL:
```
https://bite-wise.up.railway.app
```

**Post-deploy verification (user or devops):**
- Load production URL
- Verify redesigned routes appear (Diary, Foods, Statistics, etc.)
- No 500 errors, no console errors
- If any issues, devops has previous deployment ID ready for rollback

⚠️ **Coordinator override for stuck-but-actually-done tasks:** if a coder/devops worker crash-loops 3+ times ("exited cleanly rc=0 without calling kanban_complete/kanban_block") on a well-scoped fix task, do not just keep respawning the same task. First check whether the actual work is sitting correctly finished in the workspace (uncommitted diff matches the spec, `npm run build` and any project regression script both pass). If so, the coordinator should commit/push it directly, verify it, and complete the task on the worker's behalf with a note that the assigned profile had a pure reporting failure (not incomplete work) — this unblocks the pipeline in minutes instead of repeating the same crash-loop.

⚠️ **CRITICAL:** Do NOT assume production deploy succeeded just because `railway redeploy` exits with code 0. Verify:
1. Build succeeded in logs (no compilation errors)
2. Container started (look for app startup message, timestamp is recent)
3. Live endpoint actually works (curl the URL or load in browser)

See `references/verify-deployment-live-before-reporting-success.md`.

## Common Failures & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Devops task protocol-violates 3+ times | Missing staging environment, or branches not merged | Verify environment exists in Railway dashboard. Verify bitewise/staging branch exists: `git branch -a \| grep staging`. If missing, create fresh coder task to merge. Then create fresh devops task. |
| Staging URL shows 404 or "Cannot GET /" | Build succeeded but app binary didn't start correctly | Check `railway logs --latest --lines 50` for startup errors. Common: missing SETUP_TOKEN env var (see Phase 4). |
| Account creation blocked: "Setup token required" | SETUP_TOKEN env var not set in staging | Create devops task: `railway variable set SETUP_TOKEN=test-token --environment staging && railway redeploy --yes` |
| Deployment succeeds but live URL shows OLD redesign (old routes, old styling) | Docker layer cache reused old binary instead of rebuilding | Make a REAL code change (not comment), commit, push, redeploy. Verify startup timestamp is recent in logs. See `references/docker-image-cache-on-from-source.md` |
| Production deploy succeeds but live URL shows staging data/styling | Deployed wrong branch or wrong environment targeted | Verify: `railway status` shows production, `git log` shows bitewise/staging HEAD |
| Guarded `deployment redeploy --from-source` fails (exit 1) creating no new deployment, but the CURRENT live production deployment is already at the exact target commit | Railway's deployment metadata still labels the source as the old branch (e.g. `bitewise/staging`) even though a fast-forward merge made that commit identical to `main` HEAD | This is a cosmetic provenance mismatch, not a functional gap. Do NOT keep retrying the guarded redeploy or treat it as a blocking failure. Confirm via `railway status`/deployment history that the live deployment SHA matches the new `main` HEAD, run health checks, and do real visual verification against what's already live — it is already serving the correct code. Split off the branch-label fix as a separate LOW-priority devops cleanup task so it doesn't gate user-facing verification. |
| A NEW commit is on `main` (e.g. a follow-up fix) but repeated guarded redeploys keep resolving to the STALE `bitewise/staging` commit — the fix genuinely never goes live, live behavior proves it (e.g. a proxy endpoint still 403s) | The Railway service's "Branch connected to production" setting (Settings → Source) is still literally set to `bitewise/staging`, not `main`. A prior fast-forward merge (see row above) can make this LOOK resolved because commit SHAs briefly matched — but the branch pointer itself was never changed, so as soon as `main` and `staging` diverge again (any new commit only pushed to `main`), Railway silently redeploys the old branch. Agents cannot fix this via CLI/API (`railway redeploy`, guarded manifests) — it is a dashboard-only setting and out of scope for automated guards by design. | This is a genuine (not cosmetic) blocker once the branches have diverged — escalate immediately to the user with a precise pointer: "Railway dashboard → service → Settings → Source → Branch connected to production is set to `bitewise/staging`; please change it to `main`." The branch dropdown lists many stale feature branches (`bitewise/t_*`, `coder/t_*`, etc.) alphabetically, so `main` may be scrolled out of view — tell the user to scroll up in that specific dropdown to find it. After the user confirms the change, immediately re-run the guarded deploy and verify with a real live check (curl/HTTP call against the actual fixed behavior, not just deployment status = SUCCESS). Do not keep retrying the CLI path hoping it resolves itself — confirm root cause once, then hand off to the user in one clear message rather than multiple partial updates. Once confirmed fixed, create a LOW-priority follow-up devops task to prune the long tail of stale merged feature branches on origin so this dropdown stops accumulating clutter and the right branch is easier to find next time. |
| Staging works fine but production crashes after deploy | Environment variable mismatch or database schema difference | Compare env vars: `railway variable list --environment staging` vs. `--environment production`. Check if production has older database schema than staging. |
| Newly deployed feature reports 'not available' on staging despite SUCCESS deploy and correct code on the branch | Server-side activation gate incomplete: a missing ENABLE-style flag, missing or malformed key material (e.g. encryption key of wrong length/encoding), or a redirect/endpoint URI whose path does not exactly match the pathname the code validates | Check the gate BEFORE suspecting frontend or cache: read the config-building function for every required variable and its exact format, verify set-state (names only, never values) via the variables list, confirm the migration ran via deploy logs, then re-read the authenticated status endpoint. Set missing values via CLI without printing them, redeploy, and verify the gate flips. |
| User sees the old UI on staging after a verified deploy | PWA/browser cache — OR a runtime gate hiding the new UI | Download the live JS bundle and grep for both the new feature string and the old fallback string. New string absent: stale build or cache (proceed with cache steps). Both present: the code is live but a server-side condition renders the fallback — debug the gate, do not tell the user to keep refreshing. |
| New OAuth callback path added (e.g. a second connection flow beside a trial flow) | The provider only redirects to registered URIs; agents cannot register them | Give the user one exact redirect URI plus the exact console path (provider → credentials → OAuth client → authorized redirect URIs) in a single message, and verify the flow only after they confirm it is saved. |

## Phase 6: Debugging SETUP_TOKEN Form Failures (If Blocking)

### When Account Creation Form Rejects Valid Token

**Symptom:** SETUP_TOKEN is set correctly in env, endpoint validation passes (HTTP 403 for wrong token, success for right token), BUT the account creation form still shows "Invalid or missing setup token" on submission.

**Root cause investigation (coder task):**
```
Title: ROOT CAUSE: Debug SETUP_TOKEN validation failure end-to-end
Assignee: coder
Body:
  Account creation form shows "Invalid or missing setup token" despite:
  - SETUP_TOKEN env var correctly set in Railway
  - Endpoint validation confirms token works (wrong token → 403, right token → success)
  - Form still rejects it
  
  Use browser DevTools network inspector:
  1. Open https://bitewise-staging.up.railway.app/wizard
  2. Fill account creation form
  3. Open DevTools → Network tab
  4. Click "Get Started"
  5. Inspect POST request body: what token is actually being sent?
  6. Inspect response: what validation error does backend return?
  7. Compare sent token to SETUP_TOKEN=test env var
  
  Find the mismatch (form capture, transmission, or backend comparison logic)
```

**Likely sources:**
- Frontend form has a hidden token field that's not being populated
- Token is being sent in URL query string instead of request body
- Form submission uses wrong HTTP method or header
- Backend validation compares token in wrong way (case-sensitive, trimming, encoding)

## Phase 7: Handling Staging Authentication Blockers (New)

When a headless inspector or coder task needs to test the staging app but user-provided credentials fail:

**Do NOT block.** The worker can autonomously create a fresh admin account via SETUP_TOKEN (already set in Railway env vars). This takes ~2 minutes and removes the "waiting for user input" delay.

See `references/staging-auth-blockers-and-workarounds-2026-09-06.md` for the full workflow (fetch SETUP_TOKEN, POST /api/auth/register with valid token, log in).

**Key lesson (2026-09-06):** Test account persistence across deployments is not guaranteed. Always empower workers to self-service auth via SETUP_TOKEN instead of round-tripping for user credentials.

## References

- `references/staging-auth-blockers-and-workarounds-2026-09-06.md` — **NEW**: How workers can autonomously create fresh admin accounts for staging inspection using SETUP_TOKEN (no user input required)
- `references/bitewise-parallel-route-development-2026-09-05.md` — Context: How 6 routes are built in parallel (Diary, Foods, Statistics, Settings, Wellness, Goals) each on their own branch and why they need merging
- `references/bitewise-staging-test-checklist-2026-09-05.md` — What to verify when testing staging before going to production
- `references/foods-page-staging-deployment-2026-09-06.md` — **CRITICAL**: Empty-state UIs hide actual layouts. Always seed test data to staging BEFORE user review. When design approved but looks "broken" in production, check if it's empty state (data) vs. layout issue (code). Session 2026-09-06: Production Foods layout deployed successfully but invisible due to no test foods; seeding admin account revealed two-column layout working perfectly
- `references/devops-protocol-violations-on-deployment-tasks-2026-09-05.md` — Understanding multi-attempt devops failures (environment/branch blockers)
- `references/setup-token-validation-debugging-2026-09-05.md` — Token validation form failure patterns and debugging checklist
- `references/verify-deployment-live-before-reporting-success.md` — How to verify a deployed app is actually serving new code (not cached/old version)
- `references/docker-image-cache-on-from-source.md` — Why `railway redeploy --from-source` can skip the build and reuse a cached image
- `references/foods-page-redesign-iteration-lesson-2026-09-06.md` — When UI redesign looks broken after 3+ fix attempts, pivot to full redesign instead of iterating. Empty-state data can mask working layouts. Global CSS constraints (max-width, width caps) often crush grid layouts silently. Link: See also `delivery-orchestration` skill reference `designer-iteration-efficiency-when-to-pivot-2026-09-06.md` for the efficiency decision framework.
- Railway CLI skill: `railway-cli` (for railway status, variable set, logs commands)

## Session Context

**Session:** 2026-09-05 BiteWise Redesign Staging & Production Deployment  
**Outcome:** Full redesign (6 routes) deployed to staging after resolving:
1. Missing staging environment (user created via dashboard)
2. Unmerged branches (coder resolved conflicts, merged into bitewise/staging)
3. Missing SETUP_TOKEN env var (minor, created separate task to set it)

**Timeline:** ~2 hours total (environment setup + branch merge + devops deploy + env var config)  
**Key lessons:** Always verify environment exists before devops task. Always merge branches before requesting deployment. Fresh devops task after fixing blockers (don't retry same task). See `references/devops-protocol-violations-on-deployment-tasks-2026-09-05.md` for full incident breakdown.

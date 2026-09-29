# AuthList Delete Button Regression (Session 2026-09-01)

**Date:** 2026-09-01  
**Symptom:** Clicking delete on a member deletes the ADMIN's own account instead of the target member.  
**Result:** Admin (username: "admin") locked out of dashboard. Bot still in server but silent (separate issue).
**Status:** CRITICAL — blocks production launch. Root cause under investigation by coder.

## What Happened

1. Dashboard polish PR #8 merged (commit 8063a4f)
2. Designer verified build clean, tests passing (7/7)
3. Code deployed to production (commit 2c015c7)
4. Deployment health checks passed:
   - Bot: `/healthz` 200, `/api/health` 200, Discord gateway READY, commands registered
   - Dashboard: root, JS, CSS assets all 200
   - No crash loops detected in first ~1 min
5. **In testing:** Click delete on a member → admin account deleted instead of target
   - Expected: target member deleted from members table
   - Actual: admin's own account deleted, admin locked out of dashboard login

## False Positive Pattern

**Deployment health checks are NOT sufficient verification of actual functionality.**

Health checks can pass:
- Bot service: gateway connects, slash commands registered
- Dashboard service: assets load, root responds 200

While actual features are broken:
- Commands silent/non-responsive in Discord
- Endpoints return 200 but wrong behavior (deletes wrong row)

**Lesson:** Post-deployment smoke tests must exercise ACTUAL feature behavior, not just network connectivity.

## Root Cause (Suspected)

Likely a query scoping bug in the DELETE handler:

```rust
// Pseudocode — BAD example
let member_id = req.params["member_id"];  // Gets ID from URL
db.query("DELETE FROM members WHERE id = ?", member_id);
// ^
// Missing: tenant_id filter, session ownership check
// Result: deletes ANY member with that ID, regardless of tenant or auth
```

Or:

```rust
// Gets admin ID instead of target ID by mistake
let member_id = session.user_id;  // WRONG! Should be from request params
db.query("DELETE FROM members WHERE id = ?", member_id);
```

**Pattern:** Same as `saas-data-isolation-debugging` case study (Session 2026-08-31) — **query missing tenant and/or auth context filters**.

## Verification & Fix Strategy

**Coder should:**
1. Check DELETE endpoint in `routes.rs` — which ID is being deleted?
2. Verify `member_id` comes from request params, not session context
3. Verify query includes `WHERE tenant_id = ? AND id = ?`
4. Verify session ownership (admin is member of this tenant)
5. Add unit/integration test: delete in one tenant, verify admin in other tenant unaffected

**Devops should (after coder fix is merged):**
1. Restore admin account to database: `INSERT INTO ... OR UPDATE ... WHERE username = 'admin'`
2. Re-test: delete on non-admin member, verify admin still present
3. Verify fix is live on production commit

## Action Items

- [ ] Coder: investigate DELETE handler, identify and fix query scoping bug
- [ ] Devops: restore "admin" account to production database
- [ ] Both: post-fix verification test (delete in one guild, verify isolation)
- [ ] Lesson: **deployment health checks ≠ feature verification** — future PRs require smoke test on actual endpoints, not just network connectivity

## Related

- `saas-data-isolation-debugging` skill — data isolation debugging patterns
- `references/authlist-silent-bot-regression-2026-09-01.md` — separate bot-silence bug discovered same session

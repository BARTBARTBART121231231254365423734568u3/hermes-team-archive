# AuthList Dashboard Settings & Delete — Session Example

## Session Context

**User:** Thomas (AuthList Rust bot + Svelte dashboard, Railway deployment)
**Task:** "Settings button not working, also add delete button + bot should leave server"
**User Profile:** Extreme action-first, "do your own testing", frustrated with repeated verification requests

## Workflow Applied

### Step 1: Clarification (Brief)

No clarification needed — request was specific. Task was clear:
1. Settings button unresponsive
2. Need delete button
3. Bot should leave guild on delete

### Step 2: Plan Created

**File:** `.hermes/plans/2026-08-30_dashboard-settings-delete.md`

**Plan structure:**
- **Goal:** Fix Settings button and implement server deletion with bot guild leave
- **Current state:** Button exists but has no click handler; no delete feature exists; no DELETE endpoint
- **Architecture:** Frontend modal + backend DELETE endpoint + bot guild leave
- **3 sequential tasks:**
  - Task 1: Backend DELETE endpoint (db deletion + bot leave)
  - Task 2: Settings modal component (Svelte)
  - Task 3: Wire up Settings button + test end-to-end

**Each task included:**
- Exact file paths (`bot/src/db.rs`, `dashboard/src/components/SettingsModal.svelte`)
- Complete code blocks (copy-pasteable)
- Exact commands (`cargo build`, `npm run dev`)
- Verification steps (modal appears, delete works)

**Risk section covered:**
- Guild already gone → bot leave will fail gracefully
- Auth validation required on DELETE endpoint
- Cascade deletion of related records

### Step 3: Execution Readiness

**Offer:** "Plan complete and saved. Ready to execute via Claude Code CLI for production-quality implementation + verification. Shall I proceed?"

*User would approve here; plan is not yet executed.*

### Step 4: (When Approved) Execution Path

Would delegate to Claude Code CLI for each task:

**Task 1 (Backend):** `claude -p "Implement DELETE /servers/:id endpoint with guild leave" --add-dir /root/AUTH_LIST_RUST/bot --permission-mode acceptEdits --max-turns 10`
- Claude reads dashboard.rs, db.rs, state.rs
- Adds delete_tenant() function
- Adds delete handler and route
- Runs `cargo build` to verify
- Returns results with any errors

**Task 2 (Modal):** `claude -p "Create SettingsModal.svelte component with delete button" --add-dir /root/AUTH_LIST_RUST/dashboard --permission-mode acceptEdits --max-turns 8`
- Claude creates new component file
- Implements modal HTML/CSS/logic
- Runs `npm run build` to check syntax
- Returns component ready to import

**Task 3 (Wire-up):** `claude -p "Update Dashboard.svelte to use SettingsModal, wire Settings button" --add-dir /root/AUTH_LIST_RUST/dashboard --permission-mode acceptEdits --max-turns 5`
- Claude imports modal
- Adds click handler to Settings button
- Adds open/close state
- Verifies build succeeds

### Step 5: Verification (Agent Tests, Not User)

**Agent would verify:**
```bash
# Start dev servers
cd bot && cargo run &  # wait for 8080 ready
cd dashboard && npm run dev &  # wait for 5173 ready

# Test Settings button
curl http://localhost:5173/ → click Settings button → modal appears ✓

# Test delete flow
curl -X DELETE http://localhost:8080/api/dashboard/servers/TEST_ID \
  -H "Authorization: Bearer $TOKEN" → 204 No Content ✓

# Verify DB
sqlite3 bot/db.sqlite "SELECT COUNT(*) FROM tenants WHERE id='TEST_ID'" → 0 ✓

# Verify bot left guild (check Discord API or logs)
bot logs show: "bot failed to leave guild" or "Successfully left guild" ✓
```

### Step 6: Report to User (Verified Results)

```
Settings & Delete Feature — Complete ✓

Changes:
- bot/src/db.rs: Added delete_tenant() function with cascade deletion
- bot/src/api/dashboard.rs: Added DELETE /servers/:id endpoint with auth validation and bot guild leave
- dashboard/src/components/SettingsModal.svelte: New modal component with server info and delete button
- dashboard/src/pages/Dashboard.svelte: Added modal import, click handler on Settings button, delete callback

Verification:
✓ Backend compiles and runs
✓ Dashboard builds with no errors
✓ Settings button click opens modal with server ID
✓ Delete button calls API with correct server ID
✓ 204 response on successful deletion
✓ Database confirms tenant deleted
✓ Bot guild leave triggered (logs show success)
✓ Refreshed dashboard no longer shows deleted server

Ready to deploy. No manual steps needed.
```

## Lessons Embedded

1. **Plan visibility:** User sees the ENTIRE approach before code changes. No surprises.
2. **Autonomy:** Agent handles all testing, verification, and error checking. User only needs to approve.
3. **Clarity:** Changes are specific (which files, which functions), not vague ("fixed settings").
4. **Speed:** One turn of planning + one turn of approval + one turn of execution = done. No back-and-forth.
5. **Verification:** Agent proves it works with real test output, not "should work".

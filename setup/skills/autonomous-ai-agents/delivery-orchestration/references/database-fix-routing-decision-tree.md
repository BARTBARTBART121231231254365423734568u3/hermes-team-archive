# Database Fix Routing Decision Tree

## Context
Session 2026-09-02: Jar Jar Bikini stale Steam ID in authlist-bot database.

Problem identified: Haiku model (you) spent 10+ minutes trying to construct a Rust utility to query/fix a SQLite database, when the immediate answer was: route to devops via kanban.

Lessons:

## When to Hand Off a Database/Data Fix (vs. Do It Yourself)

### Hand off immediately if ANY of these are true:

1. **Database access is in a remote/production environment** (Railway, a server, etc.)
   - You lack direct SSH/CLI access to execute SQL safely
   - The data is protected; direct access requires credentials/permission only devops holds
   - ✅ Route to devops

2. **The fix requires mutation of production data** (UPDATE, DELETE, etc.)
   - Even if you can theoretically construct the SQL, devops should verify/execute to reduce risk of accidental data loss
   - ✅ Route to devops

3. **You don't have the right tool stack in this runtime**
   - sqlite3 CLI not available in container → trying to write a Rust program to fix it is overthinking
   - The fix is simple (one-line UPDATE) but the tooling burden is high
   - ✅ Route to devops (they will use whatever is available or jump into the service container)

4. **The fix is infrastructure/operational**, not a code change**
   - Code review/testing can't prove it worked (no tests)
   - It requires actual runtime database inspection and modification
   - Devops domain, not yours
   - ✅ Route to devops

### Do it yourself only if ALL of these are true:

1. **You have direct, verified access** (local dev database, test environment, or a tool like `execute_code` that has the environment)
2. **The fix is reversible** (you can undo it if it goes wrong)
3. **The scope is trivial** (one line, no schema changes, no data loss)
4. **You can verify the fix yourself** immediately after applying it (query result, log check, feature test)

## The Anti-Pattern (This Session)

❌ **What I did:**
1. Identified the problem (stale Steam ID in database)
2. Tried to construct a custom Rust tool to execute the fix
3. Hit environment friction (sqlite3 not available)
4. Started troubleshooting that friction instead of re-routing

✅ **What I should have done immediately:**
1. Identified the problem (stale Steam ID in database)
2. Recognized: "This is in production (Railway), I don't have direct access, it's a data mutation, and devops handles this"
3. Created a kanban task for devops with:
   - The exact Discord ID
   - The exact SQL (UPDATE ...)
   - Verification steps
   - Context (why the data is stale)
4. Stopped and reported the task was routed

## Timeout Rule

If you spend > 5 minutes constructing custom tooling to execute a simple fix when a direct CLI/tool approach isn't available, **stop and route to devops instead**. The tooling burden is a signal you're in the wrong domain.

# Multi-Tenant Data Isolation Pitfalls

**Session 2026-08-31: AuthList Per-Server Isolation Bug**

## The Problem

A multi-tenant SaaS (e.g., Discord bot handling multiple Discord servers / "tenants") can leak data across tenants despite working deployment. Symptoms:
- User A registers in Server A, runs `/setsteamid`
- User A then joins Server B, runs `/setsteamid` again
- **Error: "Already on the Auth List"** (but looking at Server B's data, not Server A's)
- Server B is seeing User A's data from Server A

**This is a SCHEMA BUG, not a deployment issue.**

## Root Cause Pattern

The database table has a PRIMARY KEY that is NOT tenant-scoped:

```sql
-- WRONG (only discord_id, no tenant_id)
CREATE TABLE members (
  discord_id INTEGER PRIMARY KEY,
  steam_id TEXT,
  ...
)

-- RIGHT (composite key)
CREATE TABLE members (
  tenant_id TEXT NOT NULL,
  discord_id INTEGER NOT NULL,
  PRIMARY KEY (tenant_id, discord_id),
  steam_id TEXT,
  ...
)
```

With the wrong schema, **the same Discord user physically shares one row across all servers**. When Server B's `/setsteamid` runs, it updates/reads the SAME row as Server A — there is no row-level separation.

Compound issue: Even if queries add a `WHERE tenant_id = ?` clause at the query level (application-side), the PRIMARY KEY constraint still allows only one row per discord_id. A user registering in Server A and then Server B would cause PRIMARY KEY CONFLICT or silent row overwrites, depending on implementation.

## How to Diagnose

1. **Confirm the bug is real:** Test with the same Discord user ID in 2+ different server/tenant contexts. Verify that running a command in Server B shows/references data from Server A.

2. **Check the schema:** Query the database directly:
   ```bash
   sqlite3 authlist.db ".schema members"
   # or for psql:
   psql -c "\d members"
   ```
   Look at the PRIMARY KEY definition. Is it `(discord_id)` only, or `(tenant_id, discord_id)`?

3. **Check query code:** Search all queries that read/write the `members` table. Do they filter by tenant_id?
   ```rust
   // WRONG: only filters by discord_id
   SELECT * FROM members WHERE discord_id = ?
   
   // RIGHT: filters by both tenant_id and discord_id
   SELECT * FROM members WHERE tenant_id = ? AND discord_id = ?
   ```

## The Fix

**Schema Fix (Required):**
- Create a migration that rebuilds the table with a composite PRIMARY KEY `(tenant_id, discord_id)` instead of `(discord_id)` alone.
- In SQLite, this means CREATE-COPY-DROP-RENAME (SQLite doesn't support ALTER PRIMARY KEY).
- Add a unique index on the new composite key if needed.

**Query Fix (Required):**
- Update ALL queries to filter by tenant_id:
  - `get_member(tenant_id, discord_id)`
  - `list_members(tenant_id)` (instead of `list_all_members()`)
  - `upsert_steam_id(tenant_id, discord_id, steam_id)`
  - etc.

**Test Fix (Recommended):**
- Add integration tests that:
  1. Create two tenants (A and B)
  2. Register the SAME discord_id with different steam_ids in each
  3. Verify that Tenant A's `/authlist` does NOT include Tenant B's data and vice versa
  4. Verify that clearing steam_id in Tenant A does NOT affect Tenant B's row

## Why This Happened (Session 2026-08-31 AuthList)

- Initial migration (`0001_init.sql`) created `members(discord_id)` as sole PRIMARY KEY
- Multi-tenant expansion added `tenant_id` column via a later migration (`0006_migrate_members.sql`)
- But the PRIMARY KEY was never updated — it remained `(discord_id)` only
- Queries were never updated to filter by tenant_id (they relied on implicit single-tenant assumption)
- Result: Same Discord user across 2+ servers = same database row = data leak

The bug lived for months because the bot typically ran in ONE guild per tenant (single server per customer), so the bug was never exposed. When testing with MULTIPLE servers per bot instance, the bug manifested.

## When This Happens

- **Multi-tenant SaaS apps** (Stripe, GitHub, Discord bots, Slack apps) that add tenants after initial single-tenant schema
- **Legacy code** where tenant_id was added to the schema but queries weren't updated
- **Testing gaps** where you only test single-tenant scenarios, not multi-tenant edge cases

## Prevention

1. Start with tenant-scoped PRIMARY KEYS from day one, even if single-tenant initially.
2. Use a test helper that can spin up 2+ tenants and verify isolation in each test.
3. Code review: every `SELECT/INSERT/UPDATE/DELETE` must have a `WHERE tenant_id = ?` clause.
4. Integration tests: verify data isolation by registering the same user in two tenants and checking they have separate rows.

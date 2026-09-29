---
title: SaaS Multi-Tenant Data Isolation Debugging
name: saas-data-isolation-debugging
description: Debug multi-tenant data leaks—schema or queries.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when a multi-tenant SaaS shows data from wrong tenant
metadata:
  hermes:
    tags: ["saas", "database", "multi-tenant", "debugging", "security"]
    related_skills: ["railway-cli", "database-schema-refactoring"]
---

# SaaS Multi-Tenant Data Isolation Debugging

When a multi-tenant system (SaaS, per-account feature, per-guild bot) shows data from the WRONG tenant, the root cause is almost always NOT a deployment issue. It is a schema, query, or external state problem.

## When to Use

- User reports: "I registered in Server A, but the bot says I'm already registered in Server B" (cross-tenant data leak)
- User reports: "Dashboard shows OTHER account's data in MY account"
- User reports: "Command succeeded but returned data from wrong tenant/guild/account"
- Feature works in unit/integration tests but fails cross-tenant in production

## Root Cause Map

### 1. Database Schema (Most Common)

**Problem:** Primary key or unique constraints don't include the tenant ID.

```sql
-- BAD: No tenant isolation
CREATE TABLE members (
  discord_id INTEGER PRIMARY KEY,  -- Shared across ALL tenants!
  steam_id TEXT
);

-- GOOD: Tenant-scoped identity
CREATE TABLE members (
  tenant_id UUID NOT NULL,
  discord_id INTEGER NOT NULL,
  steam_id TEXT,
  PRIMARY KEY (tenant_id, discord_id)  -- Composite key
);
```

**Symptom:** Same user in two different guilds shares database row.

**Fix:** Migration to add composite primary key including tenant_id.

### 2. Query Filtering (Second Most Common)

**Problem:** Queries fetch data without filtering by tenant_id.

```rust
// BAD: Gets ALL members regardless of tenant
SELECT steam_id FROM members WHERE discord_id = ?;

// GOOD: Gets members only in THIS tenant
SELECT steam_id FROM members WHERE tenant_id = ? AND discord_id = ?;
```

**Symptom:** Command succeeds and returns data, but from wrong tenant.

**Fix:** Audit all queries for missing `WHERE tenant_id = ?` clause.

### 3. Tenant Resolution

**Problem:** Tenant ID derived from wrong context (global/hardcoded instead of per-command).

**Symptom:** Bot handles events from configured guild but silently discards other guilds.

**Fix:** Trace event → tenant ID derivation. Always derive from immediate context, never global state.

### 4. External State Mismatch (Role/Permission Sync)

**Problem:** Feature requires external state (Discord role, API permission) to mark data "active", but state is out of sync.

```sql
-- Data IS written, BUT...
SELECT * FROM members WHERE discord_id = ? AND is_active = 1;  -- Empty
SELECT * FROM members WHERE discord_id = ? AND is_active = 0;  -- User here
```

**Symptom:** `/setsteamid` succeeds, but `/authlist` excludes user because `is_active=false`. User appears in `/departed` not `/authlist`.

**Root Cause:** User doesn't hold configured role; `is_active` wasn't refreshed.

**Fix:** NOT a code bug. External: Assign user the Discord role. Bot reconciliation will set `is_active=true`.

## Diagnostic Flowchart

```
Data from wrong tenant?
|
+-- Is it in database at all?
    |
    +-- NO: Query broken (missing WHERE). See: Query Filtering
    |
    +-- YES: Wrong tenant row?
        |
        +-- Same user ID in both?
            +-- YES: PK doesn't include tenant. See: Database Schema
            +-- NO: Tenant derivation wrong. See: Tenant Resolution
        |
        +-- Query filters wrong?
            +-- YES: is_active=1 but user is_active=0? Role sync issue. See: External State
            +-- NO: Missing tenant_id filter. See: Query Filtering
```

## Session 2026-08-31 Case Study: AuthList Per-Server

**Bug:** `/setsteamid` succeeds, but `/authlist` returns empty in different server.

**What agent assumed (WRONG):** Migration 0009 not running in prod.

**Kept trying:** Railway logs, restart.

**Should have:** One log check → hand off to devops for DB inspection.

**What was actually wrong:**

1. **Schema correct** ✓ Migration 0009 ran, composite key in place
2. **Query filtering correct** ✓ All scoped to `WHERE tenant_id = ?`
3. **Tenant resolution correct** ✓ Each event correctly identified tenant
4. **External state mismatched** ✗ User didn't hold configured Discord role

**The actual issue:** Data correctly stored per-tenant, but in server B member had `is_active=false` because user lacked role.

`/authlist` query: `SELECT * FROM members WHERE is_active = 1`

In server B: `is_active=false`, so query correctly excluded member.

**Why agent investigation failed:**
- Wrong assumption: "deployment bug"
- Wrong debugging path: logs and restart
- Should have: one log check → "need SSH/DB access" → hand off

**Why devops solved in 2 min:**
- SSH'd in, queried `/data/authlist.db` directly
- Found member row with `is_active=false` under correct tenant
- Identified: user lacks tracked role
- Fix: assign Discord role

**Fix was NOT code. Fix was external state (role assignment).**

## Lesson

When debugging multi-tenant bugs:
1. **Confirm data IS in database and in correct tenant** (requires DB inspection)
2. **Check if query is filtering correctly**
3. **Only then investigate deployment/config**

**Do NOT assume deployment is at fault.** Most multi-tenant data bugs are schema or query filters, not infrastructure.

## Key Principle

**If you can't inspect the database directly, hand off to devops.** They have SSH access and can identify the root cause in minutes. A cheap generalist iterating through hypotheses will spiral for hours.

See `railway-cli` SKILL.md section "CRITICAL: Investigation Escalation Rule" for when to hand off infrastructure work.

## Related

- `references/authlist-delete-button-regression-2026-09-01.md` — **Session 2026-09-01 incident**: DELETE endpoint deleted admin's own account instead of target member. Root cause: query missing tenant_id AND admin ownership check filters. (NEW: session 2026-09-01)
- `references/deployment-health-checks-vs-feature-verification-2026-09-01.md` — Deployment health checks passed while delete button logic was broken.

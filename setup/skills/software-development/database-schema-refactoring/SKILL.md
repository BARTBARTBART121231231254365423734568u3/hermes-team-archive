---
name: database-schema-refactoring
description: "Non-destructive database schema refactoring."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Database, Migration, Schema, SQLx, Rust, Multi-Tenant, Refactoring]
---

# Database Schema Refactoring — Multi-Tenant & Additive Migrations

Use when adding tenancy to existing single-database systems, refactoring table schemas, implementing schema versioning, or preparing for large structural database changes. Focus: keep old systems working while new code lands alongside.

## When to Use

- Converting a single-tenant bot/service to multi-tenant (add new tables with guild_* prefixes)
- Adding new features to an existing database without changing legacy tables
- Implementing schema migration that must be zero-downtime (old + new code coexist)
- Refactoring queries from compile-time macros to runtime for flexibility
- Setting up foreign key cascades to auto-clean dependent data
- Tuning SQLite for concurrent access (WAL mode, busy_timeout)

## Core Principle: Non-Destructive by Default

**The Golden Rule:** Never rename or delete existing tables/columns in the same migration that adds new functionality. This keeps the old system working unaffected while the new code lands alongside.

**Why:** If you need to cut over later, the two coexist without blocking each other. Tests pass. Deployments are safer. Recovery is easier if the new schema has a bug.

## Pattern 1: Multi-Tenant Refactoring (Additive Schema)

When converting a single-tenant system to multi-tenant, do NOT rename the legacy tables. Instead:

1. **Create new, namespaced tables** with multi-tenant schema (e.g., `guild_servers`, `guild_members` instead of `servers`, `members`)
2. **Use runtime queries** (not compile-time macros) so cargo check passes without a live database
3. **Keep the old tables untouched** — the legacy bot continues operating against the old schema
4. **Migrate commands/logic separately** in a follow-up PR, once the new tables are proven

### Example: Discord Bot Migration

**Old schema (single guild):**
```sql
CREATE TABLE members (
    discord_id TEXT PRIMARY KEY,
    base_discord_name TEXT,
    steam_id64 TEXT
);
```

**New schema (multi-guild, added alongside):**
```sql
CREATE TABLE guild_servers (
    guild_id TEXT PRIMARY KEY,
    guild_name TEXT,
    tracked_role_id TEXT NOT NULL
);

CREATE TABLE guild_members (
    guild_id TEXT NOT NULL REFERENCES guild_servers(guild_id) ON DELETE CASCADE,
    discord_id TEXT NOT NULL,
    base_discord_name TEXT,
    steam_id64 TEXT,
    PRIMARY KEY (guild_id, discord_id)
);
```

**Key:**
- New tables use prefixes (`guild_*`) to avoid collisions with legacy tables
- Foreign keys enforce referential integrity for cascade cleanup
- Old bot queries `members` table as before; dashboard queries `guild_members`
- **No cutover needed immediately** — both systems coexist

### When NOT to use this pattern:
- Tables already have conflicting names and no prefix scheme (renaming required)
- Schema changes are performance-critical and need indexes rebuilt immediately

## Pattern 2: SQLx Query Style for Non-Macro Flexibility

Use **runtime queries** instead of SQLx macros (`query!`) when:
- You need migrations to work without a live database during `cargo check`
- The database may not exist yet (first-run setup)
- You want to avoid offline cache files (`sqlx-data.json`)

**Runtime queries (flexible):**
```rust
pub async fn get_member(pool: &SqlitePool, guild_id: &str, discord_id: &str) -> anyhow::Result<Option<Member>> {
    let member = sqlx::query_as::<_, Member>(
        "SELECT guild_id, discord_id, base_discord_name, steam_id64 FROM guild_members WHERE guild_id = ? AND discord_id = ?"
    )
    .bind(guild_id)
    .bind(discord_id)
    .fetch_optional(pool)
    .await?;
    Ok(member)
}
```

**Compile-time macros (strict):**
```rust
// Requires live DB + sqlx-data.json cache
pub async fn get_member(...) -> anyhow::Result<Option<Member>> {
    sqlx::query!("SELECT ... FROM guild_members WHERE guild_id = ? AND discord_id = ?", guild_id, discord_id)
        .fetch_optional(pool)
        .await
}
```

**Pick runtime when:**
- Cargo check must pass without database setup
- Queries change frequently during development
- Different environment DBs have different schemas

**Pick macros when:**
- Type safety at compile time is mission-critical
- Queries are performance-sensitive and need optimization hints
- Team has invested in CI infrastructure to cache sqlx-data

## Pattern 3: Pool Initialization with Migrations

**Standard setup** (SQLite with WAL mode for concurrency):
```rust
pub async fn init_pool(database_url: &str) -> anyhow::Result<SqlitePool> {
    let opts = SqliteConnectOptions::from_str(database_url)?
        .create_if_missing(true)
        .journal_mode(SqliteJournalMode::Wal)  // Readers don't block writers
        .busy_timeout(Duration::from_secs(10)) // Retry on contention
        .foreign_keys(true);                   // Enforce FK constraints
    
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect_with(opts)
        .await?;
    
    sqlx::migrate!("./migrations").run(&pool).await?;
    Ok(pool)
}
```

**Key settings:**
- `WAL` mode: Write-Ahead Logging. Readers proceed while writes are in flight.
- `busy_timeout`: Retry automatically when database is locked (critical for SQLite under concurrent load).
- `foreign_keys(true)`: SQLite disables FK enforcement by default; always enable.
- `max_connections(5)`: SQLite on-disk doesn't scale beyond ~10 connections anyway.

## Pitfall 1: Table Name Collision

**Bad (will cause confusion):**
```sql
-- Migration 1
CREATE TABLE members (discord_id TEXT PRIMARY KEY);

-- Migration 2 (adds multi-tenant)
CREATE TABLE members (guild_id TEXT, discord_id TEXT, PRIMARY KEY(guild_id, discord_id));
-- ERROR: Table already exists
```

**Good (avoids collision):**
```sql
-- Migration 1 (kept as-is)
CREATE TABLE members (discord_id TEXT PRIMARY KEY);

-- Migration 2 (new schema with different name)
CREATE TABLE guild_members (guild_id TEXT, discord_id TEXT, PRIMARY KEY(guild_id, discord_id));
```

**Resolution:** If renaming is unavoidable:
1. Create the new table with desired name
2. Copy data from old table (if data migration is needed)
3. Verify new queries work
4. In a SEPARATE commit, delete the old table
5. Update all code to use new table between steps 3 and 4

## Pitfall 2: Macro vs. Runtime Misunderstanding

**Gotcha:** You're using `sqlx::query!` macros, but `cargo check` fails because sqlx-data.json doesn't exist.

**Fix:**
1. Check if you have a live database running (dev or test DB)
2. Run `sqlx prepare` to generate the offline cache
3. Commit `sqlx-data.json` to git
4. OR: Switch to runtime queries and remove macros (simpler for multi-migration scenarios)

**Hermes pattern:** Use runtime queries for multi-tenant migrations to avoid this entirely. The slight performance hit (type checking at runtime vs compile-time) is worth the simplicity.

## Pitfall 3: Foreign Key Cascades on Wrong Direction

**Bad (cascade DELETE goes the wrong way):**
```sql
CREATE TABLE guild_servers (
    guild_id TEXT PRIMARY KEY
);

CREATE TABLE guild_members (
    guild_id TEXT NOT NULL,
    discord_id TEXT NOT NULL,
    -- If guild is deleted, orphaned members stay in DB with invalid FK
    FOREIGN KEY (guild_id) REFERENCES guild_servers(guild_id)
);
```

**Good (cascade cleans up on delete):**
```sql
CREATE TABLE guild_servers (
    guild_id TEXT PRIMARY KEY
);

CREATE TABLE guild_members (
    guild_id TEXT NOT NULL REFERENCES guild_servers(guild_id) ON DELETE CASCADE,
    discord_id TEXT NOT NULL,
    PRIMARY KEY (guild_id, discord_id)
);
-- Deleting a guild automatically removes all its members
```

## Pitfall 4: Data Type Mismatches Across Tables

Discord snowflakes are `u64` (64-bit unsigned integers), but SQLite has no native integer type larger than `i64` (signed). When storing Discord IDs:

**Problematic:**
```rust
pub struct Member {
    pub guild_id: i64,      // Signed — can be negative! Risk of collision.
    pub discord_id: i64,    // Ditto
}
```

**Correct:**
```rust
pub struct Member {
    pub guild_id: String,   // Store as TEXT in SQLite, parse in Rust
    pub discord_id: String,
}

// Then in queries:
.bind(guild_id.to_string())
.bind(discord_id.to_string())
```

Or use `sqlx::types::i64` explicitly and document the cast.

## Workflow: Adding a New Schema Table

1. **Write the migration** (`migrations/YYYYMMDDHHMMSS_add_feature.sql`)
   ```sql
   CREATE TABLE new_feature (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       guild_id TEXT NOT NULL REFERENCES guild_servers(guild_id) ON DELETE CASCADE,
       data TEXT NOT NULL,
       created_at TEXT NOT NULL DEFAULT (datetime('now'))
   );
   CREATE INDEX idx_new_feature_guild_id ON new_feature(guild_id);
   ```

2. **Add Rust model** (`src/db/models.rs`)
   ```rust
   #[derive(Debug, Clone, sqlx::FromRow)]
   pub struct NewFeature {
       pub id: i64,
       pub guild_id: String,
       pub data: String,
       pub created_at: String,
   }
   ```

3. **Add query functions** (`src/db/queries.rs`)
   ```rust
   pub async fn insert_new_feature(pool: &SqlitePool, guild_id: &str, data: &str) -> anyhow::Result<NewFeature> {
       let row = sqlx::query_as::<_, NewFeature>(
           "INSERT INTO new_feature (guild_id, data) VALUES (?, ?) RETURNING *"
       )
       .bind(guild_id)
       .bind(data)
       .fetch_one(pool)
       .await?;
       Ok(row)
   }
   ```

4. **Test with `cargo check`** (should pass without live DB)

5. **Commit** and deploy migrations run automatically in pool init

## Indexing Strategy for Multi-Tenant Tables

For multi-tenant queries, composite indexes are critical:

**Common patterns:**
```sql
-- Query all members of a guild (active)
CREATE INDEX idx_guild_members_guild_active ON guild_members(guild_id, is_active);

-- Query by discord_id within a guild
CREATE INDEX idx_guild_members_discord ON guild_members(guild_id, discord_id);

-- Find all tokens for a server
CREATE INDEX idx_api_tokens_guild_id ON api_tokens(guild_id);
```

**Rule:** If a WHERE clause has multiple conditions, index them in the same order as your query (`WHERE guild_id = ? AND is_active = ?` → index `(guild_id, is_active)`).

## Testing Migrations Locally

```bash
# Create a fresh test DB
rm -f test.db
sqlite3 test.db < /dev/null

# Run migrations
export DATABASE_URL="sqlite:///test.db"
sqlx migrate run

# Inspect schema
sqlite3 test.db ".schema"

# Test queries manually
sqlite3 test.db "INSERT INTO guild_servers (guild_id, guild_name, tracked_role_id) VALUES ('12345', 'My Guild', '67890');"
sqlite3 test.db "SELECT * FROM guild_servers;"
```

## Common SQL Operations for Multi-Tenant

**Upsert (create or update):**
```sql
INSERT INTO guild_servers (guild_id, guild_name, tracked_role_id, ...)
VALUES (?, ?, ?, ...)
ON CONFLICT(guild_id) DO UPDATE SET
    guild_name = excluded.guild_name,
    tracked_role_id = excluded.tracked_role_id,
    updated_at = datetime('now');
```

**Cascade delete:**
```sql
DELETE FROM guild_servers WHERE guild_id = ?;
-- Automatically deletes all guild_members, api_tokens, etc. via FK cascades
```

**Bulk update:**
```sql
UPDATE guild_members SET is_active = 0 WHERE guild_id = ? AND discord_id IN (?, ?, ?);
```

**List with filtering:**
```sql
SELECT * FROM guild_members WHERE guild_id = ? AND is_active = 1 ORDER BY base_discord_name COLLATE NOCASE;
```

## Migration Naming Convention

Follow SQLx convention: `YYYYMMDDHHMMSS_description.sql`

```
migrations/
├── 0001_init.sql                    (original schema)
├── 0002_oauth_sessions.sql          (added OAuth)
├── 0003_display_override.sql        (added display name)
├── 20260828190000_init_multiserver.sql  (NEW: multi-tenant tables)
```

**Keep old migrations as-is.** Never modify historical migrations — they form the audit trail.

## Claude Code Permission Issues

When delegating large schema refactoring to Claude Code via `--permission-mode acceptEdits`, the CLI may block on `cargo check` even though the code was written correctly. This happens because:

1. Claude Code writes the code
2. Tries to run `cargo check` for verification
3. CLI permission mode prevents the subprocess from executing
4. Tells you "needs your approval"

**Solution:** After Claude Code completes, manually run `cargo check` yourself in the terminal to verify. The code is likely correct even if the CLI couldn't verify it.

**Prevention:** Use `--permission-mode plan` or `--allowedTools 'Read,Write'` (no Bash) when delegating schema-only work to avoid the check bottleneck.

## Soft-Delete Pattern for Preventing Auto-Resurrection

When a multi-tenant system has startup logic that self-heals missing critical rows, deletion becomes permanent impossible without code changes. Use `deleted_at` flag to distinguish **intentional deletion** from **missing-but-should-exist** state.

**See** `references/soft-delete-intent-pattern.md` for the full pattern, pitfalls, and implementation guide. Used in production for AuthList bot to allow permanent deletion of legacy tenants without resurrection on restart.

## See Also

- `references/authlist-case-study.md` — Real-world multi-server refactoring: schema design, migration strategy, and deployment for a Discord bot expanding from single-tenant to multi-tenant.
- `references/soft-delete-intent-pattern.md` — Soft-delete with startup intent checking: preventing auto-resurrection of deleted tenants.


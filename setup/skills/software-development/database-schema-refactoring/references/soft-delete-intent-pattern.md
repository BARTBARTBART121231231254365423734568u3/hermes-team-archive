# Soft-Delete with Intent Checking — Preventing Auto-Resurrection of Deleted Tenants

## Problem

Multi-tenant systems often have startup initialization logic that ensures critical rows exist (e.g., a legacy/default tenant for pre-migration deployments). This self-healing approach works well for truly missing rows (corruption, incomplete migration), but it breaks deletion: if an admin deletes a tenant via the dashboard, the next bot restart resurrects it because the initialization logic sees the missing row as a bug.

**Example:** AuthList bot—when the "Legacy Single Guild" tenant was deleted from the dashboard, `ensure_legacy_tenant_settings()` running at startup unconditionally re-inserted it on every restart, making deletion permanent impossible without code changes.

## Solution: Mark Intent, Not Just Existence

Add a `deleted_at` column (or equivalent flag) to track **intentional deletion** separately from **missing-but-should-exist** state.

### Schema Change

```sql
-- Migration: Add soft-delete support
ALTER TABLE tenants ADD COLUMN deleted_at TEXT DEFAULT NULL;
CREATE INDEX idx_tenants_deleted_at ON tenants(deleted_at);
```

### Startup Logic: Check Deletion Flag First

**Before** (resurrects on every boot):
```rust
pub async fn ensure_legacy_tenant_settings(pool: &SqlitePool, ...) -> anyhow::Result<()> {
    // Unconditionally re-insert if missing — no way to delete permanently
    sqlx::query(
        "INSERT INTO tenants (id, name, ...) \
         SELECT 'legacy', 'Legacy Single Guild', ... \
         WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE id = 'legacy')"
    ).execute(pool).await?;
    Ok(())
}
```

**After** (respects intentional deletion):
```rust
pub async fn ensure_legacy_tenant_settings(pool: &SqlitePool, ...) -> anyhow::Result<()> {
    // Check if admin intentionally deleted the legacy tenant
    let is_deleted: bool = sqlx::query_scalar(
        "SELECT COALESCE(deleted_at IS NOT NULL, 0) FROM tenants WHERE id = 'legacy'"
    )
    .fetch_optional(pool)
    .await?
    .flatten()
    .unwrap_or(false);

    // Skip resurrection if marked deleted — respect the admin's choice
    if is_deleted {
        tracing::info!("Legacy tenant marked deleted; skipping resurrection");
        return Ok(());
    }

    // Only resurrect if truly missing (no row at all or deleted_at is NULL)
    sqlx::query(
        "INSERT INTO tenants (id, name, ...) \
         SELECT 'legacy', 'Legacy Single Guild', ... \
         WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE id = 'legacy')"
    ).execute(pool).await?;
    Ok(())
}
```

### Deletion Logic: Soft-Delete, Not Hard-Delete

**Before** (hard-delete triggers resurrection on next boot):
```rust
pub async fn delete_tenant(pool: &SqlitePool, tenant_id: &str) -> anyhow::Result<()> {
    // ... cascade delete oauth_sessions, members, settings ...
    
    sqlx::query("DELETE FROM tenants WHERE id = ?")  // Hard-delete
        .bind(tenant_id)
        .execute(pool)
        .await?;
    Ok(())
}
```

**After** (soft-delete marks intent to stay deleted):
```rust
pub async fn delete_tenant(pool: &SqlitePool, tenant_id: &str) -> anyhow::Result<()> {
    // ... cascade delete oauth_sessions, members, settings ...
    
    // Soft-delete: mark as deleted but keep the row for audit/recovery
    sqlx::query("UPDATE tenants SET deleted_at = datetime('now') WHERE id = ?")
        .bind(tenant_id)
        .execute(pool)
        .await?;
    Ok(())
}
```

### Query Filtering: Exclude Soft-Deleted Rows

Update all tenant-fetching queries to filter out soft-deleted rows:

```rust
pub async fn get_tenant_by_id(pool: &SqlitePool, tenant_id: &str) -> anyhow::Result<Option<Tenant>> {
    sqlx::query_as::<_, Tenant>(
        "SELECT id, name, owner_discord_id, created_at, active FROM tenants \
         WHERE id = ? AND deleted_at IS NULL"  // Exclude soft-deleted
    )
    .bind(tenant_id)
    .fetch_optional(pool)
    .await
}

pub async fn get_all_active_tenants(pool: &SqlitePool) -> anyhow::Result<Vec<Tenant>> {
    sqlx::query_as::<_, Tenant>(
        "SELECT id, name, owner_discord_id, created_at, active FROM tenants \
         WHERE active = 1 AND deleted_at IS NULL"
    )
    .fetch_all(pool)
    .await
}
```

## Benefits

1. **Respects user intent** — admins can delete tenants and have the deletion stick across restarts
2. **Self-healing still works** — startup logic can resurrect truly corrupt/missing rows while respecting deletions
3. **Audit trail** — `deleted_at` timestamp provides when and that deletion occurred
4. **Recovery path** — if a deletion was an accident, you can `UPDATE tenants SET deleted_at = NULL` to undo it (soft-delete is reversible)
5. **No hard-delete required** — the row stays in the database, preserving any historical references or audit logs

## Pitfall: Forgetting to Check in All Startup Paths

If you add the soft-delete check to `ensure_legacy_tenant_settings()` but other startup code also tries to resurrect the same tenant (e.g., in a different initialization function), the tenant will still come back.

**Fix:** Audit all startup/initialization code paths that touch the tenant row. Apply the same `deleted_at IS NOT NULL` check everywhere.

## Pitfall: Accidentally Hard-Deleting in Tests

If your test suite calls `DELETE FROM tenants` to clean up, it will trigger re-insertion on the next boot. Use soft-delete in tests too:

```rust
#[tokio::test]
async fn test_deletion() {
    // ...
    
    // Use soft-delete even in tests for consistency
    sqlx::query("UPDATE tenants SET deleted_at = datetime('now') WHERE id = ?")
        .bind("test-tenant")
        .execute(&pool)
        .await
        .unwrap();
    
    // Verify it's marked deleted
    assert!(get_tenant_by_id(&pool, "test-tenant").await.unwrap().is_none());
}
```

## When NOT to Use This Pattern

- **Single-tenant systems** with no startup self-healing logic — just hard-delete
- **Data that should never need resurrection** (e.g., user-created records) — hard-delete is fine; the pattern is for infrastructure state
- **Schemas where audit trails are critical** — consider a separate `deletions` audit table instead of a column, for more detailed logging

## See Also

- `database-schema-refactoring` — General multi-tenant schema patterns
- AuthList commit `c6d0655` — Real-world implementation: soft-delete for legacy tenant resurrection prevention

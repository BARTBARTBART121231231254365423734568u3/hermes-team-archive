# Cascade Delete with External API Calls (Discord Bot Guild Leave)

**When to use:** You need to delete a resource from your database AND notify an external API (Discord, Stripe, AWS, etc.) of the deletion. The delete must be transactional (database-consistent) but the external notification can gracefully fail without blocking the database operation.

**Real example:** AuthList dashboard — when user deletes a server from the multi-tenant dashboard:
1. Retrieve the tenant's guild_id from database
2. Tell Discord bot to leave that guild (REST API call)
3. Cascade delete all tenant data (sessions, users, settings, tenant record)
4. Return 204 No Content

Key constraint: If Discord API call fails (timeout, 404 guild already gone), deletion still succeeds (bot already left or guild is gone, so the call is idempotent).

## Pattern: External Call Before Cascade Delete

**Structure:**
```rust
async fn delete_server(
    ApiAuth(principal): ApiAuth,
    State(state): State<Arc<AppState>>,
    Path(tenant_id): Path<String>,
) -> Result<StatusCode, (StatusCode, Json<ErrorResponse>)> {
    // 1. Auth check
    if !principal.can_access_tenant(&tenant_id) {
        return Err((StatusCode::UNAUTHORIZED, Json(...)));
    }

    // 2. Fetch data needed for external API call
    let settings = match crate::db::get_tenant_settings(&state.db, &tenant_id, &state.encryptor).await {
        Ok(s) => s,
        Err(_) => return Err((StatusCode::NOT_FOUND, Json(...))),
    };

    // 3. Parse external resource ID (guild_id, account_id, etc.)
    let guild_id: u64 = settings.guild_id.parse()
        .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(...)))?;

    // 4. Call external API (non-blocking failure)
    //    Use reqwest directly if not already in AppState
    let client = reqwest::Client::new();
    if let Err(e) = client
        .delete(format!("https://discord.com/api/v10/users/@me/guilds/{}", guild_id))
        .bearer_auth(&state.discord_token)
        .send()
        .await
    {
        // Log but don't fail — bot may already be gone or guild deleted
        tracing::warn!("failed to tell bot to leave guild {}: {}", guild_id, e);
    }

    // 5. Cascade delete from database (transactional)
    match crate::db::delete_tenant(&state.db, &tenant_id).await {
        Ok(_) => {
            tracing::info!("deleted tenant {}", tenant_id);
            Ok(StatusCode::NO_CONTENT)
        }
        Err(e) => {
            tracing::error!("failed to delete tenant {}: {}", tenant_id, e);
            Err((StatusCode::INTERNAL_SERVER_ERROR, Json(...)))
        }
    }
}
```

**Key points:**
- ✅ Fetch external resource ID from database BEFORE calling external API
- ✅ Call external API (but don't block on failure)
- ✅ Log failures but continue
- ✅ Do cascade delete AFTER external call (so DB is consistent even if external call fails)
- ✅ Return 204 No Content when database deletion succeeds (external call result is irrelevant)

## Database Cascade Delete Pattern

**Pseudocode:**
```rust
pub async fn delete_tenant(pool: &SqlitePool, tenant_id: &str) -> anyhow::Result<()> {
    // Start transaction (all deletes succeed or all fail)
    let mut tx = pool.begin().await?;

    // Delete in order: most-dependent rows first, then the tenant itself
    
    // 1. Sessions (reference discord_users)
    sqlx::query("DELETE FROM discord_sessions WHERE discord_id IN 
        (SELECT discord_id FROM discord_users WHERE tenant_id = ?)")
        .bind(tenant_id)
        .execute(&mut *tx)
        .await?;
    
    // 2. OAuth tokens (reference discord_users)
    sqlx::query("DELETE FROM oauth_tokens WHERE user_id IN 
        (SELECT discord_id FROM discord_users WHERE tenant_id = ?)")
        .bind(tenant_id)
        .execute(&mut *tx)
        .await?;

    // 3. Users (reference tenant)
    sqlx::query("DELETE FROM discord_users WHERE tenant_id = ?")
        .bind(tenant_id)
        .execute(&mut *tx)
        .await?;

    // 4. Settings (reference tenant)
    sqlx::query("DELETE FROM tenant_settings WHERE tenant_id = ?")
        .bind(tenant_id)
        .execute(&mut *tx)
        .await?;

    // 5. Tenant itself
    sqlx::query("DELETE FROM tenants WHERE id = ?")
        .bind(tenant_id)
        .execute(&mut *tx)
        .await?;

    // Commit all deletes together
    tx.commit().await?;
    Ok(())
}
```

**Why manual delete order (not FOREIGN KEY CASCADE)?**
- More explicit (audit logs show each delete)
- Easier to handle partial failures (can retry individual steps)
- Can emit events for each deleted entity (webhooks, logging, metrics)
- Works with soft deletes if you ever need audit trails

If you use `FOREIGN KEY CASCADE`, SQLite handles the order, but:
- ❌ Harder to debug what got deleted
- ❌ Can't selectively recover if something goes wrong
- ❌ No intermediate audit trail

## Pitfall: External API Call AFTER Cascade Delete

**Bad (inconsistent state):**
```rust
// Delete from database first
db::delete_tenant(&pool, &tenant_id).await?;  // Tenant gone from DB

// Then tell external API
client
    .delete(&format!("https://discord.com/api/v10/users/@me/guilds/{}", guild_id))
    .send()
    .await?;  // ❌ If this fails, DB is already gone but Discord bot is still there
```

**Problem:** If external API call fails after database delete:
- Database shows tenant deleted ✅
- Discord bot is still in the guild ❌
- No way to know to retry the external call
- Inconsistent state: database record gone, external resource lingering

**Good (always call external API first):**
```rust
// Tell external API first
client.delete(...).send().await?;  // If fails, nothing changed locally

// Then delete from database (guaranteed to succeed if we reach here)
db::delete_tenant(&pool, &tenant_id).await?;
```

Now if either step fails, state is consistent:
- External call fails → Database unchanged, user can retry
- Database delete fails → External resource unchanged, user can retry
- Both succeed → Fully consistent

## Pitfall: Credentials Not Available in Handler

**Bad (storing Http client in AppState fails):**
```rust
pub struct AppState {
    pub http: Arc<Http>,  // ❌ Http doesn't implement Clone
}
```

Serenity's `Http` client is not `Clone`-safe because it holds non-cloneable resources (connections, caches, etc.). Wrapping it in `Arc` doesn't help — `Arc<Http>` still can't be cloned for passing to different async tasks.

**Good (store credentials, not the client):**
```rust
pub struct AppState {
    pub discord_token: String,  // ✅ String is Clone
}

// In handler, create a fresh reqwest client
let client = reqwest::Client::new();
client
    .delete(url)
    .bearer_auth(&state.discord_token)
    .send()
    .await?
```

This works because:
- `reqwest::Client` is thread-safe and cheap to create
- String credentials can be cloned easily
- Each handler gets its own client (no contention)

## Pitfall: Forgetting to Parse String to Typed ID

**Bad (type mismatch):**
```rust
let guild_id = settings.guild_id;  // String

client
    .delete(&format!(".../guilds/{}", guild_id))
    .send()
    .await?  // guild_id is already in string form, this works
```

Works here but hiding a mistake. If you later tried to call a typed Discord API:
```rust
let guild_id = settings.guild_id;  // String
state.http.leave_guild(guild_id.into())  // ❌ Type mismatch: expected GuildId, got String
```

**Good (explicit parse + error handling):**
```rust
let guild_id: u64 = settings.guild_id.parse()
    .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(
        error_response("Invalid guild ID stored in database")
    )))?;

// Now guild_id is u64, can be used with typed APIs
client
    .delete(&format!("https://discord.com/api/v10/users/@me/guilds/{}", guild_id))
    .send()
    .await?
```

Catch parsing errors early, before the external call.

## Testing Cascade Delete

```rust
#[tokio::test]
async fn test_delete_tenant_cascade() {
    let db = setup_test_db().await;
    
    // Create tenant with users and sessions
    db.create_tenant("test-tenant").await.unwrap();
    db.add_user("test-tenant", "user-123").await.unwrap();
    db.add_session("user-123", "session-abc").await.unwrap();
    
    // Verify data exists
    assert!(db.get_tenant("test-tenant").await.unwrap().is_some());
    assert_eq!(db.count_users("test-tenant").await.unwrap(), 1);
    assert_eq!(db.count_sessions("user-123").await.unwrap(), 1);
    
    // Delete tenant
    db.delete_tenant("test-tenant").await.unwrap();
    
    // Verify all cascade deletes occurred
    assert!(db.get_tenant("test-tenant").await.unwrap().is_none());
    assert_eq!(db.count_users("test-tenant").await.unwrap(), 0);
    assert_eq!(db.count_sessions("user-123").await.unwrap(), 0);
}

#[tokio::test]
async fn test_delete_tenant_external_api_failure() {
    let db = setup_test_db().await;
    let mut mock_client = MockHttpClient::new();
    
    // Discord API returns 404 (guild already gone)
    mock_client.expect_delete().return_once(Err(404));
    
    // Create and delete tenant
    db.create_tenant("test-tenant").await.unwrap();
    let result = delete_tenant_with_api(&db, &mock_client, "test-tenant").await;
    
    // Deletion still succeeds despite external API failure
    assert!(result.is_ok());
    assert!(db.get_tenant("test-tenant").await.unwrap().is_none());
}
```

## Deployment Checklist

- [ ] External API credentials stored in AppState (String, not Arc<Client>)
- [ ] External API call happens BEFORE cascade delete
- [ ] External API failures logged but non-blocking
- [ ] Cascade delete is transactional (wrapped in sqlx transaction)
- [ ] Delete order respects foreign key dependencies
- [ ] Returned status code is based on database result, not external API
- [ ] Audit log captures what was deleted from database
- [ ] Tests cover both external API success and failure cases

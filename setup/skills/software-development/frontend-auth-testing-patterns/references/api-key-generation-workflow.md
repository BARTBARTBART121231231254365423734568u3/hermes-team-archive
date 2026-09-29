# API Key Generation and Distribution Workflow

When moving from test mode (any-key-accepted) to production (real API key validation), you need a way to generate and distribute API keys to users.

## The Challenge

In the AuthList session, we faced this:

1. **Dashboard created and live** ✅
2. **API authentication middleware implemented** ✅
3. **But no mechanism to CREATE valid API keys** ❌
4. **Result**: Test mode fallback needed until API key generation was in place

## Solution: Admin-Gated Tenant & Key Creation

The pattern is:

1. **Admin only** can create new tenants via `/api/tenants` endpoint
2. Admin provides a Bearer token with admin privileges
3. When a tenant is created, the API generates a unique API key
4. That key is returned ONCE to the admin (not stored in plaintext)
5. Admin distributes the key to the tenant via secure channel
6. Tenant uses that key to authenticate dashboard login

## Implementation in Rust/Axum

```rust
// Handler to create a new tenant (admin-only)
#[derive(Deserialize)]
pub struct CreateTenantRequest {
    pub name: String,
    pub guild_id: String,
    // ... other fields
}

#[derive(Serialize)]
pub struct TenantResponse {
    pub id: String,
    pub name: String,
    pub created_at: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub api_key: Option<String>,  // Only returned on CREATE, never on GET/LIST
}

async fn create_tenant(
    ApiAuth(principal): ApiAuth,  // Must be admin
    State(state): State<Arc<AppState>>,
    Json(req): Json<CreateTenantRequest>,
) -> Result<Json<TenantResponse>, StatusCode> {
    // 1. Verify admin
    if !principal.is_admin() {
        return Err(StatusCode::FORBIDDEN);
    }

    // 2. Create tenant
    let tenant_id = uuid::Uuid::new_v4().to_string();
    let api_key = uuid::Uuid::new_v4().to_string();  // Random key, one-time only

    // 3. Store in database
    crate::db::create_tenant(&state.db, &tenant_id, &req.name).await?;
    crate::db::set_tenant_api_key(&state.db, &tenant_id, &api_key).await?;

    // 4. Return key ONLY on creation
    Ok(Json(TenantResponse {
        id: tenant_id,
        name: req.name,
        created_at: chrono::Utc::now().to_rfc3339(),
        api_key: Some(api_key),  // One-time only
    }))
}

// When listing tenants, NEVER return the key
async fn list_tenants(
    ApiAuth(principal): ApiAuth,
    State(state): State<Arc<AppState>>,
) -> Result<Json<Vec<TenantResponse>>, StatusCode> {
    let tenants = crate::db::get_all_active_tenants(&state.db).await?;
    Ok(Json(
        tenants
            .into_iter()
            .filter(|t| principal.can_access_tenant(&t.id))
            .map(|t| TenantResponse {
                id: t.id,
                name: t.name,
                created_at: t.created_at,
                api_key: None,  // NEVER return this
            })
            .collect(),
    ))
}
```

## Workflow for Admin

```bash
# 1. Create a test tenant
curl -X POST https://bot.example.com/api/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Server",
    "guild_id": "123456789",
    ...
  }'

# Response:
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "name": "Test Server",
#   "created_at": "2026-08-29T13:30:00Z",
#   "api_key": "abcd1234-efgh5678-ijkl9012-mnop3456"
# }

# 2. Copy the api_key and give to tenant
# 3. Tenant pastes it into dashboard login → authenticated ✅
```

## Security Considerations

1. **API key returned ONCE only** — after creation, it's not accessible again (not stored in plaintext)
2. **Admin token required** — only privileged callers can create tenants
3. **HTTPS enforced** — Railway enforces HTTPS only
4. **Database isolation** — each tenant's key is scoped to their tenant_id
5. **Rotation** — if key is compromised, admin can revoke and issue a new one

## Database Schema

```sql
CREATE TABLE tenant_settings (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT NOT NULL UNIQUE,
    api_key TEXT NOT NULL UNIQUE,  -- hashed or salted in production
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX idx_api_key ON tenant_settings(api_key);
```

## What NOT to Do

- ❌ Store API keys in plaintext in the database (hash them like passwords)
- ❌ Return keys on GET/LIST endpoints (one-time-only on CREATE)
- ❌ Allow non-admin users to create tenants
- ❌ Make keys easy to guess (use UUID4 or equivalent)
- ❌ Log API keys in error messages or logs

## Testing the Workflow

1. Create a tenant with admin token ✅
2. Copy the returned API key
3. Try to list tenants with that key (should show only this tenant) ✅
4. Try to list tenants again with admin token (should show all tenants) ✅
5. Try to create a new tenant with the tenant key (should get 403 Forbidden) ✅

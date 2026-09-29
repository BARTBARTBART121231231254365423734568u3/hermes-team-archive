# Multi-Tenant Auth Security Patterns

## Problem: Three Critical Vulnerabilities Found in AuthList Bot (Aug 30, 2026)

When deploying multi-tenant Discord bots with dashboards, three security anti-patterns emerged:

### 1. Plaintext Secret Storage

**The issue:** Discord bot tokens and Steam API keys were stored as plaintext TEXT columns in SQLite.

**Threat:** Database/backup leak = immediate credential compromise of all connected Discord bots and Steam accounts.

**Code example (BAD):**
```rust
// In tenant_settings table: discord_token = "**** actual token ****" (plaintext in SQLite)
struct TenantSettings {
    discord_token: String,  // PLAINTEXT — anyone with DB access owns all your Discord bots
    steam_web_api_key: String,  // PLAINTEXT
}
```

**Fix: AES-256-GCM Encryption**

Encrypt secrets at the application layer BEFORE writing to the database. Use AES-256-GCM with random nonces:

```rust
// bot/src/crypto.rs
use aes_gcm::{Aes256Gcm, Nonce, Key};
use aes_gcm::aead::Apayload;
use rand::Rng;

pub struct Encryptor {
    key: Key<Aes256Gcm>,
}

impl Encryptor {
    pub fn from_env_value(key_b64: &str) -> anyhow::Result<Self> {
        let key_bytes = base64::engine::general_purpose::STANDARD.decode(key_b64)?;
        if key_bytes.len() != 32 {
            return Err(anyhow::anyhow!("encryption key must be 32 bytes, got {}", key_bytes.len()));
        }
        Ok(Self { key: Key::<Aes256Gcm>::from_slice(&key_bytes).clone() })
    }

    pub fn encrypt(&self, plaintext: &str) -> String {
        let cipher = Aes256Gcm::new(&self.key);
        let mut nonce_bytes = [0u8; 12];
        rand::thread_rng().fill(&mut nonce_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);
        
        let ciphertext = cipher
            .encrypt(nonce, plaintext.as_bytes())
            .expect("encryption failed");
        
        // Format: base64(nonce || ciphertext+tag)
        let mut payload = nonce.to_vec();
        payload.extend_from_slice(&ciphertext);
        base64::engine::general_purpose::STANDARD.encode(&payload)
    }

    pub fn decrypt(&self, ciphertext_b64: &str) -> anyhow::Result<String> {
        let payload = base64::engine::general_purpose::STANDARD.decode(ciphertext_b64)?;
        if payload.len() < 12 {
            return Err(anyhow::anyhow!("ciphertext too short"));
        }
        
        let (nonce_bytes, ct) = payload.split_at(12);
        let nonce = Nonce::from_slice(nonce_bytes);
        let cipher = Aes256Gcm::new(&self.key);
        
        let plaintext = cipher.decrypt(nonce, ct)?;
        Ok(String::from_utf8(plaintext)?)
    }
}

// Usage on write:
let encrypted_token = encryptor.encrypt("raw-discord-token")?;
// Store encrypted_token in database

// Usage on read:
let plaintext_token = encryptor.decrypt(&db_value)?;
// Use plaintext_token to authenticate to Discord
```

**Setup:**
1. Generate a random 32-byte key:
   ```bash
   openssl rand -base64 32
   # Output: example-key-base64-encoded-32-bytes
   ```
2. Store as `ENCRYPTION_KEY` environment variable on Railway
3. On application startup, initialize `Encryptor::from_env_value()` once and store in `AppState`
4. Encrypt all writes; decrypt all reads transparently

**Migration (existing plaintext data):**
On startup, scan for rows where decryption fails (still plaintext), and re-encrypt them:

```rust
pub async fn migrate_plaintext_tenant_secrets(
    db: &SqlitePool,
    encryptor: &Encryptor,
) -> anyhow::Result<()> {
    let mut rows = sqlx::query!("SELECT id, discord_token FROM tenant_settings")
        .fetch_all(db)
        .await?;
    
    for row in rows {
        // Try to decrypt; if it fails, it's plaintext
        if encryptor.decrypt(&row.discord_token).is_err() {
            // Still plaintext, encrypt it
            let encrypted = encryptor.encrypt(&row.discord_token)?;
            sqlx::query!("UPDATE tenant_settings SET discord_token = ? WHERE id = ?", encrypted, row.id)
                .execute(db)
                .await?;
        }
    }
    Ok(())
}
```

**Session 2026-08-30 (AuthList):** All 4 production tenants had plaintext secrets stored in SQLite. Migration identified and encrypted all 3 legacy plaintext rows on startup. New rows encrypted automatically.

---

### 2. Broken OAuth Access Control

**The issue:** Any Discord user who logged in via OAuth was granted `AuthPrincipal::Admin`, allowing them to see/modify ALL tenants' data.

**Threat:** Any guild member can access and modify other servers' configurations, export member lists, etc.

**Code example (BAD):**
```rust
// Old auth pattern: OAuth always means Admin
async fn oauth_callback(...) -> Response {
    let authorized_user = oauth.authorize_and_check_membership(&code, &guild_id).await?;
    
    // WRONG: session is always Admin, regardless of which guild the user belongs to
    let session = create_session(&db, &authorized_user.discord_id, "ADMIN").await?;
    // Now user can access /api/tenants, see ALL tenants
}
```

**Fix: Tenant-Scoped Sessions**

OAuth login creates a session scoped to the tenant (guild) the user is a member of, not Admin:

```rust
async fn oauth_callback(
    State(state): State<Arc<AppState>>,
    Query(query): Query<OAuthCallbackQuery>,
) -> Response {
    // ... CSRF state validation (see section 3) ...
    
    let authorized = state.oauth.authorize_and_check_membership(&code, &guild_id).await?;
    
    // Look up the TENANT for this guild (not all tenants)
    let tenant = get_tenant_by_guild_id(&state.db, &guild_id).await?;
    
    // Create session scoped to this specific tenant, not Admin
    let token = create_session(
        &state.db,
        &authorized.discord_id,
        &tenant.id,  // Scoped: this user can only access this tenant
    ).await?;
    
    // Return token (user logs in to dashboard for this guild only)
    Redirect::temporary(&format!("{}/?token={}", state.dashboard_url, token))
}
```

**Middleware enforcement:**

```rust
// Every /api/* route checks the token and resolves to a specific tenant
pub async fn api_auth(headers: &HeaderMap) -> anyhow::Result<AuthPrincipal> {
    let <REDACTED_SECRET>(headers)?;
    
    // Resolve token to user + tenant
    let (user_id, tenant_id) = get_session_principal(&db, &token).await?;
    
    // User can ONLY access endpoints for their tenant_id
    Ok(AuthPrincipal::Tenant(tenant_id))
}

// In route handlers:
#[post("/api/tenants/:id/members")]
async fn list_members(
    principal: AuthPrincipal,  // Extracted by middleware
    Path(tenant_id): Path<String>,
) -> Response {
    // Middleware already verified principal is scoped to a tenant
    // Now verify it's THIS tenant (not a different one)
    match principal {
        AuthPrincipal::Tenant(scoped_tenant_id) if scoped_tenant_id == tenant_id => {
            // Allowed: user can access this tenant
            list_members_impl(&db, &tenant_id).await
        }
        AuthPrincipal::Tenant(_) => {
            // Denied: user tried to access a different tenant
            StatusCode::FORBIDDEN.into_response()
        }
        AuthPrincipal::Admin => {
            // Admin (password login) can access any tenant
            list_members_impl(&db, &tenant_id).await
        }
    }
}
```

**Test scenarios:**
- Create two tenants (Guild A, Guild B)
- Log in as User1 (member of Guild A) via OAuth → should see ONLY Guild A data
- Log in as User2 (member of Guild B) via OAuth → should see ONLY Guild B data
- User1 tries to access `/api/tenants/B/members` → 403 Forbidden
- User1 with Admin token (password login) tries the same → 200 OK

**Session 2026-08-30 (AuthList):** All OAuth sessions now properly scoped. Tested with 7 authorization scenarios (tenant mismatch, wrong principal type, etc.).

---

### 3. Missing OAuth CSRF State Verification

**The issue:** OAuth state tokens were generated and round-tripped by Discord but never validated server-side.

**Threat:** Cross-Site Request Forgery (CSRF): attacker crafts a malicious link sending a user to your Discord OAuth authorization URL, then hijacks the callback to a server under attacker's control. Without state validation, attacker can use the code to complete the login flow on your app.

**Code example (BAD):**
```rust
// On login:
async fn oauth_login(...) -> Redirect {
    let state = "random-value";  // Generated but never stored
    Redirect::to(discord_oauth_url(&state))
}

// On callback:
async fn oauth_callback(Query(query): Query<OAuthCallbackQuery>) -> Response {
    let code = query.code;  // Use code
    // WRONG: never check if query.state matches what we sent
    let <REDACTED_SECRET>(&code).await?;
}
```

**Fix: CSRF State Verification**

Generate and validate state tokens:

```rust
// Generate a random state on /oauth/login
async fn oauth_login(State(state): State<Arc<AppState>>) -> Redirect {
    let csrf_state = generate_random_state();  // 32-char hex string
    
    // Store state server-side (in-memory map or cache, valid for 10 minutes)
    if let Ok(mut states) = state.oauth_csrf_states.lock() {
        states.insert(csrf_state.clone());
    }
    
    let url = state.oauth.authorize_url(&csrf_state);
    Redirect::temporary(&url)
}

// Validate state on /oauth/callback
async fn oauth_callback(
    State(state): State<Arc<AppState>>,
    Query(query): Query<OAuthCallbackQuery>,
) -> Response {
    // CSRF state validation FIRST, before anything else
    let Some(csrf_state) = &query.state else {
        return (StatusCode::BAD_REQUEST, "Missing CSRF state").into_response();
    };
    
    // Check if state is in our set of valid states
    let csrf_valid = if let Ok(mut states) = state.oauth_csrf_states.lock() {
        states.remove(csrf_state)  // Remove after validation (one-time use)
    } else {
        false
    };
    
    if !csrf_valid {
        tracing::warn!("OAuth callback with invalid/missing CSRF state");
        return (StatusCode::FORBIDDEN, "CSRF validation failed").into_response();
    }
    
    // NOW proceed with the code exchange
    let code = query.code?;  // Already validated state, safe to proceed
    let authorized = state.oauth.authorize_and_check_membership(&code, &guild_id).await?;
    // ...
}
```

**State generation (Rust):**
```rust
use rand::Rng;

fn generate_random_state() -> String {
    let random_bytes = rand::random::<[u8; 16]>();
    let mut hex = String::with_capacity(32);
    for byte in &random_bytes {
        use std::fmt::Write;
        write!(hex, "{:02x}", byte).unwrap();
    }
    hex
}
```

**Cleanup:** States are one-time use and should expire after 10 minutes. Implement a background cleanup job or use a TTL cache.

**Session 2026-08-30 (AuthList):** CSRF state verification was missing. Implemented as in-memory HashSet, generated on login, validated and removed on callback. All future OAuth flows now protected.

---

## Testing Checklist

**Encryption:**
- [ ] Encrypt plaintext → decrypt → matches original
- [ ] Different plaintexts → different ciphertexts (due to random nonces)
- [ ] Decrypt invalid base64 → error
- [ ] Decrypt wrong key → decryption error (no panic)

**OAuth Scoping:**
- [ ] User in Guild A logs in → session scoped to Guild A
- [ ] Same user tries `/api/tenants/B/members` → 403 Forbidden
- [ ] User in Guild B logs in → session scoped to Guild B
- [ ] User in Guild B tries `/api/tenants/A/members` → 403 Forbidden
- [ ] Admin (password) login can access all tenants → 200 OK

**CSRF State:**
- [ ] `/oauth/login` generates a state and stores it
- [ ] Callback without state → 400 Bad Request
- [ ] Callback with invalid state → 403 Forbidden
- [ ] Callback with valid state → 200 OK, state removed from storage
- [ ] Replay same state twice → 403 on second attempt (one-time use)

**Logout Revocation:**
- [ ] User logs out → session deleted from database
- [ ] User tries to reuse old token → 401 Unauthorized
- [ ] New login generates new token → 200 OK

---

## References

- AES-256-GCM: https://en.wikipedia.org/wiki/Galois/Counter_Mode
- OAuth 2.0 CSRF protection: https://tools.ietf.org/html/rfc6749#section-10.12
- OWASP: https://owasp.org/www-community/attacks/csrf

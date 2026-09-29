# Coordinating Multiple Services on Railway

## Problem

You have multiple services (Discord bot, HTTP API, SvelteKit dashboard) that need to be:
1. Deployed together to the same Railway project
2. Share a database and configuration
3. Communicate with each other (dashboard calls bot API)
4. Deploy from a single monorepo with multiple Dockerfiles

This reference covers coordinating these services on Railway so they work seamlessly as a unified platform.

## Architecture Pattern

```
Railway Project: authlist-bot
├── Service: bot (Rust binary with Axum HTTP server)
│   ├── Listens on 0.0.0.0:8080
│   ├── Discord event handler
│   ├── REST API routes (/api/health, /api/dashboard, /api/tenants)
│   └── Uses: database, config
│
├── Service: dashboard (Node.js / SvelteKit express server)
│   ├── Listens on 0.0.0.0:3000
│   ├── Serves built frontend
│   ├── Calls bot API via public URL
│   └── Uses: config (apiBase URL)
│
└── Shared: database (SQLite on persistent volume /data)
    └── authlist.db with multi-tenant schema
```

## Setup in Railway

### 1. Create Project

```bash
railway project create --name authlist-bot
railway environment create --name production
```

### 2. Create Services from Monorepo

**Option A: Create from GitHub (Recommended)**

```bash
# Via CLI
railway service create --name bot \
  --repo https://github.com/user/authlist-bot \
  --branch main \
  --root-directory bot

railway service create --name dashboard \
  --repo https://github.com/user/authlist-bot \
  --branch main \
  --root-directory dashboard
```

**Option B: Create via Dashboard UI**

1. Login to railway.app
2. New Project → Import from GitHub (select repo)
3. Create Service → Select service (bot/dashboard/etc from directory)

### 3. Configure Shared Volume (Database)

```bash
railway volume create --name authlist-data --size 1G
railway service attach --service bot \
  --volume authlist-data:/data
railway service attach --service dashboard \
  --volume authlist-data:/data  # Optional if dashboard needs read access
```

Now both services can see `/data/authlist.db`.

### 4. Configure Environment Variables

**Shared across all services:**
```bash
railway env set DATABASE_URL=sqlite:///data/authlist.db?mode=rwc
railway env set API_TOKEN=your-admin-key  # Shared by all services
```

**Bot-specific:**
```bash
railway env set DISCORD_TOKEN=xoxb...
railway env set LOG_LEVEL=info
railway env set PORT=8080
```

**Dashboard-specific:**
```bash
railway env set PORT=3000
```

### 5. Dockerfile Configuration

**bot/Dockerfile** (Rust)
```dockerfile
FROM rust:latest as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates
COPY --from=builder /app/target/release/authlist_bot /app/bot
WORKDIR /app
CMD ["./bot"]
```

**dashboard/Dockerfile** (Node.js/SvelteKit)
```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/server.js ./server.js
COPY --from=builder /app/package.json ./package.json
CMD ["node", "server.js"]
```

### 6. Verify Services Start

```bash
railway logs --service bot --tail 50
railway logs --service dashboard --tail 50
```

Expected output:
- Bot: "Discord client logged in", "listening on 0.0.0.0:8080"
- Dashboard: "Dashboard running on port 3000"

## Inter-Service Communication

### Bot → Database

**Pattern:** Direct connection via DATABASE_URL

```rust
// bot/src/db.rs
let pool = sqlx::SqlitePool::connect(&env!(
    "DATABASE_URL",
    "sqlite:///data/authlist.db"
))
.await?;
```

Both services on the same volume see the same SQLite file → shared database.

### Dashboard → Bot API

**Pattern:** HTTP calls via public Railway URL

**Dashboard detects Bot URL at runtime:**

```typescript
// dashboard/src/App.svelte
let apiBase: string

if (typeof window !== 'undefined') {
  if (window.location.hostname === 'dashboard-production-da2a.up.railway.app') {
    apiBase = 'https://bot-production-7612.up.railway.app/api'
  } else {
    apiBase = 'http://localhost:8080/api'
  }
}
```

This works because:
1. Dashboard deployment has a public URL (dashboard-production-*.up.railway.app)
2. Bot deployment has a public URL (bot-production-*.up.railway.app)
3. Dashboard is a static frontend that calls the bot API
4. No hardcoding of URLs → works in any deployment

### Bot → External APIs (Optional)

If bot needs to call third-party APIs:

```bash
railway env set STEAM_WEB_API_KEY=...
railway env set OAUTH_CLIENT_SECRET=...
```

These are per-service environment variables.

## Deployment Flow

### Single Deploy (Both Services)

```bash
# Edit code
cd /path/to/monorepo
git add -A
git commit -m "feat: add new API endpoint"
git push origin main

# Railway detects push → builds both services in parallel
# ✅ Bot deployed at bot-production-*.up.railway.app
# ✅ Dashboard deployed at dashboard-production-*.up.railway.app
```

### Staggered Deploy (One Service at a Time)

If you only want to deploy the bot:

```bash
# Option A: Empty-commit redeploy
cd bot
git commit --allow-empty -m "trigger: redeploy bot"
cd ..
git push origin main

# Option B: Railway CLI
railway redeploy --service bot --yes
```

## Database Migrations

**Pattern:** Run migrations at bot startup

```rust
// bot/src/db.rs
#[tokio::main]
async fn main() -> Result<()> {
    let pool = sqlx::SqlitePool::connect(&database_url).await?;
    
    // Run pending migrations
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await?;
    
    tracing::info!("Migrations applied successfully");
    
    // Continue with startup
    discord::start(&pool).await?;
    http::start(&pool).await?;
    
    Ok(())
}
```

**Advantage**: Migrations run automatically on every bot startup, so new deployments are schema-compatible immediately.

**Migrations directory structure:**
```
bot/migrations/
├── 0001_initial_schema.sql
├── 0002_add_tenants.sql
├── 0003_add_tenant_settings.sql
├── 0004_add_oauth_sessions.sql
└── 0005_add_indexes.sql
```

## Persistent Volume Management

### Check Volume Contents

```bash
railway shell
ls -la /data
stat /data/authlist.db  # Check size and modified time
```

### Backup Database

```bash
railway shell
cp /data/authlist.db /data/authlist-backup-$(date +%s).db
ls -la /data/*.db
```

### Restore from Backup

```bash
railway shell
cp /data/authlist-backup-1695000000.db /data/authlist.db
```

## Troubleshooting Multi-Service Issues

### Bot and Dashboard Both Running, But Dashboard Gets 404 on API Calls

**Symptom:** Dashboard loads (HTML renders) but shows "Not Connected" or network errors.

**Check:**
1. **Is bot running?**
   ```bash
   curl https://bot-production-*.up.railway.app/healthz
   # Should return: ok
   ```

2. **Can dashboard reach bot URL?**
   ```bash
   # From browser console (you're on dashboard):
   fetch('https://bot-production-*.up.railway.app/api/health')
   # Should return JSON or 401 (auth required, but service is reachable)
   ```

3. **Check CORS headers:**
   ```bash
   curl -i https://bot-production-*.up.railway.app/api/health
   # Look for: Access-Control-Allow-Origin header
   ```
   If missing, add CORS middleware to bot.

### Dashboard Keeps Getting 401 on API Calls

**Symptom:** Dashboard logs in fine but all API calls fail with 401.

**Check:**
1. **Is the API key valid?**
   ```bash
   curl -H "Authorization: Bearer $KEY" \
     https://bot-production-*.up.railway.app/api/dashboard/stats
   # Should return 200 with data
   ```

2. **Is dashboard sending the key correctly?**
   ```typescript
   // Dashboard DevTools console:
   localStorage.getItem('api_token')  // Should show your key
   
   // Network tab → inspect API call → Headers
   // Should have: Authorization: Bearer ...
   ```

3. **Did key get rotated?**
   ```bash
   # Check database
   sqlite3 /data/authlist.db
   SELECT api_key FROM tenant_settings LIMIT 1;
   # Compare with what's in localStorage
   ```

### Both Services Running but Database Isn't Shared

**Symptom:** Bot creates data but dashboard doesn't see it (or vice versa).

**Check:**
1. **Are both services attached to the volume?**
   ```bash
   railway env show  # Check DATABASE_URL path
   railway volume ls
   ```

2. **Is the path consistent?**
   - Bot: `/data/authlist.db`
   - Dashboard: `/data/authlist.db` (if it queries DB directly)
   Both must use same path.

3. **Is SQLite WAL mode enabled?**
   ```bash
   sqlite3 /data/authlist.db "PRAGMA journal_mode;"
   # Should return: wal
   ```
   WAL mode allows multiple processes to read/write concurrently.

### One Service Deploys But Not the Other

**Symptom:** After git push, bot updates but dashboard is stale.

**Check:**
1. **Did both services trigger a build?**
   Railway Dashboard → Deployments tab
   - Should see entries for both bot AND dashboard

2. **If only one shows:**
   - Dockerfile path may be wrong
   - Service root-directory not set in railway.json
   - Fix: Update railway.json with correct service paths

3. **Force redeploy both:**
   ```bash
   git commit --allow-empty -m "trigger: redeploy all services"
   git push origin main
   ```

## Railway Configuration File (Optional)

**railway.json** (in repo root)

```json
{
  "services": [
    {
      "name": "bot",
      "root-directory": "bot",
      "builder": "dockerfile",
      "dockerfile-path": "bot/Dockerfile"
    },
    {
      "name": "dashboard",
      "root-directory": "dashboard",
      "builder": "dockerfile",
      "dockerfile-path": "dashboard/Dockerfile"
    }
  ],
  "volumes": [
    {
      "name": "authlist-data",
      "path": "/data",
      "services": ["bot", "dashboard"]
    }
  ]
}
```

This makes deployment deterministic and repeatable.

## Performance Notes

- **SQLite on shared volume:** Works fine for small-to-medium databases (<1GB), multiple concurrent readers/writers
- **Parallel builds:** Both services build in parallel (faster than sequential)
- **Deployment time:** Total time = max(bot_build, dashboard_build) + startup time
- **Example:** Bot builds in 3min, dashboard in 1min → 3min total

## Security Considerations

1. **Environment variables are per-service:** Bot gets DISCORD_TOKEN, dashboard doesn't (good)
2. **Database on shared volume:** Both services can read/write (ensures data consistency)
3. **API keys in database:** Admin token + tenant keys stored in tenant_settings table (encrypted at rest if you configure SQLite encryption)
4. **CORS headers:** Configure bot to allow dashboard domain:
   ```rust
   .layer(CorsLayer::very_permissive())  // Dev only
   // Production: specify allowed origins
   ```

## Migration Patterns

### Migrating Single-Tenant to Multi-Tenant

**In this session:** We created migrations 0004-0007 that add multi-tenant tables:
- `tenants` (guild_id → tenant_id mapping)
- `tenant_settings` (api_key per tenant)
- `tenant_members` (user assignments)
- `oauth_sessions` (Discord OAuth state)

**They're backward-compatible:** Old single-tenant data stays in place, new data uses new schema.

### Running Migrations

```bash
# Automatic (at bot startup)
# ✓ No manual steps needed

# Manual (if needed for debugging)
railway shell
sqlx migrate run --database-url sqlite:///data/authlist.db
```

## See Also

- `rapid-code-deploy-cycle` — Deploying via git push
- `railway-cli` — Detailed Railway CLI commands
- `axum-rest-api-design` — Building the bot API
- `database-schema-refactoring` — Multi-tenant schema design

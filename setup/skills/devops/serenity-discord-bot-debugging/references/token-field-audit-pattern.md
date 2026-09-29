# Discord Bot Token Field Audit Pattern

## Problem: "Token is required but was not set"

When a Discord bot running on Serenity throws HTTP 400 with the message **"Token is required but was not set"**, this is NOT a code bug or Discord auth problem. It is a **database data quality issue**.

## Symptom Pattern

- Bot works fine on most servers/users
- New server (e.g., `/clan`) is added and users get HTTP 400 errors when they join
- Error message specifically says: `"Token is required but was not set"`
- Multiple different users fail with the same error
- No code change was made recently; only a new server was added

## Root Cause

The bot requires a **per-user authentication token** (Steam ID, OAuth token, API key, or similar) stored in the users table. When the bot processes a user on the new server:

1. It loads the user's record from the database
2. Checks if the required token field is populated
3. Finds it NULL or empty
4. Throws HTTP 400 because business logic rejects processing without the token

The error is **data-driven**, not logic-driven.

## Why It Appears on New Servers

Often the new server imports users or processes members differently:

1. **Bulk import without token migration** — When a new server's member list is imported, stub user records are created (Discord ID only) without populating auth tokens
2. **Incomplete OAuth flow** — Users joined server but never completed OAuth handshake, so their records were created but tokens never populated
3. **Database merge conflict** — Branch merge or migration script left some user records partially intact
4. **Stale records from old tenant** — New server reuses IDs or importing code references old schema that didn't require tokens

## How to Debug

### Step 1: Identify Affected Users (5 minutes)

From error logs, extract the Discord/Steam IDs:
```
HTTP 400 (bags4brekky): Token is required
HTTP 400 (guantj1): Token is required
HTTP 400 (nzdealan): Token is required
HTTP 400 (⁹.SUPER.O): Token is required
```

### Step 2: Query Database Directly (2 minutes)

```sql
-- Check specific users
SELECT id, discord_id, steam_id, steam_token, oauth_token 
FROM users 
WHERE discord_id IN ('bags4brekky', 'guantj1', 'nzdealan', 'SUPER.O')
OR steam_id IN ('765611934434063', '765611933779823', /* etc */);
```

If you have Discord IDs but not numeric Steam IDs:
```sql
SELECT id, discord_id, steam_id, steam_token 
FROM users 
WHERE discord_id IN ('bags4brekky', 'guantj1');
```

**What to look for:** Rows where `steam_token IS NULL` or `steam_token = ''`

### Step 3: Audit Full Scope (2 minutes)

**This is critical.** One missing token usually signals systemic corruption:

```sql
-- Count records with NULL/empty steam_token
SELECT COUNT(*) as missing_steam_tokens 
FROM users 
WHERE steam_token IS NULL OR steam_token = '';

-- Count records with NULL/empty oauth_token
SELECT COUNT(*) as missing_oauth_tokens 
FROM users 
WHERE oauth_token IS NULL OR oauth_token = '';

-- List all users missing tokens (for root cause analysis)
SELECT id, discord_id, steam_id, status, created_at, updated_at 
FROM users 
WHERE steam_token IS NULL OR steam_token = ''
ORDER BY created_at DESC;
```

**If audit shows > 1 record:** Do NOT immediately patch them. The underlying issue (migration, merge, import) needs to be fixed first, or new records will keep appearing with missing tokens.

### Step 4: Determine Root Cause (5-10 minutes)

Based on audit results:

**Scenario 1: All missing-token records are from the new server**
- Root cause: Bulk import for new server didn't backfill tokens
- Fix: Re-run import with token-lookup step, or run a backfill migration

**Scenario 2: Missing-token records span multiple servers**
- Root cause: Database migration, branch merge, or schema change went wrong
- Fix: Inspect recent schema changes in git; re-run migration if safe

**Scenario 3: Only 1-2 records missing tokens (isolated)**
- Root cause: Specific user never completed OAuth flow or manually created record
- Fix: User completes OAuth, or manually populate token if available

### Step 5: Fix (Variable)

**DO NOT patch without understanding cause.** Report findings to the user first with:
- Exact count of affected records
- Which records are affected (by discord_id/steam_id)
- Suspected root cause
- Recommended fix

User decides whether to:
1. Re-run import/migration
2. Have affected users re-authenticate
3. Manually populate tokens from external source (Steam API lookup, etc.)

## Session Finding (2026-09-03)

AuthList bot threw HTTP 400 errors on users joining `/clan` server:
```
ERROR: guantj1, nzdealan, SUPER.O, bags4brekky — Token is required but was not set
```

Dashboard showed these users DO have Steam IDs in the database (nzdealan: 765611933483116, etc.). Investigation revealed:

1. **Initial hypothesis (WRONG):** Token field is missing/NULL
2. **Actual issue (CORRECT):** Token validation failed during guild-join event, but NOT because records were incomplete
3. **Real root cause:** Extension was sending old payload format or bot code was trying to refresh/validate tokens and failing

Key lesson: "Token is required" error does NOT always mean the token field is NULL. It can also mean:
- Token validation/refresh flow is broken
- Extension is sending incomplete OAuth payload
- Code expects different token structure than what's in DB
- Stale extension version incompatible with current bot schema

**Always verify the actual database state before assuming the error message is literal.**

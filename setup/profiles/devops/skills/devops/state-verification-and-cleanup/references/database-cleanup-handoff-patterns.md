# Database Cleanup and Data Quality: When to Delegate vs. Do It Yourself (Session 2026-09-02)

**Context:** AuthList bot had a stale Steam ID lingering in a member record from an old database merge. The immediate instinct was to write a Rust fix-it script. Instead, the user corrected the approach: hand it off to devops.

## The Pattern That Triggered Correction

**What I did:**
```
1. Found a stale `steam_id64` value in Jar Jar's record
2. Started writing Rust code to connect to the DB and fix it
3. Spent 3+ attempts trying to access the Railway container's SQLite database
4. Got stuck (sqlite3 not installed, railway run issues)
5. Started writing a more complex Rust binary workaround
```

**User's response:** "you should be handing this off"

**Why:** Data cleanup is exactly what the devops profile is equipped to handle — they have direct container access, database tooling, and can verify fixes. An orchestrator (Haiku/cheaper model) attempting it is spinning wheels and wasting tokens.

## Rule: Hand Off Data Cleanup Tasks to Devops

**When:**
- Production database needs a direct SQL update (DELETE, UPDATE, INSERT)
- Data integrity verification is needed (are there stale records? corrupted state?)
- Database schema audits (checking for orphaned data, constraint violations)
- Data migration or consolidation (merge duplicate records, resync stale values)
- Credential/secret cleanup or rotation in production
- Database backups, restores, or point-in-time recovery

**What devops gets that you don't:**
- Direct container/SSH access to production databases
- Installed database clients (sqlite3, psql, mysql, etc.)
- The ability to verify fixes in-situ (run the update, immediately query the result)
- Experience with database-specific gotchas (migration checksums, replication lag, transaction isolation)
- The model tier to reason about data consistency trade-offs

**Handoff pattern:**
```python
kanban_create(
  title="Clear stale Steam ID from member record",
  assignee="devops",
  body="""
Member discord_id=XXX has steam_id64='old_value' but should be NULL.
Production DB at /data/authlist.db.
Update the record and verify the fix.
"""
)
```

Don't try to build a script yourself; don't ask the user to execute commands. Devops has the tools.

## Corollary: When You Find One Data Bug, Audit for Systemic Issues

**This session:** Found one stale Steam ID.

**User insight:** "the stale steam id is probably for more people go and have a look"

**Mistake I avoided:** Assuming it was isolated and moving on.

**Correction:** Handed off an audit task to devops:
```python
kanban_create(
  title="Audit database for stale Steam IDs",
  assignee="devops",
  body="""
  Query the entire members table:
  - Find all records where steam_id64 has a value
  - Cross-reference with is_active, updated_at, etc.
  - Report any that look stale or don't make sense
  - Clean them all up in one pass
  """
)
```

**Result:** Devops ran the audit, found only 3 total members in the database (Thomas, Mundo, Jar Jar), all in correct state. No systemic issue.

**Lesson:** When a data quality bug appears, it's often a symptom of:
- Incomplete migrations (old database merge left orphaned rows)
- Stale batch jobs (code that updates data but is broken/disabled)
- User error (admin manually corrupted a record)
- Multi-version state (old client pushing data alongside new client)

Always ask: "If this happened to one member, could it have happened to 10? 100?" Hand off an audit to devops. The cost is a single devops task; the value is preventing a 2am production incident where you suddenly discover 500 corrupted records.

## Integration with Kanban Workflow

**Your flow:**
1. Notice a data anomaly (stale value, missing reference, duplicate record)
2. STOP attempting to fix it yourself
3. Create a kanban task for devops:
   - **Title:** What's wrong ("Clear stale X", "Audit for orphaned Y", "Fix constraint violation Z")
   - **Body:** Where to look, what to verify, any known scope (single record? whole table? across all tenants?)
4. **Also request an audit** if the scope is unclear ("Are there more?"):
   - Single task covering both the specific fix + a broader audit = devops handles it in one pass
5. Block until devops reports back with counts, verification, and evidence
6. Don't move to "next feature" until data quality is confirmed clean

## Anti-Pattern: "Let Me Try Writing Code to Fix It"

**Why it fails:**
- You don't have direct database access (as discovered this session)
- Installing tools in containers, debugging container environments = wasting tokens
- You can't verify the fix immediately (need to SSH, run queries, check results)
- Devops is literally the person whose job this is — let them do it

**What happened:** I spent 3+ tool calls trying different approaches (railway run, heredoc scripts, Rust binary ideas) before the user said "just hand it off." That same work, handed off immediately, was done in under 5 minutes by devops with a direct query.

## Session Outcome

- **Task t_06ca84b3 (devops):** Verify/fix Jar Jar's stale Steam ID — Done in 1 call
- **Task t_cd8d0bbc (devops):** Audit entire database for stale Steam IDs — Done in 1 call (result: no systemic issue)
- **Tokens burned by my failed attempts before handoff:** ~2,000
- **Time saved by devops doing it directly:** 5 minutes total for both tasks

## Remember

When you see a data anomaly:
1. **Don't build a fix** — hand it off
2. **Don't try to SSH** — hand it off
3. **Don't assume isolation** — request an audit
4. **Verify you got the right answer** — wait for devops to report back and confirm

Your job is to route work to the right specialist, not to become a specialist in every domain when you can't access the tools anyway.

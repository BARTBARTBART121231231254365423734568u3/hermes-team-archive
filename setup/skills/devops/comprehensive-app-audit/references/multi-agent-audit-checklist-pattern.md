# Multi-Agent Audit Checklist Pattern

## Overview

When preparing a complex multi-service project for multi-agent review, create a structured **audit checklist** that each specialist can work through independently. This pattern emerged from coordinating audits of a multi-tenant SaaS bot + dashboard system.

## Checklist Structure

Break audit into **sections by specialty** (not by feature). Each section has:
- Clear acceptance criteria (what "PASS" means)
- Specific commands to run
- Known issues to investigate
- Expected findings
- Actionable work items to create

### Example Sections

**SECTION A: Deployment Status (DevOps)**
```
- [ ] Verify service is live at URL
- [ ] Check health endpoint returns 200
- [ ] Verify persistent volume exists and is mounted
- [ ] Check logs for startup errors
- [ ] Confirm external service connections (Discord, etc.)
- [ ] Document current project structure

Expected Result: Service operational, no critical errors
```

**SECTION B: Database Schema (DevOps + Researcher)**
```
- [ ] List all tables: sqlite3 path/db.db ".tables"
- [ ] Verify legacy schema applied (migrations 0001-0003)
- [ ] Check if new schema applied (migrations 0004-0007)
  - tenants table exists with columns: id, name, owner_discord_id, created_at, active
  - tenant_settings table exists with guild-scoped config
  - etc.
- [ ] Run: sqlite3 path/db.db ".schema tenants"
- [ ] Verify foreign keys configured

Expected Result: Schema matches project requirements
```

**SECTION C: API Routing (Coder)**

Test endpoints in two groups:

*Legacy Endpoints (Should Work):*
```
- [ ] GET /healthz → 200
- [ ] GET /authlist.csv → 401 or 200 with data
- [ ] GET /backup.csv → 401 or 200 with data
```

*New Endpoints (Testing):*
```
- [ ] GET /api/health → Should return JSON
- [ ] GET /api/dashboard/stats → Should return stats
- [ ] POST /api/tenants → Should accept request
```

Document:
- Which work (200)
- Which return 404
- Which return 500
- Error messages

**SECTION D: Code Structure (Coder + Researcher)**
```
- [ ] Read bot/src/api/routes.rs
  - Verify all routes are defined
  - Check type signatures on nested routers
- [ ] Check bot/src/models.rs
  - Verify Tenant/TenantSettings structs exist
  - Check database schema matches models
- [ ] Review bot/src/db.rs
  - Look for multi-tenant query functions
  - Verify tenant_id is threaded through queries
- [ ] Inspect bot/src/discord/handler.rs
  - Verify events are routed by guild_id
  - Check tenant loading on startup

Expected: All infrastructure in place, functions correctly
```

**SECTION G: Security (Security Agent)**
```
- [ ] Search codebase for hardcoded secrets:
  - No Discord tokens
  - No API keys
  - No database passwords
- [ ] Review authentication implementation
  - Token validation logic
  - Permission checks on mutations
  - Session expiration handling
- [ ] Check multi-tenant data isolation
  - Verify tenant_id foreign keys
  - Test that query filters by tenant
  - Ensure cross-tenant access is impossible
- [ ] Review error messages
  - Don't leak system info
  - Don't reveal which resources exist
- [ ] Check CORS on API endpoints
  - Verify proper origin whitelisting

Expected: No secrets, proper auth, isolation enforced
```

## Known Issues Section

Include a **"Known Issues to Investigate"** section in the checklist:

```markdown
## 🔍 KNOWN ISSUES TO INVESTIGATE

### Issue 1: /api/* Routes Return 404 (CRITICAL)
**Status:** Blocking integration testing
**Evidence:**
- Routes defined in code (routes.rs lines 30-47)
- Handlers implemented (health.rs, dashboard.rs)
- All deployed via Railway
- Testing shows 404 even though code looks correct

**Investigation Tasks:**
1. Check if route handlers compile
2. Verify Axum version compatibility
3. Test locally: `cargo build && ./target/release/binary`
4. Check Railway build logs
5. Verify type signatures on nested routers

**Possible Root Causes:**
- Railway caching old Docker image
- Handler compile error (hidden)
- Type signature mismatch in Axum nesting
- Axum version incompatibility

**Fix Priority:** HIGH - Blocks API testing
```

This framing tells agents:
- What's been found so far
- What the investigation path should be
- What the possible causes are
- Whether it's critical or low-priority

## Morning Handoff Structure

When preparing a project for agent audit, provide:

1. **Quick Status Summary** (1 page)
   - What's deployed and working
   - What needs review
   - Key decisions awaiting user
   - Links to live services

2. **Audit Checklist** (AGENT_AUDIT_CHECKLIST.md)
   - Sections by specialty
   - Specific commands to run
   - Expected findings
   - Known issues documented
   - Work item templates

3. **Known Issues & Root Causes**
   - Investigation status
   - Possible causes
   - Priority and blocking impact
   - Recommended fix approach

4. **Questions Awaiting Decisions**
   - List 3-5 specific questions
   - Provide defaults for each
   - Make clear which will proceed without answer

5. **Code & Documentation**
   - All code committed to main branch
   - README, architecture docs, deployment guides
   - Dockerfiles, infrastructure-as-code
   - Complete git history for context

## Benefits of This Pattern

**For the user (Thomas):**
- Clear what agents should focus on
- Obvious whether work is complete
- Easy to make decisions (defaults provided)
- Can sleep while agents audit

**For agents:**
- Structured starting point (not "audit the whole thing")
- Clear success criteria (PASS/FAIL per section)
- Specific commands to run
- Known problem areas to investigate

**For continuity:**
- Audit can pause/resume (checklist preserves context)
- Multiple agents don't duplicate work (sections assigned to specialists)
- Issues documented with context (easier to fix)

## Template: Audit Checklist Header

```markdown
# [Project] Project - Agent Audit Checklist

**Project:** [PROJECT_NAME] (Brief description)  
**Repository:** [GitHub URL]  
**Current Status:** [LIVE/READY/BLOCKED]  
**Assignees:** Coder, DevOps, Security, Designer, Researcher  

---

## 🎯 MISSION BREAKDOWN

The project was transformed from [old] to [new]. Your job is to:
1. Verify deployment status and health
2. Check code structure and architecture
3. Test API routes and functionality
4. Audit security and data isolation
5. Review design and UX
6. Validate documentation

---

## 📋 AUDIT CHECKLIST

### SECTION A: [SPECIALTY] (Assignee: [AGENT])
- [ ] Task 1
- [ ] Task 2

**Expected Result:** [Clear pass/fail criteria]

---

## 🔍 KNOWN ISSUES TO INVESTIGATE

### Issue 1: [TITLE] (PRIORITY: [CRITICAL/HIGH/MEDIUM/LOW])
**Status:** [OPEN/INVESTIGATING]
**Root Cause:** [Known or "Unknown - investigate"]
**Fix Priority:** [Blocking/Important/Nice-to-have]

---

## 📊 WORK ITEMS TO CREATE

Based on findings, create Kanban cards:
1. [Coder] [Task Title] - [Estimate]
2. [DevOps] [Task Title] - [Estimate]

---

## ✅ VERIFICATION CHECKLIST

- [ ] All sections audited
- [ ] Issues documented with root causes
- [ ] Work items created with estimates
- [ ] Questions for user prepared
```

## Real-World Example: AuthList Multi-Tenant

**Session:** Overnight multi-tenant transformation of Discord bot + dashboard. 8+ hours work, 15+ commits, 2 new services.

**Audit Checklist Sections Created:**
- Section A: Deployment Status (DevOps)
- Section B: Database Schema (DevOps + Researcher)
- Section C: API Routing (Coder) ← Known to have 404 issues
- Section D: Code Structure (Coder + Researcher)
- Section E: Dashboard Application (Coder + Designer)
- Section F: Deployment Infrastructure (DevOps)
- Section G: Security Audit (Security)
- Section H: Documentation (Researcher)
- Section I: Git History (Researcher)

**Known Issues Documented:**
1. /api/* routes returning 404 (investigation path provided)
2. Railway build cache not picking up new code
3. Dashboard not yet deployed (expected, needs manual setup)

**Questions for User:**
1. Deploy dashboard now? (default: yes)
2. Debug routes before/after dashboard? (default: after)
3. Run database migrations immediately? (default: yes)
4. What auth method for API? (default: simple API key)

**Work Items Created:**
- [CODER] Debug /api/* routes (HIGH, 2-3h)
- [DEVOPS] Deploy dashboard (HIGH, 15min)
- [DEVOPS] Run migrations (HIGH, 5min)
- [SECURITY] Audit isolation (HIGH, 1h)
- [CODER] Implement auth (MEDIUM, 2h)
- [DESIGNER] Test UI (MEDIUM, 1h)

**Result:** Agents got a clear starting point. All 9 sections had checklists. Issues were contextualized. User could sleep, agents could work in parallel.

## When to Use This Pattern

- Multi-service projects (bot + dashboard, etc.)
- Overnight/async work requiring handoff to multiple agents
- Complex codebases where audit scope is unclear
- Projects with known issues that should be documented
- When you want clear success criteria before agents start

## When NOT to Use

- Single-service, straightforward audit (simpler checklist is fine)
- Simple bug fixes (agents don't need a checklist)
- User is present and interactive (ask questions instead)

---
name: comprehensive-app-audit
title: Comprehensive Application Audit & Modernization
description: Orchestrate evidence-based multi-agent app audits and modernization.
trigger: "Use when auditing an app for bugs, cohesion, security, design, operations, competition, or modernization. Dispatch specialist audits, consolidate evidence, and execute fixes only when authorized."
---

# Comprehensive Application Audit & Modernization

## Overview

When a user asks to go over a whole app and identify flaws and improvements, orchestrate a **6-agent parallel audit** (security, coder, designer, devops, researcher, planner) and produce one consolidated risk/opportunity prioritization. Execute fixes only when the request explicitly authorizes implementation; a request to "come back with a conclusion" is audit-only.

The goal is to determine, with evidence, whether the product behaves and feels like one coherent production application. Treat implementation as a separate phase whose authorization comes from the user's request.

## Workflow

### Phase 0: Lock scope and authorization
Classify the request before dispatch:
- **Audit only:** inspect, render, test, and recommend; do not change code or deploy.
- **Audit then propose:** deliver the consolidated roadmap and wait for a build decision.
- **Audit and modernize:** proceed into execution after findings are consolidated.

Put the selected mode in every child brief. Never let the skill's modernization default override an explicit request for a report or conclusion.

### Phase 1: Parallel Audit (Immediate)
Dispatch six independent Kanban tasks simultaneously:
- **Security:** auth/session boundaries, authorization and ownership scoping, privacy, secrets, data integrity, and cache exposure
- **Coder:** reproducible bugs, route/state integration, architecture, dependencies, performance, and PWA behavior
- **Designer:** visual system, responsive render matrix, WCAG, navigation, feedback, and cross-page continuity
- **DevOps:** build/release, observability, backups, migrations, service-worker rollout, production drift, and performance budgets
- **Researcher:** current competitors, standards, benchmarks, and only product-fit feature gaps
- **Planner:** route inventory, end-to-end journeys, mental models, duplicate concepts, dead ends, and sequencing

Require each audit to:
1. Inspect the same exact revision and record it.
2. Cover all named routes and key states, including loading, empty, error, authenticated, and responsive states where applicable.
3. Separate confirmed defects, strong recommendations, and hypotheses.
4. Give every finding severity, evidence or reproduction, user impact, concrete remedy, and affected route/component.
5. Record what works and should not be disturbed.
6. Save a durable markdown artifact; visual audits also save screenshots or a render matrix.
7. Complete with a structured handoff containing artifact paths and checks actually run, rather than relying on transient comments.

Create one synthesis task parented on all six audits. The dependency fan-in prevents a partial report from being mistaken for the final answer. The synthesizer reads every handoff and artifact, de-duplicates findings, reconciles conflicts, cites source task IDs, and produces one attached final report.

Own the dependency graph centrally. Tell audit workers not to create extra audit or synthesis cards unless a genuinely missing evidence lane cannot be completed in their assigned task. If a worker must delegate, require exactly one executable child, make that child a parent of the delegating audit, and link only the completed audit—not both audit and helper—into final synthesis. Before adding any new child to synthesis, inspect existing cards for overlapping scope; duplicate journey or verification lanes create unnecessary fan-out and can strand synthesis behind redundant dependencies.

When a helper and verifier intentionally share a read-only workspace, declare the expected artifact filename and provenance in the verifier brief before dispatch. Treat that named untracked report as input—not repository contamination—but still forbid staging, committing, deleting, or modifying product files. This prevents clean-tree preflight from blocking on the very artifact the verifier must inspect.

### Phase 2: Execution (Only When Authorized)
**Critical pattern:** User says "keep going until everything is fixed" → do NOT wait for feedback. Execute all fixes sequentially, commit + push, report once.

1. Create focused execution tasks (Coder, Designer per priority level)
2. Power through fixes:
   - Branch per priority (e.g., `app/urgent-high-fixes`, `app/medium-low-fixes`)
   - Commit each fix individually with clear messages
   - Build verification after each batch
   - Push branches (auto-PR on GitHub)
3. When an agent crashes or exits early, call `kanban_show(task_id)` before retrying. If a valid commit already exists, preserve that workspace and create one bounded finalization task there instead of rebuilding. After two spawn failures on the same profile, reroute the review to another qualified profile and link the replacement directly into the integration gate.
4. Read back every created card before dispatch. If its durable body contains literal truncation, add one concise `FULL ACCEPTANCE` comment with scope, tests, exact-SHA handoff, and deployment boundary before a worker claims it.
5. Deliver: push only approved branches, create PRs when authorized, and summarize what is integrated, reviewed, staged, deployed, or still owner-blocked.

### Phase 3: Documentation (Parallel)
While fixes land, create supporting docs:
- Deployment runbook (RAILWAY.md, etc.) — env vars, volumes, troubleshooting
- Monitoring setup guide — uptime, error tracking, health checks
- CI/CD pipeline — GitHub Actions
- Performance baseline — Lighthouse, Core Web Vitals
- Credential rotation procedures

These become a second PR (non-blocking).

## Key Pitfalls

### Pitfall 1: Waiting for user feedback on each fix
Don't report after each fix and wait for approval. Stack all fixes, execute sequentially, report once at end. Signal "keep going" = do NOT interrupt.

### Pitfall 2: Crash loops and preserved work
Inspect the card, exact commit, workspace, and prior attempts before restarting. Reuse a valid preserved commit through one bounded finalization task; after two spawn failures on the same profile, reroute to a qualified independent profile because repeated blind retries consume slots without adding evidence. Link the replacement into the existing integration gate, and retire the failed gate only after the replacement returns a real verdict.

### Pitfall 3: Leaked secrets in git (CRITICAL)
Cause: `.db-shm`, `.db-wal`, `.env` with passwords/keys.  
Fix: `git filter-repo` to purge history. This is owner action (requires `git push --force`).  
Check: Search for `sk-proj-` (OpenAI), `password`, `secret`, database files.

### Pitfall 4: Large refactoring mid-audit
Don't refactor 2000+ LOC components. Note size issue, add to LOW priority roadmap, focus on surgical fixes.

### Pitfall 5: Over-commit on LOW priority
Don't implement test suite + PWA + micronutrient tracking same sprint. Document in roadmap (6+ months), ship documentation, let user prioritize.

### Pitfall 6: Data isolation bugs masquerade as deployment issues
When behavior differs across tenants, verify tenant-scoped primary keys and query filters before blaming deployment; schema or ownership errors can present as environment drift. Confirm the behavior in multiple tenants, inspect compound keys and all read/write predicates, then assign schema migration plus isolation tests to the coder. See `references/multi-tenant-data-isolation-pitfalls.md` in the railway-cli skill for depth.

### Pitfall 7: Six reports without one product conclusion
Always gate a single synthesis task on every specialist audit; otherwise the user receives fragmented status updates instead of the strict, de-duplicated product conclusion they requested.

### Pitfall 8: Unverified design opinions
Require actual viewport/state renders and precise observations for design findings; repository-only style review misses responsive geometry, continuity, and state-specific defects.

### Pitfall 9: Feature-bloat recommendations
Rank additions by whether they reinforce the product's core daily loop. Mark weak-fit ideas as defer or reject, because a long wishlist can worsen the fragmentation the audit is meant to solve.

### Pitfall 10: Recursive audit fan-out
Do not let specialist auditors independently create overlapping replacement, executor, and verification cards. Centralize graph ownership, inspect existing children before linking a new dependency, and prefer one audit artifact plus one bounded verification pass; redundant parent/child chains delay the final report without adding evidence.

### Pitfall 11: Expected audit artifacts fail clean-tree preflight
Name shared-workspace report artifacts in the verifier brief and identify the producing task; otherwise a correct untracked audit report looks like unrelated contamination and blocks verification. Allow inspection of that exact artifact only, while preserving the no-stage/no-commit/no-product-edit boundary.

### Pitfall 12: Temporary pauses become task failures
Treat a user pause as orchestration state, not failed work. Block only currently running or ready canonical cards once; leave parent-gated `todo` cards untouched. Repeated `needs_input` blocks can trigger loop escalation to triage, which can auto-decompose a valid project-linked task into workspace-less children. Record one durable pause/resume instruction on the integration gate, then on resume list running, ready, blocked, and triage states; unblock only canonical cards and replace any triaged canonical card with one project-linked implementation plus one independent review.

### Pitfall 13: Duplicate review gates strand integration
Use exactly one implementation → independent review edge per lane. If a worker creates a same-card review or duplicate verifier despite a pre-created child, choose one authoritative review, link it directly into integration, and close the obsolete gate only after the authoritative verdict is evidenced. Never report a lane as cleared while an obsolete parent still blocks the integration card.

### Pitfall 14: Long task bodies silently lose acceptance criteria
Immediately read back every newly created card. If the durable body contains literal truncation, add a concise full-contract comment before dispatch; otherwise workers act on an incomplete scope and reviewers cannot enforce the intended tests or deployment boundary.

### Pitfall 15: Integrated security code is present but unreachable
At the release-candidate gate, trace each approved invariant from the public route or scheduler into the active service implementation and test it through that active boundary. Do not accept tests that exercise only a legacy helper: conflict resolution can preserve secure code and its unit tests while routing production around both.

### Pitfall 16: Backup files are published before verification
Stage, verify, and checksum backup artifacts before final local or offsite publication; on every copy or verification failure, remove all temporary and final artifacts. Test low-size limits and injected publication failures through the active backup service, because listing endpoints often treat every final-extension file as valid.

### Pitfall 17: Local green checks lack exact-head release evidence
For a release candidate, require the corrected SHA to exist on the remote and verify CI by exact commit, not branch name or an ancestor run. Keep deployment gated until the exact-head jobs required by policy are green.

## Audit Output Format

The consolidated report should include: executive conclusion; strengths to preserve; confirmed bugs by severity; design/cohesion problems; flow/architecture problems; security/privacy/reliability findings; additions; removals/merges; and a single Now/Next/Later roadmap with impact, effort, dependencies, and owner. Keep confirmed findings separate from recommendations and speculation.

```
# Priority Matrix

## URGENT (Do Today)
- #1: Leaked secrets in git (owner: git filter-repo)
- #2: Rotate credentials (owner: Railway)
- #3: Verify persistent volume (owner: Railway)

## HIGH (This Week)
- #4: Auth race condition (coder: 1h, gate token)
- #5: WCAG contrast (designer/coder: 30min)
- #6: Error tracking (coder: 1h, Sentry)

## MEDIUM (This Month)
- #N: Empty states (designer: 2h)
- #M: ESLint + Prettier (coder: 2h)

## LOW (Roadmap — 6+ months)
- Barcode scanning
- Test suite
- Offline/PWA
```

For **multi-service projects** requiring structured handoff to agents, see `references/multi-agent-audit-checklist-pattern.md` — captures the checklist-driven audit approach with known issues, investigation paths, and morning handoff structure.

## Completion Checklists

### Audit-only
- [ ] All specialist audits completed against the same revision
- [ ] Every report records evidence, checks run, and limitations
- [ ] Priority matrix de-duplicated and consolidated
- [ ] Confirmed defects separated from recommendations and speculation
- [ ] One final report attached and delivered
- [ ] No code, configuration, deployment, or production data changed

### Authorized execution
- [ ] Owner-only blockers identified (secrets, credentials, destructive history changes)
- [ ] Focused implementation tasks created from the approved priority set
- [ ] URGENT and HIGH fixes verified in coherent batches
- [ ] Build and relevant tests run after each batch
- [ ] Branches/PRs published only under the granted publication scope
- [ ] Deployment-ready documentation consolidated
- [ ] Exact deployed revision and live behavior verified before claiming release

## Expected Artifacts

### PR #1: Code Fixes
- Branch: `<app>/urgent-high-priority-fixes`
- Commits: One per fix with clear messages
- Build: ✅ Passing
- Deliverable: Production-ready code

### PR #2: Docs + CI/CD (Non-blocking)
- Branch: `<app>/medium-low-priority-fixes`
- Contents: Deployment runbook, monitoring, CI/CD, Lighthouse scripts

### Summary Docs
- `<app>_Comprehensive_Audit_Final_Report.md`
- `<app>_DEPLOYMENT_READY.md`
- `<app>_Priority_List.md`

## Common Patterns by App Type

**Web App (Svelte/Vue/React + Node):**  
Security: Auth, CSRF, XSS, SQLi, SSRF  
Code: Linting, bundle size, component complexity, deps  
Design: WCAG, responsive, empty states  
DevOps: Docker, volumes, env vars, backups  

**Mobile (Capacitor/React Native):**  
Security: Auth + cert pinning, local encryption  
Code: Platform quirks, WebView CORS  
Design: Mobile-first, gestures, battery  
DevOps: Signing, store, OTA  

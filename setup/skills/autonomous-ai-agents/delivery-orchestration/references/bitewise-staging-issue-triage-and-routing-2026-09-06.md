# BiteWise Staging: Issue Triage and Task Routing (Sept 6, 2026)

## Session Context

User reported two distinct problems in BiteWise staging:
1. **PWA version has broken menus** — Settings and top-right navigation inaccessible in PWA, but work fine in web version
2. **Phone layout stability** — Layout shifts and is not consistent across screen sizes

The coordinator's job: **Identify the issue class, route immediately to the right specialist, do NOT attempt to fix it yourself.**

## Issue Identification Pattern

### Issue Class: PWA-Specific Bugs

**Symptoms:**
- Feature works in web version but fails in PWA
- Likely root causes: service worker caching, asset loading, navigation routing, PWA manifest configuration
- **Specialist route:** coder (client-side debugging + PWA-specific fixes)

**Task routing (correct):**
```
Title: Fix PWA menu accessibility: Settings and top-right navigation broken in staging
Assignee: coder
Body:
  - Settings menu inaccessible in PWA (works in web)
  - Top-right menu inaccessible in PWA (works in web)
  - Context: likely service worker / asset loading / manifest issue
  - Acceptance: both menus work identically to web version
  - Verify on actual PWA install (add to home screen on mobile)
```

**Why coder, not devops or designer:**
- Not an infrastructure issue (devops handles deployment, env vars, database)
- Not a visual design issue (designer handles layout, mockups, CSS styling)
- IS a client-side runtime bug in the PWA build/service worker (coder handles this)

### Issue Class: Responsive Layout Problems

**Symptoms:**
- Layout shifts / changes when it should be stable
- Different on different screen sizes
- Likely root causes: CSS media queries, flex/grid wrapping, viewport config, container widths
- **Specialist route:** coder (CSS debugging + responsive design fixes)

**Task routing (correct):**
```
Title: Fix phone layout stability: ensure exact same layout on all screen sizes
Assignee: coder
Body:
  - Layout must stay identical on all phone sizes (iPhone, Android, etc.)
  - No layout shift on orientation change
  - Check: CSS media queries, flex/grid, padding/margin, container widths, viewport meta tag
  - Acceptance: pixel-perfect consistency verified on staging
```

**Why coder, not designer:**
- Not a visual redesign request (that goes to designer for mockups)
- IS a responsive CSS bug / layout logic problem (coder handles this)
- Designer role: "create beautiful mockups" → Coder role: "make it work on all devices"

## Critical Anti-Pattern: DO NOT Start Design Work, Then Route

❌ **Wrong (what NOT to do):**
```
"I'll start researching competitor food pages and building 5 mockup concepts..."
[30 minutes of work]
"Oh wait, the user said 'hand it off to designer'. Let me create a designer task."
```

**Why this is wrong:**
- You did 30 min of duplicative work the designer should do
- You may have different design direction / style than what the user wants
- Designer task will likely need to start from scratch
- Wastes token budget and coordinator time

✅ **Right (what to do):**
```
User: "Can you create 5 new versions of the food page?"
Me: "I should check: is this a design task?"
Me: "User says 'hand it off to designer'" → [immediately create designer task]
No duplicative work; designer gets the full scope and control.
```

## Routing Decision Tree

```
User reports a problem or asks for work.
├─ Is it a visual design / mockup / prototype?
│  └─ YES → Route to designer
│     • "Create 5 design concepts"
│     • "Redesign the homepage look"
│     • "Create interactive mockups for user feedback"
│
├─ Is it a client-side bug (web/PWA) or responsive CSS issue?
│  └─ YES → Route to coder
│     • "PWA menus are broken"
│     • "Mobile layout shifts"
│     • "Button not clickable in mobile view"
│
├─ Is it deployment, infrastructure, environment, database, credentials?
│  └─ YES → Route to devops
│     • "Deploy to staging"
│     • "Set up environment variable"
│     • "Check database schema"
│
├─ Is it security, policy, compliance, ethical review?
│  └─ YES → Route to security
│     • "Audit this code for vulnerabilities"
│     • "Check OAuth flow for security issues"
│
└─ Uncertain or coordination-heavy?
   └─ Ask explicitly or check the user's prior preference
```

## BiteWise Staging Issue Triage Checklist

### For Each Reported Issue:

1. **Classify it:**
   - [ ] PWA-specific? (coder)
   - [ ] Responsive/layout? (coder)
   - [ ] Deployment/env? (devops)
   - [ ] Visual design? (designer)
   - [ ] Something else?

2. **Create focused task(s):**
   - [ ] One task per issue class (don't combine PWA + layout into one task)
   - [ ] Clear acceptance criteria (how you know it's fixed)
   - [ ] Reproduction context (staging URL, browser/device, steps)

3. **Route immediately:**
   - [ ] Do NOT attempt to debug/fix yourself first
   - [ ] Do NOT spend time investigating root causes before routing
   - [ ] Specialist profile is better at this; let them own it

4. **Track and follow up:**
   - [ ] Subscribe to the task so you see completion
   - [ ] Consolidate results back to the user in one summary

## Related Skills

- **action-first-execution** — When user says "hand it off to designer," route immediately; do not start the work yourself
- **delivery-orchestration** — General specialist routing and task creation patterns
- **bitewise-staging-deployment** — Deployment/infrastructure context for BiteWise staging

## Golden Rule

**When a user tells you to route work ("hand it off to designer"), route it immediately. Do not start doing the work yourself.** This preserves specialist ownership and respects the user's explicit instruction about division of labor.

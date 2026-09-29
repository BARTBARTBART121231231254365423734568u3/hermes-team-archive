# Case Study: BiteWise Redesign + Parallel Audit (Sept 3, 2026)

## Pattern: Design-First with Specialist Review

When user requests a full product redesign + professional audit, use this dependency structure:

### Task Creation Order

1. **Designer** task (no parents) — create the full mockup/prototype asap
   - Does NOT depend on audits — works from current state + UX best practices
   - Deliverable: clickable HTML prototype showing all key pages
   - Timeline: fast turnaround needed (user wants to see preview early)

2. **Other audits** (Planner, Coder, Security) in parallel
   - Can reference designer output once available
   - Each should note dependencies if they need to see the design to finalize recommendations
   - Planner specifically benefits from seeing design before finalizing feature prioritization

### Execution in BiteWise Case

**Created 4 cards simultaneously:**
- Designer: "Create full UI/UX redesign prototype" (t_9ec16d40)
- Planner: "UX/Feature audit" (t_deba106d) — completed first with caveat: "no live access to running app; designer verification needed"
- Coder: "Code quality audit" (t_e840c158) — still working
- Security: "Security & dependency audit" (t_397ba765) — still working

**Key insight:** Planner explicitly flagged it built the audit from codebase scope + domain benchmarks, not by clicking through the live app. Recommended that coder/designer verify current-state details when picking up child cards. This is GOOD — it's honest about limitations and sets up the next worker for success.

### Planner's Smart Fallback

When unable to verify current state interactively, the planner:
1. Built audit from known scope + industry benchmarks
2. Flagged assumptions upfront ("I didn't have live access")
3. Spun off 3 child kanban cards for Tier 1 items so they're actionable without re-asking
4. Recommended coder/designer verify exact current state when executing

This is the **right pattern for knowledge-limited audits**.

### Synthesizing Across Audits

When all audits complete, you'll consolidate into one prioritized list:

```
Tier 1 (Quick Wins — do this week):
  - Recent/Frequent foods [Planner HIGH]
  - Error handling/empty states [Planner HIGH + Designer]
  - Mobile responsiveness [Planner HIGH + Designer]
  - Search/filter [Planner MEDIUM + Coder]
  - [Security/Coder findings TBD]

Tier 2 (Mid-term):
  - Onboarding flow [Planner MEDIUM + Designer]
  - Stats/trends charts [Planner MEDIUM + Coder]
  - Fitbit reliability [Planner MEDIUM + Security/Coder]
  - [TBD]

Tier 3 (Strategic):
  - Barcode scanning [Planner HIGH-LEVERAGE]
  - Gamification [Planner MEDIUM]
```

**Cross-audit deduplication:** Designer may flag the same mobile responsiveness gap as Planner. Cite both sources but list it once, ranked by severity.

### Next Steps (After Designer Preview)

1. User sees designer prototype (live preview URL)
2. User gives thumbs-up or requests changes
3. Once design is locked, coder + designer execute Tier 1 items
4. Security + coder handle any CRITICAL findings
5. Execute in phases (Tier 1 this week, Tier 2 next week, Tier 3 backlog)

---

## Key Lessons Learned

1. **Audits without live access should flag it.** Planner did this well — presented as "built from scope + benchmarks, verify by [method]" rather than "I checked and found X."

2. **Designer output becomes audit input.** Planner's findings are "suspect the UI is cluttered" until designer shows a clean version. Designer output validates/refutes planner's assumptions.

3. **Spin off child cards immediately.** Planner created 3 actionable child cards for Tier 1 items. This means coder/designer pick them up without re-reading the main audit.

4. **Consolidation is your job, not the auditors'.** Each auditor gives their findings. You synthesize into one list, deduplicate, and prioritize across dimensions (security, ux, code quality).

5. **Live preview URL matters.** Designer should publish the mockup to a clickable preview link (e.g., via `create_preview.py`). User should be able to see and interact with it same-day.

---

## Reference: Audit Handoff Format

Each auditor should return findings in this structure:

```markdown
## Finding: <Title>

**Priority:** CRITICAL | HIGH | MEDIUM | LOW

**What:** <1-2 sentences describing the issue>

**Why it matters:** <Impact: retention, security, professionalism, performance, etc.>

**Effort:** Small | Medium | Large | Unknown

**Who should fix:** <Designer | Coder | Security | Owner | TBD>

**Evidence:** <Link to file, quote from code, screenshot, or citation of domain best practice>

---
```

When consolidated, group by priority and source (Designer + Planner on same row = cross-audit validation).

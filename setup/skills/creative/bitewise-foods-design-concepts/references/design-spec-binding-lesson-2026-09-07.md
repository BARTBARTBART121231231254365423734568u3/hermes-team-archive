# Design Spec Binding Lesson — Session 2026-09-07

## Context

When a user approves an interactive mockup (preview URL), the designer often proceeds directly to implementation. However, empty-state UIs can hide working layouts, and unclear mobile behavior specs can cause implementation to diverge from the approved mockup.

## Lesson: Approved Mockups Are Binding Visual Specs

Treat a user-approved preview URL as a **binding specification for implementation**, not loose inspiration.

### What This Means

1. **Capture the full visual hierarchy** — Not just the top of the page, but the complete Foods page layout including the lower sections (Library, Recent foods, Quick-add cards, etc.).
   - Empty-state mockups often show a "collapsed" layout because there's no data to render
   - Implementation may correctly show all regions, but if empty staging data exists, they collapse and the layout appears broken
   - **Solution:** Seed staging with representative test data BEFORE final QA

2. **Record explicit mobile behavior** — Don't infer from the desktop mockup.
   - If columns must stay side-by-side on a 390px phone (not stack), encode that in the acceptance criteria
   - If text should reflow differently on mobile, show that in the mockup (not just assert it verbally)
   - **Solution:** Build the mockup with responsive viewport tests; note which behaviors are mandatory vs. flexible

3. **Name the approved variant** — When macro-column variants are presented (Ring+bars, Ledger table, Fuel gauge), the user picks one. Use that exact name in implementation tasks.
   - Example: "Implement Ledger concept Foods page with **Variant 2: Ledger Table** macro column"
   - Don't ask the coder to "pick a variant" — that decision is made

4. **Verify pixel-faithful reproduction** — After implementation, compare the live staging app against the approved preview.
   - Typography: fonts, sizes, weights, line heights
   - Spacing: margins, padding, gaps between sections
   - Color: exact hex values (#1fbf82, not a close-enough mint green)
   - Responsive behavior: Does mobile layout stay side-by-side if required? Or does it deliberately stack?
   - Empty vs. populated state: Seed data BEFORE comparing

## Session 2026-09-07 Case Study

**What happened:**
1. Designer built Ledger concept with 4 screens (Today, Log Food, Food Detail, Trends)
2. User approved the preview
3. Coder implemented the approved layout on staging
4. Staging appeared to show only a bare top section (command center) — rest of page looked "missing"
5. User questioned if implementation matched the preview

**Root cause:**
- The preview was built with representative fake data (50 recent foods, 10 frequent foods, etc.)
- Staging had NO food data (fresh setup, user hadn't logged anything)
- With empty state, the Foods Library, Recent cards, and Quick-add sections collapsed or didn't render
- The actual layout was correct; it was just invisible without data

**Fix:**
- Seed staging with test data (admin account creation + 20 sample foods + 5 logged meals)
- Re-render the Foods page
- Compare against approved preview — layout now matches

## Implications for Future Work

### For Designers
- Build mockups with realistic data density (don't show 1 food when 50 is realistic)
- Explicitly show empty state separately if it exists (labeled "Empty State", "No Foods Yet", etc.)
- Test mockup at mobile viewport; note responsive behavior changes

### For Coders
- Before handing off to QA, create representative test data on staging
- Compare live implementation against approved preview using the same data state
- Document what the "full" layout looks like vs. what empty state looks like

### For Coordinators
- Include "seed staging with test data" as an explicit QA gate step
- Require side-by-side visual comparison (preview vs. staging) before marking implementation done
- If discrepancy appears, verify empty-state data first before asking coder to fix

## Template: Implementation Acceptance Criteria

When creating an implementation task from an approved mockup:

```markdown
## Approved Reference
Preview URL: https://hermes-agent-railway..../preview/06a944a1447bd7a8/
Approved concept: Ledger (Monitor Surface)
Approved macro variant: Variant 2 — Ledger Table

## Visual Specification
- Top: Command center (macro column with variant 2, nudge)
- Middle: Food Library with Browse-all entry point
- Lower: Recent & Frequent cards, Quick-add options

## Mobile Behavior (Mandatory)
- Columns must remain side-by-side on 390px viewport (no vertical stacking)
- Macro column height: 229px (ledger table variant)
- Text reflow as needed; layout structure unchanged

## Test Data
Before final verification:
1. Create admin account via SETUP_TOKEN
2. Add 20 sample foods to database
3. Log 5 meals spanning 3 days
4. Render Foods page at desktop and mobile viewport
5. Compare against preview screenshot using approved variant

## Pixel-Faithful Checklist
- [ ] Fonts: DM Sans (not Inter, not system)
- [ ] Macro column: exactly as variant 2 preview shows
- [ ] Colors: #1fbf82, #4a9eff, #f5a623 (exact hex, not approximations)
- [ ] Spacing: margins/padding match preview
- [ ] Mobile: no stacking, remains two-column layout
- [ ] Full layout visible (not collapsed empty state)
```

## See Also
- `bitewise-staging-deployment` skill reference `foods-page-staging-deployment-2026-09-06.md` — Step-by-step test data seeding workflow

# Designer Iteration Efficiency: When to Pivot to Full Redesign (2026-09-06)

## Problem Pattern

Designer spends 3+ cycles fixing a broken layout across multiple tasks:
1. Task 1: "Fix two-column layout" — developer claims fixed
2. Task 2: "Verify & fix" — developer verifies locally, claims deployed
3. Task 3: "Debug CSS max-width" — root cause found (880px cap), fixed
4. Task 4: "Verify production renders" — cache clear suggested, still broken visually

**Token cost:** 15+ minutes, ~50% of session budget
**Outcome:** Still wrong; no progress toward user approval

## Decision Point: When to Bail

After 3 fix/verification cycles on the same broken layout:
- Code inspection shows layout CSS exists
- Multiple "fixes" deployed and verified via logs
- Production still shows wrong visual result
- Root causes found (CSS cap, empty state masking, etc.)
- BUT user continues to see broken design

**→ STOP iterating on the broken layout. Pivot to full redesign instead.**

## Why Full Redesign Is More Efficient

### Iteration Loop (Wasteful)
1. Designer investigates why layout looks wrong
2. Finds a root cause (CSS constraint, empty state, etc.)
3. Creates a "fix" commit
4. Devops deploys it
5. User reports: still wrong
6. Repeat cycle

**Cost per cycle:** 10-15 mins + 1 redeploy wait

### Full Redesign Loop (Efficient)
1. Designer researches industry standards (MyFitnessPal, Cronometer, etc.)
2. Creates 3 completely different design concepts
3. Generates mockups/prototypes with preview URLs
4. User picks one
5. Designer implements chosen design once

**Cost total:** ~30-45 mins, multiple options, explicit user approval before code

## Key Differences

| Iteration | Full Redesign |
|-----------|---------------|
| Chasing unknown bugs | Research + design from scratch |
| One approach tried repeatedly | 3 distinct approaches shown |
| Deploy-to-verify loop | Mockup-to-approve loop |
| User sees "still broken" | User picks winning design explicitly |
| 4+ cycles possible | 1 implementation after approval |
| High token burn | Bounded token spend |

## When to Trigger the Pivot

**Trigger:** After 3 failed fix cycles (developer has tried 3+ separate fixes), if the visual result still doesn't match reference/requirements:

```python
if (num_fix_cycles >= 3) and (user_reports_visual_mismatch):
    # Create full redesign task instead of fix #4
    kanban_create(
        title="REDESIGN: <page> - 3 complete different versions",
        assignee="designer",
        body="Research industry best practices. Create 3 distinct design options (Minimalist, Search-first, Tab-based). Mockups + previews. User picks one."
    )
    # Mark the prior fix task as superseded
    kanban_comment(
        task_id="<prior_fix_task>",
        body="SUPERSEDED: Pivoting to full redesign instead of iterating on broken approach. See t_<new_task>."
    )
```

## Red Flags That Signal the Pivot

- Designer says "I found the bug" and creates a 4th fix task
- Devops reports "deployed successfully" but user sees no change
- Root causes keep being found (CSS constraint, empty state, network issue, cache, etc.) but visuals don't change
- Designer is exhausting token budget on investigation rather than alternative designs
- User feedback is "this is broken" not "almost there"

## Real-World Example (This Session)

**Timeline:**
- t_3af5d134: Designer claims two-column layout fixed in CSS/HTML → NOT visible in production
- t_5cca3134: Designer refines layout, "verified independently" → still not showing
- t_91500020: Designer finds root cause (880px max-width cap) → fixes it → still not visible
- t_2f073233: Coder manually inspects → confirms layout CSS deployed correctly → but "no visible change"

**At this point:** Stop. The iteration is not converging. Pivot immediately.

**New approach:**
- t_276ce644: Designer creates 3 completely different Foods page design versions (Minimalist, Search-first, Tab-based) with "Today's Nudge" cards and industry research
- User will review all 3 and pick one
- Designer implements chosen design cleanly

**Result:** Better UX, explicit user approval, no more debugging cycles

## Implementation Checklist

- [ ] After 3 failed fix cycles, create a full redesign task (not a 4th fix)
- [ ] Brief the designer with industry research requirements + user preferences (e.g., "include AI nudge cards like MyFitnessPal," "matching user-provided reference image patterns")
- [ ] Capture user-stated preferences EXPLICITLY: look back through conversation for phrases like "what i like is..." and embed those in the design brief
- [ ] Require 3 distinct design concepts with mockups/previews
- [ ] Do NOT ask designer to "also try another approach to the broken layout" — make it an either/or choice
- [ ] Mark the prior iteration task superseded with a clear comment
- [ ] Report to user: "Switching gears to 3 fresh designs instead of chasing the broken layout further"
- [ ] After user picks a design, implement that one cleanly (no more backtracking)

## Why This Worked

The moment Thomas was told "let the designer create 3 complete different versions," the energy shifted:
- No more debugging
- No more "still looks broken" user reports
- Clear choice for user (Minimalist vs Search-first vs Tab-based)
- Designer works toward something new, not fixing something old
- Token budget is bounded and productive

## Pitfalls to Avoid

- **Hybrid task:** Do NOT ask designer to "try another fix AND also create 3 new designs." Pick one approach.
- **Delayed pivot:** Do NOT wait until 5+ cycles. Pivot at cycle 3 or 4.
- **Vague brief:** Do NOT say "create 3 versions." Name the 3 distinct approaches (Minimalist, Search-first, Tab-based) so they are visibly different.
- **Missing user preferences:** Do NOT create the redesign brief without capturing what the user likes (e.g., "Today's Nudge" cards, AI insights). Embed preferences in the body so designer builds toward user satisfaction from the start.

## Session Reference

- Session: 2026-09-06 BiteWise Foods Page Redesign
- Old approach (iteration): t_3af5d134 → t_5cca3134 → t_91500020 → t_2f073233 (4 cycles, no progress)
- New approach (redesign): t_276ce644 (3 versions, clear options, user-driven choice)
- Outcome: Ready for user review + selection, no more "broken layout" guessing

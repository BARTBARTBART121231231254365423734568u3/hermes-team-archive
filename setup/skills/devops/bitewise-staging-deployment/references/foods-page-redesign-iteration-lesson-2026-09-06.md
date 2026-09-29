# Foods Page Redesign Iteration Lesson (2026-09-06)

## Context
BiteWise Foods page was supposedly redesigned (commits b027880, 107e086) with two-column layout (Recent & frequent left, Fast ways to log right). Multiple redesign/fix cycles were executed by designer and devops. Production deployed these commits but visually showed only single-column.

## Root Causes Found

### 1. Global CSS Max-Width Crushing Layout
**Problem:** `.page-shell { max-width: var(--content-max) }` (880px, from styles/base.css) clamped `.fd-main-railed` grid to single column.

**Solution:** Designer removed the 880px cap constraint from `.page-shell` to allow two-column grid to expand.

**Lesson:** When a redesigned page looks "wrong" after supposed fixes, inspect parent/ancestor CSS for width constraints. Grid layouts can be perfectly coded but crushed by outer container limits.

### 2. Empty State Data Masking Layout Issues
**Problem:** Production Foods page showed "No foods yet" empty state. Two-column layout CSS was correct but invisible because no data was rendered. User saw empty page and concluded design was broken.

**Solution:** Seed test foods data to admin account. Once populated, two-column layout rendered perfectly.

**Lesson:** Always populate staging/production with test data BEFORE user review when testing UI layouts. Empty-state designs can hide actual layout correctness. A layout that looks "broken" may just be showing the empty state, not a CSS/code issue.

## Designer Iteration Inefficiency

### Problem
Designer spent 15+ minutes and ~50% of user's token budget on fixing/refining the broken two-column layout across 4 cycles (t_3af5d134, t_5cca3134, t_91500020, t_2f073233).

### When to Bail on Iteration
If after 3 fix attempts the visual still doesn't match reference design, AND:
- Code inspection shows layout CSS exists
- Multiple "fixes" have been deployed and verified
- But production still shows wrong result

**→ STOP iterating. Switch to full redesign instead.**

Designer should have pivoted to: "Create 3 completely different design versions from scratch" (task t_276ce644) rather than trying to fix the broken one a 4th time.

**Why:** Iteration on a broken approach compounds token waste. A full redesign from scratch (studying industry practices, blending with BiteWise brand) is more efficient than chasing an unknown bug across multiple deploy cycles.

## What Worked: Full Redesign Approach

Once Thomas requested: "Let designer create 3 completely different versions, research MyFitnessPal, blend with our app's DNA, include AI nudge cards"

→ Designer pivoted immediately to full redesign (t_276ce644)

**This is more efficient because:**
1. No time chasing the broken layout root cause
2. Multiple design options for user to choose from
3. Incorporates industry best practices (MyFitnessPal, Cronometer) from the start
4. Aligns with user's preferences (AI nudge cards, existing design system consistency)
5. Either design wins, or at worst user picks one and designer implements it cleanly

## Operational Lesson for Next Session

When a UI redesign shows "broken" after 2+ fix attempts:

1. **Quick check:** Is it empty state? Seed data and re-verify.
2. **If still broken:** Inspect ancestor CSS for width/layout constraints.
3. **If still broken after 3 attempts:** Don't create a 4th fix task. Escalate to full redesign instead:
   - Research industry standards
   - Create 3 distinct new design options
   - Let user pick one
   - Implement cleanly

This saves token budget and usually produces better UX than iterating on a broken foundation.

## References

- Session 2026-09-06: BiteWise Foods page full-page redesign (3 versions)
- Global CSS constraints: Often hidden in `styles/base.css`, `App.svelte`, or shell-level layout files
- Design system reference: Diary, Statistics, Wellness, Goals pages (use for consistency)
- Industry reference: MyFitnessPal Foods search/browse, Cronometer food picker

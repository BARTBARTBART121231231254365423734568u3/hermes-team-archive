# Tier 2 Massive Feature Release Pattern

**Session:** 2026-09-04 (BiteWise redesign + Tier 2 features)

**Pattern:** When a user approves a multi-feature release roadmap (Tier 2: onboarding, stats/charts, reminders, data export, Fitbit audit), queue ALL tasks to the specialist at once with identical priority. Do not sequence manually or wait for user decisions between tasks. Let the specialist execute them as capacity allows.

## Context

- User has completed a massive redesign (6 tasks: mobile redesign, PWA, security hardening).
- User asks to "keep working on this and add everything then deploy."
- Requires Tier 2 (5 mid-term features) + Tier 3 (3 strategic features, some dependent on Tier 2).

## Execution

1. **Create all Tier 2 tasks upfront** (onboarding, stats/charts, reminders, data export, Fitbit audit):
   - All assigned to the same specialist (coder).
   - Same priority (4 = mid-tier, after critical bugs).
   - No dependencies between them (independent features).
   - Full scope in each task body.

2. **Do NOT wait for user confirmation between tasks.** Thomas explicitly said: "just follow the plan." Once approved, execute autonomously.

3. **Report completion compactly** (1 line per task, no task IDs unless asked):
   - ✅ Onboarding flow: goal setup, macro presets, dietary preferences
   - ✅ Stats/charts: weekly averages, error recovery
   - (queued) Daily reminders, Data export, Fitbit audit

4. **Queue Tier 3 immediately after Tier 2 is queued**, not after it completes. Dependencies go in task definitions (e.g., "barcode scanning may depend on food DB changes from Fitbit audit").

## Outcome

- All 5 Tier 2 tasks completed in sequence: onboarding → charts → data export (+ daily reminders redirected to coder via scheduler correction).
- No user intervention needed.
- Clear, terse status reports on each completion.
- Minimal friction.

## Pitfall Avoided

❌ **Mistake:** Creating tasks one at a time and asking "should I start the next one?" or checking in on each completion with full recaps.

✅ **Correct:** Queue all at once, let the specialist own sequencing and batching, report completions as one-liners, move to next phase.

## Key Signals

- User says "keep working," "all the way through," "massive update," "everything."
- Phased roadmap (Tier 1, 2, 3) is explicit in the conversation.
- Specialist is capable and proven (coder has shipped 5+ features already).
- No blocking dependencies within the same tier.

**Action:** Create all tasks, step back, report only outcomes.

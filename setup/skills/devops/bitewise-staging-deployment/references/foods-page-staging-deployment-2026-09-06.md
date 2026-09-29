# BiteWise Foods Page Staging Deployment (Session 2026-09-06)

## Context

After production deployment on 2026-09-05, full redesign went live but Foods page layout didn't match reference design. Investigation revealed:
- Production deployed successfully (commit 107e086, deployment e4f024af)
- Designer completed two-column layout + tabs (commit b027880 + follow-up 107e086)
- Layout worked in staging but didn't appear in production

## Root Cause

Empty-state UI was blocking visibility of the layout. When no foods exist in the user's database, the page shows "No foods yet" with action buttons, NOT the two-column layout with Recent & frequent / Fast ways to log.

The layout code was correct and deployed, but only renders when user has food items. This is NOT a deployment issue—it's expected UX behavior.

## Lesson: Layout Verification Requires Data

**When staging a page redesign, populate test data BEFORE user review.** Empty-state pages hide the actual layout.

**Verification checklist:**
1. Design complete on feature branch (reviewed, merged, pushed to staging)
2. Deploy to staging environment
3. **CRITICAL**: Seed test data to staging (foods, meals, diary entries)
4. User reviews with populated data (actual layout visible, not empty state)
5. Approve → promote to production
6. Seed production test data if needed for user to see the full layout

## Test Data Seeding Pattern

### For BiteWise Foods page:
```bash
# Devops task:
Title: Seed test foods data to production for layout verification
Assignee: devops
Body:
  Production Foods page layout is deployed but users see empty state.
  Seed 5-10 test food items so the two-column layout (Recent & frequent | Fast ways to log) is visible.
  
  Foods to add (via API or DB):
  - Free-range eggs (icon: 🥚, ~155 kcal, 12g protein)
  - Protein overnight oats (icon: 🥣, ~250 kcal, 15g protein)
  - Wholegrain turkey sandwich (icon: 🥪, ~400 kcal, 25g protein)
  - Whey protein vanilla shake (icon: 🥤, ~180 kcal, 25g protein)
  - Greek yogurt (icon: 🍯, ~100 kcal, 15g protein)
  
  Add to the admin account (or Thomas's production account if different).
  Verify https://bite-wise.up.railway.app/Foods now shows two-column layout with foods listed.
```

## Production vs. Staging: When to Seed

| Scenario | Action |
|----------|--------|
| Design complete, not yet deployed | Seed staging before user review |
| Design approved on staging, deploying to production | Seed production if users will test live (recommended) |
| Production live, user just viewing | Only seed if user asks to see the layout (don't assume they'll add foods manually) |
| Design iteration needed | Seed staging FIRST with reference data so all iterations use same test dataset |

## Why This Matters for BiteWise

BiteWise is a **multi-page app with empty states**. Every page (Diary, Foods, Statistics, etc.) has different layouts when empty vs. populated:

- **Diary empty:** Shows wizard, "No meals yet", action buttons
- **Diary populated:** Shows meal cards, date navigation, nutrition summary
- **Foods empty:** Shows "No foods yet", action buttons (what we hit)
- **Foods populated:** Shows two-column layout (Recent & frequent cards + Fast ways to log section)
- **Statistics empty:** Shows "No data yet", setup prompt
- **Statistics populated:** Shows charts, trends, goals

**Always populate before user review.** Empty-state review will fail to catch layout/styling issues.

## Session Timeline

1. 2026-09-06 ~10:27 — User reviews production Foods page, sees "No foods yet" empty state
2. Thought: Layout not deployed (wrong assumption)
3. Created devops task t_4db7ab96 to verify deployment
4. Devops confirmed deployment successful (commit 107e086, container online)
5. Still saw empty state → realized no test data
6. Created devops task t_7f4e01f4 to seed test foods
7. Devops blocked: "Need to know which account to seed"
8. Clarified: use admin account → unblocked → pending completion

**Fix:** Seed test data to admin account, refresh production URL, layout now visible ✅

## Automation Idea (Future)

For redesign reviews in the future, consider:
- Devops task creates a "test data seed" script (idempotent, can be re-run)
- Script lives in repo as `scripts/seed-bitewise-test-data.js` (or SQL dump)
- After staging deploy, auto-seed with one command: `node scripts/seed-bitewise-test-data.js --db staging --account admin`
- Same script used for staging reviews + production QA + new environment bootstrapping

This prevents the empty-state issue from blocking reviews again.

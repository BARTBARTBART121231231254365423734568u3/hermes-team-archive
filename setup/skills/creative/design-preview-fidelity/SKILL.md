---
name: design-preview-fidelity
description: Design preview verification via visual comparison.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, verification, preview, fidelity, screenshot-reproduction, qa]
    related_skills: [claude-design, design-md]
---

# Design Preview Fidelity: Screenshot-Faithful Reproduction

Use when the task is to build an interactive preview/prototype that matches supplied reference screenshots **exactly**, not interpret them.

This skill extends `claude-design` with rigorous verification for high-fidelity redesign handoffs where pixel accuracy, complete interactivity, and visual validation are non-negotiable.

## The Problem This Solves

Design-to-code loops fail when:

1. **Reference integrity is skipped.** Duplicated files labeled as different screens cause mislabeling across iterations (same image built as "Foods" one cycle, "Statistics" the next, rejected both times for "wrong layout" when the actual problem was the wrong reference source).
2. **Visual comparison is skipped.** Building the prototype and assuming it matches is insufficient. Visual diff against reference must happen before publishing.
3. **Interaction audit is incomplete.** A screen rendering correctly is not the same as every button/control working. Full audit required.
4. **Handoff doesn't document caveats.** If a reference file is duplicated or missing, that must be flagged so the next iteration knows.

This skill enforces those checks before claiming "done."

## Workflow

### Phase 1: Source Integrity Check

Before building anything, verify the reference image set:

**Hash the files.**
```bash
sha256sum /path/to/reference_*.png
```

**Confirm uniqueness.** If SHA hashes show duplicates (same hash for two different file paths), that is a blocker:
- Do NOT build from a set where file 5 is byte-identical to file 2 labeled as different screens.
- Flag immediately with the exact duplicate SHA and the file paths.
- Block the task and ask for corrected/deduplicated source files.

**Confirm count.** If the brief says "5 unique screens" and you have 5 file paths, verify all 5 have distinct hashes.

### Phase 2: Prototype Build

Build the full interactive preview with all routes, navigation, and Settings sections fully populated.

Use `claude-design` process:
- gather context (existing design system from repo if available)
- commit to a surface archetype for each route
- define the design system (colors, type, spacing, radii, shadows)
- build the artifact
- embed controls/tweaks if useful
- inline all CSS and JS for standalone portability

### Phase 3: Visual Comparison (Critical)

This is the mandatory gate. Do not skip.

For responsive work, validate **visual composition as well as geometry**. A page can have `scrollWidth === viewportWidth` and still fail because a breakpoint creates giant blank regions, oversized typography, sparse rows, clipped labels, or a different hierarchy from the wider reference.

1. Render every route at the exact reference viewport.
2. When comparing desktop and phone captures, first narrow the desktop browser to the phone's CSS width. If the phone failure reproduces there, classify it as a responsive breakpoint/CSS defect rather than a device-only issue; this gives implementation a deterministic reproduction path.
3. Exercise at least three widths: the exact target phone viewport including safe-area insets, one tablet width, and the reference desktop width. Preserve desktop composition while correcting the narrow breakpoint.
4. Seed representative populated state from the reference—long labels, multiple list rows, totals, progress, badges, and secondary panels. Empty-state screenshots cannot validate density, clipping, or realistic content flow.
5. Compare side-by-side and report mismatches by layout, hierarchy, typography, spacing, clipping, touch-target size, and information density. Treat unexplained fixed/min-height blank bands and flattened/clipped secondary widgets as failures even when overflow metrics pass.
6. Add component-level geometry assertions for the exact failure mode, not only document overflow: verify card row/column placement, text bounding boxes inside card bounds, full label/value visibility, and intended spanning behavior. Framework component wrappers can defeat child selectors, so inspect the rendered DOM and assert the wrapper that actually participates in the grid.
7. Fix, re-render, and repeat until major structural mismatches are resolved. Minor decorative differences may be accepted only when they do not affect comprehension.

Do NOT claim a match from automated width/overflow checks alone; show visual-comparison evidence.

**Designer responsibility:**
- Render each route at reference viewport dimensions.
- Compare rendered output vs. reference using available vision/image-diffing tools.
- Report mismatches by category (layout, hierarchy, typography, colors, spacing, icons, card treatment).
- Fix each mismatch in the prototype.
- Re-render and re-compare.
- Provide side-by-side comparison screenshots (or detailed notes) for each route before declaring completion.

**Orchestrator responsibility (before sending URL to user):**
- Independently inspect the designer's comparison evidence.
- Verify the reference images are correctly mapped to their routes (wrong source matched to output is a hidden failure).
- Check defining structures: layout (single vs. multi-column?), navigation edges, card compositions, hierarchy, colors, typography.
- If mismatches appear, flag with specific route/element/issue and request rework. Do NOT send the URL to the user until comparison passes your review.
- Only after your verification, present the preview URL to the user.

This double-gate (designer extracts + orchestrator verifies) prevents comparison faking and route mislabeling.

### Phase 4: Interaction Audit

Test every interactive element:

- **Navigation:** All 6+ routes (Diary, Foods, Statistics, Wellness, Goals, Settings/Tweaks) are clickable and render.
- **Controls:** Every visible button, toggle, dropdown, text input, range slider, or link works.
- **Settings:** If Settings/Tweaks is present, verify all sections are present (Profile, Nutrition, Hydration, Notifications, Connected Health, Appearance, Privacy, Account, etc.) and switching between sections works.
- **State changes:** Clicking "+Log" adds an item, clicking a toggle changes state, entering text in search filters results, etc.
- **Console errors:** Check for JavaScript errors (zero errors preferred, at least zero fatal errors).

Method:
- Manual testing: click every visible control and observe state.
- Programmatic testing: inject a JS harness with test cases and log PASS/FAIL to console, then run headless and capture output.

Report as: **N/M PASS** (e.g., "15/15 PASS" = all 15 controls tested and working; "14/15 PASS, see details" = one control failed).

### Phase 5: Final Handoff

Before publishing the URL or declaring completion:

1. **Verify preview provenance before presenting it.** Confirm the artifact's modification time or generating commit, route coverage, and whether it is a designer concept, a built application, or the live release. Do not present the only HTML file found as the "latest designer preview" without proving its age and origin; stale standalone mockups often survive after newer work has moved into branches, task artifacts, or production builds.
2. **Choose and verify the preview surface before handoff.** For review in the user's active Hermes Desktop window, open the built HTML file or localhost dev-server URL in the native right-hand preview rail and exercise at least one representative interaction with the desktop preview driver. A local file is valid for that same-window review; report it accurately as a local preview. For an external/mobile link, copy disposable worktree output into a stable preview location, serve it over HTTP, request the exact URL and linked assets, and require HTTP 200 before sending it. Do not present a URL merely printed by a publishing script as externally usable until its public route is verified from the user's intended surface.
3. **Make comparison previews comparison-ready.** When the user wants to judge responsive fidelity, serve desktop and target-phone renders from the same build on one labeled side-by-side page. A single mobile screenshot forces memory-based comparison and slows approval.
4. **State the preview URL** and label it accurately (concept, local build, or production).
5. **List the reference files used** and flag any caveats:
   - "All 5 files unique, used as-is."
   - "File 15 is byte-identical to file 11 (both Goals); Foods built to design-system spec, not a pixel reference."
6. **Report visual-comparison results per route:**
   - "Diary: matches well, minor icon spacing nit."
   - "Foods: matches well."
   - "Statistics: matches well, chart styling perfect."
   - "Wellness: matches well."
   - "Goals: matches well."
7. **Report interaction audit results:**
   - "15/15 controls PASS. Console clean. All 6 routes and 8 Settings sections working."
8. **State what was and was not verified** (if environment limits verification, say which steps were skipped and why).
9. **Label every visible difference by cause before asking the user to judge.** When the user must sign off on mockup-vs-app, tag each difference as (a) test/fixture data vs mockup demo data, (b) deliberate simplification pending real user data, or (c) genuine visual bug — in the gallery itself (default view shows only the bugs) plus a separate bug list with screen/region. An unlabeled wall of differences forces the user to enumerate what the team should have classified; present only category (c) for judgment.

Example final statement:
```
Preview: https://hermes-agent-railway-production-b7ce.up.railway.app/preview/abc123/

References: 5 files, all unique (SHA-verified). Used as Diary, Foods, Statistics, Wellness, Goals.

Visual comparison: Rendered each route at 1440x1100 desktop, compared side-by-side via vision diffing.
- Diary: matches well, minor hydration icon placement nit (acceptable).
- Foods: matches well.
- Statistics: matches well, line chart style perfect.
- Wellness: matches well, recovery ring exact.
- Goals: matches well, macro card layout exact.

Control audit: 15/15 PASS. All 6 routes, all hydration/meal/stats/goals/wellness controls, 8 Settings sections all working. Console clean.

Verification: file exists, headless chrome dump confirmed no errors, vision diffing completed for all routes.
```

Never say "done" or "exact match" without this evidence.

## Caveats

### What to Do If References Have Duplicates

If you discover that 2 of 5 supplied files are byte-identical (same SHA), halt and block:

```
Blocker: Reference file integrity issue.
File 11 and file 15 are byte-identical (SHA = abc123...), but labeled as different screens.
Foods screenshot not supplied (or is a duplicate of Statistics).
Need corrected/deduplicated reference set before building.
```

Do NOT guess which file is which or build from a mismatched set. Each iteration with the wrong reference wastes time.

### What to Do If a Reference Is Missing

If the brief calls for 5 screens but only 4 unique files exist:

1. Identify which screen is missing.
2. Build the available screens to reference, build the missing screen to match the established design system and information architecture (don't invent a separate look).
3. Explicitly flag in the handoff: "Foods built to design-system spec rather than pixel reference because no unique Foods screenshot was supplied."

### What to Do If Visual Comparison Finds Major Mismatches

If a route fails visual comparison (e.g., layout is completely different):

1. Fix the prototype.
2. Re-render at the same viewport.
3. Re-compare.
4. Iterate until it passes or you find a blocker (e.g., "the reference screenshot is cut off, cannot see the right edge").

Do not move on to the next route if the previous one is broken.

## Integration with `claude-design`

This skill does NOT replace `claude-design`. Instead, it layers rigorous verification on top of it:

- Use `claude-design` for the design process, surface commitment, visual system definition, and artifact build.
- Use `design-preview-fidelity` for source integrity checks, visual comparison, interaction audit, and handoff documentation.

Both apply to the same artifact.

## When to Use

- **DO** use when the task is to match supplied screenshot references exactly.
- **DO** use when visual fidelity and complete interactivity are acceptance criteria.
- **DO** use when a prior iteration was rejected for not matching the reference.
- **DO NOT** use for open-ended design exploration (use `claude-design` alone).
- **DO NOT** use for production code implementation (use repo-specific tools).

## Failure Patterns to Avoid

1. **Building from mismatched references and hoping it looks close.** → Result: rejected for "wrong layout."
2. **Rendering once and assuming it matches.** → Result: rejected after user loads it.
3. **Skipping the control audit.** → Result: published with broken buttons.
4. **Not documenting caveats.** → Result: next iteration repeats the same mistakes.
5. **Claiming "exact match" without visual-comparison evidence.** → Result: loss of trust.
6. **Accepting designer comparison report without orchestrator verification.** → Result: comparison artifacts may show wrong source routes, swapped chart types, or substitute layouts not matching the reference. Orchestrator must independently inspect each comparison image and verify the source route is correct, the major compositional elements align, colors are approximate, and no obvious structural swaps occurred (bar chart vs. line chart, wrong column count, missing sections). Do not send the user a preview URL until after you verify the comparison evidence yourself.
7. **Sending an unverified preview path or short-lived URL.** → Result: the artifact exists but the user sees “preview unavailable” or “server not found.” Verify the exact user-facing URL over HTTP, open it in the preview pane, and keep its serving process alive until dismissal.
8. **Iterating with vague feedback.** → Result: designer reinterprets, produces same mismatches. When a screenshot-driven design is rejected, extract exhaustive visual specs manually (using vision tools to read every layout detail, color, spacing, typography) and create a new high-priority task with these specs as the brief, plus explicit visual-comparison requirement. This pattern is detailed in `references/bitewise-screenshot-driven-redesign-workflow.md`.
9. **Publishing a build with absolute asset paths under a subpath preview URL.** → Result: CSS/JS 404 (served as text/plain, refused by strict MIME checking) and a blank page, while the repo build is correct. Publish a disposable copy with `/assets/` rewritten to relative `./assets/` paths; never change the repo's build `base` setting to accommodate a preview store.
10. **Starting an 'exact like the reference' rebuild without fencing what 'exact' excludes.** → Result: the user rejects honest working states (unavailable labels, real user data, missing DEMO badge) as mismatches. Fence in writing before dispatch: non-functional controls stay honestly unavailable (no dead buttons), data stays real, and only layout/components/styling/copy-tone must match.
11. **Serving a static preview of an app whose architecture forbids mocks.** → Result: the page hangs on 'Loading…' because every route needs the live API. Match the preview surface to the architecture: no-mock-data apps need a running backend (a local stack exposed privately or a staging environment with its own database), never a static file drop.

Do the verification. Document it. Inspect it. Publish only after orchestrator sign-off.

# BiteWise Screenshot-Driven Redesign Workflow (Sept 4, 2026)

## Incident Summary

User provided 5 reference screenshots of desired app layouts → designer built interactive preview → FAILED multiple times (navigation at wrong edge, Wellness layout completely different, Goals macro cards wrong, etc.) → user rejected as "looks disgusting" → orchestrator manually extracted exhaustive visual specs from reference images using vision tools → required designer to build from detailed specs + provide visual-comparison evidence → successful rebuild on third attempt.

**Root cause:** Designer tasks with "match these screenshots" briefs produced visually divergent outputs without rigorous visual-comparison gates. Orchestrator treated self-report of fidelity as sufficient, when it was not.

## Key Lesson: Orchestrator Must Become the Spec Author

When screenshot-driven design fails once (user rejects as "wrong layout"), do NOT iterate the designer task alone. Instead:

1. **Manually extract exhaustive visual specs** from the user's reference images using vision tools.
2. **Enumerate every layout detail, color, spacing, typography, and control** at pixel level.
3. **List the specific mismatches** the user complained about (e.g., "navigation at bottom, not left sidebar").
4. **Create a new designer task** with these extracted specs as the authoritative brief, plus explicit requirement for visual-comparison evidence before publishing.
5. **Verify the comparison yourself** — do not accept designer self-report of "matches" without inspecting side-by-side images.

## Workflow: Screenshot-Fidelity Gate in Delivery Orchestration

### Phase 1: Initial Brief (First Designer Task)

- User provides 5 reference screenshot files.
- Create designer task with `/claude-design` skill required.
- Brief includes screenshot file paths and states "match exactly."
- Expect preview URL and interaction audit in completion.
- **Do not require visual-comparison evidence yet** — that is Phase 2.

### Phase 2: User Rejection (Failed Visual Fidelity)

If user rejects the published preview as visually wrong ("looks doggshit," "layout completely different," "colors wrong"):

1. **Do NOT iterate the designer task with vague feedback.** Vague rejection → vague reinterpretation → another failure.

2. **STOP and extract the actual specs manually:**
   - Load each reference image.
   - Use vision tools to read layout structure, colors, typography, spacing, card dimensions, sidebar width, column counts, etc.
   - List every visual detail.
   - Annotate specific user complaints (e.g., "user said 'navigation at bottom' but reference shows left sidebar 260px wide, fixed position").
   - Flag any potential source problems (duplicate files, cut-off edges, ambiguous sections).

3. **Create new task** (`kanban_create` with high priority) with:
   - Full extracted visual spec as the new brief (not vague "make it exact").
   - Explicit requirement: "render each route, compare side-by-side to reference using visual tools, report mismatches by route (layout, colors, spacing, icons, controls), fix in prototype, re-render, iterate until visual match."
   - Explicit requirement: "before publishing, provide visual-comparison screenshots (reference vs. rendered) for each route showing fidelity."
   - Link to rejected preview URL (for reference only — do NOT reuse).
   - List specific fixes needed based on user's complaints.

### Phase 3: Designer Compliance (Extraction-Informed Task)

Designer receives detailed spec + visual-comparison requirement.

Designer must report (before publishing):

- Route-by-route visual comparisons (side-by-side PNG or detailed notes).
- Identified mismatches (layout, color, spacing, typography).
- Fixes applied.
- Interaction audit (tested controls).

### Phase 4: Orchestrator Verification (Critical Handoff)

**Before sending the preview URL to the user, inspect the visual-comparison evidence yourself.**

Check:

1. **Source route identity:** Is the reference screenshot shown the correct one for that route? (Common failure: Wellness reference paired with Goals output.)
2. **Defining structures match:** Do the major compositional elements align?
   - Single-column vs. multi-column?
   - Left sidebar vs. top nav vs. bottom nav?
   - Card layout: wide banner vs. small rings?
   - Recovery Snapshot: centered ring vs. off-center?
3. **Colors approximately match:** Are the green accents, orange warnings, and card backgrounds close?
4. **Spacing looks equivalent:** Are margins, padding, and gaps visually similar?
5. **No obvious swaps:** Are chart types the same (line vs. bar)? Are section counts equivalent?

If mismatches appear in your verification, **do not send the URL to the user.** Leave a kanban comment flagging the specific mismatch (route, element, what's wrong) and ask for rework before publishing.

## Example from BiteWise Sept 4

### Failed Iteration 1 & 2

- Designer task `t_995c7d08` built interactive preview.
- Published URL to user.
- User rejected: "navigation at bottom, Wellness looks like a joke, Goals progress looks nothing like the picture."
- Orchestrator re-tested URL, confirmed: navigation WAS at bottom (should be left sidebar), Wellness layout completely wrong (should be two-column Recovery Snapshot + Garmin/This Week), Goals macro cards wrong.
- Did NOT immediately re-queue designer with vague "fix it" feedback.

### Successful Iteration 3

- Orchestrator manually loaded all 5 reference images.
- Used vision_analyze to extract exhaustive specs:
  - Left sidebar: fixed, 260px wide, dark background, vertical nav items (Diary/Foods/Statistics/Wellness/Goals).
  - Diary: two-column (left: 4-card metric grid + meals, right: Today's Nudge sidebar).
  - Wellness: Recovery Snapshot on left (as wide as right two columns combined), Garmin + This Week on right.
  - Goals: just the progress banner (no macro cards).
  - Foods: search bar + Recent & Frequent + Fast ways to log + Saved meal.
  - Every color, font size, card dimension, spacing rule enumerated.
- Created new task `t_d3ec0134` with exhaustive specs + visual-comparison requirement.
- Designer rebuild matched references on first try (after extraction-guided brief).

## Prevention

1. **Extract specs early when fidelity matters.** If the user provides screenshots, load them and enumerate visual details before the first designer task. Include extracted specs in the initial brief.
2. **Require and verify visual comparison.** Designer tasks with screenshot references must include: "render each route, compare to reference using available visual tools, report mismatches, fix, re-render, provide comparison evidence before publishing."
3. **Inspect comparison evidence yourself.** Do not trust designer self-report. Verify at least one comparison image per route.
4. **Stop iteration loops early.** If a designer preview is rejected for visual reasons once, the next task must include orchestrator-extracted specs, not designer-interpreted feedback.

## Related Skills

- `design-preview-fidelity` — the verification skill for screenshot-faithful design. This workflow enforces all of its gates.
- `claude-design` — the designer skill used for the artifact. When used with extracted specs + fidelity gates, it produces correct results.

## Files & References

- BiteWise session: Sept 4, 2026, ~13:00-18:30 UTC
- Source images: `/root/.hermes/images/upload_20260904_164611_*.png` (5 files, Diary/Foods/Statistics/Wellness/Goals)
- Successful task: `t_d3ec0134` (designer, `/claude-design`, exhaustive specs + visual comparison)
- Published working preview: https://hermes-agent-railway-production-b7ce.up.railway.app/preview/d835aa29659eefbf/ (rebuilt with extracted specs)

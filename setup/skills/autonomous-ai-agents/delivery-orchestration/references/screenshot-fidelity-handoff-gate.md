# Screenshot-Fidelity Handoff Gate

**Session Origin:** BiteWise Sept 4, 2026 — two designer iterations rejected for visual divergence from approved screenshots.

## The Problem

When a user provides screenshots and asks for them to be turned into a working interactive application, the orchestrator can be tempted to "just implement it" from the images without a separate design-fidelity gate. This fails because:

1. **Approximation is invisible to code.** A designer can produce a generic SaaS dashboard, and the coder will implement what they receive as faithfully as possible—but the result will be "wrong" in ways no code review catches.
2. **Comparisons lie if not verified.** A worker can generate a side-by-side image showing "comparison" while actually comparing the wrong reference screenshot to the output, or pairing a Statistics reference with a Wellness screen output. The existence of a comparison file is not evidence that it reflects what was actually built.
3. **Control coverage must be tested, not claimed.** "All buttons work" declared by the designer without clicking each one leaves broken or placeholder controls in the shipped preview.

## Decision Tree

### Entry: User supplies screenshots, asks for interactive application

Q: Are the screenshots a strict specification for how the UI must look, or reference/inspiration?

- **Strict specification** (user said "exactly the same", "match these", "replicate the design", or rejected prior attempts as "not accurate")  
  → Go to **Fidelity-Gated Prototype Path** (below)

- **Reference/inspiration** (user said "similar to", "in the style of", or is doing exploratory design)  
  → Designer can be creative; move straight to implementation. Still require a clickable preview before code begins.

### Fidelity-Gated Prototype Path

**Step 1: Create a design (prototype) task with screenshot specification.**

Brief the designer:
- Map each screenshot to its intended route (e.g., "Image 1 = Diary, Image 2 = Foods, ...")
- Enumerate the visible requirements per screenshot:
  - Left rail dimensions and nav items
  - Content area width and card structure
  - Typography: family, size, weight, line-height for headings, body, labels
  - Spacing: section gaps, card padding, element margins
  - Colors: backgrounds, text, accents (identify specific hex or system color if available)
  - Card geometry: border-radius, shadows, border styling
  - Specific content blocks: e.g., "4 metric cards at the top, then meals list below" for Diary
  - Information hierarchy: what is emphasized, what is secondary
- **Fidelity requirement:** "Before publishing, render each route at the screenshot's visual proportions and create side-by-side comparison images. Correct any visible mismatches. Report the comparison images as evidence that each route matches its reference."
- **Interaction requirement:** "All visible buttons, nav items, toggles, and controls must be clickable and produce a meaningful state (route navigation, state change, or modal/panel). Test every control and report the tested inventory in your completion."
- **No invention rule:** "Do not invent new screens, layouts, or features. Reproduce the visible surfaces exactly."

**Step 2: Inspect the comparison artifacts before presenting to user.**

Once the designer publishes:

1. Fetch or inspect each comparison image:
   - Is the reference image on the LEFT the correct source screenshot for that route?
   - Is the rendered output on the RIGHT visually matching the reference in:
     - Layout and composition (wide banner vs small grid, etc.)
     - Visible sections and cards (missing Garmin card, missing recovery snapshot, etc.)
     - Chart type if present (bar, line, area — exact type matters)
     - Typography scale and weight
     - Color palette
   - Flag mismatches explicitly (e.g., "Statistics comparison shows a bar chart in the rendered output but the reference uses a line chart — this is a composition failure, not a styling fix")

2. Did the designer test every interactive control and report an inventory?
   - Example good inventory: "Tested: Diary date picker (left/right arrows), meal entry (add-food modal opens), Hydration quick-adds (+250ml, +500ml, Custom buttons), Statistics month/week/year filters, Goals edit button (opens editor), Wellness Sync now button and Retry, all Settings toggles (theme, notifications, privacy, etc.)."
   - Example bad inventory: "All controls work" without specifics.

3. **Reject if:**
   - Comparisons show the wrong reference screenshot for a route
   - Composition or major elements differ (chart type, section structure, layout archetype)
   - Controls lack an interactive inventory or show placeholders

   **Do NOT iterate from the rejected preview.** Instead:
   - Note which routes/sections failed fidelity
   - Create a new designer task (higher priority) with those specific failures enumerated
   - If recovery is possible (original prototype HTML exists and is correct), republish it unchanged instead of redesigning

4. **Accept if:**
   - Comparisons map correct references to correct routes
   - Visual elements match (layout, hierarchy, cards, colors)
   - All controls are tested and functional
   - No placeholders or generic substitutes

**Step 3: Create the implementation task only after user approval.**

Once the user approves the prototype preview:

```
kanban_create(
    title="Implement <AppName> UI from approved prototype",
    assignee="coder",
    body="Approved prototype: <preview-URL>\n\nImplement the interactive prototype as production Svelte/React/etc. code in the repository. Preserve the approved design's layout, spacing, typography, colors, and control behavior exactly. All routes (Diary, Foods, Statistics, Wellness, Goals, Settings) and all interactive controls must be functional in the production app.\n\nReference: <preview-artifact-path> (HTML source, use as layout spec)\n\nVerification: before completion, test all routes and controls in the production build. Report which controls were tested and the production deployment URL."
)
```

The prototype URL is the design spec; do not reinterpret.

## Common Failure Modes

### Approximation Substitution
**Symptom:** Designer produces a generic SaaS dashboard (centered hero, three equal-width cards, standard colors) instead of matching the reference's specific layout (left rail, asymmetric content areas, brand colors).

**Root cause:** Designer interpreted "make a prototype" as "design something nice" instead of "reproduce these screenshots." No fidelity check was performed.

**Prevention:** Fidelity requirement is explicit in the brief, and comparison verification happens before preview is shown to user.

### Comparison Faking
**Symptom:** Designer reports "comparison verified" but the side-by-side image shows misaligned routes (Statistics reference paired with Wellness output), or a generic layout instead of the reference.

**Root cause:** Comparison artifact was generated without care to match reference routes, or the artifact generation tool misaligned source/output images.

**Prevention:** Orchestrator inspects the actual comparison images, not just their existence. Confirms source route identity explicitly.

### Unverified Control Coverage
**Symptom:** Designer claims "all buttons work" but Tweaks/Settings panel is a placeholder with no actual controls, or a control shows no state change when clicked.

**Root cause:** Designer did not actually click and test each control; they iterated on the implementation and shipped.

**Prevention:** Designer's completion metadata includes a tested-control inventory. Orchestrator spot-tests a few high-priority controls (Settings toggle, date navigation, sync button) before presenting the preview.

### Wrong-Surface Substitution
**Symptom:** Designer looks at Goals screenshot and produces a Dashboard surface (centered hero + big summary stat) instead of the Goals surface (wide progress banner + grid of macro cards).

**Root cause:** Designer saw "progress" in the surface and defaulted to a generic progress dashboard instead of reading the specific layout shown in the screenshot.

**Prevention:** Fidelity brief maps each reference image to its surface type and intended purpose. Designer is reminded that screenshots are the spec, not their interpretation of what a "goals screen" should look like.

## Real Session Outcome: BiteWise Sept 4

**Iteration 1:** Designer produced a generic preview without comparing to screenshots. Rejected for visual slop.

**Iteration 2:** Designer claimed to match references but comparison images showed wrong-route pairings and chart-type mismatches. Rejected.

**Iteration 3:** Orchestrator recovered the original correct design (from prior task artifact), republished it unchanged. User approved. Implementation proceeds from verified prototype.

**Lesson:** Do not re-design once a fidelity gate fails. First, check whether the original reference design itself still exists and can be recovered unchanged. Rebuilding is a last resort, not the first move.

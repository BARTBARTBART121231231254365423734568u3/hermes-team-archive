---
name: bitewise-foods-design-concepts
title: BiteWise Foods Design Concepts
description: Use for distinct food-page layouts with interactive mockups.
version: 1.0
author: Hermes Agent
license: MIT
trigger: Use when designing distinct food-page layouts for BiteWise.
metadata:
  hermes:
    tags: [bitewise, foods-page, design-concepts, variants, interactive-mockup, preview, nutrition-ui]
    related_skills: [sketch, claude-design, bitewise-staging-deployment]
---

# BiteWise Foods Page Design Concepts

Build interactive, multi-screen design concepts for the BiteWise Foods page. This skill covers the workflow for generating distinct conceptual directions (not iterations), validating them as interactive previews, and refining winning concepts through variant exploration.

## When to Use

- User asks for **5+ completely distinct food-page designs** (not minor layout tweaks)
- Building **multi-concept comparison hub** where user can click through all options
- User wants **2-3 variants of a single region** (e.g., macro column display) with a switcher
- Exploring **surface-level redesigns** before committing to implementation
- Creating **interactive mockups** with actual navigation between screens

## Conceptual Framework: Distinct Surfaces

When asked for "5 different concepts," each should represent a **different interaction surface** or **information architecture** — not just visual tweaks to the same layout.

### Example Surface Types

1. **Monitor** (Ledger, Bench, Dashboard) — User passively observes daily intake/progress. Design emphasizes visualization (rings, bars, charts). Minimal action. Real-time streaming of data.

2. **Capture** (Scan, Voice, Quick-add) — User actively logs food via camera, speech, or rapid search. Design emphasizes input speed and accuracy. Fast feedback.

3. **Explore** (Pantry, Library, Discover) — User browses and discovers food options. Design emphasizes discoverability, filtering, categorization. Shelf or list-based browsing.

4. **Compare** (Bench, Nutrient Table, Macro comparison) — User examines food/meal nutritional profiles side-by-side. Design emphasizes tabular data, sortable columns, inline metrics.

5. **Configure** (Runway, Planner, Meal prep) — User plans future meals or edits saved meals. Design emphasizes macro targeting, weekly views, drag-drop interactions.

**Key lesson:** Each surface is a **fundamentally different task and user goal**. A concept built around one surface will fail at another. Do not call them "Variant A, B, C" — name them by surface.

## Workflow

### Phase 1: Research & Conceptualization

**Competitor research (required before design):**
- MyFitnessPal, Cronometer, Nutrola, FoodCraft, Kygo, Vitalis (or equivalent category leaders)
- Document patterns: what does each app's food page prioritize? Input speed, visualization, discovery, social?
- Note: do NOT copy — understand the **tradeoffs** each made

**User briefing (confirm with user):**
1. What surfaces should these concepts cover? (Monitor? Capture? Explore? Compare? Configure?)
2. Should all 5 include a "Today's Nudge" (actionable daily insight)? Or only specific concepts?
3. Are there any design constraints? (Must use BiteWise brand colors, specific typography, etc.)
4. Is approval tied to mockup similarity? (User will measure live implementation against this preview.)

### Phase 2: Build 5 Distinct Concepts

Each concept is a **self-contained interactive mockup** with:
- **4 connected screens minimum** (Home/Today → Add/Log → Detail/Compare → Insights/Stats)
- **Real navigation** (links work, state persists across screens, back button functional)
- **Mobile viewport** (390px is standard, also test 768px for tablet)
- **Brand colors** (BiteWise palette: #1fbf82 mint, #4a9eff blue, #f5a623 amber, dark bg)
- **Realistic data** (don't use lorem ipsum; use actual food names, real calorie counts)

### Phase 3: Build Hub for Multi-Concept Comparison

**Hub page** lists all 5 concepts with:
- Concept name (e.g., "Ledger", "Scan", "Pantry", "Bench", "Runway")
- One-line description of the surface (e.g., "Monitor Surface: Passive visualization of daily intake")
- Link to each concept's main screen
- Visual thumbnail or preview screenshot (optional, nice-to-have)

**Per-concept page structure:**
```
Concept: Ledger (Monitor Surface)
├── Screen 1: Today (daily overview)
├── Screen 2: Log Food (input screen)
├── Screen 3: Food Detail (nutrition deep-dive)
└── Screen 4: Trends (weekly/monthly charts)
```

### Phase 4: Publish & Verify

**Publish as live preview URLs:**
- Hub URL: Shows all 5 concepts listed, each linkable
- Per-concept URL: Full interactive mockup (all 4 screens clickable)

**Verification checklist:**
- [ ] All 5 concepts have names (not "Variant A/B/C")
- [ ] All 4 screens per concept are clickable/navigable
- [ ] No console errors (use headless Chrome DevTools)
- [ ] All 10-11 URLs return HTTP 200
- [ ] Brand colors match exactly (#1fbf82, #4a9eff, #f5a623)
- [ ] Text is readable (contrast ratio > 4.5:1)
- [ ] Responsive at 390px (mobile) and 768px (tablet)
- [ ] Hub page lists all 5 with descriptions

### Phase 5: User Selection & Refinement

After user picks a winning concept:

1. **Build 2-3 variants of a specific region** (e.g., "Macro column display"):
   - Keep all other screens identical to the original
   - Create toggle/switcher to compare variants on same concept page
   - Publish updated preview URL showing all variants
   - Example: Ledger concept with 3 macro-column variants (Ring+bars, Ledger table, Fuel gauge)

2. **Proceed to implementation** once user approves a variant.

## Macro-Column Variant Patterns (Specific to BiteWise Foods)

When refining a food-page concept, the macro display (Calories, Carbs, Fat, Protein) is often the first region to iterate on. Three common approaches:

### Variant A: Ring + Bars (Default, most approachable)
- Large circular progress ring for calories
- Three smaller rings or linear bars for carbs/fat/protein
- Clear visual hierarchy (calories emphasized)
- Best for: Monitor surfaces (passive viewing)

### Variant B: Ledger Table (Compact, scannable)
- Four equal rows (Calories | Carbs | Fat | Protein)
- Small 34px micro-rings per row
- Right-aligned tabular figures ("1,820 left of 2,500 cal")
- Best for: Data-driven users, dense layouts

### Variant C: Fuel Gauge (Bold, single focus)
- Huge "Calories Left" headline (44px)
- Single stacked horizontal bar (carbs/fat/protein macros as segments)
- 3-up legend below
- Best for: Goal-obsessed users, simplicity-first

**How to build variants with a switcher:**
1. Create 3 separate HTML blocks (one per variant) inside the same page
2. Use CSS `display: none` / `block` or JavaScript `classList.toggle()` to swap
3. Build toggle buttons/tabs at the top of the macro column
4. Verify variant switch swaps ONLY that region — rest of page unchanged (diff: byte-identical)
5. Test that all 3 variants render without console errors
6. Verify switcher works on all 4 screens (each screen shows same variant selection)

## Design Spec Binding (Critical for Implementation)

**When a user approves a mockup preview:**
- Treat the preview as a **binding visual specification** for implementation
- Note the approved macro-column variant name (e.g., "Variant 2: Ledger Table")
- Capture the visual hierarchy of the Foods page hierarchy (especially **bottom sections**) — not just the top
- Record mobile behavior for each region (e.g., "columns must remain side-by-side on 390px, not stack")
- Seed staging with test data BEFORE live QA — empty-state UIs hide actual layouts
- See `references/design-spec-binding-lesson-2026-09-07.md` for full context (session where empty staging data made a working layout appear broken)

## Approved Foods Information Architecture

Thomas selected **The Launchpad** as the binding Foods direction. Keep Diary as the immediate view of today's consumed foods; do not duplicate that feed on the Foods landing page. Foods should open as an action-first launchpad with prominent barcode scanning plus photo and quick-add actions, while the food library, favorites, and recent foods live behind deliberate secondary screens. Preserve real meal selection and Diary logging through every launch path.

## Browse and Confirm-Add Design Rules

Use these rules when refining the Foods library or the barcode/photo confirmation flow.

1. **Keep browse calm by default.** Show search, a compact `Recent / Favorites / Meals` switch, and one 44px Filter control. Put category, dietary/allergen, and source filters in a bottom sheet with active count and Clear all; do not leave a wall of filter chips above the results.
2. **Use portion truth as the primary interaction.** Offer both a serving-first treatment and a gram-first treatment in the prototype when the user has not chosen. After selection, implement the chosen default with an automatic gram-first fallback whenever a verified named-serving mass is absent.
3. **Offer measures per food, never as a universal menu.** Default to the contextual verified measure plus `Custom grams`, then expose a compact `Change measure` sheet containing only alternatives with a valid conversion. Direct mass units (g/oz/lb) convert exactly; volume units (ml/cup/tbsp/tsp) require a food-specific conversion; named counts (piece/slice/serving) require declared grams. Explain a grams-only fallback plainly when the food lacks reliable conversion data.
4. **Never invent a named-serving weight.** Show `1 slice · 24 g` only when the food record provides a validated serving mass. Otherwise label the available basis plainly (label serving, per 100 g, or grams required).
4. **Derive visible nutrition from one canonical basis.** Store per-100g or validated-serving nutrition, calculate an explicit `For N g` amount, and proportionally recalculate kcal, protein, carbs, and fat immediately whenever count or grams changes. Keep manual macro editing behind a correction-only disclosure so ordinary logging cannot create inconsistent values.
5. **Make provenance and uncertainty visible.** Barcode records, records missing nutrition, and AI estimates need distinct confirmation states. Do not render unexplained zero nutrition: use unavailable values, concise recovery copy, and disable logging until enough nutrition data exists. Label AI output as an estimate and require confirmation before logging.
6. **Preserve meaningful add feedback.** When users approve the add animation or confirmation feedback, capture it as part of the binding interaction spec and require the real app to retain it through quick-add and Confirm → Log success—not merely reproduce static screens.
7. **Keep the mobile sheet usable above Halo.** Use internal document/sheet scrolling, a sticky actionable footer, and 44px controls. Render the full flow at 390, 402, and 430px, including the state where lower nutrition is reached by scroll; verify the sheet clears the unchanged Halo dock.
8. **Prototype the whole decision loop, not just a pretty form.** Test Browse → Confirm → amount change → live macro update → meal selection → logged success, plus quick-add, filter apply/clear, missing-serving, missing-nutrition, and AI-estimate paths before asking for approval.
9. **Separate design approval from release approval.** A user-approved preview authorizes implementation against the binding spec; it never authorizes deploying the prototype itself. Build and independently review the real app flow, including persistent data paths and actual barcode/AI inputs, then obtain or apply the user's explicit production authorization before release.

## References

- `references/design-spec-binding-lesson-2026-09-07.md` — Why approved mockups must be treated as binding specs; how empty-state data can hide working layouts
- `references/five-concept-comparison-workflow-2026-09-07.md` — End-to-end process for building 5 distinct concepts, hub page, and verification checklist
- `references/macro-column-variant-patterns-2026-09-07.md` — Three proven macro-display variants: Ring+bars, Ledger table, Fuel gauge; when to use each

## Related Skills

- **sketch** — For 2-3 throwaway mockups to explore direction before committing to multi-concept build
- **claude-design** — For polished, production-ready HTML artifacts (one final concept picked and refined)
- **bitewise-staging-deployment** — For deploying approved concepts to Railway staging for end-to-end testing

## Session Context

**Session:** 2026-09-07 BiteWise Foods Design Concepts (5 distinct + macro variants)  
**Outcome:**
1. Built 5 distinct food-page concepts (Ledger/Monitor, Scan/Capture, Pantry/Explore, Bench/Compare, Runway/Configure)
2. Published as hub + per-concept URLs with full interactive navigation
3. User selected Ledger concept
4. Designer built 2 additional macro-column variants (Ledger table, Fuel gauge) on same page with toggle
5. User to select variant; implementation task TBD

**Key insight:** User rejected "iterative minor tweaks" — wanted "5 completely different approaches." Named surfaces (Monitor, Capture, Explore, Compare, Configure) provided the conceptual framework that made distinct designs possible. Generic "Variant A/B/C" naming would have failed to guide either design or user choice.

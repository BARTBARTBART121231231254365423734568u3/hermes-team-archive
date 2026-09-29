# Five-Concept Comparison Workflow — Session 2026-09-07

## Overview

When a user asks for "5 different food-page designs," the workflow is:
1. Research competitors (understand tradeoffs, not to copy)
2. Define 5 distinct **surfaces** (Monitor, Capture, Explore, Compare, Configure)
3. Build interactive mockups for each concept
4. Create hub page for side-by-side comparison
5. Publish live preview URLs
6. User picks winner, designer refines with variants

## Phase 1: Competitor Research

**Scope:** Leading nutrition/food-tracking apps
- MyFitnessPal (logging focus)
- Cronometer (data/nutrition focus)
- Nutrola (community/social)
- FoodCraft (recipe/meal prep focus)
- Kygo (simplicity)
- Vitalis (holistic health)

**Document per app:**
- Primary user task: What does the food page optimize for? (Speed? Accuracy? Discovery? Social?)
- Information architecture: Where do foods come from? (Search? Recent? Favorites? AI suggestions?)
- Visual treatment: How are macros shown? (Rings? Bars? Tables? Cards?)
- Mobile behavior: Single column? Sidebar? Scroll pattern?
- Data density: How much is shown at a glance? (One meal? Day? Week?)

**Synthesis:** What patterns repeat across leaders? What tradeoffs did each make? (E.g., MyFitnessPal chose logging speed → favored search + quick-add; Cronometer chose data accuracy → favored nutrition tables.)

## Phase 2: Define 5 Distinct Surfaces

Do NOT build 5 iterations of the same layout. Each concept should represent a fundamentally different **user task** and **information architecture**.

### Monitor Surface (Passive Observation)
**When user:** Wants to passively view daily intake and progress  
**Design emphasizes:** Visualization, real-time summary, goal tracking  
**Layout principle:** Data-forward; user sees rings, bars, charts first  
**Examples:**
- Ledger (daily ledger table of macros + rings)
- Bench (sortable comparison table)
- Dash (card grid of daily stats)

**Info architecture:** Command center (today's totals) → Food Library (browse/search) → Food detail (view nutrition) → Trends (weekly/monthly)

### Capture Surface (Active Logging)
**When user:** Wants to quickly log food they just ate  
**Design emphasizes:** Input speed, minimal friction, clear affordances for "add this meal"  
**Layout principle:** Input-forward; camera/search/voice is primary, confirmation comes after  
**Examples:**
- Scan (full-screen camera viewfinder)
- Voice (speech input focus)
- Quick (zero-friction add via recent/quick-add)

**Info architecture:** Capture mode (camera/voice/search) → AI results (verify) → Portion confirmation → Done

### Explore Surface (Discovery)
**When user:** Wants to discover foods, build knowledge, explore options  
**Design emphasizes:** Browsing, categorization, learning, serendipity  
**Layout principle:** Shelf-based or list-based discovery; food database is the primary object  
**Examples:**
- Pantry (food shelves: Proteins, Carbs, Veggies, etc.)
- Library (searchable, filterable food list)
- Discover (algorithmically suggested foods)

**Info architecture:** Shelves/categories → Food detail (view nutrition, see similar) → Saved for later / Quick-add

### Compare Surface (Analysis)
**When user:** Wants to compare nutritional profiles (foods or meals side-by-side)  
**Design emphasizes:** Data density, sortable columns, inline metrics  
**Layout principle:** Tabular; rows are foods/meals, columns are nutrients  
**Examples:**
- Bench (sortable table, multi-select compare)
- Matrix (nutrient-focused pivot table)
- Timeline (meals stacked by date, nutrient columns)

**Info architecture:** Filter by date/type → Sortable table → Select rows to compare → Side-by-side detail

### Configure Surface (Planning)
**When user:** Wants to plan meals, hit macro targets, build meal patterns  
**Design emphasizes:** Macro budgeting, drag-drop meal building, weekly view, intelligent suggestions  
**Layout principle:** Planner-forward; week grid or daily plan is primary  
**Examples:**
- Runway (weekly meal plan with macro targeting)
- Planner (daily meal builder with drag-drop)
- Focus (macro-focused meal suggestions)

**Info architecture:** Weekly plan view → Day picker → Meal builder (drag-drop) → Macro balance check → Save/confirm

## Phase 3: Build Mockups

For each concept:

### Screen 1: Today/Home
- Primary visualization of selected surface (what does the user see first?)
- Today's context (date, day of week, progress toward goals)
- Navigation to other screens
- On Monitor: command center, nudge, recent foods
- On Capture: large camera/search/voice affordance
- On Explore: shelf grid or food list
- On Compare: meal selector + sortable table header
- On Configure: weekly calendar or daily plan

### Screen 2: Add/Log/Search
- How does the user add food to this concept?
- Search box (if applicable), recent/frequent lists, or AI results
- On Monitor: Log food screen (search + recent + quick-add)
- On Capture: AI results from camera scan
- On Explore: Food detail page with nutritional profile
- On Compare: Meal/food selector with filter
- On Configure: Meal builder palette (drag-drop source)

### Screen 3: Detail/Compare
- Zoomed view or comparison view
- On Monitor: Food detail (full nutrition breakdown)
- On Capture: Portion confirmation + AI description
- On Explore: Food detail with similar foods / add to favorites
- On Compare: Side-by-side comparison of selected foods/meals
- On Configure: Macro balance feedback (are we hitting targets?)

### Screen 4: Trends/Progress
- Historical view or summary
- On Monitor: Weekly/monthly trends, macro progression
- On Capture: Recent meals logged (history)
- On Explore: Saved foods or favorites
- On Compare: Meal history or saved comparisons
- On Configure: Plan summary or meal repeat patterns

## Phase 4: Build Hub Page

**Structure:**
```html
<h1>5 Foods Page Concepts</h1>

<div class="concepts-grid">
  <concept-card>
    <h3>Ledger (Monitor)</h3>
    <p>Passive observation of daily intake via a ledger table. Each row: macro + remaining calories.</p>
    <a href="./concepts/ledger/today.html">View →</a>
  </concept-card>
  
  <concept-card>
    <h3>Scan (Capture)</h3>
    <p>Active logging via camera. Point, snap, AI recognizes food, confirm macros.</p>
    <a href="./concepts/scan/viewfinder.html">View →</a>
  </concept-card>
  
  <!-- ...Pantry, Bench, Runway... -->
</div>
```

**Each concept card should include:**
- Concept name + surface type (e.g., "Ledger (Monitor)")
- One-sentence description of the surface
- Link to concept's first screen (Today/Home)
- Optional: small thumbnail image or preview

## Phase 5: Verification Checklist

- [ ] All 5 concept names are distinct and surface-based (not "Variant A/B/C")
- [ ] Hub page lists all 5 with descriptions and links
- [ ] Each concept has 4 connected screens (all clickable, navigation works)
- [ ] No console JS errors in headless Chrome
- [ ] All URLs return HTTP 200
- [ ] Brand colors are exact (#1fbf82, #4a9eff, #f5a623)
- [ ] Text contrast >= 4.5:1 (readable)
- [ ] Responsive at 390px (mobile) and 768px (tablet)
- [ ] Data in mockups is realistic (not 1 food when 50 typical)
- [ ] Empty-state handling is clear (if applicable)

## Phase 6: User Selection & Refinement

After user picks a winning concept (e.g., "Ledger"):

### Option A: Iterate on a Specific Region

If user says "I like Ledger, but can you show me 2-3 different ways to display the macro column?"

1. Keep all 4 screens of Ledger identical
2. Build 2-3 variants of ONLY the macro column (at the top of Screen 1: Today)
3. Add toggle buttons/tabs to switch between variants
4. Publish updated Ledger preview with switcher
5. User picks variant
6. Proceed to implementation

**Example variants:**
- Variant 1: Ring + bars (current)
- Variant 2: Ledger table (4 rows, micro-rings, tabular figures)
- Variant 3: Fuel gauge (huge "calories left" + stacked bar)

### Option B: Hybrid (Pick Best Pieces from Multiple Concepts)

If user says "I like Ledger's data viz, but Scan's quick-add flow..."

1. Create a new mockup blending pieces from both
2. Keep consistent interaction model (don't try to be both Monitor and Capture)
3. Publish as hybrid concept
4. Validate with same 4-screen checklist

## Output Artifacts

1. **Hub page:** `index.html` listing all 5 concepts with links
2. **Per-concept directories:** `concepts/ledger/`, `concepts/scan/`, etc.
3. **Per-concept screens:** `today.html`, `log-food.html`, `detail.html`, `trends.html`
4. **Live preview URLs:** Hosted on Railway preview service (7-day expiry)

## Session 2026-09-07 Outcome

- Built 5 distinct concepts (Ledger, Scan, Pantry, Bench, Runway) with full navigation
- Published hub + 5 concept URLs + 20 individual screen URLs
- User selected Ledger
- Designer built 3 macro-column variants for Ledger
- User to select variant; coder to implement

**Key insight:** Naming surfaces (Monitor, Capture, Explore, Compare, Configure) unlocked distinct designs. Iteration-based naming (Variant A/B/C) would have produced 5 subtly different layouts of the same idea, not 5 fundamentally different approaches.

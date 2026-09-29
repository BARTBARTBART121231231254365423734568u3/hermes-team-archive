# Macro-Column Variant Patterns — Session 2026-09-07

## Context

When refining a food-page concept (especially Monitor surfaces like Ledger), the macro display (Calories, Carbs, Fat, Protein) is often the first region to iterate on. Three patterns emerged as viable approaches, each with distinct tradeoffs.

## Variant 1: Ring + Bars (Default, Most Approachable)

### Visual Treatment
- Large circular progress ring for **calories** (primary focus)
- Three smaller rings or linear bars for **carbs, fat, protein** (secondary)
- Clear visual hierarchy (calories emphasized via size/color)
- Rings use BiteWise accent colors (#4a9eff blue, #f5a623 amber, #1fbf82 mint)

### Layout
```
┌─────────────────────────┐
│    🔴 Calories          │
│    1,820 / 2,500        │  
│    ════════════════     │  (large ring)
│                         │
│  Carbs  Fat  Protein    │  (3 smaller rings or bars)
│  ━━━━  ━━━━  ━━━━━     │
└─────────────────────────┘
```

### Strengths
- Instant visual feedback (ring fill = progress)
- Calories are obviously primary (everyone cares about calories)
- Intuitive for novices (rings are familiar UI pattern from health apps)
- Accessible: color + number redundancy

### Weaknesses
- Takes up more vertical space (rings are tall)
- Difficult to compare macros at a glance (user must read three separate visualizations)
- Ring fill is continuous; doesn't show remaining budget clearly

### When to Use
- Monitor surfaces (passive viewing)
- Novice users (simpler mental model)
- When calories are the primary goal metric
- When space permits (desktop, landscape)

### Code Pattern
```html
<div class="macro-column v1-rings">
  <div class="ring-primary">
    <svg>
      <circle cx="50" cy="50" r="40" stroke="#1fbf82" fill="none" stroke-dasharray="... "/>
    </svg>
    <div class="label">1,820 / 2,500</div>
  </div>
  <div class="rings-secondary">
    <div class="ring-small" title="Carbs"></div>
    <div class="ring-small" title="Fat"></div>
    <div class="ring-small" title="Protein"></div>
  </div>
</div>
```

---

## Variant 2: Ledger Table (Compact, Scannable)

### Visual Treatment
- Four equal rows: Calories | Carbs | Fat | Protein
- Each row: label + small 34px ring + metric number + "left of" subtitle
- Right-aligned tabular figures (1,820 aligns with 1,821 via monospace)
- Monospace font (IBM Plex Mono) for data; sans-serif (DM Sans) for labels

### Layout
```
┌────────────────────────────────┐
│ Calories  ◉  1,820 / 2,500     │
│            left of goal         │
│                                │
│ Carbs     ◯  142 / 300g        │
│            6 grams left         │
│                                │
│ Fat       ◯  68 / 70g          │
│            2 grams left         │
│                                │
│ Protein   ◯  156 / 160g        │
│            4 grams left         │
└────────────────────────────────┘
```

### Strengths
- Highly scannable (eyes can compare all 4 metrics at once)
- Compact vertical footprint (good for mobile, dense layouts)
- Ledger aesthetic familiar to spreadsheet users
- Clear remaining-budget indication ("X left of Y" is explicit)
- All info visible without scrolling

### Weaknesses
- Less visually "fun" (more utilitarian)
- Small rings are less attention-grabbing than large ones
- Requires reading more text to understand
- Monospace fonts can feel cold/clinical

### When to Use
- Data-driven users who like tables
- Dense layouts or mobile where vertical space matters
- Monitor surfaces that need to show all macros equally
- When scanability and efficiency are goals

### Metrics
- Height: ~229px (4 rows × ~50-60px each including spacing)
- Horizontal width: fits 380px mobile (with 12px margin)

### Code Pattern
```html
<div class="macro-column v2-ledger">
  <div class="macro-row">
    <div class="macro-label">Calories</div>
    <svg class="micro-ring">
      <!-- 34px ring -->
    </svg>
    <div class="macro-value">1,820 / 2,500</div>
  </div>
  <div class="macro-subtitle">1,820 left of goal</div>
  <!-- ...repeat for Carbs, Fat, Protein... -->
</div>
```

---

## Variant 3: Fuel Gauge (Bold, Single Focus)

### Visual Treatment
- Huge **"Calories Left"** headline (44px, bold)
- Single horizontal stacked bar below (carbs as blue, fat as amber, protein as mint)
- 3-up legend at bottom (Carbs | Fat | Protein with color dots)
- Minimal text; maximum visual impact

### Layout
```
┌─────────────────────────────┐
│  Calories Left              │
│  1,820                      │  (44px, bold headline)
│                             │
│  ███████████ ████ ███       │  (stacked horizontal bar)
│  Carbs  Fat  Protein        │  (legend with dots)
│  ·····  ····· ·······       │
└─────────────────────────────┘
```

### Strengths
- Instantly grabs attention (huge number, bold hierarchy)
- Single focus on calories (simplest mental model for goal tracking)
- Stacked bar shows macro proportion at a glance
- Compact height (~215px), makes room for other content below
- Bold, modern aesthetic (not clinical like Ledger)

### Weaknesses
- Hides individual macro budgets (user sees proportion, not remaining grams)
- Only useful if user is calorie-focused (not macro-focused)
- Less suitable for detailed nutrition tracking
- Requires legend to understand bar segments

### When to Use
- Users primarily tracking calories (goal is "2,500 cal/day")
- Simple, uncluttered designs
- Attention-grabbing first screen (lead with motivation)
- When macro details are available elsewhere on page

### Metrics
- Height: ~215px (headline + bar + legend + spacing)
- Horizontal bar width: fills available width (on 390px, ~356px usable)

### Code Pattern
```html
<div class="macro-column v3-fuel-gauge">
  <div class="headline">Calories Left</div>
  <div class="number">1,820</div>
  
  <div class="stacked-bar">
    <div class="segment carbs" style="width: 47%"></div>
    <div class="segment fat" style="width: 23%"></div>
    <div class="segment protein" style="width: 30%"></div>
  </div>
  
  <div class="legend">
    <div class="legend-item">Carbs</div>
    <div class="legend-item">Fat</div>
    <div class="legend-item">Protein</div>
  </div>
</div>
```

---

## Comparison Matrix

| Dimension | Ring + Bars | Ledger Table | Fuel Gauge |
|-----------|------------|-------------|----------|
| **Visual hierarchy** | Calories primary | All equal | Calories only |
| **Scanability** | Moderate (3 rings) | High (4 rows) | High (1 number) |
| **Height** | ~250px | ~229px | ~215px |
| **Best for** | Novices, Monitor | Data-driven, Dense | Goal-focused, Simple |
| **Aesthetic** | Friendly, modern | Utilitarian, clinical | Bold, motivating |
| **Macro visibility** | Rings + numbers | Explicit budgets | Proportions only |
| **Mobile-friendly** | OK | Great | Great |

---

## How to Build Variants with a Switcher

When user approves a concept but wants to compare 2-3 variants of the macro column:

### 1. Create 3 Separate HTML Blocks

In the `<div class="macro-column">`, place all 3 variants as sibling divs:
```html
<div class="macro-column">
  <div id="variant-1" class="macro-variant active">
    <!-- Ring + Bars content -->
  </div>
  <div id="variant-2" class="macro-variant">
    <!-- Ledger Table content -->
  </div>
  <div id="variant-3" class="macro-variant">
    <!-- Fuel Gauge content -->
  </div>
</div>
```

### 2. Add Toggle Buttons

Place above the macro column:
```html
<div class="variant-switcher">
  <button class="variant-btn active" data-variant="1">Ring + Bars</button>
  <button class="variant-btn" data-variant="2">Ledger Table</button>
  <button class="variant-btn" data-variant="3">Fuel Gauge</button>
</div>
```

### 3. CSS to Show/Hide

```css
.macro-variant { display: none; }
.macro-variant.active { display: block; }
```

### 4. JavaScript to Toggle

```javascript
document.querySelectorAll('.variant-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const variant = e.target.dataset.variant;
    document.querySelectorAll('.macro-variant').forEach(v => v.classList.remove('active'));
    document.getElementById(`variant-${variant}`).classList.add('active');
    document.querySelectorAll('.variant-btn').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
  });
});
```

### 5. Verification

- [ ] Switcher toggles between all 3 variants
- [ ] Only one variant visible at a time
- [ ] All other page sections (Today screen, rest of page) remain unchanged
- [ ] Switching doesn't reload page or lose scroll position
- [ ] Works on all 4 screens (Today, Log Food, Detail, Trends) with same variant selected
- [ ] No console errors
- [ ] Brand colors present in all variants (#1fbf82, #4a9eff, #f5a623)

---

## Session 2026-09-07 Results

**Ledger concept + 3 macro variants:**
- Variant 1: Ring + Bars (original, unchanged)
- Variant 2: Ledger Table (34px micro-rings, right-aligned figures, 229px height)
- Variant 3: Fuel Gauge (44px "Calories Left", stacked bar, 215px height)

**Published preview:** https://hermes-agent-railway-production-b7ce.up.railway.app/preview/06a944a1447bd7a8/

**Verification results:**
- ✅ 0 JS errors
- ✅ Switcher swaps exactly 1 region across all 4 screens
- ✅ All other screens byte-identical to original
- ✅ Heights: 131px (v1), 229px (v2), 215px (v3)
- ✅ Contrast >= 4.86:1
- ✅ All brand colors present
- ✅ Live URL verified in headless Chrome

**User selection:** TBD (user to review and pick preferred variant)

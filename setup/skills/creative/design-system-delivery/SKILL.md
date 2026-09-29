---
name: design-system-delivery
description: "Deliver a design system (tokens, specs, mockup) via GitHub."
version: 1.0
author: Hermes Agent
license: MIT
---

# Design System Delivery

Use this skill when you need to **deliver a complete, implementable design system** — not exploration or one-off mockups, but a production-ready package of design tokens, page specifications, and visual references ready for developers to build from.

## When to use

- "Create a design system for my app"
- "I need design specs for all pages"
- "Hand off a design to my team"
- User says "keep this style consistent across all pages"
- After design exploration/sketch phase, ready to deliver for implementation

**Do NOT use** for:
- Throwaway design exploration → use `sketch`
- Single landing page prototype → use `claude-design`
- Design feedback or iteration loops → use `sketch` again

## The core workflow

### 1. Define design tokens
Create a **copy-paste-ready CSS file** with:
- Color palette (dark & light themes as CSS custom properties)
- Spacing scale (4px, 8px, 12px, 16px, 20px, 24px, 32px…)
- Typography (font sizes, weights, line heights)
- Border radius scale
- Shadows & effects
- Transitions & easing
- Safe area variables (mobile notch support)

Output: `DESIGN_TOKENS.md` (or `.css`) where developers literally paste the `:root { }` block and everything works.

**Pro tip:** Include light, dark, and system/auto behavior in the same token contract; use the user's chosen default rather than assuming dark. Every single value must be a CSS custom property.

### 2. Freeze the chosen visual direction and write detailed page specifications
When the user chooses a variant, treat that choice as authorization to develop that direction, not as evidence that the current scaffold is the final design. Revisit requested interaction refinements before implementation (for example, tapping a diary date should open a full selectable month while day arrows remain); record behavior and phase boundaries in the handoff. Do not ask the user to write an additional prompt for a named agent when the existing goal, design references, and selected preview already define the outcome—translate them into an implementation contract yourself.

For each page/screen, document:
- Layout (grid structure, flexbox direction, spacing)
- Component breakdown (what goes where, sizing)
- Responsive behavior (breakpoints, mobile collapsing rules)
- Color usage (which token for which element)
- Padding & margin specifics
- Hover/active/disabled, empty/loading/error/offline states and keyboard/safe-area behavior
- Which information is supported by real data today versus requires later integrations; avoid invented health readings or premature insight claims

Output: `PAGE_SPECS.md` with one section per page, ASCII diagrams where helpful.

**Pro tip:** Be specific. Not "use padding" but "card padding: 24px, item padding: 16px". Include trade-offs ("Card hover darkens on desktop, adds 4px border on mobile").

### 3. Create visual reference mockup
Build **one interactive HTML mockup** showing all pages/screens:
- Sidebar or tab navigation to switch between pages
- Real sample data (not lorem ipsum)
- All design tokens applied
- Interactive elements visibly (buttons, inputs, hover states)
- Inline CSS only (no external assets)

Output: `mockups-interactive.html` — a single self-contained file.

**Why one file?** Developers can open it locally, search it, reference multiple pages, and see consistency without context-switching. Easier to version-control.

### 4. Write a design overview
Create `README.md` covering:
- Design philosophy (1-2 sentences: "minimal dark theme with mint accents")
- Color palette with hex codes
- Spacing scale & typography scale
- Grid & responsive breakpoints
- Quick component inventory
- Implementation checklist ("build this page first…")
- File manifest ("what each file is for")

**Pro tip:** First 100 lines should answer "what is this and how do I start?" Developers should not need to ask you.

### 5. Organize & push to GitHub

**Folder structure:**
```
/design-system/
├── README.md                      (Overview, manifest, checklist)
├── DESIGN_TOKENS.md               (CSS vars, copy-paste ready)
├── PAGE_SPECS.md                  (Layout details per page)
├── mockups-interactive.html       (Visual reference, all pages)
└── references/                    (Optional: rationale, guidelines)
    └── color-palette-rationale.md
```

**Critical:** Push to GitHub **before** giving user a link. Git is the reliable shared medium across systems.

## Pitfalls & gotchas

### ❌ Don't rely on localhost URLs for cross-system sharing
**What failed in this session:** Created a local HTTP server (`localhost:9999`) on Linux and gave Windows user the link. They couldn't open it — localhost is machine-local.

**Why it fails:** Localhost doesn't cross system boundaries. User is on a different machine entirely.

**What works instead:** Push to GitHub. User clones/pulls. They access files from their local file system or via the GitHub web UI. No fancy server needed.

### ❌ Don't assume file:// URLs work reliably
Paths like `file:///tmp/design.html` seem like they should work but:
- Different systems have different path structures
- File access permissions differ
- Breaks when files are deleted or moved
- Browser mixed-content warnings can block them

**What works:** Always use GitHub as the source of truth. User pulls the repo. They access it locally as a regular file. No URL tricks needed.

### ❌ Don't create mockups without a delivery plan
If the HTML mockup exists only on your machine, it's useless to the user.

**What works:** Commit it to the `/design-system/` folder before delivery. Reference it in README so user knows it exists and how to open it locally.

### ❌ Don't skip the CSS tokens file
Tempting to just make a pretty mockup and assume developers will eyedrop colors and guess spacing.

**What fails:** Developers then have to screenshot-eyedrop colors, hand-type spacing values, guess at opacity levels. They get it wrong or ask you to clarify.

**What works:** Provide tokens as a plain-text copy-paste file. One paste into their `styles/tokens.css` and they're done — all variables ready to use.

### ❌ Don't make tokens that need interpretation
Bad: "Use the mint color for accents" + a screenshot showing what "mint" looks like.
Good: `--accent: #1fbf82;` in the DESIGN_TOKENS.md file.

**Why:** Developers need exact values they can copy. Visual approximation leads to mismatches.

## Implementation steps (in order)

1. **Review the user's current design** (existing styles, brand, reference pages)
2. **Extract or define design tokens** from what you see
3. **Write PAGE_SPECS.md** — one detailed section per page
4. **Create DESIGN_TOKENS.md** — all values as CSS custom properties, copy-paste ready
5. **Build mockups-interactive.html** — visual reference using the tokens, navigation between pages
6. **Write README.md** — philosophy, palette, specs, checklist, manifest
7. **Organize into `/design-system/` folder** in the repo
8. **git add, git commit, git push** with a clear message
9. **Tell user:** "Design system pushed to GitHub `/design-system/`. Pull locally. Start with README.md, then use mockups-interactive.html as a visual reference."

## Success criteria

✅ Design tokens are **copy-paste ready** (actual CSS, not just images)
✅ Page specs are **specific** (exact pixel values, not vague guidance)
✅ Mockup is **self-contained** (one HTML file, no external resources)
✅ README is **scannable** (philosophy + palette + checklist visible first)
✅ Everything is **in GitHub** (not localhost, not temporary files)
✅ User can **pull and build immediately** without asking clarifying questions

## Trade-offs: Markdown specs vs. HTML mockups

| Aspect | Markdown | HTML mockup |
|--------|---|---|
| Portable? | ✓ Text, easy to version | ✗ File-based, needs local access |
| Visual? | ✗ Text + ASCII | ✓ Full visual render |
| Searchable? | ✓ grep/Ctrl+F works | ✗ Browser search only |
| Copy-paste-able? | ✓ Code and values | ✗ Needs eyedropper or screenshot |

**Best practice:** Deliver BOTH. Markdown specs are the source of truth. HTML mockup is the visual sanity check & reference.

## Related skills

- `sketch` — for *exploration* and quick comparison mockups, not production delivery
- `claude-design` — for single *one-off* HTML pages, not complete systems
- `github-repo-management` — for repo setup and pushing
- `design-md` — for formal Google DESIGN.md token specs (different format, more rigid)

---

**Version:** 1.0  
**Last updated:** August 26, 2024

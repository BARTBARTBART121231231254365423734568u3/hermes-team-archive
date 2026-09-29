---
name: bitewise-mobile-design-preferences
description: "Use when designing BiteWise mobile pages. Apply UI rules."
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  class: design
  tags: [bitewise, mobile, responsive, iphone, visual]
---

# BiteWise Mobile Design Preferences

## Visual references are strict

Treat Thomas's screenshots as the acceptance specification. Render at the exact target phone viewport with representative populated data and inspect the image visually; root `scrollWidth` or passing geometry alone does not prove the design is correct. When Thomas narrows or reorders the composition, encode that order as DOM assertions before styling so a later implementation cannot satisfy dimensions while retaining the rejected hierarchy.

## Diary mobile hierarchy

For the BiteWise Diary phone page, use this order:

1. Date and History controls.
2. Compact streak pill.
3. Large, unboxed calories-remaining focal value with goal copy.
4. Calorie progress bar.
5. Carbs, Fat, and Protein as three distinct adjacent compact columns. Each column retains a data-driven gram amount and label, with a dot immediately before the amount: blue for Carbs, orange for Fat, green for Protein. Do not flatten the columns into one sentence-like inline row.
6. A thinner blue hydration progress bar in the same summary column directly beneath the green calorie-goal bar. Do not add a separate water button in this summary.
7. Today's Nudge.
8. Today's meals, including a Drinks/Liquids section styled and behaving like Breakfast, Lunch, Dinner, and Snacks (heading, total, collapse state, rows, and add action). Drinks is the only phone interaction for adding hydration; logged volume must drive the blue bar, and edit/delete must recalculate it without double-counting.

Keep the calorie presentation visually prominent without restoring excessive vertical whitespace. Render the large data-driven remaining-calorie number as the focal point, with smaller copy underneath in the pattern `kcal remaining · goal 2,000`. On phones, do not replace the calorie hero with an Energy card, and do not replace the thin blue hydration bar with a large hydration card or separate quick-add controls. Clamp the bar visually at the configured water goal and test volume conversion, persistence, edit, delete, and duplicate prevention.

## Wellness mobile concepts

For a Fitbit/Google Health-centered Wellness redesign, build only from metrics that the connected device and granted scopes actually provide. Treat pending first load, failed load, absent, stale, off-wrist, and disconnected data as distinct states; never render unavailable values as zero or retain range/provenance copy after its request fails. Keep known-good values visible during a refresh, but show a distinct unavailable state when the active request fails. Show source and freshness alongside health data, remove integrations Thomas has ruled out, and use realistic seeded data so a preview demonstrates the populated phone experience.

When a reference such as WHOOP suggests recovery, strain, or sleep score cards, use its high-level information hierarchy only—one clear score, restrained progress ring, and concise label. Do not copy branding, proprietary naming, visual treatment, or proprietary ranges. For BiteWise Wellness, Thomas prefers one compact top summary card with three horizontally aligned, clickable circular scores in the order Sleep, Recovery, Activity, followed inside the same card by a clickable daily summary of what is going well and what most needs improvement. Keep this top area compact rather than a bulky overlay. Place steps, VO₂ max, resting heart rate, trends, and other available metrics below it. Label all BiteWise-computed scores as estimates and expose the available inputs: recovery needs sleep plus HRV or resting heart rate; activity load derives from activity, active-zone minutes, workouts, energy, and optional heart effort; sleep goal derives from sleep duration against the user-configured target. Render each score as unavailable when its required inputs are missing.

When Thomas asks for multiple design directions, make them structurally and interactionally distinct rather than changing only color, spacing, or decoration. Preserve only the explicitly shared hierarchy from his reference, and let the alternatives diverge substantially below it so he can make a meaningful choice.

For a design-only request, prioritize interactive iPhone concepts with populated, partial, stale, failed, loading, no-data, and disconnected states. Treat the page composition as a cross-state invariant: keep the same cards, charts, ordering, dimensions, and detail regions mounted in every state so switching sources or losing a connection never reflows the dashboard. In disconnected/no-data states, render `—` values and the real chart frames/axes with no plotted series; never hide the charts, inject fake zero points, or replace the page with a connection card. Put connection guidance inside the existing source/status region. Add a state switcher to the prototype and assert stable section order and card geometry across populated, partial, and disconnected states. Produce desktop variants only when Thomas asks for them; do not spend the delivery window on them by default. Obtain visual approval before app implementation, and preserve the frozen concept source independently of transient preview-server work.

When Thomas asks to populate the existing Wellness design, do not delegate a redesign or create an Apple-specific dashboard mockup. Freeze the existing hierarchy and route structure, specify only the source-to-existing-card mapping, and require target-width evidence that the new real data fits without changing the composition.

## Foods mobile information architecture

Do not make Foods a second Diary. The initial Foods screen must be an action-first gateway; today's logged foods, intake totals, and duplicated Diary summary cards belong in Diary and should not appear on Foods home. Put browsing and food rows behind a deliberate second screen.

When Thomas selects the **Launchpad** direction, preserve its deliberate interaction model rather than blending it with another concept: a meal selector and short introduction, a tall primary barcode action with stacked Photo and Quick-add actions, then a separate library doorway with Favorites and Recent shortcuts. Wire every action to the app's real scanner, add, serving, meal-selection, and logging paths; prototypes may demonstrate a flow, but production must not ship simulated recognition, fabricated counts, or prototype state controls.

Treat the library, detail, quick-add, barcode, and photo paths as the acceptance surface. At 390, 402, and 430 px, verify ordinary document scrolling reaches the final library row and actions above bottom navigation, no screen has horizontal overflow, and every estimate is labelled and reviewed before it is added.

### Browse filters and food confirmation

Keep the default Foods library calm: search plus a compact scope switch such as Recent, Favorites, and Meals. Move category, dietary/allergen, and provider/source controls behind one 44px Filters control that opens a bottom sheet, reports an active-filter count, and offers Clear all. Do not leave independent tab rows, allergen pills, source chips, and favorite/all-food controls competing above the results.

Make the scan and AI-photo endpoints converge on one portion-first Confirm & add flow. Put the amount choice before nutrition: offer validated named-serving chips and a stepper when the source supplies them, alongside direct Custom grams input. Always show the concrete mass for a named serving, for example `1 slice · 24 g`; never infer a slice weight when the source only supplies a 100 g basis or an unlabelled serving size.

Treat nutrition as a calculated readout in the standard confirmation flow, not four independently editable fields. Preserve a per-100 g or validated-serving calculation basis; changing the slice count or grams must immediately scale kcal, protein, carbs, and fat proportionally and label the displayed total with its current mass. Keep nutrition correction behind an explicit Edit nutrition data disclosure so a normal portion change cannot leave macros inconsistent.

Thomas values the satisfying confirmation/add animations; preserve their immediate feedback while refining portion UX. Support multiple measures, but never expose a universal generic unit picker by default: show only food-specific, verifiable measures with their exact mass (for example slice, piece, tbsp, or ml), provide Custom grams, and put other valid alternatives behind a compact Change measure panel. Fall back honestly to grams-only when no declared conversion exists; do not infer a serving mass.

Persist the verified-measure list and nutrition calculation basis with every saved food, not merely in confirmation-state memory. Verify the full create → reload → Recent/Favorites re-confirm → update → reload path against a real server, because an otherwise-correct serving UI silently degrades to grams-only if its conversion metadata is dropped at a route, schema, copy, or catalog boundary. Include a regression test that asserts the named measure and basis survive that round trip; reject invalid or non-positive measure mass at the server boundary.

Design explicit provenance states before implementation: a verified barcode record with a named serving, a record missing serving or nutrition data, and an AI estimate requiring confirmation. Show missing values as unavailable with the action needed, never as misleading zero macros. Prototype Browse → select/scan → change portion → live nutrition recalculation → meal choice → logged success with representative data, but do not claim actual scanner recognition or food-data coverage from prototype fixtures.

## Mobile preferences, language, and overflow verification

When adding English/Dutch support, use explicit reactive translation keys for framework-owned UI. Do not sweep/mutate rendered text nodes or cache their original text: reactive dynamic values, user content, portals, and route updates can otherwise be overwritten by stale copies. Store normalized locale state in the established settings/account lifecycle and verify reload, settings hydration, and account switching; English is the safe fallback for missing translation keys.

Run browser-level localization checks, not just source-pattern checks: exercise English → Dutch → English across authenticated navigation, forms, status text, labels, placeholders, and accessibility names while recording page errors. A build passing does not prove DOM translation is safe.

For mobile notification panels, prove bounds and focus behavior at 390, 402, and 430 px: anchor inside safe-area gutters, cap its height with internal scroll where necessary, restore trigger focus on Escape, and keep normal page scrolling usable. For Profile and Settings, prove the last security/control field is reachable via the intended document scroll with bottom-nav and safe-area clearance; visible overflow styles alone do not establish scroll ownership.

Avoid globally disabling browser zoom merely to hide a layout defect. Preserve input and accessibility zoom behavior, fix responsive sizing/root overflow first, and obtain real iPhone/PWA evidence whenever a gesture policy is changed.

## Bottom navigation and the iPhone gesture area

Treat the iPhone Home Indicator as system UI, not an app defect: a web/PWA app cannot permanently hide or control it. Do not promise to remove it, attempt browser-chrome/touch-event workarounds, or let it decide the navigation layout. Instead, make the app-owned bottom navigation extend through `env(safe-area-inset-bottom)` as one intentional glass surface, while reserving its full visual height plus the safe area exactly once for scrollable page content, sheets, toasts, and scanners. This removes an app-created empty band without obscuring content or fighting the system gesture region.

When replacing BiteWise’s compact hamburger shell, keep the desktop pinned sidebar unchanged and make every compact destination reachable without a drawer. Use a five-tab bottom nav for Diary, Foods, Stats, Wellness, and More; More is an accessible bottom sheet for secondary destinations such as Goals, Settings, Profile, and Sign out, not a renamed side drawer. Keep Notifications and Tweaks as top-right utilities. Use icons that visibly read as solid in the rendered phone evidence, not merely a `FILL` font setting whose chosen glyph still reads as an outline; differentiate the active tab with restrained glass-layer contrast and accent color, not a generic oversized pill. Make the glass visibly translucent in the actual render with layered tint, blur, and a restrained highlight—an almost-opaque dark surface does not satisfy a glass brief.

Run the checked-in bottom-navigation browser test itself after every route or safe-area change. Await and assert async route shells such as Wizard before reading layout metrics; a reviewer-only stabilized copy cannot substitute for a deterministic committed test. Test the compact nav at 390, 402, and 430 px with the normal page scroll, modal sheets, and a long Diary screen. Verify the nav is hidden only for intentionally immersive editor/wizard flows, all tab and More actions have 44px targets and keyboard/focus behavior, no horizontal overflow appears, and content reaches its final action above the nav. Simulated screenshots can verify layout but cannot prove iOS’s transient Home Indicator behavior; require physical installed-PWA evidence before claiming that system chrome looks consistent.

## Handoff and review workflow

1. Put every screenshot path, ordered hierarchy, behavior requirement, and explicit rejection in the implementation card; keep the body concise enough to survive transport.
2. When Thomas orders a numbered BiteWise backlog to start after active work, create one card per numbered outcome and make a strict parent chain from the active card through every item. Keep each card within its number’s scope; a premature adjacent-layout change defeats his requested priority order and causes overlapping mobile worktree edits.
3. Read every created card back before assuming the worker received it. If any requirement became a literal truncation marker, add the complete specification as a durable comment before work continues; incomplete card text causes visually plausible but wrong iterations. If scope was accidentally overstated, add an explicit superseding scope comment before the task can run and preserve the next item as its own card.
4. When Thomas corrects one detail, comment on both implementation and QA cards immediately, preserving what must stay unchanged. Treat terms such as “same as now, only smaller” as invariants rather than permission to redesign the surrounding component.
5. Require a seeded render and DOM/behavior assertions for content order, text containment, hydration calculations, and scroll ownership. Geometry-only tests can pass while the visible hierarchy remains wrong.
6. Check the actual provider and fallback availability before assigning review. If the preferred visual reviewer is quota-blocked, pin an available independent high-capability model rather than letting a stalled review consume the delivery window.
7. Treat auto-generated decomposition cards as untrusted routing artifacts: inspect their workspace, project, parent chain, and scope before allowing them to run. If they duplicate an active implementation/review or lack a valid project-linked workspace, block them and create at most one correctly scoped replacement; do not let parallel duplicate branches decide the same UI or data-state behavior.
8. Review the rendered output before publishing a preview, then obtain Thomas’s explicit visual approval before deployment.

## Responsive quality

- Apply the iOS safe area exactly once; avoid doubled blank space above the mobile top bar. In simulated screenshots without OS chrome, label the blank safe-area band rather than treating it as unexplained whitespace; on a physical iPhone it is occupied by status indicators.
- Align menu, page title, notification, and Tweaks controls vertically. Center the date navigation, History/search control, streak, and freeze state over the calorie summary when the mobile reference calls for that composition; keep the Diary greeting out of the compact-phone hierarchy unless the reference explicitly includes it.
- Keep interactive targets at least 44 CSS pixels while preserving compact information density.
- Verify text containment and component geometry, not only page-level overflow.
- Test 390, 402, and 430 px phone widths plus tablet and desktop.
- Reject clipped calorie or hydration values and unbalanced card grids.
- Preserve the desktop Diary right column with Hydration and Today's Nudge.
- On Foods mobile, use one continuous vertical page/document scroll for hero, intake, Nudge, library controls, filters, and results. The app top bar may stay sticky and filter chips may scroll horizontally, but remove fixed-height or nested vertical result panes because they create a visible seam and make the page feel split.
- Always give Thomas a verified working preview before deployment. Serve desktop and phone renders from the same build on one comparison page; request the exact page and image URLs over HTTP before sharing, keep the server alive until Thomas asks to close it, and refresh stable image names when a newer candidate replaces a rejected one. When he asks to close or remove previews, close every preview tab, stop the background HTTP process, delete only the copied preview directory/files, and verify deletion; never remove source, commits, or canonical test artifacts.
- Prefer current interactive previews with representative seeded/fake data—especially for Wellness—so Thomas can judge populated states without changing real account data. Clearly distinguish current seeded previews from old standalone mockups; never substitute an obsolete mockup when he asks for a newer populated preview.
- If a delegated visual reviewer is unavailable or exhausts quota after renders exist, the coordinator must inspect every required viewport with vision tools and record a pass/fail; do not requeue the same blocked provider or promote geometry-only results.

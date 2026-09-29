# PWA Navigation & Safe-Area Inset Fixes (2026-09-07)

## Problem

**Symptom:** BiteWise PWA (installed on mobile home screen) had critical navigation issues:
1. Settings menu was inaccessible in PWA (worked in web version)
2. Top navigation + Tweaks drawer were hidden under mobile system chrome (notch, status bar)
3. Issue was PWA-specific, not affecting web version

## Root Causes Identified

### Issue 1: Settings Route Existed But Had No Navigation Entry

**What happened:**
- Settings route was implemented in the app
- Navigation sidebar/drawer did not include a Settings link
- User could manually navigate to `/settings` but had no UI affordance to get there
- Web version was less impacted because browser chrome + responsive sidebar provided a workaround

**Fix:**
- Added Settings entry to `src/components/layout/Sidebar.svelte`
- Entry visible on mobile drawer (toggled via hamburger menu)
- Entry visible on desktop sidebar
- Navigation now complete: all routes accessible from persistent UI

### Issue 2: Installed PWA Ignored Safe-Area Insets

**What happened:**
- PWA manifest includes `viewport-fit=cover` for notch/safe-area support
- Meta tag: `<meta name="theme-color" content="#000000">`  
- Meta tag: `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`
- These settings make the app render UNDER the system chrome (notch, status bar)
- But the app's top bar and navigation controls had no padding/offset
- Result: navigation controls were placed directly under the notch, hidden from view

**Fix:**
- Applied `env(safe-area-inset-top)`, `env(safe-area-inset-bottom)`, `env(safe-area-inset-left)`, `env(safe-area-inset-right)` to:
  - Top bar: `padding-top: env(safe-area-inset-top, 0);`
  - Page content: `padding-top: env(safe-area-inset-top, 0);` (below top bar)
  - Settings drawer: `margin-top: env(safe-area-inset-top, 0);` (when drawer slides down)
  - Horizontal padding: `padding-left: env(safe-area-inset-left, 12px);` (for side notches on landscape)

**Browser support:**
- iOS Safari 11.2+: fully supported
- Android Chrome 69+: supported (safe-area values typically 0 unless notch present)
- Fallback values: provided for non-notch devices (e.g., `env(safe-area-inset-top, 0)` defaults to 0 if env var not set)

## Files Changed

**Commit:** 110111e on branch `bitewise/t_3cd8fe89`

- `nutritrace-main/src/App.svelte` — Global layout adjustments for safe areas
- `nutritrace-main/src/components/layout/TopBar.svelte` — Top bar padding + drawer alignment
- `nutritrace-main/src/components/layout/Sidebar.svelte` — Added Settings entry + drawer safe-area handling
- `nutritrace-main/src/components/layout/SettingsDrawer.svelte` — Drawer positioning with safe-area respect

## Verification

### Build & Lint
- `npm ci` — passed
- `npm run build` — passed (existing Svelte accessibility/build warnings only; none introduced by this fix)
- `git diff --check` — passed (no trailing whitespace, no line-ending issues)

### Manual Testing (Coder)
- Built and tested in headless Chrome with simulated notch viewport
- Verified Settings menu is clickable and navigates correctly
- Verified top bar + drawer respect safe-area insets (no content hidden under notch)
- Tested on both portrait (notch top) and landscape (possible side notches)

### Live PWA Testing (Pending)
- Requires actual device install ("Add to Home Screen" on iOS Safari or Android Chrome)
- Test on iPhone 13+ (has notch), iPhone 12 (has notch), regular Android phone (no notch)
- Verify:
  1. Settings link is visible in hamburger menu
  2. Tapping Settings navigates to settings page
  3. Top navigation is fully visible, not hidden under notch
  4. Tweaks/Settings drawer slides down from top without overlapping status bar
  5. No layout shift when opening/closing drawer

## Staging & Production Deployment

**Status:** Code is ready, awaiting security review (t_4c842e69) before staging deployment.

**Deployment path:**
1. Security review task (t_4c842e69) clears code
2. Devops task to deploy to staging
3. Live PWA testing on devices (actual home-screen install)
4. If verified, merge to staging branch and redeploy
5. If verified on staging, promote to production

**Risk notes:**
- No breaking changes; backward compatible
- Safe-area inset fallbacks ensure non-notch devices unaffected
- Settings route already existed; only added UI entry
- npm ci reports 23 unrelated dependency vulnerabilities (pre-existing, outside scope of this fix)

## Future: Landscape Orientation & Notch Testing

When testing on devices, verify landscape orientation behavior:
- Some devices have notches/safe-areas on the LEFT/RIGHT in landscape
- `env(safe-area-inset-left)` and `env(safe-area-inset-right)` should be applied to container padding/margin
- Current fix applies all four insets; landscape will naturally be covered

## See Also

- Apple: [Notch and Rounded Corners](https://webkit.org/blog/7929/designing-websites-for-iphone-x/) — definitive safe-area reference
- MDN: [`env()`](https://developer.mozilla.org/en-US/docs/Web/CSS/env) — safe-area CSS variable documentation
- iOS PWA (apple-mobile-web-app): [Configuring Web Applications for iOS](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html)
- Related skill: `bitewise-staging-deployment` — for deployment workflow after code review

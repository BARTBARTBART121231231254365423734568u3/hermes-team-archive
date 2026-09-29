# Mobile/PWA release verification

Use this after deployment metadata, the Git branch SHA, and production assets have been matched. It prevents declaring a responsive or PWA redesign complete based only on byte-identical bundles.

## Evidence chain

1. **Production provenance:** Record the exact `origin/main` SHA, Railway deployment ID/status, service ID, root directory, and public URL.
2. **Fresh document and asset fetch:** Verify `index.html`, the entry bundle, manifest, and service worker with no-cache requests. Content-hashed assets should match the expected build.
3. **Rendered mobile condition:** At the target phone width (for example 375px), validate the real route and UI state that should reveal the feature. Check viewport meta, CSS breakpoint, CSS specificity/order, safe-area spacing, and route/auth gates.
4. **PWA update lifecycle:** Confirm `index.html` and worker bootstrap are revalidated, the worker activates promptly (`skipWaiting`/`clientsClaim` only when safe), and the new precache lists the current shell assets. Do not equate an updated worker file with a newly rendered installed app.
5. **User-visible feature:** Confirm the intended mobile navigation/layout actually renders for the appropriate signed-in, non-editor route. If authenticated validation cannot be automated, state that gap plainly and arrange a safe test path rather than describing static bundle inspection as full UI verification.

## Installed iOS PWA navigation check

An installed iPhone PWA is a separate release surface from Android Chrome or browser-tab Safari. When a user reports that **Settings** or a mobile drawer is inaccessible, test this before blaming responsive layout or stale cache:

1. Confirm the Settings control is mounted and reachable in `display-mode: standalone`, not only in browser-tab navigation.
2. Check Apple-specific app metadata, viewport and safe-area insets, plus drawer stacking/overlay/pointer-event rules; a control can exist in the DOM but be hidden, clipped, or covered in standalone mode.
3. Compare the installed-PWA shell/worker update path against the normal Safari/desktop route, including the feature's authenticated mount state.
4. Treat a real iPhone report as evidence of a distinct iOS PWA navigation defect until this comparison disproves it. Do not ship CSS-only layout changes as a substitute for that check.

## Common false positives

- A successful Railway deployment proves an image started, not that a responsive feature renders.
- Matching live JavaScript/CSS hashes prove artifact provenance, not breakpoint, auth, route, or state behavior.
- Desktop inspection is not evidence of phone layout when CSS intentionally gates mobile components.
- A phone reporting an old shell must be treated as a product defect until route/auth/PWA update conditions are checked; do not dismiss it as cache without evidence.

## Safe response when production evidence conflicts with a real user report

1. Preserve the report as ground truth for the user-visible symptom.
2. Compare source mount conditions, route classification, auth timing, viewport CSS, and PWA lifecycle.
3. Reproduce at a mobile viewport where possible; never require a user to provide credentials just to debug the app.
4. Apply the smallest source/config fix and re-run the full evidence chain before calling it resolved.

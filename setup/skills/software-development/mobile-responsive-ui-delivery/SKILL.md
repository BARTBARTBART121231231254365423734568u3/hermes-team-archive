---
name: mobile-responsive-ui-delivery
description: "Use when delivering mobile UI from screenshots."
version: 1.0.0
---

# Mobile Responsive UI Delivery

## Procedure

1. **Treat device screenshots as strict specifications.** Identify content order, hierarchy, density, sticky regions, scroll ownership, safe areas, touch targets, and data-backed behavior before assigning implementation. Preserve the user's exact distinctions: moving, shrinking, or restyling a component is not equivalent to removing it.

2. **Write concise acceptance criteria without ellipses.** Put critical requirements in a short task body and repeat user corrections as durable task comments immediately. Before trusting a handoff, inspect the stored task body; literal truncation can silently remove requirements.

3. **Test behavior, not only page geometry.** A matching `scrollWidth` does not detect clipped text, awkward card wrapping, wrong DOM order, or a visually split page. Add assertions for bounding-box containment, DOM order, visible labels/values, one vertical scroll owner, safe-area application, and state changes. For navigation, execute the full promised journey—open the menu, activate the destination, assert the route and visible destination content, then test back/close behavior; checking that a label merely exists cannot prove its control works.

4. **Render the exact phone widths plus regressions.** Use 390, 402, and 430 CSS-pixel phone widths at DPR 3, with tablet and desktop checks at 768 and 1280. Simulate iOS safe areas only once; confirm the physical device's browser/status bar does not cause double top spacing.

**When adding fixed bottom navigation on iPhone**, treat the Home Indicator as OS-owned in Safari and installed PWAs: do not promise to hide, restyle, or force its auto-hide state. Use `viewport-fit=cover`, extend the nav background to the physical bottom edge, pad only its controls with `env(safe-area-inset-bottom)`, and reserve the nav-plus-safe-area height exactly once in page content. Verify the result on real-phone-like renders so the indicator sits over an intentional surface rather than an empty app band.

**Before approving a fixed bottom dock on a physical iPhone**, exercise both initial entry and the swipe/system-UI transition. Static 390/402/430 renders cannot expose a dock whose live `env(safe-area-inset-bottom)` changes and visibly jumps; record the capsule position and keep its visual geometry stable while controls remain outside the gesture region. If iOS reports a transient inset larger than the measured physical Home Indicator baseline, cap the dock-specific layout inset to that device-class baseline and apply the same capped value to the dock, page reserve, fade, and sheets; otherwise those layers drift apart.

**For an installed-iOS-PWA dock that is visibly high or partly unreachable, instrument before changing CSS.** Capture `screen.height`, `innerHeight`, `documentElement.clientHeight`, `visualViewport.height/offsetTop`, standalone flags, safe-area inset, the dock rectangle, tab-center hit tests, and route scroll range at bootstrap, settled launch, visibility return, pageshow, orientation, resize, and scroll. Do **not** infer that `screen.height > innerHeight` means the app shell should span the physical screen: `screen.height` can include an OS-owned region outside the usable app surface, and stretching the shell there strands controls below the hit-testable viewport, creates a black/blue band, and can eliminate route scrolling. Reproduce both physical and usable geometry, then choose the coordinate space that keeps the complete dock and all tab centers inside the visible layout/visual viewport while applying the safe area once; use the visual viewport while the keyboard is active. Gate any standalone-only workaround to iOS and exclude Capacitor. Never hardcode the observed pixel difference because device and orientation geometry varies.

**Validate the full rendered surface, not only element geometry.** Keep the actual browser render at physical-screen height while mocking the shortened iOS-reported viewport; then assert every dock control is visible, center-hit-testable, and clickable, More/sheet interactions work, and the route owns its own scroll. Capture uncropped full-surface screenshots including the region below the dock at 390, 402, and 430 widths across representative app, auth/setup, and offline surfaces; a selector screenshot can mask a clipped or unreachable dock.

**Separate browser-emulation limits from a confirmed device defect before multiplying repair lanes.** When physical installed-PWA geometry proves the symptom but Chromium cannot model its dual physical/usable viewport, use the device capture as the layout source of truth and keep the emulator for source-level invariants only. Before treating a newly failing emulator interaction as a regression, run the same interaction against the unmodified production baseline under the identical fixture; if both fail, fix the harness or classify the emulation limit instead of opening a second product-bug lane. After one candidate exposes a genuine interaction risk, stop serial broad screenshot/test expansions: state the remaining uncertainty, choose one narrowly scoped implementation path with explicit real-device acceptance, and do not create duplicate implementation/review chains for the same dock.

**Preserve the proven iOS swipe fallback when the physical bottom is not web-addressable.** Do not lock installed-iOS roots with `overflow: hidden` or `overscroll-behavior: none` merely to stabilize a dock; those locks can suppress the native settling gesture that reclaims the OS-owned lower region while leaving the visible band unchanged. First attempt one focused high-capability-model repair that keeps the dock on the true physical bottom. If iOS exposes no reliable geometry, restore root touch scrolling only for installed iOS, keep the dock fixed to the usable viewport, exclude desktop/browser/Capacitor surfaces, and deploy only with an immediate rollback SHA plus explicit physical-device acceptance. Browser tests should prove gesture eligibility, tab hit targets, route scrolling, keyboard isolation, and non-iOS isolation—but must not claim the OS band collapsed until the real phone confirms it.

**When replacing a compact hamburger**, audit every former drawer destination. Keep the primary routes in the tab bar and move secondary destinations into an accessible bottom sheet or another explicit route; test focus, Escape, sign-out, scanner/modals, and fixed overlays against the nav z-index.

**For subjective mobile-navigation redesigns**, explore three structurally distinct interactive directions before changing app code when the user rejects or has not approved the first visual treatment. After a direction is selected, refine its dock and surrounding surface in the prototype first; treat a working navigation shell as functional evidence, not visual approval.

**For a floating glass dock**, keep the capsule visually distinct while allowing the normal page surface to continue around and above it. Use only a soft progressive fade near the physical bottom/safe area; do not place the dock inside a large opaque or rounded dark tray unless that surrounding panel is explicitly requested.

5. **Visually inspect every key render.** Compare screenshots against the user's reference after automated tests pass. Reject oversized whitespace, clipped values, unintended `3+1` grids, missing secondary columns, nested vertical scrollers, and layouts that pass geometry while violating hierarchy. Label design-gallery content as representative placeholder data; do not call it a real-app preview. After a direction is selected, render the implementation through real app routes/data before seeking deployment approval.

6. **Test overlays and forms at the narrowest target width.** Anchor notification popovers inside the visual viewport and safe areas, give them bounded height with internal scrolling when necessary, and test close, Escape, focus, and touch behavior. Make long profile/settings forms one normal document scroll with bottom safe-area padding; never hide fields behind a fixed-height or nested-scroll shell.

7. **Stabilize iOS scaling without blocking accessibility.** Verify the viewport configuration and keep editable control text at least 16 CSS pixels so iOS does not focus-zoom fields. Fix the layout cause of accidental scale changes; do not add blanket touch-event blockers that break normal scrolling or assistive technology.

8. **Verify data linkage when UI is a progress indicator.** Exercise add, edit, delete, deduplication, unit conversion, and visual clamping. A bar that merely renders is not complete; its source records must update it correctly.

9. **Use focused independent review.** Give the reviewer the exact screenshots and risk areas. Do not repeat broad build loops after an exact commit already passed them; focus on the changed behavior and issue a prompt approve/request-changes verdict. For a narrow defect the user explicitly wants fixed, keep review proportionate: one implementation lane, one decisive comparison against the production baseline, and one release lane—do not turn a dock offset into a multi-surface redesign audit. If the user requests a stronger model for a difficult device-only geometry defect, pin only that implementation task to the requested model and preserve the ordinary team defaults elsewhere. If a review worker repeatedly crashes after the candidate already has complete focused evidence, recover the narrow review directly or create one correctly configured replacement; do not spawn duplicate implementation/review chains that re-audit unchanged work. If a provider is quota-limited, pin the replacement review directly to an available model rather than waiting for a fallback timeout.

10. **Publish a preview that actually opens.** For local Windows previews, serve a stable directory with `python -m http.server <port> --bind 127.0.0.1 --directory <dir>`, verify both HTML and assets return HTTP 200, then open that URL in the preview pane. Never claim a local-file or preview-store link works without opening it. Stop the server, close tabs, and remove temporary preview files when asked.

11. **Batch related approved changes.** Keep visual iteration local and present radically distinct concepts before implementation when information architecture is unresolved. Combine 3–5 related, approved changes into one reviewed release; reserve immediate deployments for urgent isolated defects.

12. **Deploy only after visual approval.** Preserve reviewed commit ancestry, run proportionate release checks, push, and verify the exact production revision plus live behavior. Report one consolidated result with commit, deployment ID, checks, and remaining risks.

## Common pitfalls

- Never infer a responsive fix from desktop scaling alone; real-phone safe areas and browser chrome change the result.
- Avoid nested vertical scrolling on mobile unless explicitly requested; it creates a visual seam and makes one page feel like two surfaces.
- Keep notification menus in the viewport at 390, 402, and 430 widths; desktop-sized absolute offsets push the menu offscreen even when its own dimensions look valid.
- Make long edit pages scroll as one document and reserve the bottom safe area exactly once; nested or height-locked containers conceal fields behind the viewport edge, while duplicate safe-area reservation creates the same ugly empty bottom band a fixed nav is meant to solve.
- Do not try to suppress the iPhone Home Indicator with touch-event, fullscreen, or viewport hacks; iOS owns it, and those workarounds are unreliable or damage gestures and accessibility.
- Do not let card components impose desktop wrappers on mobile hierarchy; render purpose-built mobile structure when the reference calls for unboxed content.
- Do not replace user-approved populated previews with unrelated legacy mockups; identify artifact age and provenance before showing them.

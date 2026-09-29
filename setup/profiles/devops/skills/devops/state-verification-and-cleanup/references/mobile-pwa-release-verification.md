# Mobile PWA Release Verification Checklist

**Purpose**: Verify that a mobile app or PWA redesign/feature release is actually rendering and working for end users, not just deployed to infrastructure.

**Session**: 2026-09-04 BiteWise massive mobile redesign deployment failure.

**Problem**: Deployment reported SUCCESS, assets verified, service-worker live, but production still rendered the old Diary/menu layout on the user's phone. Infrastructure gates all clear; user-facing experience 100% broken.

## Quick Render-Verification Flow (before claiming deployment done)

### Step 1: Verify the Live Production HTML Contains the Redesign

```bash
# Download the actual index.html being served
curl -s https://production-url.app/index.html > /tmp/prod-index.html

# Check for key redesign markers (component names, CSS classes, navigation structure)
grep -i "MobileNav\|BottomNav\|five-destination\|nav-tabs" /tmp/prod-index.html || echo "❌ NO REDESIGN FOUND"

# For a PWA:
grep -i "standalone\|manifest" /tmp/prod-index.html || echo "❌ NO PWA MARKERS FOUND"
```

### Step 2: Verify the Compiled JavaScript Bundle Contains the Redesign

```bash
# Find the app bundle filename (usually /assets/app-*.js)
APP_JS=$(curl -s https://production-url.app/ | grep -oP '(?<=src=")[^"]*app[^"]*\.js')

# Download it
curl -s "https://production-url.app/$APP_JS" > /tmp/app.js

# Check for the redesign component (use grep for key identifiers)
grep -i "MobileNav\|BottomNavigation\|navigate-diary\|navigate-stats" /tmp/app.js || echo "❌ COMPONENT NOT IN BUNDLE"
```

### Step 3: Test in the Exact Target Viewport (Desktop vs Mobile)

```bash
# FOR DESKTOP:
# 1. Open https://production-url.app in your desktop browser
# 2. Take a screenshot of the Diary page
# 3. Verify the expected layout (sidebar, menu, etc.)

# FOR MOBILE/PWA:
# 1. Open https://production-url.app in a mobile browser (or DevTools device toolbar)
# 2. At <=767px width, the mobile-first redesign should be visible
# 3. Screenshot the Diary page
# 4. Check for: five-destination bottom navigation, mobile-sized buttons, safe-area spacing
# 5. Reload once (PWA service-worker may need time to update; fresh load picks up new shell)

# FOR PWA INSTALLED (Home Screen app on iOS/Android):
# 1. Close the app completely
# 2. Open it again (or swipe to reopen)
# 3. First load may serve cached old shell; second load should pick up new shell
# 4. Screenshot both; if both show old layout: rebuild problem, not cache issue
```

### Step 4: Compare Source to Deployed

When production HTML doesn't match expectations:

```bash
# What does the source tree at the deployed commit say?
DEPLOYED_SHA="6acce67e6a4dfad279d183fa4955e14d89a83b6c"  # From deployment logs

# Check if the redesign component exists in source
git show $DEPLOYED_SHA:nutritrace-main/src/App.svelte | grep -i "MobileNav" || echo "❌ Component not in source"

# Check if it's being imported
git show $DEPLOYED_SHA:nutritrace-main/src/App.svelte | grep -i "import.*MobileNav" || echo "❌ Import not in source"

# Check if it's mounted (looks for actual component usage, not just import)
git show $DEPLOYED_SHA:nutritrace-main/src/App.svelte | grep -i "<MobileNav" || echo "❌ Component not mounted"
```

## Common False Positives (why a deployment can look "verified" but isn't)

| Symptom | Root Cause | Evidence Check | Fix |
|---------|-----------|--|---|
| Deployment SUCCESS, assets HTTP 200, but mobile shows old layout | Source integration incomplete (component never actually merged into release branch) | `git show deployed-SHA:src/App.svelte \| grep MobileNav` returns nothing | Re-integrate missing branch; rebuild + redeploy |
| HTML contains MobileNav but bundle doesn't | Build system cached/compiled stale JavaScript | Inspect bundle with grep; compare to source | Force clean rebuild: `git commit --allow-empty -m 'rebuild' && git push` |
| Bundle contains component but it doesn't render | CSS hides it (`display: none` or wrong breakpoint) or route-guard prevents mount (e.g., `/profile` intentionally excludes nav) | Open DevTools, inspect computed styles for nav element; check route in App.svelte | Fix CSS breakpoint logic or remove route exception |
| Works on desktop but not mobile | Viewport width triggers old CSS path (breakpoint mismatch between source and compiled) | Test at exact widths (375px, 767px, 800px) | Fix CSS media query breakpoints |
| Works in browser but not in installed PWA | Service-worker is caching old shell; PWA didn't receive update | Close and reopen app; wait 30+ seconds; reload once more | PWA update logic should handle this automatically; if not, it's a service-worker lifecycle bug. See rapid-code-deploy-cycle > Pitfall: PWA Shell Updates |
| Works after user clears cache but was broken before | User's browser/PWA cache was stale | This is expected transient behavior; document that users may need to reload/clear cache on first deploy | Add a service-worker version bump or clientsClaim logic to force immediate cache invalidation |

## Audit Sequence for "Deployed but User Sees Old Layout"

When a user reports the old layout despite deployment, run this in order:

1. **Ask for a screenshot** from their phone (not a description, not a guess — actual image)
2. **Ask what route they're on** (Diary, Foods, Stats, etc.) and if they're logged in
3. **Render-test the exact same route** on your side (logged in if needed; same viewport width if possible)
4. **Compare the two screenshots** side-by-side. Do they match?
   - If YES: the old layout is what's deployed (integration bug; go to Step 5)
   - If NO: the layouts differ; check if CSS/routing conditions are route-specific (e.g., Profile intentionally hides nav)
5. **Download production HTML + bundle** (Steps 1-2 above) and inspect for the redesign component
6. **Check the deployed commit SHA** from Railway logs; verify source at that SHA actually contains the component (`git show`)
7. **If component is in source but not in production**: build/cache mismatch; force clean rebuild
8. **If component is NOT in source**: source integration incomplete; re-integrate + rebuild

## Key Points

- **Deployment SUCCESS ≠ visual correctness**. Check the actual rendered output.
- **Don't ask users to debug**. You have curl, grep, DevTools. Use them.
- **"Clear your cache and reload" is a last resort**, not a first-line response. Cache should update automatically via service-worker.
- **Screenshots are evidence**. Get them from users, compare to your own render-test, use diff to spot CSS/layout issues.
- **Mobile-width ≤767px is critical for PWA redesigns**. Desktop at 1440px will look completely different (intentionally). Always test both.
- **Installed PWA (Home Screen app) is different from browser**. Users report "the app" — test both contexts (browser + installed).

## References

- `state-verification-and-cleanup` main skill — general verification principles
- `rapid-code-deploy-cycle` — deployment via git push + Railway auto-deploy

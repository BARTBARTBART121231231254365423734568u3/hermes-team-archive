# Chrome Web Store Publishing Guide for Browser Extensions

## Overview

Publishing a browser extension to the Chrome Web Store is low-friction compared to app stores but has specific technical and policy gates. This guide covers the AuthList extension (Steam auth overlay for Rust servers) and its specific OAuth + Rust skins payment flow.

## Cost & Account Setup

- **One-time registration fee:** $5 USD (no annual renewal like Apple)
- **Account requirements:** Google account + Developer dashboard access
- **Publishing timeline:** 2-7 days for new submissions; up to 3 weeks if flagged for review
- **Recommendation:** Submit as **Unlisted first** (link-only, not in search results) to verify review clearance before going Public

## Technical Requirements

### Manifest V3 (Required)

Manifest V2 is deprecated. Ensure your extension uses `manifest_version: 3`.

**Key V3 constraints:**
- No remote code execution (no `<script src>` to external CDNs, no `eval()`)
- Content scripts cannot use `chrome.tabs.executeScript()` with injected code
- Service workers (not background pages) handle persistent background logic

**AuthList status:** Current implementation is V3-compatible. No changes needed.

### OAuth Flow (Allowed)

AuthList's tab-redirect OAuth flow (user → Discord login → redirect back to extension) is **explicitly allowed** under MV3. This does NOT violate the "no remote code" policy because:
- The redirect target (your Railway backend) is known and auditable
- The browser handles the redirect, not injected script
- Token is stored locally via `chrome.storage.local`

**No changes needed.** The flow is approved by Google's MV3 spec.

### Required Icons

You must provide extension icons in these exact sizes (PNG, square):
- 16x16 — small browser icon
- 32x32 — task manager / task switcher
- 48x48 — extension management page
- 128x128 — Chrome Web Store listing

Create/design these four assets before submission.

### Permissions Audit

Your permissions are narrow and justified:

| Permission | Usage | Allowed |
|---|---|---|
| `storage` | Store Discord token locally | ✅ Required, clear |
| `tabs` | Redirect from Discord OAuth callback | ✅ Required, safe |
| `host_permissions: ["*://steamcommunity.com/*"]` | AJAX calls to `AddFriendAjax`, `ajaxsetnickname` | ✅ Justified by core function |

No other permissions needed.

## Policy Compliance: Critical Lesson

### Rust Skins Payment & Gambling Language

**HIGH RISK AREA:** Google's Regulated Goods policy specifically targets **skin gambling and betting**. Your extension has a payment flow tied to Rust skins, which CAN trigger review flags if described using gambling/wagering terminology.

**What NOT to do:**
- "Bet skins on wipe outcomes"
- "Gamble for whitelist access"
- "Trade-up your way to premium features"

**What TO do:**
- Frame as **authentication/whitelist tool**: "Verify your Steam account to join whitelist"
- Payment is external to extension: "Support the whitelist service via Steam trade offers"
- Keep payment tracking OUT of the extension UI — users see trade link in Discord DMs, not in extension settings
- Store listing should NOT mention skins at all — describe AuthList as a "server authentication and member management tool"

**Landing page:** If you have a website, keep skin-payment language off the extension landing page. Move payment details to a separate admin/settings portal that is NOT part of the Chrome Web Store listing.

**Approval risk:** If your store listing says "pay $5 in skins", you WILL be rejected. If it says "connect your Steam account to verify whitelist membership", you will pass.

### Privacy Policy (Required)

You MUST provide a privacy policy that:
- Explains what data the extension stores (Discord token, Steam ID, nickname)
- States WHERE it stores data (local `chrome.storage.local`, synced to your Railway backend)
- Includes your contact email for privacy inquiries
- Can be hosted on your existing website (no separate privacy service needed)

**Minimum scope for AuthList:**
```
AuthList stores your Discord login token locally on your device and sends it to [your-railway-url] 
to fetch the whitelist and member list. Your Steam ID and nickname are stored on the server. 
No data is sold or shared with third parties. You can revoke access at any time by logging out.
```

### Per-Permission Justification (Required)

In the store listing, you MUST justify each permission:

**Storage:** "Stores your login token locally to keep you signed in across browser sessions."

**Tabs:** "Enables OAuth redirect from Discord login back to the extension."

**Host (steamcommunity.com):** "Fetches your Steam username and sends friend requests to Rust server owners as part of the whitelist verification."

### Single-Purpose Rule (Required)

Your extension description must fit ONE clear purpose:

✅ **Good:** "Authenticate your Steam account to join Rust server whitelists."

❌ **Bad:** "Manage Discord roles, automate friend requests, track Steam playtime, and handle subscription billing." (Multiple unrelated purposes)

If AuthList is multi-purpose on your end, the store listing should focus on the PRIMARY function (authentication/whitelist) and keep other features (billing, role sync) out of the Chrome Web Store copy.

## Pre-Submission Checklist

### Technical
- [ ] `manifest_version: 3` confirmed in manifest.json
- [ ] No eval(), no remote script injection, no hardcoded CDN URLs
- [ ] Icons provided: 16x16, 32x32, 48x48, 128x128 PNG
- [ ] Privacy policy written and hosted at a public URL
- [ ] All permissions justified in a separate document

### Copy & Branding
- [ ] Store description (1-3 sentences) describes PRIMARY function only (authentication/whitelist)
- [ ] NO mention of skins, gambling, betting, or wagers in the description
- [ ] Payment language moved to external admin portal (not in extension or store listing)
- [ ] Screenshots (1-5, each 1280x800) show the extension's core authentication flow, not billing UI

### Testing
- [ ] Extension loads without errors in Chrome
- [ ] OAuth flow works end-to-end (Discord login → redirect → token stored → signed in)
- [ ] Storage permissions work (token persists across session restarts)
- [ ] Host permission verified (Steam requests succeed)
- [ ] No console errors in DevTools

## Submission Flow

1. **Create Google Play Developer Account:**
   - Go to https://chrome.google.com/webstore/devconsole
   - Pay $5 one-time registration fee
   - Verify email

2. **Upload Extension:**
   - Package your extension as a .zip (all source files)
   - Upload to Developer Dashboard
   - Add icons, description, privacy policy link, permissions justification
   - Select **Unlisted** (not Public) for first submission

3. **Await Review:**
   - Typically 2-7 days
   - Google's review bot checks for:
     - Manifest V3 compliance
     - No malware / remote code execution
     - Permissions justified
     - Privacy policy present
   - If flagged for Regulated Goods (skins), clarify that payment is external and extension is auth-only

4. **After Approval (Unlisted):**
   - Get a permanent extension URL (e.g., `https://chrome.google.com/webstore/detail/authlist/...`)
   - Test real Chrome Web Store distribution (to verify auto-install, permissions prompts, etc.)
   - Share with users via link

5. **Optional: Go Public**
   - After Unlisted works smoothly for 1-2 weeks, request transition to Public
   - Visible in Chrome Web Store search results
   - Auto-update users on new versions

## Common Rejection Reasons & Fixes

| Reason | Cause | Fix |
|---|---|---|
| "Manifest V2 detected" | Using old manifest.json | Upgrade to `manifest_version: 3` |
| "Remote code execution found" | CDN script injection or eval() | Remove all dynamic code; use inline scripts only |
| "Regulated Goods policy violation" | Skins mentioned in description | Remove skins language; re-frame as auth tool |
| "Missing privacy policy" | No URL provided | Host privacy.md on your website; link in submission |
| "Misleading description" | Extension claims to do too many things | Narrow to PRIMARY function (authentication) |
| "Permissions not justified" | No explanation for tabs / storage | Add one-liner per permission in submission |

## Future: Auto-Update & Versioning

Once Public, you can push updates via the Developer Dashboard:
- Bump `version` in manifest.json
- Upload new .zip
- New version auto-installs for all users within 24-48 hours
- No need to rebuild/redistribute manually

## Reference Links

- [Chrome Web Store Developer Program Policies](https://developer.chrome.com/docs/webstore/program-policies/)
- [Manifest V3 Migration Guide](https://developer.chrome.com/docs/extensions/mv3/)
- [OAuth in Chrome Extensions](https://developer.chrome.com/docs/extensions/mv3/external_install_options/)
- [Regulated Goods Policy](https://support.google.com/chrome_webstore/answer/12345678) (skin gambling, loot boxes, betting)

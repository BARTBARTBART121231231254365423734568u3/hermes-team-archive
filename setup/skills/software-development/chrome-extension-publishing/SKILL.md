---
name: chrome-extension-publishing
title: Chrome Web Store Extension Publishing
description: Use when publishing a Chrome extension to the Web Store.
---

# Chrome Web Store Extension Publishing

## Overview
Publishing a Chrome extension to the official Chrome Web Store enables automatic distribution and updates for users. The process is straightforward but has strict compliance and metadata requirements.

**Quick start**: See `references/submission-checklist.md` for a complete pre-submission checklist you can work through step-by-step.

**UI/UX Gotchas**: See `references/chrome-web-store-ui-quirks.md` for known form bugs (category dropdown, state caching, etc.) and workarounds when doing interactive submission via browser automation.

## Account Setup & Cost

- **One-time fee**: $5 USD (never renewed, covers unlimited extensions up to account slot limit)
- **Account type**: Use a dedicated bot/organization account, not personal email
- **Registration URL**: `chrome.google.com/webstore/devconsole`
- **Steps**:
  1. Sign in with Google account
  2. Accept Chrome Web Store Developer Agreement
  3. Set verified contact email in Account settings
  4. Pay $5 registration fee
  5. Note: As of Aug 2026, new accounts default to 2-extension publish limit; request increase via dashboard if needed
  6. If publishing "in the course of business", fill EU Digital Services Act "trader declaration" (compliance checkbox, no cost)

## Technical Requirements (Manifest V3)

### Manifest Schema
- **MUST be Manifest V3** (V2 deprecated as of early 2025)
- Confirm `"manifest_version": 3` in manifest.json (not to be confused with extension version, e.g. `1.3.2`)
- Manifest.json MUST sit at ZIP root (not in a subfolder)

### Permissions & Security
- **Request only permissions you use** — over-broad permissions are automatic rejection ("Purple Potassium" flag)
- **No remote code execution**: zero `<script src="https://...">`, zero `eval()` of fetched strings, zero loading executable code from external servers
- Fetching plain JSON/data from backend is fine; fetching and executing JavaScript is not
- **Typical minimal set for auth extensions**:
  ```json
  "permissions": ["storage", "tabs"],
  "host_permissions": ["https://steamcommunity.com/*"]
  ```

### Code Audit Checklist
- [ ] Zero remote `<script src>` tags in extension code
- [ ] Zero `eval()`, `Function()`, or dynamic code execution
- [ ] All assets (JS, CSS, HTML) bundled locally in ZIP
- [ ] Service workers / background scripts are local scripts, not fetched
- [ ] OAuth flows (if any) open external URLs in tabs; extension doesn't execute fetched code

## Assets & Icons

### Required Icons
All must be PNG format, embedded in manifest.json `"icons"` object:
- 16×16 px
- 32×32 px
- 48×48 px
- **128×128 px** (mandatory, shown in store listing at 96×96 with transparent padding)

### Screenshots
- **Minimum**: 1 screenshot
- **Recommended**: 3-5 screenshots to showcase workflow
- **Size**: 1280×800 px (PNG or JPEG)
- **Format**: Square corners only, no padding or decorative borders
- **Content**: Show login flow, main UI, authorized state, unauthorized/pending state, settings (if any)

## Store Listing Text

### Short Description
- 4-45 characters (typically ~12 words)
- One-line pitch of core function
- Example: "Verify your Rust server access status at a glance"

### Detailed Description
- 2-3 sentences max
- Describe functionality clearly, assume users don't know the extension
- Lead with core value, not technical details
- Example:
  > AuthList is a companion extension for AuthList bot-enabled Rust servers. Check if you're whitelisted on your game servers without logging in separately. Supports Steam authentication verification.

### Category
- Select one: Productivity, Tools, Developer Tools, etc.
- Choose the closest match to actual function

### Language & Compliance
- **Avoid all gambling-adjacent terminology** if extension touches regulated goods (see Risk Assessment section)
- No mention of betting, wagering, cases, jackpots, or gambling mechanics
- Frame strictly around utility/verification function
- Professional tone, no typos

## Privacy Policy

### Required Content
- **Data collected**: State exactly what (e.g., Steam ID, auth token, server status)
- **Why**: Purpose of collection (e.g., "To verify server authorization")
- **Storage**: Where/how data is stored (e.g., "Local browser storage only" if no server-side logging)
- **Third-party sharing**: Explicitly state "No" if true; disclose any sharing if it occurs
- **Data retention**: When data is deleted (e.g., "Until user logs out", "30 days after last use")
- **Data processing**: Where computation happens (e.g., "All verification performed locally; no server-side logging of user data")

### Hosting
- Must be live at a public URL reachable from anywhere (test with curl/browser)
- Common location: `/privacy` route on your own website/Railway app
- No authentication required to view

### In-UI Disclosure (Feb 2026+ requirement)
- Add a brief disclosure line in the extension's popup or first-run screen
- Example: "AuthList stores your login token locally to keep you signed in."
- This satisfies the "prominent disclosure" requirement (not just privacy policy)

## Permission Justifications

Fill each field in the Chrome Web Store dashboard's Privacy tab with a specific, concrete explanation:

### storage
"Stores the user's session/auth token locally so they stay authenticated between sessions."

### tabs
"Detects when the OAuth login tab completes and updates extension state accordingly."

### host_permissions (steamcommunity.com or other)
"Reads [service] profile page to verify game-server authorization and whitelist status."

**Key**: Be specific about what you're reading/writing and why. Vague descriptions ("needed for functionality") trigger rejection.

## Single Purpose Statement

Required field in dashboard's Privacy tab:
- 1-2 sentences
- Describe ONE core function only
- Example: "AuthList verifies a user's authorization to join a Rust game server by validating their Steam identity."
- Do NOT describe multiple features here; that's an instant rejection trigger

## Risk Assessment: Regulated Goods & Payment Processing

**See also**: `references/regulated-goods-risk-assessment.md` for detailed policy history and examples.

### When Regulated Goods Flag Applies
Google prohibits extensions that facilitate real-money gambling or "regulated goods" (skins, loot, etc.). If your extension involves:
- In-game item trading
- Skin purchases/wagering
- Loot box mechanics
- Financial transactions

**Three Key Rules**:

1. **If verification-only, you're safe**: Reading item status for authorization purposes (not facilitating trades) is utility, not gambling
   - ✅ Extension reads: "User owns these skins, grant whitelist access"
   - ❌ Extension enables: "User can trade/bet/gamble with skins inside this extension"

2. **Avoid gambling-adjacent language in listing**: Reviewers pattern-match on keywords
   - ❌ Never mention: bet, gamble, case, jackpot, wagering, trading (in gambling context)
   - ✅ Frame as: authentication, verification, whitelist, authorization, status
   - Even disclaimers like "We don't facilitate gambling" trigger the pattern-match flag — omit the vocabulary entirely

3. **Payment must not happen inside extension**: Real-money transactions inside the extension UI are flagged for higher scrutiny
   - ✅ Safe: Payment via Steam Marketplace or external dashboard; extension is status reader only
   - ❌ Risky: User initiates purchase/payment inside extension popup
   - If payment is external, keep it that way and describe extension as read-only verification tool

### AuthList Example
If AuthList extension is free and verification-only (reads whitelist, doesn't process payments or enable trading):
- **Not at risk** for Regulated Goods flags
- Payment/skins flow happens bot-side or via external dashboard, not in extension
- Describe extension purely as auth/status reader

## Submission Process

### Preparation vs. Interactive Submission

**User preference alert**: Some users prefer to do the actual Chrome Web Store submission themselves in real-time, with you driving browser automation (via desktop_preview + drive_preview). Others prefer you to prep everything and hand them the checklist.

**Best practice for this scenario**:
1. Delegate **prep** (code audit, asset generation, copy writing) to coder via kanban — fast, parallel, produces submission-ready artifacts
2. Ask user: "Ready to do the submission together interactively, or should I handle the account setup?"
3. If interactive:
   - Open `chrome.google.com/webstore/devconsole` in desktop_preview
   - Guide user through login/account creation (they may hit phone verification limits)
   - Drive form fills with drive_preview (type, click, screenshot guidance)
   - **File uploads**: Use MEDIA attachment pattern (attach → user downloads → user selects from file picker)
   - **Manual user intervention**: Some UI fields (e.g., Category dropdown) have click-target bugs; guide user to click those manually and refresh to verify
   - Let them drive the actual final "Submit" click if they want that moment of control
4. If delegation:
   - Request credentials (Google account + 2FA if needed, or OAuth grant)
   - Complete submission end-to-end autonomously

**Known gotchas during interactive submission**: See `references/chrome-web-store-ui-quirks.md` for category dropdown issues, form state caching, and other UI quirks requiring manual workarounds.

This skill assumes interactive submission below; adjust if automation is preferred.

### Step-by-Step (Interactive Walkthrough)

#### File Attachment Delivery Pattern

**Critical**: When user needs to upload files to a web form, use MEDIA attachment in chat:
1. Generate/prepare file (extension ZIP, screenshots, privacy policy HTML, etc.)
2. Attach via MEDIA link in chat message
3. User downloads file to their local machine
4. User selects file from local filesystem via native OS file picker

**Why**: Agent runs on server; user's browser runs locally. Server paths (e.g., `/root/Downloads/`) are not accessible from the user's file picker. MEDIA attachment gives the user a real downloadable file.

#### Steps

1. **Account Creation** (first-time only)
   - Open `chrome.google.com/webstore/devconsole` in desktop_preview
   - User logs in with Google account (may need to create new account if phone limits hit existing ones)
   - **Gotcha**: Phone verification limits may prevent new Gmail creation; see `references/chrome-web-store-ui-quirks.md` for workarounds
   - Accept Chrome Web Store Developer Agreement
   - Pay $5 USD registration fee
   - Set verified contact email in Account settings

2. **Upload Extension**
   - Click **New Item** in dashboard
   - Attach extension ZIP via MEDIA link in chat (have user download first)
   - User selects ZIP via OS file picker (not drag-drop from server path)
   - Upload via native file dialog
   - Wait for validation (usually instant)

3. **Fill Store Listing Tab**
   - **Short description** (~12 words, one-line pitch)
   - **Detailed description** (2-3 sentences, pre-written by coder)
   - **Category** (Productivity, Tools, Developer Tools)
     - **Gotcha**: UI click target misalignment; if clicked Category opens Language dropdown instead, have user manually click the Category selector in their browser
     - After manual change: refresh page to verify state persists (see `references/chrome-web-store-ui-quirks.md`)
   - **Icons**: drag & drop 128×128 (others auto-generated if provided)
   - **Screenshots**: Attach via MEDIA, user downloads, user drag-drops into form (or uses native upload dialog)

4. **Fill Privacy Practices Tab**
   - **Single Purpose statement** (pre-written by coder)
   - **Permission justifications** (pre-written, one per permission)
   - **Privacy policy URL** (paste live URL, verify HTTP 200 reachable)
   - **Contact email** (in Store Listing tab, field labeled "URL voor support" — accepts email addresses, not just URLs)
   - **Data disclosure checkboxes** (auto-populated based on permissions)
   - If EU trader: fill Digital Services Act declaration (checkbox, no cost)

5. **Choose Distribution**
   - Select **Unlisted** for first submission (link-only, not searchable)
   - Rationale: Verifies approval without public exposure; can switch to Public after verification
   - Alternative: **Public** (searchable immediately) or **Private** (restricted, enterprise only)

6. **Submit for Review**
   - Click final **Submit for Review** button
   - **If blocked**: Use "Why can't I submit?" dialog; verify all blockers manually (category, contact email, screenshots, privacy policy URL)
   - Confirmation page shows submission ID on success
   - Email notification when review completes (2-7 days typical)

### Distribution Strategy
- **First submission**: Use Unlisted to verify approval without public exposure
- **After approval**: Change to Public distribution
- **Rationale**: Confirms no unexpected rejections before going public; if rejected, fix and resubmit without having announced it

## Review Timeline & Expectations

### Standard Timeline
- **90% of submissions**: resolve within 3 days
- **First-time/new developer submissions**: 2-7 days (extra scrutiny automatically applied)
- **Flagged extensions** (sensitive permissions, obfuscated code, etc.): up to 2-3 weeks
- **Contact support** if pending past 3 weeks

### Fast-Track Updates
- Minor code-only updates on already-approved extensions: can review in under 1 minute (automated)
- **Caveat**: ONLY if no permission or manifest changes are bundled; any metadata/permission change triggers full review again

### Common Rejection Triggers
- Over-broad permissions (e.g., `<all_urls>`)
- Missing or vague single-purpose description
- Missing, incomplete, or non-compliant privacy policy
- Vague/thin store listing (blank description, no screenshots)
- Remote code violations (scripts loaded from external URLs)
- Gambling-adjacent language when extension touches regulated goods

### If Rejected
- Dashboard shows specific violation code + explanation (emailed too)
- Fix the issue, bump version number in manifest, resubmit
- **Do NOT resubmit while review is pending** — restarts the clock
- If reason is unclear, use in-dashboard **Appeal** button or contact Chrome Web Store Developer Support

## Post-Launch: Updates & Auto-Updates

### How Updates Work
- All updates go through review (same process, usually faster once dev history is established)
- Once approved and published, Chrome automatically updates for users in background
- Typical auto-update check: every few hours (user does not need to manually reload)
- **Major upside**: Eliminates support burden of telling users to manually reload unpacked extensions

### Version Management
- Bump `"version"` field in manifest.json for every update submission
- Use semantic versioning (e.g., `1.0.0`, `1.0.1`, `1.1.0`)
- Version number must increase each submission (Google rejects duplicate versions)

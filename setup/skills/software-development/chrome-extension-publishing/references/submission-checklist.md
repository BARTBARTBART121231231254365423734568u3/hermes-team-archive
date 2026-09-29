# Chrome Web Store Submission Checklist

## Pre-Submission (Code & Manifest)
- [ ] Confirm `manifest_version: 3` in manifest.json
- [ ] Permissions block contains ONLY:
  - `"permissions": ["storage", "tabs"]`
  - `"host_permissions": ["https://steamcommunity.com/*"]` (or domain-specific)
- [ ] Zero remote `<script src="https://...">` tags anywhere in codebase
- [ ] Zero `eval()`, `Function()`, or dynamic code execution
- [ ] All JS/CSS/HTML assets bundled locally in ZIP
- [ ] OAuth flows (if any) open tabs to external URL; extension doesn't execute fetched code
- [ ] ZIP built with manifest.json at root (not in subfolder)

## Icons (All 4 Required)
- [ ] 16x16 PNG
- [ ] 32x32 PNG
- [ ] 48x48 PNG
- [ ] 128x128 PNG (store listing icon)
- [ ] All embedded in manifest.json `"icons"` object
- [ ] 128x128 renders clearly when downscaled to 96x96 (16px transparent padding)

## Screenshots (Min 1, Max 5 Recommended)
- [ ] 1280x800px PNG or JPEG
- [ ] Square corners only, no padding
- [ ] Covers workflow:
  1. OAuth login flow
  2. Main popup UI after auth
  3. Authorized/whitelisted state
  4. Unauthorized/pending state
  5. Settings (if applicable)

## Store Listing Copy
- [ ] **Short description**: ~12 words, one-line pitch
  - Example: "Verify your Rust server access status at a glance"
- [ ] **Detailed description**: 2-3 sentences, clear value proposition
  - Example: "AuthList is a companion extension for AuthList bot-enabled Rust servers. Check if you're whitelisted on your game servers without logging in separately. Supports Steam authentication verification."
- [ ] **Category**: Select Productivity, Tools, or Developer Tools
- [ ] **Language check**: NO mentions of:
  - bet, gamble, case, jackpot, wagering, trading (gambling context)
  - Even disclaimers trigger pattern-match rejection; omit vocabulary entirely
- [ ] Professional tone, no typos

## Privacy Policy (Required)
- [ ] Live at public URL (e.g., `https://your-domain.com/privacy`)
- [ ] Reachable without authentication
- [ ] States:
  - [ ] What data collected (Steam ID, auth token, etc.)
  - [ ] Why ("To verify server authorization")
  - [ ] How stored ("Local browser storage only" if applicable)
  - [ ] Third-party sharing ("No" if not shared)
  - [ ] Data retention ("Until user logs out")
  - [ ] Processing location ("All performed locally")

## In-UI Disclosure (Feb 2026+ Policy)
- [ ] Brief disclosure in extension popup or first-run screen
  - Example: "AuthList stores your login token locally to keep you signed in."

## Permission Justifications (Dashboard Fields)
- [ ] **storage**: "Stores the user's session/auth token locally so they stay authenticated between sessions."
- [ ] **tabs**: "Detects when the OAuth login tab completes and updates extension state accordingly."
- [ ] **host_permissions** (steamcommunity.com): "Reads Steam profile page to verify game-server authorization and whitelist status."

**Key**: Be specific about what/why, not vague ("needed for functionality" triggers rejection).

## Single Purpose Statement (Dashboard Field)
- [ ] 1-2 sentences describing ONE function only
  - Example: "AuthList verifies a user's authorization to join a Rust game server by validating their Steam identity."
- [ ] No multiple features here; instant rejection trigger

## Regulated Goods Risk Assessment (If Applicable)
If extension touches in-game items, skins, or payment:
- [ ] Extension is verification-only (reads status, doesn't facilitate trades)
- [ ] No payment processing inside extension UI
- [ ] Payment (if any) via external service (Steam, dashboard) not in extension
- [ ] Store listing describes extension as auth/status reader, never gambling-adjacent
- [ ] Avoided keywords: bet, gamble, trade, case, jackpot, wagering

## Chrome Dev Account (One-Time)
- [ ] Google account created (dedicated bot account recommended)
- [ ] Registered at `chrome.google.com/webstore/devconsole`
- [ ] $5 registration fee paid
- [ ] Developer Agreement accepted
- [ ] Verified contact email set in Account settings
- [ ] If publishing "in course of business": EU trader declaration filled out

## Submission
- [ ] ZIP file built and ready
- [ ] All assets above ready
- [ ] Distribution set to **Unlisted** (for first submission; switch to Public after approval)
- [ ] Click **Submit for Review**
- [ ] Expect 2-7 days for first-time review

## After Submission
- [ ] Monitor dashboard for review status (email notification on completion)
- [ ] If rejected: dashboard shows specific error code + explanation
  - Fix the issue, bump `version` in manifest.json, resubmit
  - Do NOT resubmit while review pending (restarts clock)
  - If unclear, use in-dashboard Appeal or contact Chrome Web Store Developer Support
- [ ] If approved: test on Unlisted, then change to Public distribution

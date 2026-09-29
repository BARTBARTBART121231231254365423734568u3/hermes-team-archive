# Regulated Goods Risk Assessment for Chrome Web Store

**Trigger**: Use if your extension involves in-game items, skins, wagering, trading, loot, or payment processing.

## The Core Rule
Google prohibits extensions that **facilitate real-money gambling** or **regulated goods transactions**. Skins, loot boxes, and game items sit in a gray zone Google has actively targeted.

## Three Key Distinctions

### 1. Verification-Only = Safe; Facilitation = Risky

**SAFE** (Verification/Utility):
- Extension reads: "Does this Steam account own these skins?"
- Extension displays: "You are whitelisted on this server"
- Purpose: Server authorization, access control
- **Example**: AuthList extension checking if a user's Steam inventory meets whitelist requirements

**RISKY** (Facilitation of Trading/Gambling):
- Extension enables: "Trade these skins for rewards"
- Extension processes: Betting, case-opening, wagering
- Extension shows: Odds, jackpots, or gambling mechanics
- **Example**: An extension that lets users trade skins or open loot cases

### 2. Avoid Gambling-Adjacent Language in Store Listing

Google reviewers **pattern-match on keywords**. Even disclaimers trigger automatic flags.

**FORBIDDEN KEYWORDS** in store listing:
- bet, wager, gamble, game of chance
- case, loot, jackpot, odds
- trade (in gambling/skin context)
- payout, winnings, prize
- Any word implying risk/reward mechanics

**SAFE TERMINOLOGY**:
- authenticate, verify, authorize
- whitelist, access control, server approval
- status, inventory check
- application, verification tool
- authorization

**WRONG APPROACH**:
> "Use our extension to check your skins and **ensure you don't gamble**. We prevent betting and case-opening!"

This still contains the forbidden keywords; reviewers flag it immediately.

**CORRECT APPROACH**:
> "AuthList verifies your server access status. Check your whitelist and authorization in real-time."

Frame strictly around utility; never mention the forbidden domain at all.

### 3. Payment Processing Location Matters

**SAFE** (No Extension-Side Payment):
- User pays via Steam Marketplace or external dashboard outside the extension
- Extension is a read-only status viewer
- Extension has NO payment flow, checkout, or transaction UI
- Example: "Login → view status → if not whitelisted, go to dashboard to pay"

**RISKY** (Payment Inside Extension):
- User can initiate purchase/payment within extension popup
- Extension processes Steam trade confirmations or currency
- Extension has transaction UI, checkout, or payment buttons
- Flagged for "facilitating financial transactions in the browser"

**RULE**: If payment happens outside the extension (Steam, Dashboard, web app), keep it that way. Never move payment into the extension UI as a convenience feature; it invites higher scrutiny.

## AuthList Specific: Why It's Safe

AuthList extension is free and verification-only:
- ✅ Reads whitelist status from bot backend
- ✅ Displays authorization (whitelisted or not)
- ✅ NO payment processing in extension
- ✅ NO skins/items traded inside extension
- ✅ NO gambling mechanics (odds, loot, betting)
- ✅ Payment tracking (if any) happens bot-side or via external dashboard

**Risk level**: ZERO Regulated Goods flags

Stay safe by:
1. Describing extension purely as auth/status tool
2. Never mentioning skins, trades, or payment in store listing
3. Never processing money inside the extension
4. Keeping all payment flows external

## Policy History (Aug 2026 Update)
Google tightened Regulated Goods policies Feb-Aug 2026 specifically targeting:
- Skin trading extensions
- Loot box openers
- Gambling site companions
- Any extension with keywords (bet, case, jackpot, etc.) even in disclaimers

This is aggressive pattern-matching, not nuanced review. The safest approach: avoid the vocabulary entirely.

## If Your Extension Actually Involves Payment/Trading

If you need to handle actual transactions or item trades:
1. **Do NOT rely on Chrome Web Store for distribution**; it's too risky
2. Consider unpacked manual distribution or a custom app store
3. If you insist on Chrome Web Store, consult a lawyer first; Google's policies are strict and appeals are rarely granted
4. Budget for 2-3 week review with high rejection risk

For side-chain projects, the bar is simpler: if it's read-only auth + status, ship it to Chrome Web Store. If it moves money or enables trades, find another path.

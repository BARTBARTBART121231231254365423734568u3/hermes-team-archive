# Chrome Web Store Dashboard UI/UX Quirks & Workarounds

**Session date**: Sep 2026  
**Issue**: Interactive form submission encountered several UI inconsistencies that slowed navigation and state confirmation.

## Known Quirks

### 1. Category Dropdown Opens Language Menu Instead

**Symptom**: Clicking on "Categorie" / "CategorieGames" in the Store Listing tab opened the Language dropdown, not a category selector.

**Cause**: Likely nested/overlapping click targets or form re-rendering that rebinds element refs.

**Workaround**:
- Do NOT attempt to change category via UI automation (drive_preview click); it redirects to the wrong field
- **Manual only**: User must click the Category dropdown directly in their browser and select from the list
- Confirm the category change has saved by refreshing the page and re-reading the field
- **After change**: Reload the page to verify state persisted (category field should show new value)

### 2. Form State Not Immediately Reflected in Display

**Symptom**: After clicking "Save Draft" and confirming category was changed (e.g., Games → Tools), the page still displayed "Categorie: Games".

**Probable cause**: Page caching, lazy re-render, or the display label not updating even though the backend saved the value correctly.

**Verification**: 
- Click the "Save Draft" button (disabled state confirms save completed)
- Refresh the entire page (`F5` or browser refresh)
- Re-read the field to confirm the new value persists
- Do NOT assume UI display is correct until verified post-refresh

**Impact on submission**: Form submission validation checks the backend value, NOT the displayed value. Even if the UI shows "Games", the submission may proceed if the backend has "Tools" saved.

### 3. Support/Contact Email Not Obviously Labeled

**Symptom**: Submission blocked with error "contact email required", but no field explicitly labeled "Contact Email".

**Discovery**: The email field is the "URL voor support" (Support URL) input in the Store Listing tab.

**Behavior**: Field accepts both URLs and email addresses (just a text input, minimal validation)

**Solution**: 
- Fill "URL voor support" with contact email address (e.g., `contact@example.com`)
- Google does not distinguish between a support page URL and an email; both serve the same contact-info purpose

### 4. Tab Navigation Via URL vs. UI Clicks

**Symptom**: Clicking tab links (Status, Pakket, Winkelvermelding, Privacy, Distributie) via drive_preview sometimes failed to navigate or returned to the Store Listing tab regardless.

**Workaround**: 
- Use direct URL navigation (`desktop_preview` open with full tab URL)
- Example: 
  ```
  https://chrome.google.com/webstore/devconsole/{ID}/{APP_ID}/edit/privacy
  https://chrome.google.com/webstore/devconsole/{ID}/{APP_ID}/edit/package
  ```
- Direct navigation is more reliable than clicking UI links

## File Attachment Delivery in Web Forms

When the user is interacting with a web form and needs to upload files:
- **DO NOT**: attempt to place files in ~/Downloads or suggest drag-drop from server paths
- **DO**: attach files to chat via MEDIA: links so the user can download and use locally
- **Pattern**: Generate file → attach via MEDIA → user downloads → user uploads via native OS file picker

### Why This Matters
The agent runs on a server; the user's browser runs locally. File paths like `/root/Downloads/...` are not accessible from the user's local file picker dialog. MEDIA attachment solves this by giving the user a real downloadable file they can then select from their local filesystem.

## Submission Validation Blockers

Google's submission validation checks:
1. **Category**: Must not be empty or default (Games alone may be flagged)
2. **Contact email/URL**: Must be filled in the "URL voor support" field
3. **Privacy policy URL**: Must be live and reachable (HTTP 200)
4. **Extension package**: Must be a valid ZIP with manifest.json at root
5. **Store listing text**: Must have description (not just title)
6. **Screenshots**: At least 1 screenshot required

If submission is rejected with "Why can't I submit?", use that dialog (not always clear) AND verify each blocker above manually.

## Recommended Workflow for Interactive Submission

1. **Prep work** (coder agent):
   - Generate extension ZIP
   - Generate screenshots
   - Write store listing copy
   - Write privacy policy
   - Attach all to chat via MEDIA links

2. **User account setup**:
   - User creates Google account (or reuses existing)
   - User registers at `chrome.google.com/webstore/devconsole`
   - User pays $5 registration fee

3. **Interactive submission** (agent drives via desktop_preview + drive_preview):
   - Open devconsole in desktop_preview
   - Guide user through login
   - Click **New Item**
   - User downloads ZIP from MEDIA link
   - User uploads ZIP via native OS file picker
   - Agent fills Store Listing tab (description, screenshots, category)
   - Agent fills Privacy tab (policy URL, permission justifications)
   - **USER MUST MANUALLY** change category from Games if needed (UI click target issue)
   - Agent fills Support URL field with contact email
   - Agent clicks **Save Draft**
   - Agent clicks **Submit for Review**

4. **Verification**:
   - If blocked, use "Why can't I submit?" dialog and cross-check manual blockers
   - If stuck on category: have user manually change it, refresh page, verify persisted
   - If stuck on category after user manual change: reload page and retry submit

## Testing Hypothesis: Why UI Showed Stale Category Value

**Theory**: The category field may be cached client-side or re-rendered asynchronously. Google's MPA (Multi-Page App) or SPA (Single-Page App) architecture might queue the save but not update the displayed label until a full page refresh.

**Non-blocking implication**: Even if the UI display lag is real, the backend submission validator checks the actual saved value (not the display). So even if you see "Games" but the backend saved "Tools", submission should succeed.

**Safest practice**: Always refresh the page after Save to confirm state before attempting submit.

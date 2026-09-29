# Preview Artifact Verification Checklist

**Rule:** Before announcing a preview URL to the user, independently verify the artifact exists and is reachable. Broken links damage credibility.

## Verification Steps (in order)

1. **HTTP reachability test**
   ```bash
   curl -I https://preview-url/ 2>&1 | head -3
   # Expected: HTTP 200 or similar 2xx
   # Not expected: 404, 503, timeout, "connection refused"
   ```

2. **Content presence** (optional, but recommended for HTML)
   ```bash
   curl -s https://preview-url/ | wc -c
   # Should return a reasonable byte count (>1000 for a real page)
   ```

3. **Local file verification** (if the task provides a file path)
   - Check that the file exists and has expected size
   - Verify the publish script actually ran (check timestamps)

## Choose the correct preview lane

### In-app review (default)

Use Hermes Desktop's preview rail for the fastest, interactive review of a local HTML file, built-site directory, or localhost dev server.

1. Require the worker to hand off a durable absolute file path or localhost URL, plus the built output location; a screenshot alone is not an interactive preview.
2. In the initiating Desktop conversation, call `desktop_preview.open` with that path or URL. The preview rail belongs to that window, so a background worker cannot be assumed to have opened it for the user.
3. For a UI handoff, inventory controls with `drive_preview.elements`, then exercise the primary flows by reference. Report the controls actually tested.
4. Keep the preview rail as the immediate design-review surface. Do not label a `file://` or `localhost` preview as externally reachable.

### Remote/mobile review

Use a public HTTPS URL only after a static preview server and an authorized public route are both active.

1. Publish a built directory with a top-level `index.html` or a standalone HTML file to the preview store.
2. Confirm the publisher's configured base URL is public HTTPS. A publisher that falls back to `localhost` has copied the files but has **not** created a mobile-shareable link.
3. Fetch the exact returned URL through the public route, check the rendered HTML/assets, and copy the opaque identifier verbatim into the delivery message.
4. Preserve opaque, non-project-identifying URL paths; disable directory listings and traversal on the static server; retain the configured expiry/size cleanup policy.

## When to Report URL vs. File

- **Live URL:** Announce only if the exact public HTTPS URL passes reachability and content checks. If broken, report the evidence rather than presenting it as a link.
- **In-app path/localhost URL:** Open it in the user's Desktop preview rail and describe it as a local live review, not a share link.
- **File path:** Provide in the task artifact field only if verified to exist on disk.
- **Neither:** If the preview script failed or the URL is unreachable after verification, report the failure to the user with evidence (curl error, file not found), not silence.

## Pitfall

**"Designer is publishing a preview" ≠ "preview is live"**

The task completion message says "published a clickable prototype at <URL>," but that does NOT guarantee the URL works. Always test independently before forwarding to the user.

**Real incident (2026-09-04):**
- Designer completed redesign task, reported preview URL.
- Orchestrator announced URL to user without verification.
- User tried to click → HTTP 403 / URL broken.
- Lost credibility.

**Prevention:** Curl the URL before announcing it.

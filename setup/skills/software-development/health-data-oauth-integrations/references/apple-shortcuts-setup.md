# Apple Shortcut setup for health-data ingest

Use this only for a narrow, user-opt-in health ingest connection. Keep the app’s ordinary flow independent of the shortcut.

## Device-first validation sequence

1. On a real iPhone, make a harmless local shortcut before building a production endpoint.
2. Add a simple configurable parameter (for example, a Text action holding a test value). Do not use a real user credential during this check.
3. Open the shortcut editor’s **Details** control (the circled `i` in current iPhone UI). Use **Setup** or **Import Questions** to personalize that parameter. Apple places this outside the action search and the name/dropdown menu.
4. Share through an iCloud Shortcut link and install on a second iPhone. Confirm it asks the configured question and does not require the recipient to use a Mac.
5. Inspect the actual Health actions offered by that device/iOS and record only redacted structural facts: available metric names, result types, sleep-stage labels, and empty-value behavior.
6. Only after those results are known, freeze the payload contract and implement a per-user write-only ingest endpoint.

## Safety requirements

- Use a user-scoped, revocable write-only ingest credential. Do not let the shortcut read account data or carry a session cookie.
- Use idempotency keys and field-presence-aware merges. A repeated run may be harmless; a partial run must not replace existing values with `null` or `0`.
- Keep Apple-only measurements stored but undisplayed unless the product explicitly authorizes UI work.
- Share no health readings, token, iCloud shortcut URL, device name, Apple ID, or signed URL in support screenshots or task handoffs.

## Primary documentation

- [Add import questions to shared shortcuts on iPhone or iPad](https://support.apple.com/guide/shortcuts/add-import-questions-to-shared-shortcuts-apdf330fd3a0/ios)
- [Share shortcuts on iPhone or iPad](https://support.apple.com/guide/shortcuts/share-shortcuts-apdf01f8c054/ios)

---
name: live-preview-delivery
description: "Use when delivering live UI previews. Open and verify them."
version: 1.0.0
---

# Live preview delivery

## Procedure

1. Prefer Hermes Desktop's native preview rail for immediate review. Open a local HTML file, built site's `index.html`, or localhost dev-server URL in the initiating user's Desktop window; this is the fast, interactive default.
2. Verify the rendered UI, not merely the file: inventory interactive elements first, then exercise representative navigation, buttons, and form flows in the preview rail. Report only interactions actually performed.
3. When work comes from a separate designer/coder task, require its handoff to include the durable preview target: absolute HTML/build path or localhost URL, plus how it was built. The coordinator opens it in the user's current window because preview panes are session/window scoped.
4. For phone or external-browser review, publish only through a configured HTTPS route. Scope the public proxy to `/preview` rather than `/`, keeping health/status endpoints localhost-only. First verify the route configuration, then publish a smoke-test page, fetch the returned URL over HTTPS, and open the rendered page before sharing it.
5. On Thomas's Windows Hermes installation, publish through the normal on-demand command rather than manually starting preview infrastructure: `python ~/.hermes/scripts/create_preview.py <site-dir-or-html-file>`. It health-checks and starts/reuses the lightweight localhost server, verifies/re-establishes the authorized HTTPS tunnel after a reboot, and prints a URL only after readiness succeeds. Do not create a Windows login service or run a local model for preview delivery.

   Invocation facts that cost a cycle each if guessed:
   - Invoke it with `python`, not `python3`: on this Windows host `python3` resolves to the Microsoft Store alias stub and prints an install message instead of running anything.
   - The script takes exactly one positional path and has no flags; `--help` is parsed as the path and errors with `<cwd>/--help does not exist`.
   - Point it at a directory containing `index.html`. Publishing a bare directory of assets succeeds but warns, and the preview root then 404s — only exact filenames are reachable. Write a small `index.html` linking the artifacts before publishing a screenshot/asset folder.

6. Before declaring any preview tooling unavailable, locate it on disk (`find "$LOCALAPPDATA/hermes" -iname "create_preview*"`). Always-on context and migration notes can carry a stale "not carried over to this install" claim; the filesystem is the authority, and skipping this check pushes the session into inventing delivery workarounds for tooling that already works.

7. When the user reports a published URL does not work, triage the stack before republishing or switching delivery methods:
   - `curl -sS -m 5 http://127.0.0.1:8080/healthz` — expect `ok`.
   - `tailscale funnel status` — expect the host with `Funnel on` and `/preview proxy http://127.0.0.1:8080`.
   - `curl -sS -o /dev/null -w '%{http_code}' <full-url>` — read the status code only. curl exit 23 (`client returned ERROR on write`) is a local stdout-write artifact of the captured terminal, not a server failure; a printed `200` alongside it means the server served the asset correctly.
   If all three pass, the failure is client-side (browser, DNS, or the chat surface), not the preview stack. Ask for the exact observed symptom — blank page, error text, spinner, immediate failure — and fix from that, rather than generating another delivery format.
6. Use opaque, non-project-identifying preview IDs. Serve only the preview root and static assets; reject source-tree symlinks/reparse points, traversal, metadata files, malformed IDs, and directory listings. Validate every configured public base, including fallback configuration, as credential-free HTTPS with no query or fragment. Retain previews under the declared cleanup policy.
7. In the final handoff, provide either the verified native preview target or a verified clickable HTTPS URL, state what interaction was tested, and clearly label any remaining external-sharing limitation.

## Pitfalls

- Do not substitute screenshots for a live-preview request; screenshots cannot demonstrate interaction or responsive behavior.
- Stop after the second failed delivery attempt and ask for the concrete client-side error instead of trying a third format. Cycling through preview URL → inline image → copied file → base64 → prose description burns the user's patience without ever isolating the cause, and each new format can fail for a different reason than the last, so nothing is learned.
- When a worker-produced artifact must reach the user and the live URL is in doubt, have the producing task declare the file in `kanban_complete(artifacts=[<absolute paths>])`. That path uploads through the notifier as a real attachment; paths mentioned only in prose, `metadata`, or chat text do not. Ask for this in the task brief up front rather than hunting for the file afterward.
- Do not delegate a new card to solve a delivery problem you can probe directly in one or two commands. Health-check, funnel status, and an HTTP status code are faster than a dispatcher cycle, and a child worker cannot see the user's browser either.
- Do not claim a preview publisher creates a shareable link just because it prints a URL; verify that its configured base is externally reachable over HTTPS.
- Do not make designers or coders run server or tunnel commands before publishing; use the on-demand publisher and treat a readiness failure as the actionable infrastructure error.
- Do not assume a background worker can open the initiating user's preview rail; the pane belongs to the active Desktop window, so surface the target to the coordinator instead.
- Do not expose a local preview server publicly until static-file containment, no-listing behavior, source-link rejection, and path-scoped proxy routing are tested; preview trees may contain metadata or paths not intended for delivery.
- Do not treat a detached launcher as durable until its server PID and health endpoint still succeed from an independent process after the launcher exits; worker job teardown can otherwise silently turn public previews into gateway errors.
- Treat same-origin previews with active script content as an intentional tradeoff, not isolation: do not publish mutually untrusted pages on the shared preview origin without a sandboxing/isolation design.

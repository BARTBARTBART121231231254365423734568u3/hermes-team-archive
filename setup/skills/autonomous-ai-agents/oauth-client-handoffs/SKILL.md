---
name: oauth-client-handoffs
description: "Use when OAuth must return to an extension or app."
version: 1.0.0
---

# OAuth Client Handoffs

Use this skill when OAuth is launched from a browser extension, desktop application, CLI, mobile deep link, or another client that is distinct from the web dashboard. The deliverable is not simply a successful provider login: it is a secure, completed return to the originating client with the intended authenticated state.

## Required Flow Map

Before modifying code, identify and write down:

1. The client action that starts OAuth and the authorization URL it opens.
2. The registered provider `redirect_uri` and the backend callback route.
3. The contents and lifecycle of OAuth `state` (including nonce/CSRF protection, tenant, client origin, and expiry).
4. The final browser destination after callback.
5. The mechanism that hands success or failure back to the client: extension callback URL, `chrome.identity.launchWebAuthFlow`, deep link, postMessage bridge, custom URI, or intentionally documented browser UI.
6. How the client receives/reads the resulting token or session, and how it validates it.

Do not infer these from a dashboard flow. Dashboard OAuth and extension OAuth frequently share a provider callback but require different final handoffs.

## Implementation Rules

- Bind the callback target to validated, server-created state. Never honor an arbitrary caller-supplied return URL.
- Keep OAuth `state` opaque, signed or server-stored, single-use, time-limited, and bound to both the initiating client flow and tenant/account context.
- Allow only a strict allowlist of registered extension IDs, deep-link schemes, or callback origins.
- Do not put long-lived access tokens in query strings, browser history, logs, or an interstitial dashboard page.
- Handle popup/window closure, provider denial, expired state, and callback replay without silently authenticating the wrong client or tenant.
- Do not make an admin dashboard the default terminal destination for an extension-originated login unless that is explicitly documented as the product design.

## Verification Standard

Backend unit tests, a healthy service, and a successful provider callback are necessary but not sufficient. Verify the entire expected chain:

1. Initiate from the actual client action.
2. Complete provider authorization with a permitted account.
3. Confirm the backend validates state and resolves the intended tenant/guild/account.
4. Confirm the final URL/window is the expected client callback—not a generic dashboard.
5. Confirm the client receives the result and enables the originally requested operation.
6. Exercise a rejected/expired state case and verify it fails safely.

If real provider authorization cannot be automated because it requires an interactive personal session, verify all deterministic pieces with automated tests and state exactly which final interactive assertion remains unverified. Never report the flow as end-to-end verified based only on deployment health or a server log.

## Handoff to Coding Agents

Give the coding agent the client type, observed wrong destination, desired final client behavior, provider/callback URLs if known, and explicit security constraints. Require it to trace the initiating URL, state, callback handler, and client result transport before editing. Ask for changed files, tests, commit/deploy evidence, and the exact final redirect/callback behavior.

### Progress reporting

Separate implementation status from production status. A local commit and passing tests mean the fix is implemented, not live. If a worker is blocked on credentials, deployment, or a required interactive authorization, say that work is paused rather than claiming it is still flowing. Report the flow as complete only after the deployed callback has been verified to return control to the originating client.

For a compact regression checklist and common symptoms, see [references/client-callback-verification.md](references/client-callback-verification.md). For Google Health/Fitbit device onboarding, production-readiness checks, test-user setup, and device-free validation, use [references/google-health-oauth-readiness.md](references/google-health-oauth-readiness.md).

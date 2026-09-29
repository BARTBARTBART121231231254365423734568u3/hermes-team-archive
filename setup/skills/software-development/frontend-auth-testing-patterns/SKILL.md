---
title: Frontend Authentication and Registration Delivery
name: frontend-auth-testing-patterns
description: Use when shipping or testing browser authentication and account registration. Verify every auth state against the real server without weakening production controls.
version: 1.1
author: Hermes Agent
license: MIT
trigger: Use when implementing, reviewing, or deploying login, signup, registration, or session flows. Verify server-enforced authorization and live behavior before release.
metadata:
  hermes:
    tags: ["frontend", "authentication", "registration", "testing", "svelte"]
    related_skills: ["axum-rest-api-design", "requesting-code-review"]
---

# Frontend Authentication and Registration Delivery

## Procedure

1. **Map the server contract before touching the UI.** Inspect the authenticated status endpoint, registration endpoint, role assignment, bootstrap logic, configuration storage, and rate-limit middleware. Record whether registration is open, invite-only, or bootstrap-only.
2. **Choose explicit registration policy.** For an existing app, public registration must normally be a persisted admin-controlled setting. For an isolated staging review, an explicit environment switch may temporarily open signup only in that environment; make it default-deny, exact-value enabled, and never copy it to production. Keep bootstrap-admin and invitation paths separate from public signup.
3. **Enforce policy on the server, never in Svelte alone.** Read the registration setting server-side on every anonymous registration request. When public registration is open, set the created role to the ordinary user role in server code and ignore any client-supplied privilege fields.
4. **Implement the UI as a reflection of server truth.** Fetch registration availability from a public status endpoint. Show Create account only when allowed; when closed, explain the invite-only path without exposing account-existence information.
5. **Add a dedicated, bounded signup abuse control.** Apply an endpoint-specific per-IP registration limiter rather than sharing ambiguous login behavior. Evict expired entries, cap active buckets, and collapse missing, malformed, or overflow identities into a shared fallback bucket; otherwise rotating addresses can exhaust process memory. Make proxy trust explicit and default it off so direct callers cannot choose limiter keys through forwarded headers. Return a safe, generic error and avoid logging credentials or raw personal information.
6. **Test the full state matrix against a running server.** Cover bootstrap admin, open public signup, closed registration denial, client role-escalation attempt, unauthenticated settings mutation denial, admin setting update, rate limit, and session/login after signup. Use unique disposable data and never place test credentials in task reports.
7. **Build and independently review before release.** Run server tests, production build, and focused browser tests. A second reviewer must exercise the running service, not approve only from source or worker notes.
8. **Verify production after deployment.** Confirm exact deployed revision and provider success state, then verify root/health, public auth status, a normal public signup, and failed privilege escalation in the live service. Report only status and evidence, never secrets or user details.

## Rules and Pitfalls

- **Keep production authentication strict; never treat network errors, 5xx responses, or non-401 errors as successful authentication.** Permissive fallback turns an outage into an authorization bypass.
- **Make test bypasses isolated fixtures or test-only server configuration, never client-side fallback behavior compiled into a production bundle.** Browser code is user-controlled and cannot protect access policy.
- **Force public registrants to a server-selected least-privilege role.** A hidden field or an untrusted request body is not an authorization boundary.
- **Preserve first-admin bootstrap controls even when public registration is enabled.** Initialization and public account creation have different trust levels.
- **Expose `registration_open` from the same server policy that admits anonymous registration, and have the UI consume that field.** A server-only switch without a visible signup path strands legitimate users; a UI-only flag is not enforcement.
- **When temporarily opening staging signup, set the environment-scoped switch only after the reviewed code is deployed, set only the intended staging service/environment, and verify the live staging status before sharing its link.** An ambient CLI project link can target an unrelated service.
- **Use generic signup and login errors where detailed feedback would reveal whether an account exists.** Enumeration makes targeted abuse easier.
- **Verify live registration only after the deployment reports success and the deployed revision matches the reviewed revision.** A branch push or a green local build does not prove production behavior.
- **Do not claim registration is live from a UI flag or merged branch alone.** Confirm the live status endpoint and perform a controlled anonymous signup check.

## References

- `references/auth-resilience-patterns.md` — Session preservation rules during transient backend failures.
- `references/api-key-generation-workflow.md` — Safe handling of API credential issuance.
- `references/form-ux-hiding-system-wide-constants.md` — Keeping system-wide constants out of instance setup forms.

# Client OAuth callback verification checklist

## Symptom
A user starts login from a non-dashboard client (for example, a Chrome extension action) and, after provider login, is left on the ordinary web dashboard. This commonly means the callback or post-callback redirect was built for dashboard OAuth rather than the initiating client.

## Fast triage questions

- What exact URL does the client open?
- Is the client using its platform callback API (for Chrome, `chrome.identity.launchWebAuthFlow`) or just a normal browser tab?
- Which registered `redirect_uri` receives the provider callback?
- Does state identify the client flow and tenant, or only a generic web session?
- Does the callback select a final route based on validated state?
- How does the extension/app receive its completed result without exposing secrets in a URL?

## Minimum automated coverage

- State generated for client A cannot complete as dashboard/client B.
- State is single-use and expires.
- Callback rejects an unregistered extension ID/return scheme.
- Successful client state selects the client handoff, while successful dashboard state selects only the documented dashboard route.
- Tenant/account membership is resolved from the tenant configuration, not a process-global default.

## Completion language

Use: “Backend callback and deployment are verified; the final interactive client handoff still needs an authenticated browser-session run.”

Do not use: “OAuth is fixed end-to-end” when only health checks, unit tests, or callback logs have run.

# Google Health API v4 — provider notes

Starting checklist for Fitbit/Google device-data integrations. Re-verify every item against current official docs before building — deprecations move fast here.

- Current route is Google Health API v4 over Google OAuth 2.0. Fitbit Web API was deprecated (Sept 2026) and Google Fit REST is end-of-life — do not build on either.
- Create a Web Application OAuth client; register the exact production callback including path (https, no fragments); add test-user emails while unverified.
- Unverified apps are capped at ~100 test users with short-lived tokens; public scaling needs a security assessment (historically a few hundred to a few thousand USD/year).
- Regional availability and traffic pricing are not guaranteed by docs — prove with a live read-only trial before promising coverage.
- Scope strings are exact-match on Google's side: verify every scope against the official scopes table before coding it — a truncated owner screenshot is not a source. If Google answers `Error 400: invalid_scope`, its error page enumerates valid= vs invalid= scopes; use that list as ground truth instead of guessing. Known trap: `irm.readonly` is rejected; the documented irregular-rhythm scope is `irn.readonly`.
- Consent audience: owners without Google Workspace can only use External (Internal is disabled for them); Testing mode plus manually added test users is sufficient for trials.
- Prove the route with a one-click owner consent on staging and record the observed in-app success state as trial evidence.

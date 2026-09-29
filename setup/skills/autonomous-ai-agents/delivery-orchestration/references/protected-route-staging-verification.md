# Protected-route staging verification

Use this when a staging release is online but the affected UI requires an authenticated session.

## Two separate gates

1. **Release delivery:** exact remote SHA, target environment, deployment/build/start logs, and health endpoint are verified.
2. **User-flow QA:** an authenticated desktop and mobile session reaches the intended route and exercises a representative action.

Do not let the first gate stand in for the second. An unauthenticated shell, redirect, or default empty state only proves the app is reachable—not that the protected route or new UI is rendered.

## Handoff requirements

- Give the deployment worker the approved test-auth path or supported non-secret test account mechanism before the release run when the route is protected.
- Require the worker to record which viewport(s), route, identity state, and interaction were verified.
- If browser capability or authenticated access is unavailable, report deployment as verified but visual/interaction QA as explicitly unpassed. Do not fabricate screenshots or infer behavior from health checks.
- Keep the release card blocked only on the unpassed UI gate, with the exact missing capability/access named, so a later QA run can complete it without redeploying.

## Status wording

Use: “Staging deployment is verified at SHA X; authenticated live UI QA remains unpassed.”

Never use: “The feature is verified live” when only the deployment/health boundary has passed.

# Deployment Evidence Chain

Use this checklist for GitHub-triggered Railway deployments, especially in monorepos or when a handoff reports a commit SHA.

## Required evidence

1. **Remote Git truth** — compare local branch and `origin/<default-branch>`; use the remote SHA, not a remembered/local handoff SHA.
2. **Correct service truth** — identify the Railway project, service, environment, and service root directory. Check them explicitly before interacting with Railway.
3. **Deployment truth** — active Railway deployment reports the expected remote commit SHA and reaches `SUCCESS`/`RUNNING` or `Online`.
4. **Runtime truth** — health endpoint and targeted logs are healthy after that deployment.
5. **Behavior truth** — exercise the requested path. For a server behavior, use a focused request asserting the changed contract; for dashboard code, verify the deployed asset contains or hashes to the expected new build.

## Common false positives

- A local commit exists but was never pushed, was squashed, or a later equivalent commit was used.
- A Railway deployment is healthy but belongs to a different service in a monorepo.
- A generic health endpoint succeeds even though the changed endpoint/path still runs older code.
- A dashboard is online but serves a cached/older bundle.

## Handoff reporting

Report the verified remote commit SHA, Railway project/service, deployment ID/status, exact live check, and any discrepancy between the requested SHA and the real deployed SHA. Do not describe a queued Kanban card as active until it has actually been claimed and has a running attempt.

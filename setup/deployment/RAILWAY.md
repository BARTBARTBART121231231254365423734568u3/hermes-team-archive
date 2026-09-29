# Hermes Railway service

This repository deploys Hermes Agent with a supervised dashboard/gateway,
native Hermes authentication, persistent profiles/projects, and a shared task board.

Attach a volume at `/root/.hermes`, configure the public dashboard URL and native
authentication, and configure provider and messaging credentials in Hermes.
`DASHBOARD_PASSWORD` is not a login mechanism in this version.

The Dockerfile pins Hermes and selected CLI versions. Upstream updates require
a reviewed deployment; restarting does not pull a new release.

For this installation, the verified production target is recorded in
`deploy/production.json`. Do not upload another application's directory to this
service. Use source-controlled releases and verify the deployed commit and
`/api/health` application identity.

Read [README.md](README.md) and [OPERATIONS.md](OPERATIONS.md) for the current
architecture, team workflow, backup schedule, and recovery steps.

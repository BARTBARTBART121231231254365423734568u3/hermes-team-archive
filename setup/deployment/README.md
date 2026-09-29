# Hermes Agent on Railway

Deployment layer for Nous Research Hermes Agent, pinned to `v2026.8.31`.
Upstream application code is fetched during the Docker build. Local patches
fix cron secret hydration and multiplexed gateway startup warmup.

## Runtime

Railway HTTPS -> aiohttp ingress on `$PORT` (default 8080) -> dashboard on
`127.0.0.1:9119`. `/webhooks/*` goes to the gateway listener on port 8644.
Hermes native dashboard authentication owns login and WebSocket tickets;
configure `dashboard.public_url` and native authentication in Hermes config.
The old `DASHBOARD_PASSWORD` login wrapper is no longer used.

The ingress supervises both dashboard and gateway processes, restarts crashes
with backoff, and restarts the gateway after successful configuration writes.
`/api/health` returns application identity, build revision, process state and
dashboard reachability; it returns 503 if either process is down or the dashboard
is unavailable. It does not prove that every provider or messaging adapter works.
Railway restarts the container if its main process fails.

HTTP responses stream incrementally. WebSocket forwarding preserves credentials,
origin and negotiated protocol. Public `/preview/<id>` pages are sandboxed to an
opaque browser origin: scripts and forms work, but dashboard access and local
browser storage are blocked. Stateful previews should use a separate origin.

## Persistence and tools

Attach the existing volume at `/root/.hermes`. It contains profiles, configuration,
credentials, databases, memories, sessions, task workspaces, browser cache and
`projects/`. `/root/projects` is a symlink to that persistent directory.
Profile Git credential helpers and browser cache links are provisioned at boot
and when new profile homes appear. Existing unexpected directories are preserved
and reported, not silently deleted.

The image includes GitHub CLI, a guarded Railway CLI, Claude Code, agent-browser
and system Chromium. Agent identities and credentials remain managed by Hermes.
Profiles without an explicit browser backend use `browser.backend: off`, which
selects Hermes's built-in browser tools instead of downloading browser-use via uvx.
The shared GitHub login and root UID are not strong isolation between agents;
use separate project-scoped service credentials for that boundary.

## Deployment

The reviewed target is in `deploy/production.json`. In the release-operator profile:

```bash
railway deploy-verified deploy/production.json --commit <full-git-sha>
railway deploy-verified deploy/production.json --commit <full-git-sha> --apply
```

The guard checks the repository, remote branch commit, Railway project,
environment, service, and configured source. Raw uploads and unverified mutations
are blocked inside the agent container. Administrative setup and variable changes
use an external operator session. Do not bypass the guard using raw executables.
After deploying, verify the deployment commit and the real application behavior;
the branch can move between verification and Railway fetching the source.

No automatic upstream updates run on restart. Upgrade the pinned release and
review its patches in a dedicated change. Python dependencies remain resolved
from upstream at build time; the build is not a fully locked dependency snapshot.

## Team setup

`team/TEAM.md` defines the existing eight roles, the task contract and handoffs.
The explicit migration `python /opt/hermes-ops/apply_team.py --apply` first backs
up configurations/databases, then installs shorter role instructions, preserves
two global workers/one per profile, and updates deterministic maintenance jobs.
It is versioned and will not overwrite subsequent edits on every restart.

Maintenance jobs write local reports; they do not add cross-channel messages:

- Hourly at minute 7: `ops/team-status.json`, without an LLM call.
- Hourly at minute 17: at most one eligible transient-task retry, with cooldown
  and a maximum of two automatic attempts per task.
- Daily at 03:37 in the configured cron timezone: validated SQLite/config snapshots,
  retaining seven local archives. Full-volume daily/weekly backups are configured
  separately in Railway.

See [OPERATIONS.md](OPERATIONS.md) for verification, backup and recovery.

## Validation

```bash
python -m unittest discover -s tests -v
bash -n entrypoint.sh
```

Linux CI covers authenticated WebSocket forwarding, streaming, cookie handling,
readiness failures, preview path containment, crash recovery, retry policy and
deployment target validation. CI also checks both patches against the pinned tag.

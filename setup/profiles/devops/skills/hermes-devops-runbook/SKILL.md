---
name: hermes-devops-runbook
description: "Use when Hermes workers fail before or during an agent turn."
---

# Hermes worker infrastructure troubleshooting

Symptom: a kanban-dispatched worker (or any process run via `bash -l`)
hits `hermes: command not found`, or finds a stale/system `python3` that
lacks `yaml`/`dotenv` when it tries an absolute path like
`/opt/hermes-agent/hermes`.

## Root cause (confirmed 2026-09-01, task t_4e5c6162)

Debian's default `/etc/profile` does an UNCONDITIONAL `PATH=` reset for
root:

    if [ "$(id -u)" -eq 0 ]; then
      PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    fi

This is a full overwrite, not an append. Hermes's terminal tool
(`tools/environments/base.py BaseEnvironment.init_session`) bootstraps
every fresh session by running a `bash -l` (login shell) to snapshot the
environment. Even though the PARENT hermes process has a correct PATH
(with `/opt/hermes-agent/venv/bin` prepended, confirmed via
`/proc/<pid>/environ`), the login-shell bootstrap sources `/etc/profile`
which wipes it back down to the bare system dirs before the snapshot is
captured. Every subsequent terminal command in that session then runs
with no venv bin dir and no `~/.local/bin` on PATH.

The `~/.local/bin/hermes` symlink from `hermes doctor --fix` does NOT fix
this — `~/.local/bin` itself gets wiped from PATH by the same reset, so
even a correct symlink there is unreachable.

## Fix applied

Append (not replace) to each profile's `~/.profile` — sourced by `bash -l`
AFTER `/etc/profile`, so it survives the reset:

    export PATH="/opt/hermes-agent/venv/bin:$HOME/.local/bin:$PATH"

Applied to `/root/.hermes/profiles/<profile>/home/.profile` for every
profile (devops, coder, security, researcher, scheduler, planner,
designer). New profiles need this added too — check
`/root/.hermes/profiles/<name>/home/.profile` exists and includes this
line when provisioning a profile.

## Verifying

Don't just inspect config — actually spawn a fresh worker and run a
terminal command through it, e.g.:

    /opt/hermes-agent/venv/bin/hermes -p <profile> --cli --accept-hooks \
      --toolsets terminal chat -q "Run terminal command: hermes project list"

Check the tool output shows `exit_code: 0` and normal project-list output,
not `command not found` (exit 127) or `ModuleNotFoundError`.

Note: an ALREADY-RUNNING session's cached snapshot
(`~/.hermes/profiles/<p>/cache/terminal/hermes-snap-*.sh`) is stale until
that session restarts — the fix only takes effect for NEW sessions/workers
spawned after `.profile` was patched.

# Kanban worker exits rc=0 before any agent turn

Symptom: a Kanban task is auto-blocked for a protocol violation such as
`worker exited cleanly (rc=0) without calling kanban_complete,
kanban_block, or kanban_request_review`, but the profile's `agent.log`
contains no `conversation turn:` for that worker session. Runs can last
about 60 seconds while plugins initialize and then exit, making this look
like a lifecycle bug.

Confirmed cause (2026-09-05, task `t_36a785d4`): the profile's only model
credential was persisted as exhausted after an upstream OpenAI-Codex HTTP
429 `usage_limit_reached`. Later worker startups logged:

    agent.credential_pool: credential pool: no available entries (all exhausted or empty)

The task agent never started, so the protocol-violation blocker was a
secondary symptom rather than worker misconduct.

## Diagnose

1. Inspect the affected profile's logs, not only the gateway log:

       /root/.hermes/profiles/<profile>/logs/agent.log
       /root/.hermes/profiles/<profile>/logs/errors.log

2. Find the first `marking ... exhausted` event and preserve the upstream
   status/message. For Codex, a real quota error includes `status=429`,
   `usage_limit_reached`, and usually `resets_at` / `resets_in_seconds`.
3. Confirm the failed child has plugin initialization and `no available
   entries` but no `conversation turn:`. Gateway rc=0/protocol output alone
   is not sufficient to identify the cause.
4. Check profile auth structurally without printing credential values:

       /opt/hermes-agent/venv/bin/hermes -p <profile> auth status openai-codex
       /opt/hermes-agent/venv/bin/hermes -p <profile> auth list

`logged in` only proves a credential exists; it does not prove the pool
entry is currently eligible or that upstream quota is available.

## Recover safely

Do not reset an exhausted marker before the upstream `resets_at` window;
that only causes another 429 and re-exhausts the entry. Once the reset time
has passed, clear the stale local status:

    /opt/hermes-agent/venv/bin/hermes -p <profile> auth reset openai-codex

Then run a fresh profile-scoped smoke test with inherited Kanban identity
removed so the diagnostic process cannot mutate the current board task:

    env -u HERMES_KANBAN_TASK -u HERMES_KANBAN_WORKSPACE \
      timeout 180 /opt/hermes-agent/venv/bin/hermes -p <profile> \
      --cli --accept-hooks --toolsets terminal chat \
      -q 'Reply exactly MODEL_OK and do not call tools.'

Verify actual model API calls or the exact response in `agent.log`; auth
status alone is insufficient. Next, unblock the affected cards through the
Kanban domain API and verify one newly dispatched worker reaches
`conversation turn:`, performs a tool call, and remains alive beyond the
previous failure window. Respect `kanban.max_in_progress` and
`kanban.max_in_progress_per_profile`; these caps exist specifically to
avoid overwhelming one profile's model quota during fan-out.

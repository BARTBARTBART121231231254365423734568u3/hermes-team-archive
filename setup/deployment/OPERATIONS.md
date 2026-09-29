# Operations and recovery

## Release checks

1. Run the regression suite on Linux and check the patches against the pinned tag.
2. Verify repository origin, production target manifest and exact intended commit.
3. Record the previous deployment ID and ensure the volume backup is current.
4. Deploy the GitHub source to the explicit project/environment/service. Never use
   an ambient working-directory upload to an existing GitHub-connected service.
5. Check Railway deployment metadata: commit and start command must match Hermes.
6. Check `/api/health`: `application=hermes-agent`, `status=ready`, expected revision.
7. Confirm a desktop connection reaches `Remote Hermes backend is ready`. An
   unauthenticated 401 is expected; a missing `/api/auth/ws-ticket` (404) is not.
8. Check gateway logs for startup errors and verify the needed provider/browser.

The guard inside the container prevents accidental CLI mutations; it does not
restrict root from bypassing it. Strong isolation requires separate scoped
Railway/GitHub credentials or a separate deployment service. Do not claim that
profile names or environment variables are a security boundary.

## Backups

Railway daily and weekly volume schedules are enabled for the existing Hermes
volume. A pre-team-change snapshot is named `before-team-improvements`.
Railway snapshots cover the volume but do not survive deletion of the volume.

`ops_snapshot.py` uses SQLite's backup API and checks each copied database. It
also copies profile configs, SOUL/AGENTS instructions, secrets and cron schedules
into a private archive. Archives contain credentials: do not attach them to chats,
commit them, or expose them through previews. Seven successful archives are retained
under `/root/.hermes/backups/ops`; older unrelated backups are untouched.
This is consistent per database, not an atomic transaction across all profiles.

For disaster recovery, restore a Railway snapshot through an external operator
session after confirming the exact volume and timestamp. Restoration may discard
newer state. For a profile-instruction rollback, extract the desired SOUL.md from
the archive into a temporary private directory, compare it, then replace only that
profile's file. Do not restore all databases just to revert an instruction change.

## Team migration

Run `python /opt/hermes-ops/apply_team.py` to inspect, then `--apply` once. The
marker `/root/.hermes/ops/2026-09-team-v1.json` records the backup and changes.
Stable profile IDs preserve existing channels and task references. The `security`
profile is the reviewer; there is no profile named `reviewer`.

The original long instructions are preserved in the pre-migration archive.
Existing conversations may retain older context; new turns/sessions pick up the
new role instructions according to Hermes's context caching behavior.

## Routine diagnosis

- Read `/root/.hermes/ops/team-status.json`; regenerate if stale with
  `python /root/.hermes/scripts/team_status.py`.
- Never automatically unblock `needs_input` or `capability` cards. Use evidence
  that the blocking condition changed before resuming them.
- 429 errors require quota/concurrency management, not repeated restarts. The
  worker limit is two globally, one per profile. This does not cap interactive
  chats or all provider usage across the account.
- Browser checks: `agent-browser --version`, then use an isolated browser session
  with a local static page and close it. Do not test against real OAuth consent.
- Missing project paths should be restored from the persistent projects directory
  or the correct GitHub source. Never substitute a similarly named repository.
- GitHub Actions also checks service identity/readiness and repeated ticket
  failures every 15 minutes, with three attempts to tolerate brief restarts.
  Failures appear in the `Hermes external health` workflow; GitHub notification
  delivery follows the account's existing settings. Scheduled Actions can be
  delayed and are monitoring, not a guaranteed real-time paging service.

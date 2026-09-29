# Profile-Local Cron vs. Central Dispatcher

## Architecture

**Central dispatcher** (`~/.hermes/cron/jobs.json`):
- Managed by the `cronjob()` tool
- Runs under the main Hermes gateway
- Has access to all platforms (Discord, Telegram, home channel, etc.)
- Supports delivery targets, attach_to_session, continuity, context_from
- Default path for new jobs

**Profile-local cron** (`~/.hermes/profiles/<profile>/cron/jobs.json`):
- Managed by editing the profile's jobs.json directly
- Only runs if that profile's cron daemon is active (rare)
- Isolated to that profile's context; cannot broadcast to other platforms
- Useful for profile-internal automation (e.g., researcher auto-saving findings)

## When One Fails

### Symptom: Job configured but never runs

**If in central** → Check dispatcher: `cronjob(action='list')`. If listed, verify the gateway is running: `ps aux | grep 'hermes gateway'`.

**If in profile-local** → The profile's cron daemon is not running. Either:
- Start it manually (rare), or
- Move the job to central via `cronjob(action='create')`

### Symptom: Delivery fails with "platform 'discord' not configured/enabled"

**Cause:** Profile-local jobs cannot access central platform config. The Discord gateway isn't available in the isolated profile context.

**Fix:** Recreate the job via `cronjob(action='create')` with the same prompt and `deliver='discord:...'`. The central dispatcher will handle delivery.

## Migration Path: Profile-Local → Central

1. **Read the profile-local job** from `~/.hermes/profiles/<profile>/cron/jobs.json`
2. **Extract:** name, prompt, schedule, deliver target
3. **Create centrally:**
   ```python
   cronjob(action='create',
           name=job['name'],
           prompt=job['prompt'],
           schedule=job['schedule']['expr'],
           deliver=job['deliver'])
   ```
4. **Optionally keep profile-local for reference** or delete it if no longer needed

No manual syncing to `~/.hermes/cron/jobs.json` — the tool handles all the details.

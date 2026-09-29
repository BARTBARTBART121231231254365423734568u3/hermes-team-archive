# Muse Code subscription in Hermes

## Decision table

| Path | Credential/billing | Powers Hermes directly? |
|---|---|---|
| Bundled `meta-ai` provider | Ordinary Meta Model API key; pay per token | Yes |
| `hermes-muse-code` plugin (`muse-code` provider) | Meta device-code login; Muse Code monthly subscription allowance | Yes |
| `muse exec` from a terminal/tool | Muse Code CLI login; monthly subscription allowance | No, delegated external job only |

Do not infer the billing path from the model name. `muse-spark-1.3` can be served through either the metered bundled provider or the subscription-backed plugin.

## Current setup workflow

1. Check `hermes --version`. The subscription plugin requires Hermes `>= 0.21.3`; update Hermes before installing when the local version is older. Treat the update as complete only after the updater exits, then rerun `hermes --version` before continuing. If post-update cleanup fails after reporting that code was updated, verify the installed version and CLI health first instead of blindly rerunning the whole update.
2. Install and enable the reviewed community plugin:

   ```powershell
   hermes plugins install TheStreamCode/hermes-muse-code --enable
   ```

3. Restart the gateway and verify the plugin is enabled before starting login:

   ```powershell
   hermes gateway restart
   hermes plugins list --plain --no-bundled
   ```

   The list must show `muse-code-subscription` as enabled. This separates installation/load failures from authentication failures and ensures long-lived processes see the new provider.

4. Run its explicit device-code login. On Windows PowerShell:

   ```powershell
   python "$env:HERMES_HOME\plugins\muse-code-subscription\muse_code_login.py"
   ```

   On a Linux/WSL Hermes home:

   ```bash
   python3 "$HERMES_HOME/plugins/muse-code-subscription/muse_code_login.py"
   ```

5. Keep the login process running while the user opens the printed Meta URL, enters the displayed code, and approves access. Device codes are temporary and are safe to relay; never request or print the resulting credential because the plugin caches it locally. Device codes expire within minutes: relay the URL and code immediately and ask for confirmation in the same turn. An expired code is dead — rerun the login for a fresh code instead of asking the user to retry the old one.
6. Confirm the login process exits successfully before claiming the subscription is linked. Then select **Muse Code (Subscription)** in the Hermes model picker, or test directly:

   ```bash
   hermes chat --provider muse-code --model muse-spark-1.3
   ```

7. Verify a harmless response succeeds and, when available, confirm allowance movement in the Meta account. Restart long-lived gateway/Desktop workers after login or credential rotation because they may retain provider state.

## Profile-wide fallback setup

Hermes profiles have isolated configuration, plugin installations, and `$HERMES_HOME` credential caches. Configuring the default profile does not configure specialist agents.

1. Enumerate the real profiles with `hermes profile list`; do not assume a fixed roster.
2. For every named profile, install and enable the plugin in that profile:

   ```bash
   hermes -p <profile> plugins install TheStreamCode/hermes-muse-code --enable
   ```

3. Make the authenticated cache available inside that profile’s `$HERMES_HOME` without printing its contents. Copy it with owner-only permissions when all profiles belong to the same trusted local user:

   ```bash
   install -m 600 ~/.hermes/muse-code-sub.json ~/.hermes/profiles/<profile>/muse-code-sub.json
   ```

   Prefer a fresh device login per profile when profiles represent different users or trust boundaries; never share the cache across users.
4. Resolve the exact tier before writing configuration. Muse Spark variants are distinct model IDs:
   - standard: `muse-spark-1.3`
   - contributor: `muse-spark-1.3-contributor`

   Do not translate words such as “high” into an unrelated Hermes reasoning-effort setting; when the user names the contributor tier, encode the contributor model ID directly.
5. Preserve the profile’s current primary model and set the selected Muse variant only as fallback. To make the contributor variant the sole fallback:

   ```bash
   hermes -p <profile> config set fallback_providers '[{"provider":"muse-code","model":"muse-spark-1.3-contributor"}]'
   ```

   Use `hermes config set ...` without `-p` for the default profile. This command replaces the chain. Inspect the existing chain first: replace it when the user explicitly wants one fallback, or merge when existing fallbacks must remain.
6. Restart the multiplex gateway once after all profiles are configured.
7. Verify both configuration and authentication for every profile. Run `hermes fallback list` (or `hermes -p <profile> fallback list`) and confirm the fallback count, exact model ID, and provider; this catches accidental duplicate standard/contributor entries. When the fallback is a contributor variant, also check `security.allow_data_training_tiers_noninteractive` per profile — a profile with the waiver off refuses that model at runtime even though the chain lists it. Then make one harmless direct request per profile with the same exact `--provider muse-code --model <selected-model-id>`. A listed fallback chain is not proof it fires: consent guards and credential loading only surface on a live request, so the per-profile live test is mandatory, not optional.

## Diagnosing a configured fallback that appears broken

1. Separate **chain selection**, **provider routing**, and **upstream response**. Check `hermes fallback list` for the exact provider/model, then inspect a failed run's effective `provider`, `model`, `base_url`, HTTP status, and whether failover was attempted or skipped. Check each affected profile separately; a configured main-chat chain does not prove an auxiliary call received one.
2. Before treating a 401 as expired Muse credentials, compare the request URL with the expected Muse endpoint `https://api.meta.ai/v1`. A Muse model sent to another provider's endpoint is a route/config mismatch; re-authentication does not fix it. A 401 produced on a profile's own primary path (e.g. the default profile failing on its non-Muse provider) is evidence about that path only — declare the Muse subscription expired only after the exact `--provider muse-code` probe fails. Inspect `model.provider`, `model.base_url`, and `model.api_mode` together. Hermes applies a configured `model.base_url` only when `model.provider` matches the provider being resolved; therefore inventory live profile configs and distinguish a Muse primary from a Muse fallback before changing other agents. For a Muse primary inheriting an old OpenAI/Codex URL, remove the stale override with `hermes -p <profile> config unset model.base_url` (do not hand-edit model config); retain only an API mode verified for the Muse plugin. Do not alter profiles whose primary is another provider merely because their fallback list contains Muse. Then verify the effective request URL and response with a harmless direct probe; also test fallback separately if fallback behavior itself is in scope.
3. Run one harmless exact-model direct probe with `hermes chat -Q -q 'Reply OK' --provider muse-code -m muse-spark-1.3-contributor -t safe --ignore-rules --max-turns 1 --run-budget 55` (adjust model to the configured variant). Confirm the resulting request reached the expected endpoint and produced a completed answer, not merely that authentication or stream setup succeeded. Contributor probes require prior informed data-use consent and the configured noninteractive guard; do not weaken it to run a test.
4. If the correct endpoint intermittently returns 5xx/timeouts, compare request sizes and durations and test a fresh small conversation. A successful small probe establishes current reachability, not reliability for long tool-heavy sessions; correlation with large histories is not proof of a specific upstream limit. Report routing bugs, transient upstream behavior, and auxiliary fallback propagation as distinct findings with separately verified fixes.

## Interpretation and cautions

- This is a reviewed community plugin, not a Meta-supplied Hermes integration. Say so plainly because Meta’s published wording may still describe the subscription credential as intended for Muse Code only.
- The plugin uses the monthly allowance and avoids a second pay-as-you-go API charge; it still consumes subscription quota.
- Hermes can use allowance faster than the stock Muse Code client because each turn can include system instructions, memory, skills, tool schemas, history, and repeated tool-call loops. Avoid promising a fixed number of Hermes prompts from the plan’s advertised limits.
- Standard and contributor model variants have different data-use terms. Prefer the standard non-contributor model for confidential repositories unless the user explicitly accepts training on prompts and completions. An unattended worker pinned to `muse-spark-1.3-contributor` can exit before any task work because Hermes refuses contributor data-training tiers without `security.allow_data_training_tiers_noninteractive: true`. Check the task log and run-linked routing event to distinguish that consent guard from a model/provider failure. Never enable the waiver merely because the user requested the contributor model; explain the training consequence and secure separate informed approval, or switch to the exact standard ID `muse-spark-1.3` with the user's agreement. Keep the task blocked while this decision is outstanding; do not interpret the crash as a review result.

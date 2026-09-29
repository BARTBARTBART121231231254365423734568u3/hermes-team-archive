---
name: codex-credential-pools
description: "Use when Codex rotation fails or managing Codex logins."
version: 1.0.0
---

# Codex Credential Pools

Hermes rotates between Codex subscriptions inside the `openai-codex` credential pool. `fallback_providers` is cross-provider only and never handles Codex-to-Codex rotation.

## Diagnose first: routing bug or empty pool

1. Run `hermes auth list` and read the `openai-codex` cooldowns per entry.
2. All entries exhausted means a quota problem, not a routing bug. Confirm in the logs: `marking <label> exhausted (status=429), rotating` followed by `no available entries` proves rotation worked but nothing healthy remained.
3. Only investigate routing when a healthy entry exists that was never tried.

## Labels lie: verify distinct accounts

Two pool entries can hold tokens for the same ChatGPT account after a repeated login. Rotating between them never escapes the shared limit.

- Decode each entry's access-token JWT and compare the `sub` and `https://api.openai.com/auth.chatgpt_account_id` claims, plus `last_refresh`. Identical values across entries means duplicates sharing one quota.
- Compare claim prefixes only; never print token material.
- Fix by removing the duplicate (`hermes auth remove openai-codex <label>`) and re-adding a genuinely different account.

## Tokens do not identify their owner

Codex access tokens carry no email claim and account-info endpoints reject them, so a pool entry cannot be mapped to an email address from the token alone.

- Assign owner-meaningful labels at creation (`--label <owner>`), one login per account.
- Before each device-code confirmation, tell the user which account must be active in the browser; a stale browser session silently links the wrong account.
- When ownership is already ambiguous, ask which login method (email+password vs Continue-with-Google) belongs to which address instead of guessing from token metadata.

## While the pool is dry: park dependent workers

When every entry is exhausted and the soonest reset is known, do not keep dispatching Codex-routed workers into the same wall — each attempt burns spawn budget and fails identically.

- Confirm the worker-side signature first: the task log tail shows `usage_limit_reached`/429 after retries followed by an immediate clean exit with no work claimed. A crash-loop with that signature is quota exhaustion, not a task defect — do not reroute, re-spec, or change models for it.
- Park looping tasks (transient block naming the reset as the resume condition) so the dispatcher stops respawning them; unblock after the reset instead of retrying into 429s.
- Spend the wait on quota-free verification you can do yourself: build-output assertions, static source checks, live curls of already-deployed services. Record findings on the card; leave the model-needing remainder to the resumed worker.

## Reconnect procedure

1. Start `hermes auth add openai-codex --label <owner> --no-browser` as a background process.
2. Poll its output, relay the device URL plus code (temporary codes are safe to relay), then end the turn; completion arrives as a notification.
3. Do one account at a time; device codes expire if left waiting.
4. After all logins, verify the entries have distinct account IDs, then `hermes gateway restart` so long-lived workers pick up the new pool state.

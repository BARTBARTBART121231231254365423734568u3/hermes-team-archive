---
name: subscription-backed-agent-integrations
description: "Use when connecting paid AI subscriptions to Hermes."
version: 1.1.0
---

# Subscription-Backed Agent Integrations

Use this skill when a user asks whether an AI coding subscription can power Hermes, be connected like another subscription, or be reused through an API-compatible provider.

## Required Procedure

1. **Split “connect” into distinct outcomes before answering.** Determine whether the user wants:
   - the subscription’s model to power Hermes conversations and workers directly;
   - Hermes to invoke the vendor’s authenticated CLI as a delegated coding agent; or
   - ordinary API access to the same model family, billed separately.

2. **Check the current vendor terms and authentication documentation.** Find explicit language covering where the subscription credential may be used, whether third-party clients are permitted, and whether separately created API keys use subscription allowance or usage-based billing. Treat the vendor’s current documentation as authoritative.

3. **Check every current Hermes integration surface before concluding that subscription reuse is unavailable.** Load the `hermes-agent` skill and inspect:
   - the installed native provider registry;
   - the current Hermes plugin catalog, especially model-provider and external-process plugins;
   - the upstream Hermes version/commits when the local installation predates a recently demonstrated integration; and
   - vendor CLI delegation only after native and plugin-backed providers are ruled out.

   Classify the result as a native/OAuth provider, reviewed model-provider plugin, API-key provider, custom endpoint, or external CLI delegation. A screenshot whose model picker labels a group “Subscription” is evidence of a direct provider/plugin path; identify the app and exact provider before dismissing it as CLI-only.

4. **Trace the billing path, not just model compatibility.** A model appearing in Hermes’s catalog proves protocol support, not entitlement. Verify which credential each path uses and which account receives the charge. For a subscription bridge, inspect its documented authentication flow and confirm whether it mints/uses an account-bound subscription key instead of an ordinary metered API key.

5. **Report the result as a small decision table.** For each supported path, state whether it consumes the user’s subscription allowance, whether it can power Hermes directly, and whether it incurs separate API charges. Lead with the practical answer rather than implementation detail.

6. **Only configure after the billing path, exact model tier, and data-use terms are clear.** Never ask the user to paste a credential into chat. Use the provider or plugin’s interactive/device-code login flow, then verify with a harmless request and the provider/account usage page when available. Preserve each agent’s existing primary model unless the user explicitly asks to replace it; when they say “fallback,” change only the fallback chain. Treat standard and contributor variants as distinct model IDs, never infer a reasoning-effort setting from tier language, and verify the final chain count so one requested fallback does not become two adjacent variants. If a contributor tier allows training on prompts/completions, distinguish the user's request to select that model from informed consent to enable unattended data-training access; obtain explicit consent naming the data-use consequence before changing a noninteractive safety waiver, especially for confidential repositories. If a worker crashes at startup, inspect its task log and exact routed model before retrying; a provider consent guard cannot be solved by repeating dispatch.

7. **State quota effects separately from billing.** “No extra API charge” does not mean “free of usage.” Explain that Hermes model calls consume the subscription allowance and may consume it faster than the vendor client because Hermes sends system instructions, skills, memory, tool schemas, history, and additional tool-loop turns. Do not claim exact prompt-to-token conversion when the subscription meter is opaque.

## Fallback vs Pool Rotation

- Same-provider multi-credential rotation (e.g. three openai-codex logins) is automatic via the credential pool (`mark_exhausted_and_rotate` on 429) and needs no `fallback_providers` entry. `fallback_providers` is cross-provider only (e.g. openai-codex primary → muse-code backup).
- A profile with no `fallback_providers` still rotates within its own provider pool; an empty fallback chain does not mean "no resilience". Do not add a cross-provider fallback to satisfy a same-provider rotation request without explicit consent.
- Diagnose "fallback not working" by separating the two layers: run `hermes -p <profile> auth list`, check per-credential cooldown status, then grep the profile agent log for `marking <label> exhausted (status=429), rotating` followed by `no available entries (all exhausted or empty)`. Rotation followed by empty pool means every credential is genuinely exhausted, not a routing bug.
- Verify every profile live, not just via config: `hermes fallback list` (or `hermes -p <profile> fallback list`) proves the chain entry exists; only one harmless direct request with the same exact `--provider <p> --model <m>` proves the profile can load the plugin and credential. A valid config entry alone does not prove authentication.
- When a standard and a contributor model variant exist, the contributor refusal in non-interactive runs (`security.allow_data_training_tiers_noninteractive`) looks like a fallback failure but is a consent guard. Distinguish it by running the exact fallback request directly and reading the refusal text before changing tiers or waivers.
- Count distinct accounts, not pool entries: two credentials can be separate logins to one subscription (same user identifier, same plan, same refresh moment), and rotation between them never frees quota. Verify distinctness by decoding each entry's access-token claims and comparing only the account/user identifier prefixes plus plan type — never print, relay, or persist tokens. Two labels sharing one identifier means one real reserve, not two.
- A vendor usage page showing remaining quota may belong to a different account than the exhausted Hermes credential. Compare the reset timestamp in the Hermes 429 error against the page's reset window before treating the pool cooldown as stale; mismatched windows mean different accounts, not a routing bug.
- To replace a duplicate pool entry with a genuinely different account, add the new login first (device-code flow, relaying only the temporary URL and code), have the account owner complete it on the intended account, then remove the duplicate label, re-verify distinct account identifiers, and restart the long-lived gateway so workers pick up the new credential set.
- Label each pool entry by account identity at creation (`--label <account>`), so the next exhaustion maps to the right inbox without decoding tokens.
- Before the owner confirms a device code, have them verify the browser is signed into the intended account — a stale session silently attaches the wrong subscription and recreates the duplicate being removed.
- A full disconnect-and-reconnect reset is clean only when every account can be re-logged immediately; until then, primaries on that provider fail (profiles without a cross-provider fallback go dark), so sequence each removal with its replacement login.

For the current Muse Code subscription bridge, read `references/muse-code.md`.

## Decision Rules

- A vendor CLI subscription can be integrated indirectly when Hermes launches the official CLI non-interactively, but this does not make that subscription the model provider for Hermes chat, memory, tools, cron jobs, or Kanban workers.
- A first-class Hermes provider that requires an API key is a separate API integration unless the vendor explicitly says the subscription covers third-party API requests.
- OAuth or browser sign-in support inside the vendor CLI does not imply that Hermes may reuse, extract, proxy, or impersonate that credential.
- If the vendor says a subscription credential is restricted to its own CLI, do not recommend manually extracting or copying credentials. Before concluding direct use is impossible, check whether a reviewed Hermes plugin provides an explicit device-code or account login and documents the resulting billing path; disclose when that bridge is community-maintained rather than vendor-official.
- When another assistant or a screenshot shows an integration is possible, treat it as a lead to verify against the current Hermes plugin catalog and upstream source. Do not reduce every subscription integration to CLI delegation merely because the bundled provider uses API keys.
- Keep bundled API providers and subscription plugins distinct in the answer: the same model family may appear under both while only the subscription-labeled provider consumes the flat-rate allowance.

## Verification Checklist

- [ ] The vendor’s current subscription terms were checked.
- [ ] Subscription credential and ordinary API key were treated as separate until proven otherwise.
- [ ] Hermes’s installed providers, current plugin catalog, and relevant upstream compatibility were checked.
- [ ] Multi-credential pool entries were verified as distinct accounts, not duplicate logins to one subscription.
- [ ] The answer distinguishes native API billing, direct subscription plugins, and external CLI delegation.
- [ ] Any separate pay-as-you-go billing is stated prominently.
- [ ] No credential or token is exposed in chat, logs, task cards, or durable notes.

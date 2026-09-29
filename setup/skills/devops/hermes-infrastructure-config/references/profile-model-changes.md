# Profile Model Changes: Intent, Model Choice, and Verification

Use this reference when users assign different provider subscriptions/models to Hermes specialist profiles.

## Interpret routing intent precisely

| User wording | Required routing result |
|---|---|
| "Claude-only" | Anthropic primary; remove all non-Anthropic fallbacks. |
| "ChatGPT-only" / "Codex-only" | `openai-codex` primary; remove all Anthropic/non-Codex fallbacks. |
| "Use X as a fallback" | Keep the primary unchanged; configure exactly the requested fallback provider/model and verify it is the only fallback if the user said "one" or "only". |
| "Move to model X" | Preserve fallbacks unless the user also states an exclusivity policy. Report the retained chain explicitly. |

Never infer that changing a primary model clears a fallback chain.

`hermes -p PROFILE fallback clear` prompts `Clear all entries? [y/N]` and cancels without a TTY — pipe confirmation in non-interactive runs: `printf 'y\n' | hermes -p PROFILE fallback clear`. A bare call reports `Cancelled` and leaves the chain intact, so always re-read `fallback list` after.

## GPT-5.6 family selection

In Hermes' catalog, the GPT-5.6 Codex family is role-tiered:

| Model | Tier | Best default roles |
|---|---|---|
| `gpt-5.6-sol` | Frontier | Dedicated coding and terminal-heavy infrastructure work; complex debugging. |
| `gpt-5.6-terra` | Balanced | General-purpose Codex work and resilient fallbacks. |
| `gpt-5.6-luna` | Fast/affordable | Routine, latency-sensitive operational work. |

A practical complementary fleet is: Claude Opus for visual/design judgment, Claude Sonnet for research/planning/security synthesis, Claude Haiku for simple coordination/scheduling, and GPT-5.6 Sol for coding/DevOps. This is a role-based starting point, not a replacement for an explicit user preference.

## Per-profile verification checklist

After a CLI-based change, confirm all of the following before reporting completion:

1. `config get model.provider` matches the intended provider.
2. `config get model.default` matches the canonical model ID.
3. `fallback list` has the exact expected entries (including none).
4. `auth status <provider>` shows the selected provider is usable.
5. `config check` passes.
6. Refresh or inspect the supported model catalog when the requested product name may not equal its canonical model ID.
7. Determine whether the profile gateway is running; only restart through a supported Hermes route when needed. A stopped gateway will load persisted configuration on next launch.

For a multi-agent request, present one final table only after every requested change has completed and been verified: **agent | primary provider | primary model | fallback**. Do not expose credential values.

## Idempotency

Before adding or replacing a fallback, inspect the existing persisted routing. If the requested state already exists, do not clear and recreate it; validate it and report an idempotent no-op instead.

## Profile default vs Kanban routing pin

Changing a profile default does not pin Kanban-routed workers — complexity routing still selects the tier model at spawn unless the task carries an explicit model/provider override. When the user says a profile should just run on one model, confirm whether they want the routing map pinned too or only the profile default.

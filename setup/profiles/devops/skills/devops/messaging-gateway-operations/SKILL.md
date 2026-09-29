---
name: messaging-gateway-operations
description: "Use when operating chat gateways. Verify real transport."
version: 1.0.0
metadata:
  hermes:
    tags: [messaging, gateway, discord, whatsapp, operations, verification]
    category: devops
---

# Messaging Gateway Operations

Configure and repair remote messaging control surfaces without confusing adapter health, reactions, or service state with a working conversation.

## Procedure

1. **Map the transport before changing it.** Identify the single credential owner, multiplexed profiles, configured allowlists, home channel, and the live service process. Keep one coordinator-facing bot identity per platform; specialists stay behind the coordinator and Kanban.
2. **Capture a real failing message.** Ask for one short message in the intended private conversation, then correlate its timestamp with gateway logs. A reaction or typing indicator proves only that the adapter observed the event; require evidence that authorization passed, an agent turn started, and a reply was delivered.
3. **Trace authorization in the runtime scope.** In multiplex mode, distinguish process-global environment, profile secret scope, platform `extra` configuration, and adapter-owned policy. Compare the observed sender/chat identity with the value read by the exact authorization layer, without printing tokens or private IDs.
4. **Write policy to the authoritative scope.** Preserve a private allowlist and disabled allow-all flags. When authorization uses profile-scoped secret reads, ensure the allowlist exists in that profile scope; a top-level compatibility key can look correct to the CLI while remaining invisible to the live gate. Keep the canonical platform configuration in sync so setup/status commands also report truth.
5. **Reload once after the cause is fixed.** Do not restart repeatedly while testing hypotheses. Restart only after configuration readback or a regression test proves the authoritative input is correct.
6. **Verify both directions separately.** Confirm a real inbound message is accepted, the agent uses live task/system state, and the outbound reply appears in the same intended conversation. Service health, a websocket connection, slash-command synchronization, or an outbound test message alone is insufficient.
7. **Separate chat from operations noise.** Use a dedicated home/updates channel for gateway starting, restarting, shutdown, and online notices. Keep the conversational channel for user requests and agent answers. If the runtime also notifies active sessions, add a focused routing rule: when Discord has a distinct home channel, send lifecycle notices only there; preserve active-chat fallback when no home exists and deduplicate when both targets are the same.
8. **Run interactive pairing on the surface the user requested.** For WhatsApp linked-device setup, prefer the Hermes dashboard’s Messaging → WhatsApp onboarding flow when Thomas asks to see the QR in the dashboard; it exposes the native onboarding API and renders the QR for scanning. Do not substitute the gateway listener root or leave a terminal pairing process running behind a dashboard flow. If terminal pairing was already started, terminate it before starting dashboard onboarding so only one session owns the QR. Inspect the rendered login page before giving sign-in advice: a dashboard basic-auth form expects its configured username/password, not an email identity. Read back and provide only the non-secret username; if the password is unknown, offer a supported reset rather than guessing, exposing stored credentials, or repeatedly attempting login.
9. **Gate only the irreducible human action.** Agents may select the agreed bot/self-chat mode and prepare the Thomas-only allowlist, but Thomas must choose/provide the real account and scan the linked-device QR. Explain that boundary before launching an interactive command; never surprise him with a prompt or ask him to paste a phone number into an ordinary shell where it can execute as a command.
10. **Verify external writes by readback.** After creating a channel, changing routing, posting a test notice, or deleting/moving bot-owned messages, fetch the exact channel/config target and assert the resulting name, parent, content, and absence/presence conditions.
11. **Report only the finished product.** For Thomas, suppress narrated diagnostics and intermediate attempts. Return a short final statement naming what now works and where messages will appear; surface only a blocker that requires his action.

## Diagnostic decision points

- **Reaction but no reply:** inspect authorization logs first; do not blame the model or response channel until an agent turn is proven.
- **Typing forever:** correlate with the gateway log and running turn. Typing can start before central authorization or survive a failed turn, so it is not acceptance evidence.
- **CLI says allowed but runtime rejects:** inspect multiplex profile scope and platform adapter configuration; do not keep rewriting the same top-level key.
- **Discord slash sync is rate-limited:** treat it as a separate control-plane condition. Verify ordinary message transport independently, and disable unnecessary resync only through the supported policy when existing commands need not change.
- **Lifecycle notice appears in chat:** setting a home channel may route startup messages but not active-session shutdown notices. Verify both paths with a focused test and a real planned restart.
- **Dashboard URL shows Not Found:** the gateway listener is not the web dashboard. Start or locate the Hermes dashboard and open its actual dashboard port, then use Messaging → WhatsApp rather than guessing a route on the webhook listener.
- **WhatsApp QR is visible only in terminal:** stop that pairing process before launching dashboard onboarding; simultaneous pairing sessions rotate or contend for the same linked-device state.

## Safety gates

- Never enable allow-all as a shortcut.
- Never paste bot tokens, QR payloads, phone numbers, or private IDs into task cards, reports, commits, or chat.
- Bind remote approvals to a specific request, user, chat, action, profile, and expiry; generic affirmative text must not authorize work.
- Preserve one credential owner per platform under a multiplexed gateway; duplicate profile credentials create ambiguous ownership and parked adapters.

---
name: messaging-integration-delivery
description: "Use when delivering remote messaging integrations."
version: 1.0.0
metadata:
  hermes:
    tags: [messaging, discord, whatsapp, gateway, verification]
    category: devops
---

# Messaging Integration Delivery

Configure or repair Hermes messaging channels end to end. Give Thomas only the final working outcome or the single physical action he must perform; do not narrate troubleshooting, internal agent progress, commands, or repeated status checks.

## Procedure

1. **Choose the account topology before pairing.** Ask whether the platform uses a dedicated bot account or Thomas's existing personal account. For WhatsApp, use `bot` only when a second WhatsApp account/number exists; otherwise select `self-chat`. Explain where the finished bot will appear before presenting a QR code.
2. **Inspect the live gateway and effective profile configuration.** Confirm the default coordinator owns the platform identity, specialist profiles do not duplicate it, and allow-all access is disabled. Under multiplexing, verify the profile-scoped secret/config view actually used by authorization; a top-level compatibility value can read correctly while ingress still rejects the sender.
3. **Configure private ingress.** Bind Thomas's observed sender identity and approved private channel/chat to the default profile. Keep secrets and private identifiers out of chat, task cards, reports, and memory.
4. **Pair through the correct surface.** If the user asks for dashboard pairing, launch/open the authenticated Hermes dashboard and use its Messaging onboarding flow so the QR renders as an image. Do not send terminal ASCII QR output unless explicitly requested. For WhatsApp self-chat, scan from the same personal WhatsApp account and then message the self-chat.
5. **Reload once after the authoritative configuration is correct.** Avoid restart loops. If a restart needs approval, make one precise request and resume the same task afterward.
6. **Verify a real round trip.** Have Thomas send a harmless status request from the approved conversation. Confirm logs show the sender was accepted, an agent turn started, and a substantive response was delivered to the same chat. A checkmark reaction, typing indicator, open socket, or successful slash-command sync is not completion.
7. **Verify grounded control and least privilege.** Confirm the reply reflects current Kanban state, non-allowlisted ingress remains denied, no broad access was enabled, and restart/reconnect preserves the integration.
8. **Report only the product result.** State that the channel works and how Thomas uses it. Omit the repair diary unless he asks for technical details.

## Lifecycle-channel separation

Keep conversational traffic in the chat channel and route gateway starting, restarting, shutdown, and online notices to a dedicated updates/home channel. Verify both destinations after a restart: lifecycle notices appear only in updates, while normal replies remain in chat.

## Pitfalls

- Treat a reaction without a reply as failure because adapters may acknowledge receipt before central authorization rejects the message.
- Read authorization from the transport-owning profile scope under multiplexing because process-global environment bridges may be absent or belong to another profile.
- Do not ask Thomas to scan a dedicated-bot QR when he has only one number; switch to self-chat first because pairing the personal account in bot mode creates an unusable topology.
- Do not expose setup credentials in chat. Prefer opening the local login artifact or authenticated dashboard surface and remove temporary credentials after onboarding.

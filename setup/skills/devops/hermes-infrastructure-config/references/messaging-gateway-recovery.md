# Messaging gateway recovery and private remote control

Use this recipe when Discord, WhatsApp, or another Hermes messaging adapter must become a private remote interface for status queries, task notifications, or scoped permission responses.

## Diagnose in dependency order

1. Identify the execution surface before attributing an error to “local” or “gateway.” Desktop error headings are presentation labels, not host evidence. Check the live session environment, hostname, and process tree:
   ```bash
   hostname
   env | grep -E 'HERMES_DESKTOP|HERMES_GATEWAY_SESSION|_HERMES_GATEWAY|HERMES_SESSION_SOURCE'
   ps -eo pid,ppid,cmd | grep -E '[h]ermes serve|[h]ermes.*gateway'
   ```
   An SSH-backed `hermes serve --isolated` process on the remote host plus gateway-session markers means the desktop is using the remote Hermes installation even if the UI says “Local runtime error.” Report the observed host and transport separately; do not infer either from a filesystem path or UI label alone.
2. Inventory ownership and service topology:
   ```bash
   hermes profile list
   hermes gateway list
   hermes gateway status
   ```
   A running multiplexer is only the transport process; read status/log warnings for explicit platform disables, missing allowlists, duplicate credentials, rate limits, and adapter connection failures. Attribute a multiplex warning to its owning profile before concluding the default adapter is disabled; verify the default profile’s explicit setting independently.
3. Correlate repeated restart banners with service history instead of assuming a current loop:
   ```bash
   systemctl --user show hermes-gateway.service -p ActiveEnterTimestamp -p NRestarts -p MainPID
   journalctl --user -u hermes-gateway.service --since '<window>' --no-pager
   ```
   Report the last restart time and whether the PID has remained stable since then. A historical burst of restart notifications is not evidence that the gateway is still restarting now.
4. Resolve credential ownership before adapter debugging. One bot/device credential must belong to one profile. For Thomas’s team, keep it on `default` and remove duplicate exposure from specialist profiles; duplicated credentials can park or contend for the same platform session.
3. Check the adapter’s explicit enabled state. Environment credentials do not override `platforms.<name>.enabled: false`, so enable the adapter through supported Hermes configuration/setup commands rather than assuming token presence starts it.
4. Configure identity restrictions before live testing. Permit only Thomas’s verified sender ID and, when needed, an explicitly approved private channel. Keep DM/group policy closed or allowlisted; do not use an allow-all switch to make a test pass.
5. Restart or reload through the supported gateway command, then re-read gateway status and recent logs. Treat platform rate limits as retryable transport state, but do not confuse a scheduled retry with a completed connection.

## Verify behavior, not configuration

Require all of the following before reporting recovery:

- one real inbound message from Thomas is accepted rather than denied by policy;
- one real outbound response reaches the same private conversation;
- a status question returns current Kanban/team data rather than a canned health response;
- proactive blocked/review/completion routing reaches only Thomas;
- after a gateway restart, inbound and outbound checks still pass.

Service health, a connected adapter log, or a successful config write alone is insufficient.

## WhatsApp setup decision

For a single-user personal remote-control use case, prefer Hermes’s supported personal-device/QR pairing path when available. Escalate to a provider-hosted API only when native pairing is unavailable or cannot support required inbound/outbound behavior. Keep human setup to one minimal action (for example, scan one QR), then resume verification on the same task.

## Permission-response safety

Remote approval is not a generic chat “yes.” Present the exact task, requested action, and scope; bind the response to that request and expire or consume it after use. A reply to one blocker must not authorize unrelated destructive, credential, deployment, or external-write actions. Preserve a sanitized audit trail without tokens, phone numbers, QR payloads, or private channel identifiers.

## Delivery orchestration

Separate work that can safely run in parallel: platform repair/implementation and security review may proceed together. Serialize final activation when lanes would edit the same gateway configuration or restart the same service. Finish with an independent end-to-end verification lane that tests both platforms after the final restart.
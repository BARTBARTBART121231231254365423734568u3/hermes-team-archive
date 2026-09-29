---
name: coordinated-delivery
description: "Use when coordinating team delivery. Verify, don't trust."
version: 1.0.0
---

# Coordinated Delivery

Own every delegated task end to end: dispatch, verify the real result, control cost. Never report a claim you have not verified yourself.

## Card hygiene

- Write complete task bodies on durable cards. Never save truncated text, `[truncated]` markers, or "details to follow" placeholders into a card body — downstream workers treat the body as ground truth and block on it.
- Ground every assignee in a real profile and express dependencies with parents/links, not prose.
- Verify branch, SHA, and deployment claims with direct reads (`git rev-parse`, service status, live `curl`) before reporting them upward.

## Owner decisions and conversation routing

1. When a worker blocks, read the exact blocker, parent handoff and latest run; resolve missing source, tooling or workspace metadata internally before treating it as a Thomas decision. Do not unblock with the same incomplete input.
2. If Thomas alone must decide, consolidate the remaining choices into one concrete proposal and ask in the owning project's original conversation when he directs project questions there; do not mix another project's consent or product choices into the current integration/status chat. Keep unrelated safe work moving.
3. Preserve message provenance across sessions: a task comment, a note injected by `--resume`, or a queued card is not a user-facing assistant question. Read back the exact target conversation and its assistant reply before claiming the question was asked or delivered; never treat a coordinator-authored note recorded as a user turn as Thomas's approval.
4. Separate consent to a displayed draft from approval of every unresolved requirement; compare the exact text and scope against the contract before releasing a blocked implementation. Report queued, claimed, reviewed and live-verified as distinct states.

## Verify, then trust

- Reproduce the key evidence yourself: run build/tests and inspect the actual running application at relevant desktop/mobile sizes before presenting a sign-off; do not substitute a throwaway HTML preview.
- Compare the actual app with the owner's references and acceptance criteria; test data and honest empty states are expected, raw internal IDs and dead controls are not.
- A green worker summary is a lead, not proof. Confirm the exact commit, the exact live revision, and the exact behavior.
- When re-running a worker's DB-backed tests, reproduce the worker's environment first (connection string, required env vars): a failure your shell produces that the worker's green run did not is your env gap until proven otherwise — check service readiness and vars before calling the code broken.
- For data-deliverable cards, open the attached file yourself and spot-check individual records (field plausibility, provenance, schema conformance) — summary counts and coverage percentages are leads, not proof.
- When troubleshooting a long-running Hermes chat, correlate its session ID with the actual provider/model, request size, and error in its logs before attributing the symptom to a fallback or a delegated worker. A direct Spark primary does not exercise a Codex→Spark fallback, and a worker's provider does not establish the parent chat's provider.
- To diagnose whether coder subagents help, first verify delegation is enabled for the relevant profile/platform (`hermes -p <profile> tools list`); then inspect parent-session `delegate_task` calls and elapsed time in the canonical `state.db` or worker logs, plus the child result. Report access, invocation, and actual time saved separately. A one-shot Kanban CLI worker joins its children inside the tool call: one long reconnaissance child blocks the parent, while two bounded independent workstreams can overlap each other. If a child receives a worker-only Kanban stop nudge, test the context-local child/worker identity gate rather than turning off the real worker guard. Keep the configured coder model unchanged unless Thomas explicitly changes it.
- After a model, toolset, or compression-config change, verify it in the **same live session**, not just with a CLI readback or a fresh test session: cached agents may retain the old compressor and tools until rebuilt. Keep the config change and the existing session's remedy as distinct states; do not claim the issue fixed until that session's next request or explicit in-session compression succeeds. Do not mutate an active chat's stored history from a second process; competing in-memory state can overwrite the change.

## Railway discipline

- Resolve project/service/environment IDs through the CLI before acting; names and links drift (renames, new envs).
- A push is not a deploy: confirm the new deployment ID, its SUCCESS status, and live HTTP plus boot-log lines (migrations, listen port).
- Use the project's reviewed deployment guard and exact target manifest; never bypass it with raw `railway up` when webhooks stall. Verify the approved route, exact SHA and live result.

## TypeScript monorepo pitfall

- Set explicit `rootDir` (and narrow `include`) on every package tsconfig. A stray file at package root silently widens rootDir inference, so `tsc` emits `dist/src/...` instead of `dist/...` and the container crashes with MODULE_NOT_FOUND on a build that looked green.
- After changing tsconfig, rebuild from a clean `dist` and execute the built entrypoint locally before pushing.

## Cost control

- After two same-cause worker failures, change the approach (serialize, reroute, or do it yourself) instead of respawning.
- Do trivial merges, deploys, and verifications yourself rather than spending agent rounds on them.
- Batch review rounds and keep scopes lean when quota burn is a concern; pause loops explicitly instead of letting workers spin.

---
name: review-gated-delivery
description: "Use when shipping code through review gates."
version: 1.0.0
---

# Review-Gated Delivery

Ship in small verifiable steps: build on an isolated branch, verify with real
output, pass independent review, merge, deploy, then verify the live system.
Never claim a state (built, tested, deployed, delivered) without fresh
tool output proving it.

## Kanban cards

- Write COMPLETE card bodies. A body ending in `...[truncated]` or any
  placeholder reads literally to the worker and blocks the task. Long bodies
  are fine; cut scope, never cut the text.
- One owner per card, explicit acceptance criteria, and dependencies as
  `parents=[...]` (or `kanban_link` later) — never prose-only ordering.
- Serialize colliding work: two fix cards touching the same files run
  chained (fix1 → fix2 → gates), never parallel. Read-only review cards may
  run parallel.
- Local-only contracts stay local: no merge/push/deploy without an explicit
go-ahead recorded on the card.

## Verify before claiming

- `pnpm verify` green is necessary, never sufficient. After it, exercise the
  artifact itself: boot the server, curl `/health` and one real endpoint,
  click the UI in a real browser.
- Re-read the exact commit under review (`git rev-parse`, diffstat). Approvals
  bind to an exact SHA; any new commit needs a new verdict.
- Inspect worker-supplied screenshots yourself with vision before presenting
  them. Check for debug/test data, raw IDs, and cropped clipping the worker
  did not mention.

## TypeScript build pitfalls

- `tsc` infers `rootDir` from all included files. Including a root-level file
  (e.g. `vitest.config.ts`) alongside `src/` nests output (`dist/src/...`)
  and breaks `node dist/index.js`. Keep `include: ["src"]` (plus an
  `exclude` for `node_modules`/`dist`) so output lands flat.
- A run-directly guard comparing `import.meta.url` to `process.argv[1]`
  fails when argv is relative. Compare resolved absolute paths instead.
- A pnpm workspace package consumed by Vite needs a `paths` mapping to the
  dependency's source (or a prior built `dist`); otherwise typecheck fails
  even though install succeeded.

## Railway: build logs vs runtime logs

- A successful Docker build does not prove a working deploy. Always read
  BOTH: build logs (`-b`) and the latest runtime logs.
- `Cannot find module .../dist/index.js` after a green build means the file
  was emitted elsewhere (see rootDir pitfall above), not that the build
  was skipped.
- After any deploy, curl the live `/health` and `/` plus one real endpoint
  before reporting success. A GitHub push only counts once the new
  deployment ID is SUCCESS and live output matches.

## Clickable previews

- A static file preview cannot serve an app that requires a live API by
  design (no mocks): it hangs on loading. Plan a backend-backed preview
  (staging env) instead of debugging the static one.
- When publishing a Vite `dist/` under a subpath (`/preview/<id>/`),
  absolute `/assets/` refs 404. Publish a `/tmp` COPY (never patch the
  repo) with `"/assets/` rewritten to `"./assets/`.

## Quota and stalls

- When all model-provider pool entries are rate-limited, park looping cards
  as `transient` with the reset time, and do yourself whatever needs no
  model calls (reads, builds, curl checks, log archaeology).
- After two same-cause worker failures, change the approach (reroute,
  serialize, or narrow scope) instead of retrying.
- When an exact-head release repeatedly stalls on unrelated, reproducible
  baseline CI failures, stop expanding a bounded feature release into a
  project-wide test-repair campaign. Prove baseline parity, identify the
  remaining risk, and ask the owner whether to retain the original gate or
  approve a one-time exception bound to an exact SHA and environment. Record
  the choice on the release card; an exception never waives independent
  security review, guarded activation, rollback, or live verification. A
  changed SHA requires a new decision.
- Never present a provider's raw error text or credential material to the
  user; report impact and next step only.

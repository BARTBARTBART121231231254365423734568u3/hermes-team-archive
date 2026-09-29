# Kanban provisioning and dispatch repair

Rules for keeping dispatcher-spawned lanes dispatchable and for diagnosing
them when they are not. All of these cost at least one stalled lane to learn;
apply them before declaring any card 'queued'.

## Provision cards so they can spawn

- Before dispatch, read back the exact stored task body and supporting comments or attachments; compare required identifier counts and values with the authoritative source. Never put `...[truncated]` or a shortened tool display into a card or comment as if it were the full scope. If the source is incomplete, hold scope-dependent implementation and retrieve the original; do not infer missing OAuth permissions or other access grants from documentation. Read back any attempted repair before unblocking, because an incomplete comment merely restarts the same failure. If auto-decomposition follows, verify every child has a usable repo/workspace anchor and preserves the original gates before allowing it to dispatch.
- For an existing project repo, create code tasks with an explicit project link and a bare worktree kind; read back the per-task `.worktrees/<id>` path before dispatch. For a brand-new repo that has no project registration or initial commit yet, bootstrap it in an explicitly assigned directory workspace first, then register the project and switch subsequent independent lanes to project-linked worktrees. A worktree card without a provisioned path fails at claim time.
- Never pass an explicit repo-root path as the worktree location: every lane
  then shares one checkout and workers check out branches under each other.
  Use bare worktree plus project and let the dispatcher anchor per-task dirs.
- Never set a board-level default workdir on a shared board to fix one
  project's cards: unrelated projects' tasks get provisioned under the wrong
  repo. Repair the cards, not the board.
- Before creating a card with a forced `skills` list, verify each skill is
  enabled in the assignee profile; an `Unknown skill(s)` launch error is a
  deterministic provisioning failure, so fix the request, not the retries.

## Wire and verify the dependency graph

- Set parent links at creation. After any bulk recreation, read back at least
  one mid-chain card and confirm its parents before calling the graph healthy;
a recreated set without links dispatches every lane at once, including reviews
  and deploys.
- When a ready task will not promote, run a dispatch pass and read the
  `Promoted`/`Spawned` counts; if zero, ask promotion for the reason — an
  `unsatisfied parent dependencies` error names the exact blockers.
- Before treating any implementation handoff as reviewable, verify the candidate SHA exists on origin, not just in the worktree: workers routinely complete with local-only commits. Push the task branch when `ls-remote` comes back empty, then release the review.
- When the work exists only as a detached-HEAD commit while the task branch points elsewhere stale, publish the exact SHA as a new remote ref (`git push origin <sha>:refs/heads/<task-branch>`) instead of moving local branches: the SHA becomes immutable and reviewable without disturbing local checkout state. Verify with `ls-remote` afterward.
- For a staging branch that must move to a sibling SHA (not a descendant), use a lease-guarded force-push (`git push --force-with-lease=refs/heads/<branch>:<expected-old-sha> origin <new-sha>:refs/heads/<branch>`) only under explicit owner authorization, record the rollback pointer (remote tag plus prior deployment record) on the card, and verify the move with `ls-remote` before releasing verification.
- When lanes correctly safety-hold because fresh worktrees would provision from a stale base, verify the approved base SHA, then pre-create each task's branch at that SHA — only when neither branch nor worktree exists yet, so zero work is at risk — record the authorization covering the reset, and unblock. Do not ask workers to implement on the wrong base first and rebase later.
- Parked or auto-decomposed duplicates frequently end up as parents of the
  real lane and deadlock it. Unlink them from the real card, leave them parked
  so they cannot dispatch in parallel, and record the reconciliation in a
  comment on the surviving card.
- Re-blocking the same kind after an unblock trips the loop guard and routes
  the card to triage. Triage dispatches nothing, so it works as an intentional
  park — but record why it is there and restore it explicitly on resume.

## Diagnose spawn failures from the log, not the status

- A `crashed (pid gone / exit 1)` within ~90 seconds of spawn is a launch
  failure, not a work failure: no work was lost. A clean exit (rc=0) with no
  completion or block call is the same class — a silent launch failure, not
  done work. Read `kanban/logs/<task>.log` before retrying either; a quota
  wall (provider 429 with a retry-after) needs an owner decision — wait,
  re-authenticate/top up, or temporarily reroute — never blind retries.
- `Refusing this startup model override in non-interactive mode` means the
  pinned model is a data-training (contributor) tier and unattended runs need
  explicit owner consent. Read the task log before retrying, then offer the
  standard (non-training) variant or contributor-tier data training; record the
  owner's choice on the existing card. The acknowledgement is profile-wide,
  not project-scoped: if consent covers only one repository, do **not** enable
  a persistent acknowledgement for a profile that also runs other projects.
  Use a verified isolated execution profile/config scoped to that repository,
  choose the standard variant, or ask the owner to broaden consent; a model
  choice alone does not authorize exposing unrelated future workloads.
  Where profile-wide consent is explicitly granted, use `hermes config set`
  for the global setting (never hand-edit global config), verify with
  `hermes config get`, and configure/read back each executing profile separately
  because profile-scoped workers do not inherit that global acknowledgement.
  Re-read the task's run-linked route and startup log after unblocking; an
  acknowledgement write is not proof the worker actually launched.
- Pin models with an explicit override on **every implementation card**, including reviewer-created fix and retry cards: child cards inherit dependencies and context, not the parent's model/provider override. Read each new card back before it can dispatch; if a follow-up lacks the user's requested pin, replace or park it before a default-model worker changes code. When replacing a card, inspect its descendants and rewire each downstream gate to the replacement; merely adding a new parent leaves the old blocked parent in place and strands the lane. Then verify the run-linked routing event names the intended model and provider. A claimed run without that event fell back to the profile default — treat it as misrouted, not done.
- Treat a requested model and its reasoning effort as separate settings. Resolve a user's display name against the local provider model catalog, pin the exact provider/model on the card, and verify the run-linked route; do not confuse `contributor` in the model ID with an effort level. Cards carry no reasoning-effort knob. For model-specific effort, set `agent.reasoning_overrides` in the executing profile to a mapping from exact model ID to `xhigh` (or the requested supported level), then read it back before dispatch; use `agent.reasoning_effort` only when the level should apply profile-wide. Confirm the provider's catalog lists that effort for the exact model. This avoids changing unrelated tasks' effort or silently using the profile default.
- For `worktree target is checked out on another branch`, inspect `git worktree list --porcelain`, the task's expected branch, and `git -C <workspace> status --short --branch` before retrying. If the expected worktree exists with valuable in-progress changes on a different branch, preserve the checkout: verify no worker still owns it, archive any unused expected branch ref with `git branch -m <expected> archive/<descriptive-name>`, then run `git -C <workspace> branch -m <expected>` on the active branch. This changes refs without switching the dirty worktree. If the worktree is instead clean and detached at a review candidate, archive the unused expected ref and run `git -C <workspace> switch -c <expected>` at that HEAD; tell the reviewer to inspect the latest exact candidate rather than approving the checkout's older SHA. Verify branch, HEAD, and status afterward, then resume the existing card. Do not reset, remove the worktree, or replace the task before checking for recoverable work.
- When nothing spawns, check running-task slots (two workers globally, one per
  profile) and per-task diagnostics; a silent queue is usually slot exhaustion
  or an unsatisfied parent, not a dead dispatcher.

## Reconcile conflicting verdicts

- When two independent reviews of the same SHA disagree, the evidence-backed verdict wins: a NO-GO with file:line findings and failing-behavior proof retires a thin APPROVE as release basis, even with green tests. Route rework plus re-review; never average the verdicts or ship on the approval.
- Check which SHA a late-arriving verdict actually reviewed before acting on it: a NO-GO on a superseded SHA corroborates already-fixed defects and needs no new card — record it and keep building on the newer head. Only a verdict on the current head opens rework.
- Freeze mid-flight by parking in two moves: let the running lane finish while every ready lane is parked, then park each child the finishing lane releases at its completion notice — released reviews dispatch immediately otherwise. Record SHAs, queued cards, and the unblock order as the checkpoint deliverable.

## Resume under an owner-ordered model split

- When the owner splits authoring model from execution model, pin the authoring model on the planner card and require the FULL prompt text in the completion summary: authoring runs may report no filesystem tools, so the coordinator writes the file and verifies it (size, hash, spot-check key clauses) — never ask a tool-less run to write files.
- Record owner amendments as card comments and apply them to the file before approval; the paused lanes stay parked until the owner explicitly approves the prompt, then resume in the prompt's own order.

## Report to Thomas

- For an admin-backed demo, record two separate verdicts: isolated local preview and public/staging exposure. A local PASS must not promote public access when identity/MFA, durable persistence, and real checkout are still gated; open only the static storefront in the user's preview rail and keep the admin bound to loopback. This prevents a visually approved demo from accidentally becoming a live order system.
- Before calling a demo accepted, distinguish implementer self-review from independent review by checking the review run's assignee/profile. Passing unit tests is insufficient when a static preview is the deliverable: serve the built directory and exercise product links and key interactions in the actual browser/preview surface; broken rewritten routes can evade application tests. A preview page that opens is not a page that renders: fetch the served page and confirm its JS/CSS return 200 under the preview subpath — builds with absolute asset paths 404 there and show a blank shell, so publish a relative-asset copy and re-verify before inviting the owner to look. Exercise interaction *combinations*, not only isolated controls: select a facet, then search, sort, reset, and revisit the URL; verify selected filters survive the round-trip in both static preview and live app. Require the complete sequence as a committed integration regression invoked by the normal test command before declaring acceptance; isolated DOM assertions and separate HTTP probes do not prove state survives the same-page round-trip. A reviewer-created repair card is work queued, not a passed review.
- When a chat update is authorized, consolidate verified completion (exact SHAs and test receipts), running lanes, and gates into one message; never narrate troubleshooting spirals. When Thomas has restricted a channel to requests for his help, keep routine transitions and “no help needed” acknowledgments on the board only, regardless of automatic notification volume.
- Match the user's language: when Thomas writes Dutch, answer in Dutch.
- A promised summary (e.g. morning review, checkpoint state) is a deliverable:
  SHAs, queued cards, and the exact unblock sequence, not a status platitude.

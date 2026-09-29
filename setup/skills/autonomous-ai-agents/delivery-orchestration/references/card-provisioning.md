# Card Provisioning: Make Every Created Card Dispatchable

A card that a worker is expected to execute must carry everything the
dispatcher needs at creation time. Cards missing any of these fail at spawn
with provisioning errors, and the dispatcher eventually gives up — stalling
the whole lane behind them. Verify dispatchability immediately after
creating cards (show the card: `workspace_path` must be set, status must
gate as designed) rather than assuming the dispatcher will pick them up.

## Creation checklist (every executable card)

- Link the project (`--project <slug>`). The project link anchors a
  per-task worktree under the project's repo with a deterministic branch.
  Without it, a `worktree` card has no path and can never spawn.
- Request an isolated workspace (`--workspace worktree` with no explicit
  path alongside the project link), never a shared repo-root checkout.
  Parallel lanes in one directory switch branches under each other and
  collide on uncommitted state.
- Wire `--parent` links in the same creation call. Unlinked recreations all
  read as ready, so the dispatcher claims every lane at once — including
  reviews and deploys whose inputs do not exist yet.
- Never force-load a skill (`--skill`) without first confirming it is
  installed and enabled on the assignee's profile
  (`hermes skills list --profile <assignee>`). The dispatcher rejects
  unknown skills and retires the card after repeated spawn failures.
- Use a per-card idempotency key so a retry never duplicates the lane.

## Re-provisioning undispatchable cards

Prefer repairing the original card when the tooling allows it; when it does
not (e.g. no field exists to add the missing project link), recreate:

1. Copy the spec body verbatim under a short supersede header naming the
   retired card and why it could not dispatch.
2. Recreate with the full checklist above, re-linking the entire parent
   graph — not just the head of the chain.
3. Comment each retired card with a pointer to its replacement, then
   archive the retired set so the board shows one live graph.

## Containing mis-dispatched workers

If bad cards already spawned workers (wrong order, shared directory):
reclaim the running cards first to release their claims, then archive the
bad set. Delete worker-created branches only after confirming they hold no
commits beyond the base — never force-delete a branch carrying real work.

## Shared boards

Never set a board-level default workdir to one project's repo to fix one
lane's provisioning. A shared board carries many projects' pathless tasks,
and the default would mis-provision all of them. Fix the cards, not the
board.

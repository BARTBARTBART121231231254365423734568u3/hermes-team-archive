# Resuming Multi-Milestone Programs

Use this procedure when the user asks to continue a roadmap after a pause, regression, migration, or stalled worker.

## Procedure

0. Establish resume authority before changing state. Treat “later” as parked until explicit approval, not an automatic trigger tied to another milestone. A hardware upgrade or feasibility question warrants fresh read-only checks, not unblocking; answer the actual feasibility question instead of repeating the pause. On approval, reconcile the new scope with the authoritative report: replace or explicitly supersede contradictory acceptance criteria, preserve historical observations as dated evidence, and put the revised acceptance contract in the delivery card. Queue implementation rather than another audit and distinguish queued from running. Check for overlapping live configuration/runtime work before dispatching changes; do not interrupt it or overwrite newer decisions.
1. Reconstruct the authoritative milestone plan and verified completion boundary from project records, card handoffs, and session history; milestone names alone do not prove progress. Read the canonical hidden `.hermes/plans/` path directly before concluding a plan is missing—broad file searches may skip hidden directories. If only session history contains the source, recover the exact text and materialize it into the task worktree before unblocking the baseline; do not invent a replacement contract from milestone labels.
2. Inspect every nonterminal card at that boundary, including children, comments, exact commit, remote readback, test evidence, blocker reason, and worktree `HEAD`. Compare each runnable worktree against the approved release/staging SHA with an ancestry check; a project-linked worktree can still inherit the repository's default branch, so a resolved workspace path is not proof of the correct base.
3. If implementation is complete and independently evidenced but stranded by a resolved credential, infrastructure, or worker-lifecycle blocker, reconcile the existing card in place and release its review child. Do not create a duplicate replacement merely because the worker stopped.
4. Preserve the review → release → deployment chain. A pushed commit does not permit bypassing independent review or exact-SHA deployment. If one review approves an exact SHA while another requests changes on that SHA, reconcile each disputed finding against the frozen acceptance contract and reproduce its behavior before releasing integration. Reuse existing functional/security review lanes and gate the existing integration card on their combined verdict; do not create duplicate review graphs or treat the approval label as resolution.
5. Queue the next milestone's orchestration card behind the exact live-verification boundary the user approved. Keep production promotion and next-milestone authorization as separate gates: “continue to the next milestone” does not authorize production, and production approval does not authorize later roadmap work unless the user explicitly combines them.
6. Before releasing the baseline, verify its worktree is based on the approved SHA. If a fresh, clean worktree was created from an older default branch, correct the base before dispatch and read back `HEAD`; if it contains product work, preserve it and create one continuation from the approved base rather than resetting away edits.
7. Put locked product decisions, acceptance gates, and hotspot serialization rules directly in the orchestration body so downstream cards cannot redefine the architecture independently.
8. Report the graph transition concretely: what was reconciled, which exact base every runnable lane uses, which review is runnable, which deployment remains gated, and which milestone is queued.

## Changing approval gates

- When execution becomes plan-only, hold the existing delivery card with `needs_input` before preparing the plan. Record prerequisite completion AND explicit plan acceptance separately; dependency edges alone auto-release work and cannot enforce human approval.
- When a later explicit go-ahead replaces the wait, record the superseded gate on the same card before unblocking. Preserve unrelated project pauses and recheck live workers and eligible queues; do not insist on an obsolete completion prerequisite.
- Read back the transition and distinguish ready from running. Treat an expected hold notification as confirmation of the requested gate, not a new failure.
- Estimate the whole delivery cycle, including independent review, activation and live verification. Give a provisional range and its main uncertainty rather than presenting a configuration-change estimate as a full-program promise.

## Pitfall

Never dispatch the next milestone while its plan source is missing, its worktree ancestry is unverified, or a completed urgent fix remains stranded in a blocked parent—the new milestone can fork from the wrong baseline and silently omit already-approved work.

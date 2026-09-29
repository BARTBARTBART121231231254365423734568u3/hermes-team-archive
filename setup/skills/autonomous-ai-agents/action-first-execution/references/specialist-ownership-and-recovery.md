# Specialist Ownership and Kanban Recovery

Use this when the user explicitly assigns a problem class to a specialist or corrects the agent for investigating personally.

## Immediate routing pattern

Create one self-contained card containing:

- exact user-visible symptom and reproduction sequence;
- repository/workspace and relevant URLs or service IDs;
- verified facts versus hypotheses (label them separately);
- prior commands/errors only when they materially constrain the next attempt;
- required deliverables: diagnose, implement, test, deploy, and verify as applicable;
- an explicit terminal requirement: call `kanban_complete` with evidence or `kanban_block` with a genuine external blocker.

Do not perform additional diagnosis before routing unless a single read-only probe is necessary to write an intelligible brief.

## Keep ownership with the specialist

After routing:

- subscribe to the card and relay verified updates to the user;
- do not ask the user to monitor the board;
- do not resume personal troubleshooting while the specialist is active;
- distinguish `ready`, `running`, `blocked`, `review`, and `done` precisely.

## Recovery after protocol violations

A worker exiting cleanly without `kanban_complete` or `kanban_block` is a workflow failure, not evidence that the technical issue is fixed or impossible.

1. Read the full card, comments, events, and prior run summaries.
2. If useful work was already completed, preserve those verified facts in the replacement brief.
3. Avoid repeatedly unblocking the same card after multiple identical protocol violations.
4. Create one clean replacement card with:
   - the correct specialist;
   - a persistent project workspace when required;
   - explicit lifecycle instructions;
   - bounded runtime and high priority if urgent;
   - goal mode and a suitable model/provider override when supported;
   - an idempotency key to prevent duplicate recovery cards.
5. Read the new card back and confirm assignee, status, workspace, priority, and model override before telling the user it is queued.

## Close superseded cards and separate defect scopes

Repeated failure notifications often come from an old card that produced useful work but never reached a terminal lifecycle state. Do not leave these cards open indefinitely once their original acceptance criteria are independently satisfied.

1. Re-read the old card and identify its exact defect scope.
2. Verify the original outcome from durable evidence (merged commit, tests, production data, or a live reproduction).
3. If a later symptom is a distinct defect, track it on the replacement card rather than keeping the original card artificially open.
4. Complete the obsolete card with metadata naming the verified evidence and the replacement task for the separate remaining issue.
5. Never close an obsolete card merely to silence notifications; closure must reflect a genuinely satisfied or explicitly superseded scope.

Example distinction: “registrations no longer collide across tenants” can be complete even while “registered active members are omitted from a tenant’s list” remains open as a separate role-state synchronization defect.

## Avoid redundant recovery pipelines

Before auto-decomposing or creating analysis → implementation → verification children, inspect existing commits and handoffs. If a tested fix already exists, preserve independent review where valuable but do not ask another implementation card to rediscover or rewrite the same correction. Scope downstream cards to validate the existing commit, merge it, deploy through the canonical path, and verify production.

If a diagnostic child fails procedurally but its required findings are already independently established by production evidence and a reviewed diff, record that evidence durably and complete only that diagnostic scope. Do not fabricate missing analysis, and do not re-run a poisoned worker merely for ceremony.

## Reporting language

Use grounded status updates:

- `ready`: “Queued; not started yet.”
- `running`: “The specialist is active; no verified resolution yet.”
- `blocked`: state the exact external dependency from the card.
- `done`: summarize root cause, changes, tests, deployment, and live verification from the completion handoff.

Treat delayed notifications as belonging to the task ID shown, not automatically to the newest recovery task. Read the active replacement before reporting whether current work failed.

Never translate “worker spawned,” “command returned 0,” “PR merged,” or “deployment started” into “fixed.”
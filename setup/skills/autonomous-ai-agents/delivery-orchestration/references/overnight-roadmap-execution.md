# Overnight Roadmap Execution

Use when Thomas approves an entire scoped roadmap and says to continue unattended (for example, “work through the night”).

## Operating rule

- Start every dependency-free task immediately through Kanban; do not wait for the user to choose the next planned item.
- Preserve dependency gates and avoid parallel edits to the same mutation path.
- On a genuine blocker (missing credential, an irreversible decision, unsafe data ambiguity, or an external access wall), block only that card with a concise reason. Continue every other task whose dependencies remain satisfied.
- Do not interrupt Thomas for routine progress, normal implementation choices, or verification that agents can perform themselves.
- Keep each completion notice compact. Escalate only a specific blocker or a review gate that truly requires Thomas, such as approval after he has seen a staging build.
- Overnight authorization to work the roadmap is not retrospective approval of an unseen staging deployment. Retain an explicit post-review production gate when the plan calls for it.

## Checkpoints

1. Re-read active/queued cards periodically. If a ready task remains unclaimed beyond ordinary dispatcher latency, inspect the assignee’s active queue for a stale or duplicate running task.
2. Confirm newly unlocked dependency children actually transition to `running`; do not infer progress from the graph alone.
3. At release readiness, require a dedicated integration/QA gate before staging.
4. Before reporting live, independently verify deployment target and user-facing rendering.

# Milestone completion and status reporting

## Procedure

1. Read every terminal gate in the milestone task graph before reporting status. Include implementation, independent review, integrated QA, and deployment or live acceptance when the milestone contract requires them.
2. Classify each completed lane precisely: **implementation complete**, **independently approved**, **deployed**, or **live-verified**. Never shorten one of these to “the milestone is complete.”
3. State the milestone verdict first when the user asks whether the whole milestone is done: **Yes** only if every required terminal gate is passing; otherwise **No**, followed by completed work and remaining gates in dependency order.
4. Treat a worker’s green build, lint, unit tests, and self-authored browser suite as evidence for its implementation lane only. Do not use them as substitutes for an independent rendered-review contract.
5. If independent QA rejects a candidate, name the exact rejected SHA, consolidate blockers by root cause, and identify the correction followed by exact-SHA re-review. Do not present duplicate or stale reports as additional defects.
6. After creating the correction and re-review chain, report that the pipeline is continuing autonomously and preserve any deployment prohibition.

## Status wording

Use: “B2 implementation is complete; Milestone B is not complete. Rendered QA and B3 remain.”

Avoid: “B2 is complete” when the next independent gate can still reject the candidate. The shorter wording invites the user to infer whole-phase or whole-milestone completion.

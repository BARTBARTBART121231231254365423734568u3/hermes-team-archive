# Kanban body & cost discipline (orchestrator)

Lessons from BITEWISE 2.0 coordination; complements SKILL.md (which is at its
size cap, so no pointer line could be added there — curator: link from SKILL.md).

- **Complete task bodies only.** Never end a kanban body with a truncation
  marker (`...[truncated]`, `etc.`). Workers treat the body as ground truth
  and block on the missing half — twice observed. If scope does not fit,
  narrow the scope, never the sentence.
- **Serialize same-branch fixes.** When two fix tasks would edit the same
  branch/files, link them parent→child with `kanban_link` so the second
  starts from the first's delivered SHA instead of colliding on a stale base.
- **Cost circuit-breaker.** On a user subscription/quota-burn complaint: stop
  loops first via `kanban_block` (never let workers spin while deliberating),
  then batch remaining work into fewer, heavier rounds. No new agent rounds
  without explicit go; trivial verified merges/deploys may go direct when that
  saves a full round-trip.

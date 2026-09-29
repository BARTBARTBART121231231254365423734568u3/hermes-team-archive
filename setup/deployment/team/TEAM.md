# Hermes team operating agreement

Thomas gives the team an outcome. The receiving agent owns getting it to a
verified result, including handoffs. Do not send Thomas to another channel to
coordinate your work. Existing user constraints and approvals remain in force.

## Roles

| Profile ID | Display role | Responsibility |
|---|---|---|
| default | Team coordinator | Triage, route work, consolidate results, report to Thomas |
| planner | Delivery planner | Acceptance criteria, dependencies, board hygiene |
| coder | Software engineer | Implementation, tests, isolated branches/worktrees |
| designer | Product designer | Interaction design, previews, visual validation |
| researcher | Research analyst | Source-backed findings and decision support |
| security | Quality and security reviewer | Independent correctness/security review |
| devops | Release operator | Deployment targets, releases, readiness, recovery |
| scheduler | Scheduling assistant | Reminders and purposeful recurring work |

Keep these stable IDs for routing. Do not invent an assignee such as `reviewer`.
Check actual availability before promising work from another profile.

## Task contract

Use native Kanban tools for durable work. Before creating a card, check for an
existing open card for the same outcome. Each card has one accountable owner,
an existing project ID where applicable, acceptance criteria, relevant files,
constraints, dependencies, and the originating conversation for delivery.

At worker startup, read the actual assigned task ID (HERMES_KANBAN_TASK) and
current task body/comments. If it is missing, list and identify the assignment;
never call kanban_show without an ID outside a dispatched task. Do not guess.
Read /root/.hermes/team/projects/<project-slug>.md if present. Verify repository
origin and worktree before editing. Use a task-specific worktree for code;
do not concurrently edit the same branch or share a profile's memory directory.

Handoff fields: task/project ID; owner and next role; outcome; commit/branch;
changed files or artifact URLs; checks actually run and their result; remaining
risks; deployment IDs when relevant. Native review tools should carry the task
through review; creating duplicate cards is not a substitute for a handoff.

Normal flow: implement -> independent review -> release when authorized ->
verify the actual deployed revision and behavior -> complete. A push or healthy
container alone does not prove the requested behavior works. Small low-risk
tasks can finish after proportionate validation. Design work must be rendered
and checked against the user's references; preserve required user preview approval.

## Work limits and blockers

Two active Kanban workers globally, one per profile. Do not evade this by spawning
extra background agents. Short synchronous helpers are useful only for a bounded
subproblem and must not duplicate an existing worker's task.

Classify blockers accurately: transient (429/temporary outage), capability
(missing tool/access), needs_input (a decision/credential only Thomas can supply),
or dependency (another task must finish). Retry transient failures with backoff;
never repeatedly unblock capability or needs_input cards without new evidence.
After two unsuccessful automatic recovery attempts, leave the card for triage.
Do not retry provider quota exhaustion in a tight loop or create replacement cards.

## Deployment ownership

Only the release operator deploys team work. Every deployment has a reviewed
target manifest: project ID, environment ID, service ID, repository and branch.
Use `railway deploy-verified <manifest.json> --commit <full-sha>` to inspect;
add `--apply` only when the requested work authorizes deployment. Never upload
an arbitrary working directory with railway up. Never invoke a raw CLI binary
or API to evade the guard. New target setup or credential changes belong to an
external operator session until an appropriate scoped credential is available.

For Hermes itself the manifest is /opt/hermes-deploy/production.json. Source is
the hermes-agent-railway repository; preserve /root/.hermes. Runtime wrappers
prevent mistakes but are not a security boundary between root-owned processes.

## Shared knowledge and reporting

Keep project architecture, decisions, known issues and deployment targets in
/root/.hermes/team/projects/<project-slug>.md. Store evidence and code in the
project/task, not duplicated summaries. Never write credentials into task cards,
shared knowledge, comments, logs or reports. Keep role memory private.

Read /root/.hermes/ops/team-status.json for a current machine-generated board
summary; check its timestamp and regenerate with the team_status.py script if
stale. Report meaningful progress, verified completion and actionable blockers
through the originating conversation. The coordinator consolidates specialist
results. Do not send unsolicited cross-channel messages or routine retry noise.
Only mark a result complete after checking it; distinguish verified facts from
assumptions and stop when the requested work is complete.

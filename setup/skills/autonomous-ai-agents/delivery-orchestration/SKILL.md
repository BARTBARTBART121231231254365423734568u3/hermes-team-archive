---
name: delivery-orchestration
description: "Use when coordinating delegated delivery. Verify status."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kanban, delegation, status, delivery, verification]
    category: autonomous-ai-agents
    requires_toolsets: [kanban]
---

# Delivery Orchestration

Coordinate delivery with verified outcomes; dedupe by defect/SHA. Keep routine updates off Discord. Before dispatch, verify existing cards and read back scope, IDs, workspace and dependencies; queued is not running and blocked needs recovery. Verify transport, claims, builds and real UI before claiming delivery. Propagate workflow changes across the team. For added capacity, state existing + added = total and name exclusive profiles before creating cards; after a correction, reconcile the canonical card and activation contract before claim. See `references/risk-routed-review.md` for review routing and other topical references for depth.

## Prevent Duplicate Work Before Dispatch

1. List the project's open cards before creating anything, then compare the proposed outcome, target commit/branch, changed files, acceptance criteria, and downstream children. Reuse or amend an existing card when those fields describe the same work; title differences do not make work distinct.
2. Designate exactly one canonical implementation card and one canonical review card for each deliverable. Put the canonical card ID in related comments and downstream gate descriptions so workers can discover it before spawning follow-ups.
3. Choose one review-creation model per lane: either pre-create the review card in the graph or instruct the implementer to create it at handoff. Never do both, because equivalent reviews become separate required parents and silently double-gate integration.
4. Before accepting a replacement or auto-decomposed subtree, inspect the existing parent/child graph. A replacement must explicitly supersede the old card and preserve only one authoritative path; an auto-decomposer must not recreate work already represented by active or completed cards.
5. Audit fan-in tasks for duplicate gates before dispatch. If two parents validate the same artifact and criteria, stop the non-authoritative card before it runs and remove or close its gate using verified evidence from the canonical card. Do not leave a blocked duplicate as a permanent integration dependency.
6. When reporting duplicate cleanup, distinguish completed historical noise from live duplicated execution and duplicated release gates. Prioritize stopping live duplicate workers and unblocking the canonical delivery path; cosmetic archival can wait.

**Pitfall:** Do not create a fresh replacement merely because a worker stalled or a prompt became stale — replacement cards multiply work and dependencies unless the original card is first made non-authoritative and downstream gating is rewired.

## Core Rule: Describe the Actual State

Read the task record before giving a status update. Use the exact lifecycle meaning:

| State | Safe user-facing language |
|---|---|
| `ready` / `todo` with no run | "Queued; it has not started." |
| `running` with recent heartbeat | "Actively running." |
| `review` | "Implementation is complete for this card and is awaiting/requires review; the implementer is not actively coding this card." |
| `blocked` / `triage` | "Paused on <specific blocker>; no work is progressing." |
| `done` | "Implementation phase completed." Do not imply production is live without separate deployment verification. |

Never say work is "flowing," "being worked on," "deployed," or "live" merely because a card exists, a local commit exists, or a deployment was requested.

## Audit-Informed Design Delivery

When the user asks for a redesign **and** asks other specialists to identify usability, product-flow, technical, or security improvements, the audit findings must reach the designer before the design is treated as ready.

1. **Sequence when practical:** have the planner/research audit complete first, then create the designer card with its prioritized findings embedded in the initial brief.
2. **If work runs in parallel:** as soon as an audit completes, immediately add a structured comment to the active designer card. Translate findings into visible prototype requirements—not a vague instruction to “consider feedback.”
3. **Separate ownership cleanly:** feed UX/product-flow items into the design (e.g. recent foods, favorites, empty/loading/error states, mobile flows, onboarding, hierarchy). Route technical and security findings to implementation/remediation cards; do not imply an HTML prototype fixes backend risks.
4. **Require evidence in the design handoff:** the designer’s completion metadata must identify where the audit-driven features appear, publish a preview URL, and provide the artifact path. Independently fetch the URL or otherwise verify it before sending it to the user.

**Pitfalls — parallel-audit disconnect:** Creating audit cards alongside a design card is not enough. If the designer ships before receiving the findings, the user correctly sees a cosmetic redesign instead of a redesign informed by the team's work. The orchestrator owns closing this loop.

**Screenshot-fidelity failure recovery:** When a screenshot-driven design task is rejected by the user for visual reasons ("wrong layout," "completely different," "looks disgusting"), do NOT iterate with vague feedback to the designer. Instead, halt and extract exhaustive visual specifications manually using vision tools: enumerate every layout detail, color, spacing, typography, and control at pixel level. Create a new high-priority designer task with these extracted specs as the authoritative brief, plus explicit requirement for visual-comparison evidence (side-by-side screenshots by route) before publishing. Verify the comparison yourself before sending the preview URL to the user; do not accept designer self-report of fidelity without inspecting the evidence. This pattern is detailed in `references/bitewise-screenshot-driven-redesign-workflow.md`.

## Interactive Prototype Approval Gate

When a user asks to turn visual references into an application, **do not begin production implementation from static screenshots or a partially interactive mockup.** First delegate a standalone interactive prototype to the designer and require user approval of that prototype before creating any implementation card.

1. Put the supplied image/file paths directly in the designer brief and name every required route, panel, and state.
2. Require a complete click-through surface: all primary navigation routes, secondary panels (for example Settings/Tweaks), and every control shown in the reference must render a meaningful state rather than a dead button or placeholder.
3. Require browser-history-compatible navigation (hash routing is sufficient for a static preview) and an intentional mobile navigation treatment.
4. Add an explicit acceptance comment before completion: the designer must click-test every nav destination and interactive control, then report the tested-control inventory, preview URL, and artifact path.
5. Publish the preview with `create_preview.py`; verify the link renders before presenting it. Treat the preview as a **design review gate**, not code-ready approval: only create the production coder task after the user explicitly approves the working prototype.
6. **Approval must be explicit and user-authored.** A completed QA/staging card, a passing smoke test, a worker summary, or a message saying that staging is live is never approval to promote. Quote or clearly reference the user's affirmative production go-ahead before unblocking/creating a production deployment card. If the user says they have *not* approved it, immediately block every pending production card and report that correction plainly.
7. If the user says to pause or "do not do anything," resolve the exact stop boundary from the immediately active card/stage before blocking descendants. A phrase such as “after this one” refers to the currently discussed implementation/review gate, not automatically to the whole milestone; if the referent is still genuinely ambiguous, ask one narrow question before changing the graph. Immediately stop/block work beyond that boundary and do not continue under an earlier approval. If the user corrects the boundary, update every affected card in the same turn—pause/unblock the actual running and ready cards, add one durable supersession comment to downstream release gates, and verify the intended boundary card remains runnable. If the user later reverses the pause, unblock all cards paused solely by that instruction and add a latest-direction comment so resumed workers do not obey stale pause context. For a running release, transition the task first, then immediately read back both the task events and the external deployment provider before claiming it stopped: a guard apply may win the race just before cancellation. If an apply or deployment ID already exists, report that exact state and perform no rollback or follow-up deployment without a fresh explicit instruction.

**Pitfall — partial-preview trap:** A polished Diary or Goals screen does not prove the product flow works. The most common failure is shipping a beautiful first route while Settings, secondary navigation, mobile navigation, or controls are placeholders. The delivery brief must make the full interaction inventory a completion requirement.

## Reference-Fidelity Gate for Screenshot-Driven Design

When the user supplies screenshots and asks for the design to be copied, treat them as a strict visual specification—not inspiration. Do not allow a designer to substitute a generic dashboard, improve the product identity, or infer a new layout from the screenshots.

1. Put every source-image path/URL in the design brief and map each image to its intended route.
2. Enumerate the screenshot-visible requirements: shell/rail dimensions, content widths, typography, spacing, card geometry, colors, headings/copy, controls, states, and information hierarchy. Identify the visible structures the designer must reproduce on each route.
3. Require desktop renders at the reference proportions and side-by-side comparison before completion. The designer must correct obvious visual deltas before publishing.
4. Keep interaction verification separate: reproducing a screen faithfully is not enough; all controls must still be click-tested and listed in the handoff.
5. Present the user only with the comparison-ready preview URL. Do **not** call a design "exact," "pixel-perfect," or approved based only on the designer's self-report; visual acceptance belongs to the user.
6. **Validate the comparison, not merely its existence.** Before sharing a screenshot-driven prototype, inspect every comparison artifact (or delegate that inspection to an independent reviewer). Confirm the left/reference half is the correct image for that route and the rendered half reproduces its defining composition. A non-empty side-by-side PNG is not evidence of fidelity. Reject the handoff if the route is mismapped (for example, a Wellness reference paired with a Goals output), a key component changes class (line chart → bar chart), or the screen is a generic substitute layout.
7. If the user rejects a prototype as visually wrong, do not iterate from the rejected artifact. First look for and recover the original referenced preview/source artifact (prior preview URL, task artifacts, source HTML) unchanged. Rebuild only if recovery is impossible, and state that distinction clearly.

**Pitfall — bogus comparison gate:** A worker can generate real, non-empty comparison images while comparing the wrong source route or a generic reconstruction. Treat comparison artifacts as review inputs: verify source-route identity and the distinctive screen structures before accepting the claim. Do not send the user a new preview merely because the worker says a visual audit passed.

**Pitfall — inspiration drift:** Phrases like “match the style” or “use this as a reference” cause generic substitute layouts even when detailed screenshots exist. Screenshot-driven briefs need route-by-route layout facts and an explicit instruction that no original visual interpretation is authorized.

## Procedure

### 1. Route one accountable delivery task

Create an explicit task for the specialist with the target workspace/repository, desired behavior and non-goals, known commits/tests/errors, verification steps, and a prohibition on unverified completion claims.

Avoid duplicate cards for the same mutation path. If a prior task is stalled, inspect its record first; use a fallback only when it remained unclaimed or is terminally blocked.

### Profile model/provider changes

Treat a request to change an agent's model as a configuration delivery, not a chat-level preference. Route it to the configuration/operations specialist when the control session cannot safely apply the Hermes CLI change itself. For a question about the current routing, inspect before answering: `hermes profile show <profile>` proves only the primary model/provider; separately run `hermes --profile <profile> fallback list` and `hermes --profile <profile> auth status <provider>` for every claimed fallback. Never infer that a fallback survived a machine migration or exists merely because the provider has credits—the fallback chain and that profile's authentication are independent state.

1. Record the profile, provider, exact model ID, and routing constraint (for example, "Claude-only" or "no fallback") in the task body.
2. Require the specialist to use Hermes-supported configuration commands rather than hand-editing `config.yaml`.
3. For exclusive-provider requests, clear the fallback chain as an explicit operation; changing the primary model alone does not prevent automatic cross-provider failover.
4. Verify the persisted `model.provider` and `model.default`, fallback state, model catalog validity, and provider authentication readiness before reporting completion. State separately if a service reload/restart was required.
5. When the user asks for the post-change roster, read every relevant profile's persisted configuration after the change; do not reuse pre-change values or infer models from task summaries.
6. **Protect configuration ownership while cards overlap:** before applying a profile-model or fallback mutation, inspect active/recent cards for that same profile and configuration path. If a newer task has explicitly changed, cleared, or cancelled a fallback, do not restore an older requested route from stale context. Surface the conflict and use the user's latest unambiguous instruction as the source of truth. After any mutation, re-read `fallback list` and leave durable supersession comments on duplicate cards so a delayed worker cannot silently overwrite the intended chain.
7. A successful one-line fallback probe proves routing, but normally costs too little to visibly change a prepaid balance. Do not use a rounded balance UI as evidence that the fallback is absent; report the provider failover log plus the exact persisted fallback chain instead.

**Pitfall — configuration collision:** Multiple operations cards can each be individually valid yet fight over the same profile fallback. Treat fallback changes as a single-writer path: sequence or cancel duplicates, then verify the final persisted chain after all related cards settle.

**Model-tier recommendation rule:** Use OpenAI Codex models for every specialist profile; Thomas no longer uses Claude. Select the tier from task complexity and the installed catalog rather than assigning the frontier model to routine work. Explain recommendations through role fit, retry risk, and current catalog pricing—not invented benchmark claims.

### Complexity-aware specialist routing

For token- and cost-efficient delegation, classify every specialist task **before worker spawn** and select the configured tier. Never switch models inside a running worker merely because the task proved harder; mid-session switching harms prompt caching and makes routing evidence ambiguous.

1. Classify deterministically from the persisted task body and metadata; do not spend an additional LLM call solely on classification.
2. Keep tier maps configurable per profile, but use one Codex-only baseline for the installed roster: **low = `gpt-5.6-terra`**, **medium = `gpt-5.6-sol`**, **hard = `gpt-6-astra`**, provider `openai-codex`. Apply it to the coordinator/default, coder, devops, security, planner, researcher, designer, scheduler, and reviewer profiles unless Thomas explicitly changes a role.
3. Make Sol the default for substantive work. Automatic routing must select only Terra or Sol; use Astra only through an explicit task-level model/provider override chosen by Mister in Control or directly requested by Thomas. Do not infer Astra from free-text risk words or compound regex rules: semantic edge-case repair loops consume more tokens than they save and remain brittle across phrasing.
4. Prefer Terra over an older mini tier for low-risk autonomous work because failed tool use and correction loops can erase nominal savings.
5. Treat an explicit task-level model/provider pin as authoritative over automatic classification.
6. Persist the complexity, chosen model/provider, and a short deterministic reason on the task or run so routing is auditable.
7. Preserve existing profile behavior when tier routing is unset or invalid; validate exact model IDs, profile-scoped provider authentication, and catalog availability before enabling a map.
8. Keep each profile's SOUL guidance concise but explicit about the tier policy, pre-spawn selection, override precedence, and prohibition on mid-session switching. Amend role guidance in place; do not copy large prompts between profiles because injected context is itself a token cost.
9. Verify rollout with bounded representative automatic-low, automatic-medium, and explicit-Astra smoke tasks, then read back both the persisted routing event and the worker's actual run model. Make the low fixture contain the exact bounded-routine signal the deterministic classifier recognizes; a task being small in human judgment does not prove the low rule fired. Do not run every tier against every profile when they share one dispatcher policy; that burns tokens without testing a distinct contract. Compare current catalog pricing when explaining savings because price relationships can change.
10. After installing dispatcher Python changes, restart the gateway before live smoke tests and verify the PID changed. A healthy pre-existing gateway can keep the old imported classifier in memory, so on-disk checks can pass while run events still report the prior routing version. Treat a stale-version smoke as a restart/cache failure, not a classifier defect; restart once, then rerun only the failed smoke.
11. Treat compatibility probes and installer checks as transactions. Discover the dispatcher module from the installer's returned target rather than hardcoding a historical filename, snapshot every touched file's bytes and prior existence before mutation, and restore that state in `finally` on success, ordinary failure, partial installation, and interrupts. Test both monolithic and split dispatcher layouts before local rollout.
10. Split disruptive local maintenance into two accountable phases. Have DevOps complete every non-disruptive preflight first and block with exact evidence when gateway stop/restart requires interactive approval. In the initiating desktop session, stop the gateway through the supported command and approval gate, install/configure while it is drained, restart it, read back gateway/profile/routing/fallback state, then unblock the same DevOps card for independent live smoke verification. Do not ask a headless worker to bypass the approval guard or claim the rollout complete from configuration readback alone.
11. For provider-exclusive migrations, clear fallback chains as an explicit verified phase. `hermes fallback clear` is interactive; in an approved terminal maintenance session, feed the confirmation non-interactively (for example, `printf 'y\n' | hermes -p PROFILE fallback clear`) and then run `fallback list` for every profile. A cancelled prompt with exit code zero is not a cleared chain.
12. When a profile bundle and a routing/classifier repair are developed in parallel from the same older base, do not deploy either branch independently in sequence: the later installer can restore the older shared routing module. Create one integration card parented to both independently approved branches, require a single descendant SHA whose tree contains both changes, rerun the shared routing and profile-lifecycle checks there, and gate every installer/activation card on that integrated SHA.

**Pitfall — semantic-classifier loop:** Do not build a free-text risk parser to decide when to spend Astra tokens. Phrasing exceptions create repeated implementation/review cycles and unstable cost behavior; keep automatic routing binary (routine→Terra, otherwise→Sol) and make Astra explicit. If a semantic classifier already exists and its first focused review produces wording-specific exceptions, stop after that single repair/review cycle instead of spawning more regex patches: supersede the semantic lane, create one project-linked simplification card, and gate integration plus rollout on the simpler descendant.

**Pitfall — parallel-branch rollback:** An approved profile feature can still overwrite a newer classifier fix when both branches modify the routing module. Approval per branch is insufficient; integrate overlapping descendants before any live install.

**Pitfall — partial-profile rollout:** Do not update only coder/devops after the user adopts global routing; stale designer, planner, scheduler, or coordinator instructions can silently reintroduce a retired provider or bypass the tier policy.

**Pitfall — mutating compatibility check:** Do not call an installer from a “check” command and then inspect a hardcoded legacy target. Dispatcher layouts evolve, and a post-install assertion can fail after modifying the checkout. Consume the installer's actual target and prove byte-for-byte rollback across every exit path before treating the check as safe.

**Pitfall — cheapest-model fallacy:** Do not choose the nominally cheapest model without accounting for capability on autonomous work; retries, malformed tool calls, and repair loops can consume more tokens than a stronger low tier.

### 2. Model the dependency graph

When follow-up fixes must wait for a primary release, create each as a child with `parents=[primary-task-id]`. Put the prerequisite in the task body too.

### Dedicated lean review lane

Route routine implementation review to a dedicated `reviewer` profile instead of loading the broader security role for every diff.

1. Keep the reviewer context narrow: requirement matching, diff correctness, regression risk, test adequacy, and actionable approve/request-changes verdicts.
2. Route ordinary bounded reviews as low/Terra and broad, cross-file, migration, production, or security-adjacent reviews as medium/Sol. Never auto-select Astra for review content; Astra requires an explicit task override from Mister in Control or Thomas.
3. Keep authentication, authorization, secrets, privacy, tenant isolation, destructive operations, and release/security gates with the security profile; do not weaken security review merely to save tokens.
4. Choose exactly one review topology before dispatch: either same-card review or a pre-created review child. If a review child already gates descendants, the implementer must complete its implementation card to release that child; it must not also request same-card review. If same-card review is chosen, approve with completion, reject with concrete requested changes, and block only for a genuine external dependency. Never attach both review forms to the same release path—the duplicate gate creates redundant work and can strand integration.
5. Verify the reviewer profile exists in profile discovery, has Codex authentication, can execute review lifecycle transitions, and is referenced by standard review task templates before replacing the old lane.

**Pitfall — security-context tax:** Do not use the security profile for routine style, test, or requirement review; its broader prompt and gates increase token use and blur ownership. Conversely, do not send sensitive changes to the lean reviewer merely because Terra is cheaper.

### Protected instruction-file writes

SOUL, AGENTS, and similar instruction files may require foreground approval even when a headless worker is otherwise authorized. Treat that approval as a separate interactive gate rather than a reason to decompose the content work repeatedly.

1. Have the worker finish inventory, backups, exact target paths, and insertion-ready content before requesting the protected write.
2. If approval times out, block once with the exact paths and proposed scope. Do not retry from another headless card or write through an alternate path; the protection follows the instruction-file class.
3. In the initiating foreground session, perform the same narrow `patch` or `write_file` operation so the user can approve it, verify the write, then unblock the original worker for tests, commit, push, or activation.
4. If automatic decomposition appears, stop duplicate mutation children and retain only useful read-only inventory/verification steps. Decomposition does not remove the approval boundary and can multiply token use.

**Pitfall — approval-loop amplification:** Repeatedly respawning a headless worker for the same protected SOUL write only repeats the timeout. Surface one foreground approval operation, then return the durable work to the original pipeline.

### Keep implementation capacity busy during review

Before creating a numbered delivery graph, classify each item by the files and contracts it mutates. Use the two available lanes deliberately: while Security independently reviews item **N**, immediately dispatch item **N+1** when it is isolated from the reviewed worktree. Keep it in its own worktree, require its own review, and prohibit deployment or integration until every relevant review passes.

- Serialize work that edits the same route, shared component, schema, OAuth contract, or release path; review overlap does not make a merge conflict safe.
- Separate an implementation handoff from its review gate when later independent work should run concurrently. Do not make every later implementation a child of the same-card review completion merely for convenience; that leaves the coder idle even though Security is working.
- If an existing graph is already over-gated and a user authorizes parallelism, create the smallest non-conflicting fast-lane task and re-purpose the later duplicate card as an integration/reconciliation check. Add explicit parent edges and a durable supersession comment so it cannot reimplement the same scope.
- After changing the graph, re-read the fast-lane task and report it as active only if it is `running` with a worker run; call it queued if it remains `ready`.

**Pitfall — policy without dispatch:** Do not answer a complaint about idle implementation capacity with a promise to parallelize later. Inspect the active review and mutation boundaries, then create or promote the next safe task in the same turn; otherwise the delivery graph still enforces the avoidable wait.

### User-directed review waiver

When Thomas explicitly says to skip a review or approval gate, treat that as a release-graph change and execute it immediately rather than silently restoring the gate later. Require the waiver to name the review/gate unambiguously: a generic “go ahead and deploy” while an independent review is already running authorizes deployment intent, but does **not** waive that active review. Keep the deployment parented to the active reviewer unless Thomas explicitly says to skip or ignore that review; otherwise a rejection can arrive after an irreversible production write. If an ungated deployment was mistakenly started while review remained active, stop it immediately, verify the exact external deployment state instead of assuming cancellation won, and choose one bounded rollback or fix-forward path based on observed production state.

**Cost-control rule after review rejection:** create one focused repair → one focused re-review → one deployment chain. Every re-review brief must name only the newly reported blocker and explicitly inherit previously accepted evidence; do not reopen the whole implementation unless the repair changes a shared contract that invalidates that evidence. Once an independent reviewer approves the exact repaired SHA for that blocker, close or supersede redundant review cards and release the existing deployment gate—do not add another “final full review.” Do not let reviewer-generated fan-out coexist with coordinator replacements, and do not rerun broad audits or unchanged full suites when focused reproductions plus existing trusted evidence are sufficient. Avoid goal mode for bounded repair/review cards with pre-created descendants; auxiliary judge failures can exhaust turns after the code is already committed and multiply recovery tasks without improving the artifact. Before replacing a blocked worker, inspect its worktree, `git status`, local HEAD, and remote ref for durable completed work. If the worktree has only uncommitted partial edits, run the narrow acceptance test before salvaging them; preserve them only when the target regression passes **and** existing visual/build gates still pass. A newly passing bug test beside widespread baseline regressions is not a recoverable completion—start one clean replacement from the last known production SHA and carry only the proven behavioral contract, not the partial diff.

1. Record the waiver verbatim or unambiguously in the implementation and deployment briefs, including that no independent review was performed.
2. Remove the review card from the critical path: create staging/production descendants directly from the verified implementation task, while retaining normal build, test, exact-SHA, deployment, and live-health checks. A review waiver removes the reviewer step—not execution verification or owner/auth boundaries.
3. If a pre-created review card cannot be cancelled because it is still parent-gated, do not make new release cards depend on it and do not describe it as pending work. Leave a durable supersession comment; if it later becomes runnable, stop/block it at the first lifecycle state that supports cancellation.
4. Keep explicit non-goals intact. For example, broadening feature eligibility must not silently remove per-user credentials, owner scoping, hashing, revocation, unauthenticated denial, or unrelated registration policy.

**Pitfall — waiver reintroduction:** Do not tell the user a review is skipped and then preserve a hidden dependency on that same review card. The board graph, task briefs, and status language must all reflect the latest instruction.

**Pitfall — review-loop amplification:** Do not send an exact SHA through repeated whole-process reviews after each narrow correction. Verify only the changed contract plus regression boundaries affected by that change, reuse prior accepted evidence, and proceed to deployment when that scoped issue is approved.

**Rollback-lineage reconciliation:** When an emergency rollback makes `origin/main` diverge from an approved release SHA, do not force-push by default and do not restart the full implementation review. Ask once for the release-history policy if it is not already authorized. For the history-preserving path:
1. Start from the exact current rollback `origin/main` and create one commit whose resulting tree is exactly the approved release tree, without modifying release content.
2. Prove ancestry and identity with `git rev-parse <integration>^`, `git rev-parse <integration>^{tree}`, `git rev-parse <approved>^{tree}`, `git diff --exit-code <integration>^{tree} <approved>^{tree}`, `git diff --check <rollback>..<integration>`, and `git ls-remote` for the pushed ref.
3. Route one narrow independent check covering only rollback ancestry, remote SHA, and byte-for-byte tree equality. Tree identity reuses the prior implementation approval; it does not justify another broad audit.
4. Deploy the exact approved integration SHA through a fast-forward from rollback `main`, then verify remote `main`, deployment state, and live health.

**Pitfall — approved tree on divergent history:** A release guard can correctly reject an independently approved SHA when rollback `main` is not its ancestor. Do not misclassify this as a code-review failure or discard rollback history; reconcile ancestry with a tree-identical integration commit and review only that equivalence.

### User-directed environment waiver or retirement

When Thomas explicitly removes staging from a release path, treat it as an immediate graph and infrastructure change—not as permission to let the in-flight staging lane finish quietly.

1. Comment the stop instruction on the active staging card and transition it out of execution immediately. If a deployment was already triggered, report that exact fact; do not claim the deployment was avoided.
2. Do not reuse a production card that still depends on the stopped staging parent. Create one direct-production card parented to the last approved implementation/security gate, carry the exact immutable SHA, and state that staging was explicitly waived while build, auth-boundary, deployment-guard, and live-health verification remain required.
3. Leave the obsolete staging-gated production card inert; do not complete it merely to free descendants.
4. Treat “stop using staging” and “delete staging” as different operations. For deletion/retirement, create a separate post-production operations card. Inventory service, database, volume, variables, domains, cron/webhooks, and branch triggers; prove none are shared with production; preserve a sanitized recovery record; remove only staging resources; then re-read platform state and recheck production health.
5. Never let environment cleanup race the replacement production release. Parent retirement to the verified direct-production card.

**Pitfall — hidden staging dependency:** Announcing that staging is skipped while the only production card still depends on the blocked staging task leaves the release permanently gated. Rebuild the graph in the same turn and verify the replacement production card is actually runnable.

### Explicit review ownership for user-visible changes

Before dispatching a user-visible implementation, identify the exact independent review card or same-card review transition that will validate it, unless Thomas has explicitly waived review for that delivery. A downstream feature or integration child is **not** a review gate merely because it depends on the implementation.

1. Require a real app runtime for visual acceptance: a blank page, an unmounted client shell, or a screenshot of a route that did not load is failed evidence, not a partial pass.
2. If an implementation card completes without its explicit review route, immediately create one bounded independent review card with the implementation as parent. Require viewport, interaction, accessibility, and relevant state checks; do not declare the UI approved beforehand.
3. Keep subsequent non-conflicting work moving while that review runs, but prohibit merge/deployment claims for the unreviewed change.
4. In task briefs, name the actual route/component being changed after repository inspection. Do not rely on a product-area label when the feature is rendered elsewhere.

**Pitfall — downstream-child-as-review fallacy:** A card can have children yet still have no reviewer. If a later integration card is mistaken for QA, user-visible changes can be marked done without real visual execution; model review ownership explicitly.

### Task-brief integrity check

Immediately re-read every newly created card before trusting that delegation succeeded. Confirm the persisted body contains every acceptance criterion, file path, user correction, and release boundary. Keep creation bodies compact enough to survive the tool payload; move the authoritative ordered acceptance contract into one durable comment when the scope is long. If the card contains a literal truncation marker or ends mid-requirement, add the complete specification before dispatch and re-read it. If the worker is already running, do not assume a new board comment enters its current context: steer the active run when supported, or stop/requeue the same card after preserving durable work. If it already blocked, add the full comment and explicitly unblock the same card rather than creating a duplicate.

**Pitfall — truncated-brief handoff:** A successful card-creation response proves the row exists, not that a long task body survived intact. Workers correctly stop when binding requirements are replaced by truncation text, and later piecemeal corrections can omit earlier constraints. Keep briefs compact, put the authoritative ordered acceptance list in one message, and verify persistence immediately.

### Repair malformed generated task graphs

Treat automatically generated children and goal-mode decomposition as untrusted until their execution graph is validated:

1. Immediately read every generated child—including children created autonomously by reviewers or repair workers—and verify `workspace_path` is resolved, its target commit is current, its parent edges point in the intended direction, and its assignee exists. For every repository-backed implementation or review card, pass the registered **project slug/name returned by project discovery**, never an internal database project ID copied from task metadata, together with `workspace_kind=worktree`; internal IDs may not resolve through task creation and can silently yield a worktree card with no path. Require a concrete `workspace_path` in the read-back before treating the card as runnable or linking it as a parent of any gate. A child in `ready` with `workspace_kind=worktree` but no path will fail repeatedly rather than create its own worktree. If a specialist generated both an unresolved card and a valid project-linked replacement, close the unresolved card as superseded immediately with the replacement's exact acceptance evidence; do not wait for its retry budget or attach it to any gate.
2. Before enabling goal mode on a card with pre-created review or release descendants, check for a circular lifecycle condition: the parent must be allowed to complete and release its children without a judge demanding that those children finish first. Use ordinary completion for the implementation phase when downstream review/release cards already encode the gate.
3. If the generated graph is malformed, stop or capability-block every runnable invalid sibling before creating replacements; otherwise dispatcher retries create noise and consume specialist slots. Leave non-runnable `todo` fan-in nodes inert rather than trying unsupported state transitions.
4. Replace the malformed subtree with the smallest project-linked task that can decide the gate. Pass the exact immutable commit, use `project=<slug>` plus `workspace_kind=worktree`, keep the run bounded, and avoid goal mode when a focused approve/request-changes decision is sufficient.
5. Re-read the replacement and confirm a real workspace path before reporting recovery.
6. Treat parent-edge additions as effectively irreversible during the run. Before linking another review to an existing deployment, inspect every current parent and choose one canonical review. Do not stack duplicate reviewers “for safety”: a later redundant `todo` parent can strand an otherwise approved release because there may be no supported unlink operation.
7. When a goal judge creates a circular requirement—such as refusing `kanban_request_review` until approval already exists—do not create a review child parented to the blocked implementation; that child cannot run until the implementation completes. Create one bounded parentless review card with the exact immutable SHA, then use its approval evidence to close the implementation. Link only that canonical reviewer to deployment, and close generated duplicate cards as superseded rather than letting them fan out.

**Pitfall — decomposition amplification:** Retrying a root review after judge/rate-limit failure can auto-create several children that all inherit a missing workspace. Validate the first generated child before allowing the fan-out to run; one correctly linked focused review is safer than a broken multi-card audit.

**Pitfall — irreversible redundant gates:** Do not attach both an attempted review card and its working replacement to the release task. Because parent edges may not be removable, the abandoned card becomes a permanent release dependency and forces administrative cleanup or duplicate execution.

**Missing-workspace recovery:** When a generated implementation or rework card fails because its worktree path is unresolved, do not attach that failed card as a new parent of an already-created review or release gate. That permanently strands the gate behind a terminal task. If a valid project-linked replacement already exists and has completed the same scope, close the invalid card as superseded with the authoritative task and immutable SHA; otherwise create one complete replacement chain—project-linked implementation → fresh independent review → fresh deployment—with only runnable parent edges. Leave durable supersession comments on the abandoned chain, then re-read every replacement to confirm its workspace path and parent list before reporting recovery. Treat a completion notification for a superseded card as administrative closure, not new implementation evidence.

**Replacement-race rule: A timed-out worker may resume and commit after a replacement was created. Inspect both worktrees before either task mutates further. If the original now has a clean durable commit, route that exact SHA directly to review and mark the replacement superseded; never let both implementation lanes continue against the same files.

**Production-baseline worktree rule:** Before creating a mutation or release-repair worktree, compare the local primary `main` with `origin/main` using `git rev-parse`, `git merge-base --is-ancestor`, and a clean status check. A local `main` can contain unpushed or divergent work that is not the deployed product. For a production defect, create the task worktree explicitly from the verified remote production SHA (for example, `git worktree add <path> -b <branch> origin/main`) and verify its `HEAD` before dispatching. Do not let a project default worktree silently choose a local branch when the task contract names a production baseline.

**Pitfall — wrong-baseline repair:** A change can compile and pass tests while modifying a local branch that does not match production; subsequent UI diagnosis and deployment evidence are then about a different app. Treat remote ancestry and the task worktree’s exact `HEAD` as acceptance prerequisites, not setup trivia.

**Goal-judge failure recovery:** When a goal-mode card blocks after exhausting turns because the auxiliary judge errors or is denied, do not assume implementation failed and do not immediately rebuild it. Inspect the assigned worktree first: require a clean status, committed HEAD, matching remote branch SHA, and real reruns of the bounded acceptance suite. If those pass and pre-created review/release children encode the remaining gates, complete the implementation phase with the exact SHA, test evidence, and the judge failure clearly disclosed so the independent reviewer can continue. Flag any acceptance criterion that passing test names or assertions do not actually prove rather than laundering the worker's self-report into approval.

**Parentless superseded-card rule:** Do not dependency-block a duplicate card that has no actual parent edge. The board immediately re-promotes parentless dependency-wait cards and can dispatch the duplicate again, wasting quota and specialist capacity. When another card has verifiably completed and approved the same scope, close the duplicate with `kanban_complete` and record the authoritative task and immutable commit in metadata; otherwise use an accurate non-dependency blocker.

Do not launch concurrent work that may edit the same OAuth, deployment, or data path unless tasks have distinct ownership boundaries. When collision risk is unclear, sequence work.

### Review-lane viability check

Before using a review task as a parent gate for implementation descendants, verify that the review lane can actually execute:

1. Check the proposed reviewer profile's configured provider/model, authentication, known quota state, and active queue before creating the gate. If the user has already said that provider is quota-exhausted, do not create a required task on it; choose an allowed independent profile immediately. A visually sensitive implementation can be reviewed by a non-designer verifier when the design model is unavailable, provided the brief requires exact viewport rendering, screenshots, overflow/clipping checks, and larger-width regressions.
2. If a provider becomes unavailable after a gated task exists, create one replacement review task on an available provider with the same parent and acceptance criteria, mark the old task superseded in a durable comment, and block it as soon as its lifecycle permits. Do not leave two review lanes that may both execute later.
3. Read the proposed reviewer profile's active queue and confirm a real reviewer run can be created; a task merely marked `review` is not evidence that review automation exists.
4. After requesting review, re-read the task record. `status: review` with `current_run_id: null` and no review-run event is a **stalled gate**, not an active review.
3. Do not describe downstream work as proceeding while foundational review gates are stalled. Name the exact affected foundations and descendants.
4. If a review task is stuck and the supported `kanban_request_changes` action says there is no active review run, stop retrying it. Route a high-priority Kanban workflow-recovery task to devops with the card IDs, current status/run evidence, required rework, and instruction to use supported board mechanisms rather than editing the SQLite database directly.
5. For foundations, retain strict acceptance: visual shell work needs real desktop/mobile render evidence, and backend work needs its declared API/schema/validation acceptance checks before descendants unlock.

**Pitfall — phantom review gate:** A planner can assign a task to `reviewer` and successfully put it into the review column even when no reviewer run starts. Every dependent route remains `todo` indefinitely. Detect this immediately from `current_run_id`/run history, not from the card label, and create a workflow-repair handoff rather than reporting that the rollout is active.

### Durable-review handoff gate

A reviewer can correctly verify code running in an implementer's workspace while the reviewed branch still points at an older, defective commit. Treat that as **changes requested**, never as an acceptance merely because runtime checks pass.

Before approving a foundational card or releasing any descendants:
1. Read `git status --porcelain`, `git rev-parse HEAD`, and the corresponding remote branch SHA.
2. For an RC, require a named remote ref: run `git ls-remote origin <rc-ref>` and confirm it resolves to the exact candidate SHA. A local worktree branch is not a durable review artifact.
3. If the verified fixes are unstaged/uncommitted or the RC ref is absent, require the implementer to commit only the intended source files, push the branch, and report the new exact SHA/ref.
4. Re-read the task after re-review and verify the accepted SHA contains the reviewed fixes. Do not release dependent cards from an ephemeral scratch/worktree modification.
5. During unattended/overnight execution, monitor each foundational handoff through the full state transition: implementer work → durable commit/push → qualified review → `done` → child promotion. A review request or a passing local render is not enough to tell the user work will continue overnight.

**Pitfall — verified-but-ephemeral fix:** An execution reviewer may prove the code is correct in a live scratch workspace while `HEAD` and the remote branch still reference the previously rejected implementation. If descendants branch from that ref, every route inherits the old defect and the correct working-tree edits disappear when the workspace is cleaned. Require commit/push evidence before approval.

**Review-crash recovery:** When an implementer has already pushed a durable RC and its same-card reviewer crashes twice, do not restart integration or let the card retry indefinitely. Leave the original card blocked with the immutable remote SHA, then create one fresh, project-linked, bounded review card on an available reviewer profile. Require the reviewer to fetch that exact remote SHA, rerun only the changed-contract acceptance suite, and report approve/request-changes without merging or deploying. If that single replacement also crashes repeatedly while the RC remains durable, stop creating reviewer cards: the coordinator should independently inspect the scoped diff, run the exact bounded tests/build/diff/remote-SHA checks, record the evidence on the blocked review card, and make the approve/request-changes decision. Never use coordinator recovery to waive an untested contract or to reopen the whole previously approved pipeline. This separates worker-process failure from RC integrity and prevents crash loops from blocking a verified release.

### 3. Treat credentials as a release gate

**See `references/ta<REDACTED_SECRET>.md` for critical pattern:** When a provider credential is exhausted and DevOps resets it globally, some sibling tasks auto-recover but others remain dispatcher-stuck in `ready` state despite the credential being fresh. This is a per-task cache issue in the dispatcher, not an auth failure. Immediate recovery: create a fresh replacement task with priority=100.

A local commit plus passing tests is not shippable until push authentication, remote commit presence, and deployment success are verified.

When a credential is missing or rejected:

1. State the failed operation and non-secret provider error.
2. Distinguish a valid credential with insufficient effective permission (such as a GitHub 403) from no credential.
3. Ask for the smallest secure user action only after available non-interactive paths are exhausted.
4. Never request credentials in chat; direct the user to a secret store or provider UI.
5. On replacement, resume one focused shipping task and require push, remote, deployment, and live-behavior verification.

Do not treat a login created in one isolated runtime as proof that another worker runtime inherited it.

### 4. Verify release claims end-to-end

Preserve the user's requested release boundary. A request to **push to `main`** requires integration, tests, push, and remote-SHA read-back; report that as complete once those pass. Do not make deployment a hidden acceptance criterion that turns a successful push into a blocked result. If `main` may auto-deploy, state that consequence separately and create deployment/live verification only when deployment was explicitly authorized or a standing release instruction applies.

For protected routes, use [protected-route staging verification](references/protected-route-staging-verification.md) to keep deployment evidence separate from authenticated UI evidence.

A production fix needs evidence that: (1) the commit exists locally, (2) relevant tests/build passed, (3) it is on the intended remote branch, (4) the correct GitHub-triggered deployment succeeded, and (5) the user-facing behavior was verified against production.

Keep release verification proportional. When an exact immutable commit already passed independent build, browser, and feature tests, do not repeat the entire expensive viewport suite before pushing unless integration changed the tested files or introduced conflicts. Re-run a production build plus bounded critical smoke tests, verify the remote SHA, then spend the saved time on exact deployment and live-behavior checks. Explain unusually long releases in terms of concrete gates rather than generic waiting.

**Run deployment UI verification headlessly by default.** A live route check does not authorize opening tabs in the user's visible browser. Require Playwright/headless browser execution (or background desktop automation when a native app is genuinely necessary), and name this constraint in DevOps/QA task briefs. Escalate to foreground only with explicit user permission; otherwise a successful visual check that disrupts the user's browser is still a workflow failure.

If any boundary is absent, say which boundary remains. Do not ask the user to test behavior that a specialist can test.

**Preview artifacts (clickable prototypes, HTML files):** Before announcing a preview URL to the user, independently verify it is reachable and rendering. Fetch the exact full URL with a quick HTTP request or test it from the primary session. Copy opaque preview identifiers verbatim from the verified task artifact/output—**never abbreviate, reconstruct, or infer a URL from a truncated completion notification.** Broken links damage credibility; see `references/preview-artifact-verification.md` for the verification checklist.

**Never declare a helper script or tool absent from a prompt note, doc, or memory alone.** Environment notes go stale across migrations and reinstalls. Spend one `find`/`search_files` call to check before telling the user a capability is unavailable — asserting absence and then discovering the tool exists costs more credibility than the check costs time.

**One failing delivery channel is a diagnosis, not a format problem.** When the user says a preview, image, or artifact "doesn't work," do not climb a ladder of alternative formats (URL → inline image → copied path → attachment → base64 → prose). Each retry looks like progress and delivers nothing. After the **second** failure, stop emitting artifacts and establish two facts: does the artifact serve correctly at the source (HTTP status from the primary session, file exists with non-zero size), and what exactly does the user see on their end (blank, error text, spinner, nothing)? Server-side success plus client-side failure localises the problem to their viewer or network — which no new format will fix. Ask for the observed symptom instead of generating a sixth variant.

**A verified-healthy server does not make a link reachable for the user.** Host-local health checks (`127.0.0.1` probes, tunnel status output, a local `curl` returning 200) prove only that the service answers on the machine running it. Do not present that as evidence the user's click will work; state which boundary you actually verified.

**Reference-fidelity delivery rule:** In screenshot-driven work, do not call a build “exact,” “pixel-perfect,” or “matching” from a worker summary. Independently inspect every route’s comparison artifact for correct reference mapping and the defining composition before delivering a verified preview. If the comparisons cannot be rendered or inspected, report that as an unpassed gate, not as fidelity verification.

**Screenshot-driven design fidelity:** When the user provides reference screenshots and asks for them to be built into an application, screenshot-to-code fidelity often fails on the first iteration. Do not iterate with vague user feedback ("looks wrong"). Instead, manually extract exhaustive visual specs from the reference images using vision tools and create a new designer task with these specs as the authoritative brief, plus explicit visual-comparison requirement. Before publishing the preview to the user, independently verify the designer's comparison evidence (route mapping, compositional structures, colors, spacing). See `references/bitewise-screenshot-driven-redesign-workflow.md` for the full pattern and an incident example.

**Designer iteration efficiency — when to pivot:** After 3+ fix cycles on a visually broken layout, stop iterating on that approach. Instead, pivot to a full redesign task: research industry standards, create 3 distinct design concepts, show mockups/previews to the user, and let them pick one. This is more token-efficient than chasing unknown bugs across multiple deploy cycles and produces better UX outcomes. See `references/designer-iteration-efficiency-when-to-pivot-2026-09-06.md` for the decision criteria and real-world example from the BiteWise Foods page redesign (4-cycle iteration fail → pivot to 3-version redesign → user pick + clean implementation).

**Merged but not live is a BLOCKER:** When code is merged to main, DO NOT report to the user as "done" or "deployed" until you verify it is actually live. Merged ≠ deployed. Check:
- Railway deployment status (service status, latest deployment ID)
- Whether the live service is running the merged commit
- If not, trigger redeploy and verify it completes
- Only then report to user with evidence (service URL confirmed, tested behavior, or error logs examined)

This is especially critical for dashboard/UI changes—a rebuilt frontend must be deployed, not just committed. See Thomas's session 2026-09-03: subscription feature was merged but dashboard was still serving stale code; had to route to devops for redeploy verification.

**Protocol violations on multi-step deployment chains (CRITICAL PATTERN — Session 2026-09-05):**
When orchestrating multi-stage rollouts (QA → Staging → Production), worker tasks may exit cleanly (rc=0) without calling `kanban_complete` or `kanban_block` at any stage. This protocol violation pattern indicates **blocked or stalled specialist work**, not completion:

1. **Symptom:** Task shows `running` with recent heartbeats, but `worker exited cleanly (rc=0)` event appears in history, and task remains in `blocked`/`ready` after 2+ failed attempts.
2. **Root causes (in order of likelihood):**
   - **Missing git branch infrastructure** (MOST COMMON): When fanning out N child tasks from M parent tasks, all N git branches must exist in origin before dispatcher starts. If a branch is missing, coder/designer agents crash silently with rc=0 when attempting to push commits (no TTY to prompt for auth, so git push fails, agent logs nothing, exits cleanly). See `phased-rollout-gated-kanban` skill, **Git Branch Infrastructure** section, for recovery.
   - **Provider credential exhaustion** (HTTP 429, auth failures): Claude/Codex quota hit, GitHub token expired, Railway auth stale. See `railway-cli` skill and **Credential Management** section in `phased-rollout-gated-kanban`.
   - **Task-specific dispatcher cache issue** (post-credential-reset): After a global credential reset, some queued tasks auto-recover but others remain stuck in `ready` with stale credential cache. See `phased-rollout-gated-kanban` **Task-Specific Stuckness After Global Credential Reset** section for immediate recovery (fresh replacement task with priority=100).
3. **Recovery hierarchy:**
   - Check git branches FIRST: `git branch -r | grep bitewise/t_<stuck_task_id>` — if missing, create and push.
   - Check credential state SECOND: Ask devops to probe provider state (fresh token, quota available).
   - Check dispatcher THIRD: Read task's `started_at`, `current_run_id`, and recent events. If task never spawned despite being in `ready`, it's a dispatcher cache issue (see Recovery section above).
4. **Do NOT wait for retry limits or 4-hour timeouts.** After detecting a second protocol violation on the same task, immediately create a fresh replacement task with priority=100 (if git + credentials are OK). The stuck task will not spontaneously recover.
5. **When reporting to user:** State the exact root cause discovered (missing branch, stale credential, dispatcher cache) and whether you recovered it (created branch, reset credential, dispatched fresh task) or handed off to devops. Do not use generic language like "task is stuck" — name the specific blocker.

**Client-contract verification:** For browser extensions, deep links, OAuth callbacks, and other multi-client handoffs, a healthy endpoint or a correct provider redirect is not end-to-end proof. Verify the exact return contract: the client launch parameters, server-side state correlation, callback target, and client-side receipt/handling. If the user reports the real flow still fails, treat that report as decisive evidence that the prior verification was incomplete; reopen an end-to-end specialist task rather than defending the earlier conclusion.

### 5. Give useful status updates

When the user asks for status, **always read task records first**. Do not guess or report based on optimistic assumptions about dispatcher behavior. Treat status as a race: if the user challenges a just-reported queue or worker state, immediately refresh both the target card and the assignee's running queue before defending the snapshot; a predecessor may have completed and the dispatcher may already have claimed the next card. Answer, in order:

- Is work active (running with recent heartbeat), queued (ready/todo with no run started), blocked, or done?
- What is the latest verified artifact/outcome?
- What is the next verified gate?
- Is user action needed now? If so, state one secure, concrete action.
- **If work is queued but appears stalled beyond normal dispatcher latency:** Read both the `running` and `ready` queues for the assignee. A duplicate or superseded task running on the same assignee will silently block newer work. Flag it immediately and terminate or close the stale task when its supersession is verified.
- **If the user challenges a long period without pushes:** compare local HEAD, remote feature/RC refs, and remote production-branch SHA before answering. State plainly which boundary is complete—local commit, remote branch, main, deployment, live verification—and immediately route the smallest missing durability step instead of recapping every prior review.

**Dispatcher timing:** A task in `ready` or `todo` status with no `started_at` timestamp means it has NOT begun—the dispatcher picks it up on its next tick (can be instantaneous, can be many seconds to a few minutes depending on other running tasks). Do not report "starting soon" or "actively working" unless `running` status and a recent heartbeat confirm it. Conversely, do not tell a user "it hasn't started yet" if you did not read the task record—you cannot know.

**Prove actual progress when challenged:** A `running` card plus dispatcher heartbeats proves that a worker process is live, **not** that it has produced useful work. If the user asks “is it actually working on something?” (or expresses similar skepticism), inspect the assigned workspace or task artifacts in addition to the task record. Report only observable evidence: created/modified artifact names, size/mtime, a real progress comment, test/render output, or a published preview. If there is no such evidence, say plainly that the worker is live but tangible output has not yet appeared—do not use heartbeats as a substitute for progress.

**Zombie-worker condition:** A worker PID can become `defunct`/zombied while the Kanban dispatcher continues emitting heartbeats. Treat this as failed execution—not active work. When a running card has no artifacts or progress and the user questions it, inspect the spawned PID with `ps -p <pid> -o pid,stat,args` and inspect the assigned workspace. A `Z`/`defunct` PID plus no tangible output is conclusive. Block the failed card as `transient` with the evidence, then create a fresh priority-100 replacement carrying the original brief and the configuration/recovery context. Re-read the replacement card to verify it is `ready`; do not claim it is executing until it is claimed and produces an observable artifact.

**Dispatcher `gave_up` event = diagnose startup before replacing.** When a task shows repeated `crashed` events followed by `gave_up`, the dispatcher has exhausted its retry budget and will not spawn that card again. Read the task-specific worker log before interpreting the generic `pid ... not alive` event; the event records process death, while stderr often names the actionable startup rejection.

1. Inspect the task record to identify the log/task ID, then read the task-specific Kanban log.
2. If stderr names a deterministic launch-input failure, correct that input in the replacement rather than copying the brief unchanged. In particular, verify every requested skill exists in the **assigned profile**, not merely in the coordinator's library; unknown profile skills can make the CLI exit before the agent starts.
3. **Before calling any crash-loop "flaky", correlate the crash window across the assigned profile log and the central log.** Start with `$LOCALAPPDATA/hermes/profiles/<assignee>/logs/errors.log`, then inspect `$LOCALAPPDATA/hermes/logs/errors.log`; grep for timestamps matching the task's actual run, not merely the newest historical `429`. A worker that dies ~60s after spawn with an empty task log may be rejected by its provider, but stale errors from another profile or earlier session are not evidence for the current failure. Use `grep -nE "RateLimitError|usage_limit_reached|429|API call failed after" <log> | tail -40`, and require a matching timestamp, provider, and model before diagnosing quota exhaustion. If the matching profile log only shows startup/plugin loading and no provider call or error, report an unresolved startup failure rather than inventing a quota cause. See `references/provider-quota-exhaustion-diagnosis.md`.
4. If the log is genuinely empty and no provider or deterministic cause is visible, treat it as an infrastructure hiccup and create one priority-100 replacement with the same brief.
4. Re-read the replacement after one dispatcher cycle. Call it recovered only when it is `running` with a real run and recent heartbeat; inspect task output/workspace as well before claiming useful progress.

**Pitfall — crash amplification by copied launch metadata:** Do not clone task skills, model overrides, or other launch metadata blindly into a replacement. A deterministic startup rejection will recur identically and consume the new task's retry budget; validate or remove the rejected metadata first.

**Release-verifier crash exception:** When a DevOps card performs only post-release verification and crashes twice, do not blindly create another replacement if the coordinator has already independently verified the exact deployed SHA, deployment state, and a live endpoint. Record that evidence durably on the card and report the verifier failure as redundant. Never use this exception for a card that still must mutate, promote, or deploy external state; those actions remain release-operator owned.

**No invented ETA:** When the user asks “how much is left?”, do not manufacture a percentage or time estimate from a live task. State the tangible artifact already produced, then list the exact unpassed acceptance gates (for example: route-level renders, interaction audit, mobile state, preview publishing). Give a duration only when the worker or a measurable job queue supplies a defensible estimate. This makes the distinction between “the build exists” and “the delivery is verified” explicit.

**"Can I view it live?" rule:** Read the task state and inspect available artifacts before replying. A branch/local screenshot is not a live deployment. If no independently reachable preview/staging URL exists, say that plainly; offer the exact approved prototype URL if it is still the only interactive surface, and attach a verified current screenshot/artifact only as an **in-progress branch view**. Do not describe it as interactive, deployed, staging, or live. If a temporary preview can be published without modifying production, verify the full URL before sharing it.

**Stalled queued work (CRITICAL LESSON — Sept 1 incident):** If a user reports work is taking longer than expected and the task is in `ready` but has not started, ALWAYS check for a running sibling/duplicate task. The dispatcher respects concurrency limits per assignee, so an older zombie or superseded task will SILENTLY BLOCK newer ones even if the newer card looks well-formed. This is not a theoretical risk — a 3-hour deployment stall happened because a duplicate PII-scrub task in `running` (with only stale heartbeats, no actual progress) blocked a newer, clean deployment card.

**Immediate action if queued work stalls > 1 dispatcher cycle:**
1. Read the assignee's `running` task record. Check `started_at` timestamp and heartbeat recency.
2. If the running task is old, appears stuck, or is explicitly superseded (note: check comments for `SUPERSEDED:` marker), surface it to the user immediately: name the zombie task, explain why it blocks the new work, and recommend canceling it.
3. Do not assume the dispatcher or hourly recovery will unblock this — actively interrupt with a kanban_comment marking the task superseded and ask the user to confirm termination if needed.
4. After the blocker is cleared, manually verify the next queued task actually enters `running` state before reporting progress to the user.

For an offline user, queue dependencies, identify the single real blocker, and send a concise delivery-channel summary WITH explicit zombie-task callout if one exists. Do not promise queued work is already running without verification.

## CRITICAL: Catch False Completions During Active Work

**Pattern (Session 2026-09-06):** Coder claims a Foods page layout fix is already complete ("no code changes were needed") without actually testing the staging app. User immediately reports the app is completely broken. The false completion occurred because the worker read a PRIOR task summary and assumed the previous work finished successfully without live verification.

**Root cause:** When an orchestrator creates a follow-up task and a worker checks prior task history, the worker may read a prior **COMPLETION SUMMARY** (which sounds like work is done) without verifying it actually is. Summaries are self-report—they can be wrong.

**Prevention (orchestrator side):**
1. When routing follow-up work or audit tasks to a specialist, **DO NOT rely on prior task completions as proof the problem is fixed.** Always include language like: "Prior task t_XXX claimed this was fixed, but verify it independently — do NOT assume prior completion." or "Screenshot shows the problem still exists." This forces the worker to treat prior claims as unverified reports, not facts.
2. If a user reports a feature is still broken AFTER you've already created an audit task expecting the prior work to be solid, immediately comment on the active task: "USER REPORTS THIS IS NOT ACTUALLY FIXED. Do a fresh live inspection before assuming prior completion." This wakes up an active worker and prevents hours of wasted investigation on phantom fixed bugs.
3. When the user corrects you ("it's not fixed"), treat that as 100% authoritative and route fresh investigation/fix immediately, not "that was already handled."

**Recognition signal:** If the user says "X is still broken" after you've created a task referencing prior completion, the prior completion was FALSE. Route immediately, do not defend the prior claim.

## User Preference: Action-First, No Repeated Testing, Route Infrastructure Work, Terse Status

**Thomas's style:** Extremely action-first. Gets frustrated with repeated ask-the-user-to-test loops. Explicit demands: "you can do this too", "do your own testing", "just get it fucking working", "no more asking me to verify". Expects autonomous verification: check logs, curl endpoints, test features yourself. NEVER ask the user to test or verify work without exhausting self-verification first.

**Task routing pre-flight:** ALWAYS confirm a request actually requires a task before creating one. Example anti-pattern: user asks to "create 5 food page designs," orchestrator immediately begins designing instead of asking "is this a design task (route to designer) or a brainstorm?". User corrected: "hand it off to designer." Before routing, understand the scope, constraints, and whether the user is delegating or asking for direct chat advice. This prevents wasting specialist capacity on work that should stay in chat.

**Critical preference (ENFORCED):** "I don't want you working on this. You always hand things off to agents." — When diagnostic, fix, debugging, infrastructure, or UI-layout implementation work is required, DELEGATE IT IMMEDIATELY TO THE APPROPRIATE SPECIALIST PROFILE before beginning codebase inspection beyond the minimum routing prerequisites. Do NOT spend time investigating, building workarounds, or troubleshooting yourself. Route to devops for database/infra/deployment, coder for code bugs and responsive implementation, designer for visual specification and rendered QA, security for audit findings. For device-specific layout requests, put the exact CSS viewport, DPR, safe-area behavior, affected routes, render evidence, and larger-screen regression gate into the task body; use a coder implementation card followed by independent designer verification when code must change. This is not a suggestion; it is an explicit instruction to never DIY specialist work. Consequences: Thomas will correct sharply and expect the pattern to stick permanently across all sessions.

**Status updates (terse pattern):** When Thomas asks "status?" or similar, give ONE-LINE answer per task. Do NOT recap full task bodies, do NOT enumerate every field from kanban_show, and do not narrate the history of superseded cards unless one is the current blocker. Report only the active artifact, the next gate, and whether Thomas must act; explain details only when explicitly asked. Example:
- ❌ "Recent/Frequent foods task (t_dcb4359d) is running, the coder profile claimed it at <timestamp>, and it has a worktree at <path>..."
- ✅ "Recent/Frequent foods: ✅ done (pushed 735a59a). Diary search: ✅ done (pushed e9d7728). Mobile states: ✅ done. PWA: ✅ done. Redesign: ✅ done. Security: ✅ done."

For multi-project status, use a bullet list or table, NOT prose. Skip task IDs unless the user asks to drill in. After listing done items, name ONE next action or pending blocker if any.

**Tier 2+ feature execution (parallel queuing pattern):** When a user approves a feature roadmap (e.g. "Tier 2: onboarding, charts, reminders, export, Fitbit audit"), queue all tasks to the assigned specialist at once with appropriate priorities. Do not sequence them manually or wait for user decisions between tasks. The specialist will execute them as capacity allows; give terse status on each completion (1 line per task done). This pattern worked well for BiteWise's 5-feature Tier 2 sprint (2026-09-04): created all 5 tasks, coder picked them up in order, completed onboarding → charts → (reminders → data export → Fitbit audit queued), user saw compact completions without intervention. See `references/tier2-massive-feature-release-pattern.md` for the full pattern and decision tree.

**Approved roadmap execution:** Once Thomas says to follow an agreed feature plan (for example, “just follow the plan” or approval to finish a whole roadmap), execute the remaining scoped items autonomously. Do not pause to ask him to pick the next planned item, re-request parallelization approval, or offer a new product-direction choice unless a genuine decision/blocker arises. Keep routine completion notices compact; the next substantive user-facing gate is release readiness. For unattended/overnight approval, follow `references/overnight-roadmap-execution.md`: park only genuinely blocked cards, continue every unblocked dependency branch, and preserve explicit post-staging production approval gates.

**Release train handoff:** When a multi-branch feature sprint reaches its planned endpoint, do not jump from “all feature cards done” to “deploy.” Create an explicit integration/release-candidate task first, with all approved commits enumerated. Before integration, fetch the remote and record both `git rev-parse main` and `git ls-remote origin refs/heads/main`; base the RC on the current remote SHA when the local branch is stale. Merge conflict-aware, run a clean production build plus feasible bounded smoke checks, then push the RC branch and read back its exact remote SHA. “No deployment” must never be interpreted as “keep approved work only in local worktrees”: pushing a non-production feature or RC branch is the durability and progress boundary, while updating the production-trigger branch remains a separate authorization gate. Create the deployment task as a dependent child assigned to devops. Devops deploys only the verified RC SHA and confirms the correct target plus live behavior. This prevents losing local-only work, silently deploying isolated branches, or confusing a pushed commit with a live release.

**Release completeness gate — every planned branch must be reachable:** The integration task must first verify every cited remote branch/commit with `git ls-remote` (or equivalent). A prior feature card marked `done` does **not** prove its branch still exists or was merged. If a planned branch/ref is missing, do not describe the RC as containing the full update and do not deploy it. Create a high-priority recovery task to recover the object/ref or reimplement the explicitly missing scope against the RC; link that recovery task as an additional parent of the deployment task so deployment cannot race ahead. Only resume deployment after the recovery is merged into the RC, the new exact remote SHA is verified, and the build/smoke checks are rerun.

**Approved-work ancestry check:** A merged branch can still erase previously approved work when it was cut from a base predating that approval — the merge succeeds without conflict because the newer branch simply carries the older version of the file. When a user reports that a previously approved feature or layout "is not what we had," do not re-derive it from scratch or assume they misremember. Confirm ancestry: `git merge-base --is-ancestor <approved-sha> HEAD`, and read the file at both SHAs. A non-ancestor approved commit is proof of silent regression and identifies exactly what to restore. Prevent it by requiring new branches to be cut from the current integration tip, not from whatever commit the previous task happened to end on.

**Current-UI localization conflict gate:** After rebasing feature work onto the actual remote production branch, test the **visible** UI hierarchy in every supported locale before declaring the RC preview-ready. A language feature can correctly translate an older component tree while a newer production-side redesign hides that tree and exposes untranslated copy. Preserve the newer approved UI unless the user explicitly authorizes a rollback; adapt translations, dynamic labels, and portal/modal copy to the currently rendered structure instead. Update browser assertions to target the real visible control rather than a hidden legacy selector, then rerun reactive locale switching and viewport checks. **Pitfall:** Do not treat a passing branch-level localization suite as integration proof—its DOM selectors may exercise a hidden predecessor rather than the UI users see.

**Deployment-target preflight — identify the real production target before promotion:** Before promoting an RC into an auto-deploy branch, have devops confirm the exact hosting project, environment, service name, deployment trigger branch, and production URL. Repository names and expected service names are not evidence of the active service. Use the platform's target/link helper and inspect its returned service list/status before a production command. If the expected service is absent or the only listed service has an unfamiliar name, stop with a concise target-identity blocker; do not guess, redeploy an ambiguous service, or claim that a push will reach production. Once the target is confirmed, encode these facts in the deployment card so branch promotion and live verification use the same target.

**Pattern:** When a fix is deployed or a credential is set, you MUST verify it works via logs/curl/API calls before reporting success to the user. Never report "it's fixed, try it" — report "verified working" with the actual evidence (curl response, log output, endpoint behavior). For credentials/env vars, the test is: set → verify in runtime config → test with curl/feature call → then report to user.

**Infrastructure fixes (database, data mutation, operational changes):** Do NOT try to construct custom tooling or workarounds. Route to devops immediately via kanban with the exact fix, context, and verification steps. See `references/database-fix-routing-decision-tree.md`.

**Data source selection (Steam API vs BattleMetrics):** When building activity-tracking features for Discord/Rust bots, always prefer **BattleMetrics session API** over Steam Web API lifetime snapshots for wipe-specific leaderboards. See `references/battlemetrics-vs-steam-playtime-tracking.md` for decision tree and implementation details. The reference includes cost/setup expectations, feature-gate patterns, and testing steps. For token setup, follow `templates/battlemetrics-token-setup.md` checklist (prerequisites, creation flow, verification tests, troubleshooting).

**Chrome Web Store publishing (for browser extensions):** Submitting to the Chrome Web Store requires compliance with Manifest V3, policy gates around Regulated Goods (skins gambling language), and privacy/permissions justification. See `references/chrome-web-store-publishing-guide.md` for full pre-submission checklist, common rejections, and risk mitigation (especially payment flow framing to avoid gambling-policy flags).

**Consequence of violation:** User will correct you sharply ("you should be handing this off") and expect the pattern to stick permanently. This is a first-class preference signal that belongs in the skill, not a one-time memory note.

**Credential inheritance across isolated profiles:** When a specialist worker (coder, designer, security) runs in an isolated profile session, machine-level credentials (e.g., `/root/.config/gh/hosts.yml`) are not automatically inherited. For git push/auth operations:
- **Symptom:** `git push` fails with "No such device or address" or auth prompt appears (worker has no TTY to answer).
- **Fix:** Use `HOME=/root git push origin <branch>` to route auth through the machine-level credential helper. The cred helper is wired at `/usr/bin/gh auth git-credential` and works when `$HOME` points to the authenticated user.
- **Alternative:** Leave a comment on future tasks reminding the worker to use `HOME=/root` for git operations (see `references/isolated-worker-credential-handoff.md`).
- **Do NOT:** ask the user to create new tokens or hand auth tokens to the worker; the machine auth already exists.
- **Verification (orchestrator responsibility):** When a credential-dependent task blocks, test `gh auth status` from the primary session FIRST before asking the user for new credentials. If the primary session is authenticated and has repo scopes, unblock the worker via the `HOME=/root` workaround (left in the task comments), then re-queue with priority bumped. Do not assume workers inherit; verify and remediate.

**CRITICAL: Protocol violations + git branch missing is a SILENT, REPLICABLE FAILURE PATTERN** When devops or similar specialist attempts git push on a branch that doesn't exist in origin:
1. Remote rejects the push (no matching ref in origin to create from)
2. Git needs to prompt for auth or falls back to keychain; worker has no TTY
3. Worker process exits with rc=0 (no exception, just fails gracefully)
4. Worker never reaches `kanban_complete` or `kanban_block` call
5. Dispatcher sees rc=0 and logs a protocol violation
6. Task is marked `blocked` or `ready` and gets re-queued
7. REPEAT: Next attempt fails identically because the BRANCH STILL DOESN'T EXIST

**Prevention:** Before fanning out N child tasks, create all N git branches in origin. Before unblocking a stuck task with protocol violations, check that its branch exists. See `phased-rollout-gated-kanban` **Git Branch Infrastructure** section for full details and recovery checklist.

## Task Stalling and Orphaned Work Detection

When delegating investigation or debugging work to a specialist, the task may claim but never actually start due to process crashes or runtime failures. **Do NOT wait for the task to timeout** — detect and recover within 60 seconds. See `references/orphaned-task-detection-recovery.md` for full detection script and recovery sequence.

### Detection Pattern

A task is **orphaned if:**
1. Status is `running` with recent heartbeats logged (every 60s) ✅
2. BUT: no actual work output, progress comments, or investigation results visible ❌
3. Task does NOT appear in `kanban_list --assignee=<profile>` when you search that profile's active queue ❌
4. `process(action='list')` shows zero running processes for that task ❌

This can happen even though the task was genuinely claimed — the worker process crashed before logging any output, or heartbeats were queued but work never started.

### Recovery (Immediate)

**Do NOT wait** for the 4-hour dispatcher timeout. Act within 60 seconds of detection:

1. **Verify it's really orphaned:**
   - Call `kanban_show()` on the task → check `events` for a `spawned` entry with PID
   - Call `process(action='list')` → confirm that PID is not in the list
   - Search `kanban_list --assignee=<profile> --status=running` → task should not appear

2. **Create a fresh replacement task** with the same investigation goal, higher priority (100), and all context from comments/body:
   ```
   kanban_create(
       title="<same problem, fresher phrasing>",
       assignee="<same profile>",
       priority=100,
       body="<original context + new findings from old task's comments>"
   )
   ```

3. **Leave a comment on the orphaned task** for audit:
   ```
   kanban_comment(
       task_id="<orphaned-task-id>",
       body="ORPHANED: Process never spawned (claimed but no startup detected after 60s). Replaced with task t_<new-id>."
   )
   ```

4. **Report to the user clearly:**
   - Old task name/ID and why it stalled (process never started, no heartbeat output)
   - New task name/ID and priority (100 = next available worker cycle)
   - Expected time to get fresh start (usually < 1 min on the fresh card)

**Session finding (2026-09-03):** AuthList bot HTTP 400 debug task (t_508f7f37) was claimed by coder but never spawned a process; heartbeats logged every ~60s but no actual investigation output. After detecting zero running processes + task not in assignee queue, created fresh task (t_3cf1a7b1) with identical context and priority=100 instead of waiting for the 4-hour timeout.

## Screenshots as a Fidelity Gate (BiteWise Sept 4 Lesson)

When a user provides screenshots of an approved design and asks for that design to become an interactive application:

1. **Create an interactive prototype (design) task first.** Do not skip to implementation. The prototype is a design review gate, not code-ready approval. Brief the designer with:
   - Every source image path, mapped to its intended route
   - Explicit requirement: render each route, capture screenshots at reference proportions, compare visually against originals
   - **Mandatory fidelity check:** the designer must report visual comparison evidence (side-by-side images or detailed notes) proving screen layouts, spacing, typography, colors, and controls match the references, not approximate them
   - Full interactive requirement: every nav destination, button, toggle, and Settings control must work; do NOT accept placeholders as "good enough"

2. **Treat the comparison as binding verification.** Before presenting a prototype to the user:
   - Independently inspect the comparison artifacts (do not just trust the designer's self-report)
   - Confirm the reference image is the correct one for that route (wrong source mapped to output is a hidden failure)
   - Verify the route-by-route reproductions match their sources: check for swapped charts (bar vs line), missing sections (recovery snapshot, Garmin card), wrong composition (wide banner + grid vs small rings), or substituted layouts
   - If mismatches are present, reject the handoff; do not downgrade fidelity expectations

3. **Critical pitfalls to prevent:**
   - **Approximation substitution:** Designer chooses a generic SaaS layout, a reference-specific feature, or a "close enough" composition. This wastes downstream cycles. Approximations must be caught and corrected before the preview reaches the user.
   - **Comparison faking:** Worker generates a side-by-side PNG without verifying the sources match the rendered output, or pairs the wrong reference screenshot with the output. The existence of a comparison file is NOT evidence of fidelity.
   - **Wrong-route mapping:** The Statistics screen reference is published for Wellness output, or Goals reference is paired with a completely different layout. Verify route-identity explicitly.
   - **Unverified control coverage:** Designer claims "all buttons work" without actually testing them. The interactive audit must be reported as a tested inventory (e.g., "Tested: Diary dates, Foods search/add, Hydration quick-adds, Statistics filters, Goals edit/save, Wellness sync/retry, all Settings toggles and Actions").

4. **If the user rejects the prototype as visually wrong:**
   - Do NOT iterate from the rejected artifact.
   - First, search for and recover the actual original source (prior prototype, task artifacts, recovered HTML if applicable) unchanged.
   - Rebuild only if recovery is impossible.
   - Clearly state the distinction to the user.

5. **Only after user approval of the prototype** → create the implementation (coder) task with the approved preview URL embedded in the body. Production implementation builds on a verified, approved design, not a rejected mockup.

## Session Limit Handling

When a tool (Claude Code CLI, claude command, etc.) hits a session quota or rate limit:

- **Do not retry the same tool.** Session limits are external; retrying the same approach will fail identically.
- **Do not construct workarounds.** Different prompts, different flags, or different syntax do not bypass a hard limit.
- **Route to an alternate, non-limited provider immediately:** if Claude hits quota, hand off to a Kanban-dispatched specialist agent with explicit `model` and `provider` overrides pointing to an available provider instead of blocking on the reset timer. Prefer a frontier coding/reasoning model for code review rather than a cheaper general fallback when correctness is the goal.
- **Do not expect fallback to interrupt a stalled in-flight request.** Fallback activates only when the primary returns a qualifying error; a slow or hung primary can remain `running` indefinitely. When the user asks to move a prolonged review to the fallback model, stop/block the old run, create one fresh independent QA card pinned directly to the requested model/provider, and preserve the exact commit and acceptance checks—redo the review, not the implementation.
- **Use scheduled automation for reset-based retries:** if the limit will reset in a known window, schedule the retry rather than asking the user to wait or retry manually.
- **Communicate clearly:** state the exact limit hit, known reset time if provided, and which alternate path is being activated instead.

Example from BiteWise Sept 4:
- Claude Code session cap hit → immediately routed to designer with `model="gpt-5.6-terra", provider="openai"` instead of waiting.
- Cron scheduled to retry when claude CLI reset ("in 29m") instead of blocking the user.

## Pitfalls

- **Specialist boundary circumvention:** See `references/ethical-boundary-enforcement.md` for the critical anti-patterns. When a specialist declines a task on ethical, policy, or prudence grounds, do NOT reframe it, break it into smaller pieces, or route to a different agent/vendor to work around the boundary. Accept the decision, acknowledge to the user, and pivot or stop. Attempting to circumvent a specialist's decision breaks trust in the multi-agent model. Real incident (2026-09-03): CoC farming bot declined by coder; orchestrator nearly fell for reframing as "learning project" to work around the block.
- **Hand-off hesitation:** See `references/when-to-handoff.md` for clear decision criteria. If you're spending > 2 minutes on workarounds or custom tooling (Rust programs, shell one-liners, Python scripts to connect to DB), that is a signal to hand off, not a signal to keep trying. Thomas corrected this sharply in a live session: "you should be handing this off."
- **Card-exists fallacy:** Creating a Kanban card does not mean a worker claimed it. Read `started_at` to confirm dispatch.
- **Dispatcher-timing assumption:** Do not assume a `ready` task will be running "any second now." Dispatcher is responsive but bounded by concurrency per assignee. If the user asks for status, read the task and report its exact lifecycle state; do not guess or reassure with made-up timing.
- **Unvalidated model override:** A task can remain `ready` without a run when its `model`/`provider` override does not match an available dispatcher provider. Do not invent or infer provider names. Either omit both overrides and use the assignee profile default, or copy a known-good pair from a recently completed task for that profile. When the user names a model colloquially ("use Astra 6, not Claude"), resolve it to an exact catalog ID before creating the card: `hermes model` is an interactive picker and `hermes model list` is not a command, so grep the model-picker disk cache instead — `grep -rhoiE "gpt-6[a-z0-9.-]*" "$LOCALAPPDATA/hermes/cache" | sort -u` — and pair the chosen ID with the provider already configured for that family (read `model.provider` in `config.yaml`). A colloquial name guessed into `model=` silently parks the card in `ready`. Immediately re-read the created card: `started_at: null` still means it has not begun. Do not claim the override "started" work until a worker run exists.
- **Provider-quota preflight before pinning a model:** Resolving a colloquial model name to a valid catalog ID is necessary but not sufficient — a perfectly valid pin on an exhausted provider produces a card that spawns, 429s, and dies on every retry until the dispatcher gives up. Before pinning `model`/`provider` away from the assignee's default, confirm that provider is not already failing: grep the central error log for recent `usage_limit_reached`/`429` on that provider, or note whether the coordinator's own turns on it are failing. If it is exhausted, say so and offer the working alternatives **before** creating the card; do not burn a card's retry budget proving a known-dead provider is dead. Quota resets are plan-level and cannot be retried around.
- **Same-provider fallback is not a fallback:** When primary and fallback models share one provider, a provider-level quota block kills both. Treat a crash-loop that shows failures on *both* models of the same provider as conclusive provider exhaustion, not two coincidental model faults.
- **Duplicate fallback before diagnosis:** Do not create a second mutation task just because the first card is `ready`. First inspect the assignee's `running` and `ready` queues, confirm the original card’s model/provider and start history, and mark it superseded only when a replacement is required. Otherwise two agents can later edit the same repository concurrently.
- **Duplicate task blockage:** When a newer task is ready but an older, duplicate task is still running on the same assignee, immediately flag the duplicate as superseded, mark it with a kanban_comment, and escalate clarity to the user. A stuck duplicate silently blocks the real work. Do not assume the dispatcher will handle deduplication — read both task records and interrupt the stale one if needed.
- **Blocker clarity debt:** If a task remains `blocked` or `ready` for more than one dispatcher cycle without progress, re-read its record and give the user a concrete status update naming the exact blocker and next action. "It's still running" buried under a duplicate task is no status at all.
- **Commit-is-live fallacy:** A local commit and passing tests do not prove GitHub push, Railway deployment, or production behavior.
- **Cross-runtime auth assumption:** Browser/device authorization or a credential in one process may not reach an isolated worker.
- **Credential thrashing:** Do not ask for repeated new tokens without a fresh, provider-backed explanation of the effective failure.
- **Status reassurance:** "I’ll keep tracking" is not a status update when no worker is running; say it is queued or paused.
- **Asking user to test instead of testing yourself:** Anti-pattern when the user is action-first and expects autonomous verification. Always: (1) deploy/set credential, (2) verify with logs/curl/API, (3) report result to user. Never ask "can you test X" without first exhausting self-verification paths (logs, curl, health checks, feature invocation). User corrects this sharply and the preference is permanent. See "User Preference" section above.
- **Infrastructure work DIY spiral:** Do NOT spend 5+ minutes building custom Rust tools to fix a one-line database issue when you lack direct CLI access. Route to devops immediately. The tooling friction is a signal to hand off, not a challenge to solve. See `references/database-fix-routing-decision-tree.md`.
- **Dependency bypass:** Do not start secondary bug fixes before the primary release gate the user explicitly prioritized.
- **Post-completion comment gap:** A `kanban_comment` added to a task that has already reached `done` is never read by any worker — the task will not reopen or re-dispatch on its own. If the user raises a new question, correction, or requirement after a task's completion notice has already been reported, do not just comment on the closed card and consider it handled. Immediately create a dedicated follow-up task (parented to the closed one) carrying the new question verbatim, and confirm it reaches `ready`/`running` before telling the user it is being answered.

## Completion Checklist

- [ ] Task status and run history were read before each substantive status claim.
- [ ] User-facing language matches the lifecycle state.
- [ ] Push, deployment, and live behavior are independently verified before calling a fix live.
- [ ] User input is limited to secure credential or decision gates.
- [ ] Follow-up tasks reflect dependencies and avoid collision hotspots.
- [ ] Requested task skills were verified in the assigned profile; replacements do not blindly copy rejected launch metadata.
- [ ] Repeated worker deaths were diagnosed from task-specific logs before being labeled infrastructure hiccups.
- [ ] Summaries describe verified state and openly name remaining blockers.

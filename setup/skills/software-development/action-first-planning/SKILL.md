---
name: action-first-planning
description: "Plan before executing: write specs for action-first users."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, action-first, workflow, efficiency, user-preference]
    related_skills: [plan, test-driven-development, requesting-code-review]
---

# Action-First Planning

When working with action-first users (especially those frustrated by repeated testing, back-and-forth clarifications, or explanations), **always create a detailed written plan BEFORE executing any code or changes**. This prevents rework cycles and satisfies the user's preference for autonomous, verified work.

## User Profile: Action-First Users

Action-first users share these traits:
- Strongly prefer "just get it working" over step-by-step collaboration
- Hate being asked to test or verify work repeatedly
- Frustrated by multi-turn explanations or walkthroughs
- Demand autonomous execution with verification baked in
- Explicitly correct workflows that stray from this pattern: "why are you asking me to try things?" or "just test it yourself"

**Memory clue:** If a user has said "you can do this too", "do your own testing", "just get it fucking working", or repeatedly asked to skip verification steps they can handle themselves, they are an action-first user.

## The Workflow

### Step 1: Ask for or Infer the Request

If the user's request is vague ("fix the dashboard"), clarify briefly:
- ONE short question, not a questionnaire
- Directly quote the ambiguity
- Offer your best inference as a default

**If they say "make a plan first",** stop immediately and proceed to Step 2. Treat approval as scoped: plan approval authorizes implementation of that plan, not staging, production, or the next roadmap phase unless those transitions are explicitly included.

### Step 2: Create a Written Plan

Use the `plan` skill to create a comprehensive, task-by-task breakdown. Do NOT execute yet. For a new customer-facing commerce project, include the operator's daily back-office journey alongside the storefront: distinguish payment from fulfilment status, show what an order owner needs to inspect, and test the paid-order → label → tracking handoff. Choose the commerce architecture from the user's hosting and ownership requirements before drafting admin or checkout: if the user wants an independent Railway-hosted shop, specify a secured first-party admin and database rather than anchoring the plan on Shopify. Use clearly marked, rights-safe sample images, prices, and descriptions when real product data is unavailable; keep sample inventory non-purchasable until real commerce is approved. When the user requests style options, compare several related palettes on the SAME simple layout with clickable mobile/desktop states; changing both layout and color obscures the decision. Treat proposed colors as provisional until the user selects one. Require the planning agent's handoff to explain HOW the coding agent implements each step—schema, API contracts, files, interactions, tests, and stop gates—not merely WHAT to build. Resolve named coding models to exact provider/model IDs and supported reasoning-effort settings before dispatch; a model nickname or team-profile name is not proof that the requested model and effort were selected. For design-first work, hand the visual style sheet and interactive spec to the requested designer model/effort, then derive the implementation `/goal` prompt from that actual artifact as a separate dependent deliverable; pin the requested builder's provider/model separately rather than allowing automatic routing to substitute it. If the user corrects routing during a run, treat the wrong-model output only as draft input and verify the replacement run's model and effort before presenting the design as final. For a visual storefront refinement, specify the back-office experience as carefully as the catalog: compact order status views with meaningful payment/fulfilment mapping, a guided product-add flow that persists into the public catalog, and consistent filter/search/sort/reset interactions in both live and static previews. Treat legal/footer pages as separately navigable drafts with explicit business-input gaps, never invented enforceable terms. Produce distinct rights-safe logo previews for the user's selection but keep branding changes gated until a concept is approved.

**Plan MUST include:**
- **Current state** — what's broken or missing right now
- **Architecture** — how the fix/feature will work
- **Exact file paths** — not vague references
- **Complete code blocks** — copy-pasteable, not pseudocode
- **Sequential tasks** — each 2-5 minutes of focused work
- **Exact commands** — with expected output
- **Verification steps** — how to confirm each task worked
- **Files modified summary** — what changed and why
- **Risks & pitfalls** — what can go wrong and how to detect it

Save to `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`.

### Step 3: Offer Execution Paths

After saving the plan, tell the user what's ready and offer execution options.

For visual cleanup or consolidation, distinguish **functionality** from **presentation** in the plan. Preserve validated backend/data/state work unless removal is actually requested; describe which duplicate surfaces will be merged into existing UI. After approval, implement on an isolated branch, render populated and edge states, and show a non-deployed preview for visual yes/no before changing staging. A screenshot crop must be labeled so the user does not mistake an out-of-frame score or section for removal.

**For small plans (< 5 tasks, single file):**
```
Plan saved. Ready to execute immediately. Shall I proceed?
```

**For medium plans (5-10 tasks, 2-4 files):**
```
Plan saved. Ready to execute via the configured OpenAI Codex coding workflow for production-quality implementation + verification.
Shall I proceed?
```

**For large plans (10+ tasks, multi-component, or architecture changes):**
```
Plan saved. Ready to delegate task-by-task to specialized agents (coder, security, devops)
and orchestrate on the shared kanban board.
Shall I proceed?
```

### Step 4: Execute Once Approved

Once the user approves, preflight the planning and implementation profiles **before** making a dependency graph: confirm the planner can read the repo and write a durable handoff (e.g. `HERMES_HOME=<planner-home> hermes tools list` must include `file` and `terminal`), and confirm each named model's provider and effort separately. If tools are disabled, enable only the needed toolsets with `hermes tools enable file terminal skills`, read back the configuration, and restart the blocked planning task in a fresh session; toolset changes do not appear mid-run. Keep the coding child dependency-gated until the planner attaches its versioned specification and exact build prompt.

For a public-facing preview, open and read the rendered page through the preview pane or a bound local HTTP server; a successful file/open call or loopback `curl` alone does not prove the recipient can open a shareable link. Keep a local demo preview distinct from a public Railway/admin release.



**Small to medium plans:** Execute directly or delegate through the user's requested, verified coding model/provider; do not substitute the profile's default model for a named model.

**Large plans:** Use `kanban_create` to decompose into child tasks with explicit assignees (coder, security, devops). Each task gets the full plan excerpt relevant to it, plus dependencies. Pin the exact requested provider/model on **every** coding and repair card, not just the first: dependencies do not inherit model overrides. Read back the card before dispatch, verify the run-linked model route, and keep reasoning effort as a separate model-specific profile setting.

**CRITICAL:** For action-first users, **test EVERYTHING yourself** before reporting success:
- Run commands and check output
- Verify files were written correctly
- Test API endpoints with curl
- Check logs for errors
- Run test suites
- **NEVER** ask the user to "try it and tell me what happens"

### Step 5: Report Verified Results

After execution, report ONLY what actually happened:
- What was changed (with diffs if relevant)
- What was tested and how
- What passed and what failed
- If anything failed, why and what the fix is
- Any unexpected side effects or edge cases discovered

Do NOT hand back unverified work or ask the user to verify for you.

---

## Why This Matters

Action-first users prioritize:
1. **Autonomy** — the agent does the work, not the user
2. **Verification** — the agent proves it works, not the user
3. **Clarity** — the agent shows exactly what changed and why
4. **Speed** — no back-and-forth, no explanations, just results

A plan satisfies points 1-3 upfront; execution + verification satisfies point 4.

Without a plan, you risk:
- Rework cycles (user sees implementation, asks for changes, you redo it)
- Testing loops (user asks you to verify, you ask them to verify, deadlock)
- Scope creep (you execute without clear boundaries, user corrects midway)
- Wasted tokens (multiple passes to get the implementation right)

## Anti-Patterns

### ✗ Don't: Dive into code without planning
```
User: "Settings button isn't working"
Agent: *immediately reads Dashboard.svelte, finds the bug, patches it*
User: "Wait, but I also need delete functionality!"
Agent: *now has to redesign and add new pieces*
```

### ✓ Do: Plan first
```
User: "Settings button isn't working and I also want delete functionality"
Agent: Creates plan covering:
  - Why button is broken (missing click handler)
  - What delete needs (API endpoint + UI + bot leave)
  - Exact changes needed in each file
  - Tests to verify
User: "Looks good, go"
Agent: *executes plan, verifies each step, reports results*
```

### ✗ Don't: Ask the user to verify your work
```
Agent: "I've deployed the fix. Can you test it and let me know if it works?"
```

### ✓ Do: Verify it yourself
```
Agent: "I've deployed the fix. Tested with curl on localhost:8080/api/endpoint and verified 200 OK response. Bot successfully left test guild. Dashboard page loads and Settings modal appears."
```

### ✗ Don't: Explain your reasoning
```
Agent: "So what I did was, I looked at the code structure, and I noticed the button was missing an onclick handler..."
```

### ✓ Do: Report what changed
```
Agent: "Changes: Added click handler to Settings button → opens SettingsModal component. Modal displays server info and delete button with confirmation flow."
```

## Checklist: Before Reporting Completion

- [ ] Plan was approved before execution
- [ ] Each task in the plan was executed in order
- [ ] Each task was tested immediately after completion
- [ ] No step was skipped or assumed to work
- [ ] If any step failed, the root cause was found and fixed
- [ ] Entire feature was tested end-to-end
- [ ] No manual steps remain for the user
- [ ] Results are reported with verification evidence (logs, curl output, test results)

## Integration with Other Skills

**plan:** Use this skill to create the detailed breakdown. You stay in plan-mode; don't execute.

**codex:** After plan approval, delegate implementation through the configured OpenAI Codex workflow for production-quality code + verification.

**test-driven-development:** When the plan includes code changes, use TDD: write failing tests first, implement, verify tests pass.

**requesting-code-review:** If the user asks for review after execution, offer `kanban_request_review` with verified results, not a request to re-test.

---

## Session Example: AuthList Settings & Delete

**User:** "Fix settings button and add delete with bot leave."

**Agent (this session):** 
1. Created plan with 3 tasks (backend DELETE endpoint, Settings modal, wire-up)
2. Included exact file paths, complete code, test commands, verification steps
3. Saved to `.hermes/plans/2026-08-30_dashboard-settings-delete.md`
4. Offered execution options

**Next session (when user approves):**
1. Execute tasks 1-3 in order
2. Test each: compile backend, build dashboard, verify clicks work
3. Test full flow: click Settings → modal appears → click Delete → confirm → server removed from DB, bot leaves guild
4. Report: "Settings button fixed (click handler added), modal displays server ID and delete button, delete works end-to-end and triggers bot guild leave. Tested with [guild ID], bot confirmed left Discord."

---

## Remember

- **Plan first, execute second, test third, report verified results.**
- **Never ask action-first users to test for you.**
- **The user's time is more valuable than the agent's compute time.**
- **A detailed plan prevents 3 rework cycles.**

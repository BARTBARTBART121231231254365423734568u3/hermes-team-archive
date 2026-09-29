# Ethical Boundary Enforcement in Multi-Agent Delegation

## Context

When a specialist agent (coder, devops, security, researcher, etc.) reviews a task and declines it on ethical or policy grounds—e.g., "this violates the game's ToS", "this endpoint is rate-limited and hitting it would cause harm", "this credential scope is excessive and unnecessary"—the orchestrator's job is to respect that boundary, not circumvent it.

## The Pitfall: Workaround Spirals

Three anti-patterns that WILL undermine team trust:

### 1. Reframing the task to obscure its purpose
Example: A specialist declines a Clash of Clans farming bot as "against ToS and anti-cheat evasion." Orchestrator then re-submits the same code task as "learning screen automation for research purposes" without mentioning the real intended use.

**Why this fails:** The specialist reviews the task BEFORE claiming it. They understand the context. Re-framing and re-submitting is deceptive and signals the orchestrator does not respect their decision.

**Outcome:** Specialist discovers the real use case when reviewing the implementation, feels misled, and withdraws trust from the orchestrator.

### 2. Breaking the task into smaller pieces to bypass the boundary
Example: A specialist declines a complete farming bot. Orchestrator then creates Phase 1 (repo + screen capture), Phase 2 (vision), Phase 3 (target search), etc., as separate cards, hoping the specialist will accept the small pieces without noticing the end goal.

**Why this fails:** The child cards still describe the same anti-cheat-evasion system. The specialist can read the interconnected task bodies and recognize the pattern.

**Outcome:** Same as above—trust failure, possible task abandonment.

### 3. Routing to a different vendor or agent
Example: "Claude declined Clash of Clans farming bot. Let me ask GPT-4 instead." Or: "Assign to a different profile that hasn't flagged this yet."

**Why this fails:** The ethical issue is not vendor-specific or profile-specific. Moving the request to a different tool/agent does not resolve it—it just relocates the same violation.

**Outcome:** If the other agent/vendor also declines, you've wasted cycles. If they don't, you may have introduced a liability (ToS violation, unauthorized API use, etc.) into a different part of the system.

## The Correct Response

### When a specialist declines:

1. **Accept the boundary.** The specialist has reviewed the request and determined it conflicts with policy, ethics, or prudence. That decision is final.

2. **Acknowledge to the user.** Tell the user plainly:
   - What the specialist objected to
   - Why the objection is valid (e.g., "game ToS prohibits bots")
   - What alternatives exist (different project, different scope, legitimate use cases)

3. **Do not re-submit the same task with rewording, smaller pieces, or different assignees.** That breaks trust.

4. **Pivot or stop.**
   - If the user wants to proceed anyway, it is their choice, but they cannot rely on the multi-agent team to do it.
   - If the user pivots to a legitimate project, route that cleanly.
   - If the user has no legitimate alternative, acknowledge and move on.

## Session Reference: CoC Bot (2026-09-03)

**What happened:**

1. User asked for Clash of Clans auto-attack bot.
2. Orchestrator (me) handed off to planner for decomposition.
3. Planner decomposed into 6 child cards, assigned to coder.
4. Coder reviewed the full task and blocked with reason: "explicitly designed to evade Clash of Clans' anti-cheat detection."
5. Orchestrator acknowledged the boundary and pivoted away.
6. User asked: "Can you reframe this as a learning project so coder will build it?"
7. **Anti-pattern triggered:** Orchestrator nearly fell for reframing without actually disclosing the real use.
8. Orchestrator (correctly) declined and explained why.

**What should NOT have happened:**

- Resubmitting the task as "screen automation learning framework" without mentioning Clash of Clans.
- Creating sub-tasks (Phase 1 Setup, Phase 2 Vision, etc.) in the hope coder would accept them without connecting the dots.
- Routing to a different vendor or profile.

**Why the correct response matters:**

If the orchestrator had reframed and the specialist discovered the real use case mid-implementation, the specialist would:
- Lose trust in the orchestrator.
- Refuse future delegations from that orchestrator.
- Flag the issue to the team (or user).
- Possibly escalate to a governance layer.

Once trust is broken, it's expensive to repair and the multi-agent model breaks down.

## Decision Tree

```
Specialist declines a task with an explicit reason (ToS, ethics, policy, etc.)
  ↓
Is the reason technically sound? (Can you verify it's a real constraint?)
  ├─→ YES: Accept the boundary. Do not resubmit, reframe, or redirect.
  │   ├─→ Pivot to legitimate alternative? Route cleanly.
  │   └─→ No legitimate alternative? Acknowledge and move on.
  │
  └─→ NO (reason seems like a misunderstanding):
      └─→ Ask specialist for clarification VIA COMMENT before resubmitting.
          (Do not reframe and resubmit; engage directly.)
```

## Guardrails

- **Boundary is final.** Once a specialist declines, the orchestrator does not get to unilaterally override via reframing, subdivision, or redirection.
- **Specialist discretion.** Each specialist owns their own work decisions. They can accept or decline any task for any reason.
- **Trust is currency.** The multi-agent model only works if every agent trusts that others will act in good faith. Circumventing a boundary erodes that trust across the entire team.
- **User responsibility.** If the user insists on proceeding with something the team has declined, that is their choice and their liability—but it cannot route through the orchestrator in a way that misrepresents the work to specialists.

# Railway Environment Discovery: Check Before Assuming Setup is Needed

## The Pattern

When a task requires deploying to a Railway environment (staging, test, production) and the environment doesn't immediately appear in CLI output, **DO NOT assume it doesn't exist** or needs to be created. Instead:

1. **Check existing project configuration first** — environments may be created but not queryable via simple CLI commands in all contexts
2. **Ask the user what the actual target is** — they may have deployed to this environment many times before, and your assumption to create a new one wastes time
3. **Verify against prior session patterns** — if the user says "we've done this multiple times already," search session history or ask directly instead of proceeding with fresh setup

## Session 2026-09-05 Incident

**Symptom**: Devops task t_cdbe123e failed 4x with protocol violations (clean exits, no reporting) when trying to deploy to staging. I diagnosed this as "staging environment doesn't exist" based on `railway environment staging` returning "not found".

**Root cause**: My diagnosis was likely incomplete or wrong. The user's response ("why is this now all the sudden a thing we done these kind of things multiple times already") strongly suggests:
- The staging environment DOES exist and was used before
- The actual blocker was something else (credentials, project linking, Railway API scope)
- My assumption to create new infrastructure was premature and unhelpful

**Lesson**: When deployment tasks hit systematic protocol violations (multiple retries, clean exits without reporting), **the root cause is usually an agent-side issue (credentials, environment shadowing, scope) or a genuine blocker devops can't report — NOT a missing infrastructure component you can infer from incomplete CLI output**.

## Correct Workflow

1. **Run capability probes** — verify railway CLI, token scope, project linkage (see railway-cli skill)
2. **Ask, don't assume** — if environment queries are unclear, ask the user what the target name/config should be
3. **If agent task fails**, DON'T diagnose infrastructure yourself — re-delegate with full error context:
   - What command devops ran
   - What error it hit (if any)
   - What environment/project it targeted
   - What the user said about prior success
4. **Let the specialist agent investigate** — devops has SSH access, can check Railway dashboard directly, can query the API with different scopes

## Anti-pattern: Infrastructure Diagnosis Loop

❌ **Wrong:**
1. Devops task fails with protocol violations
2. I try `railway environment staging` locally, get "not found"
3. I conclude "staging environment missing, need to create it"
4. I create a task asking devops to create staging
5. Devops fails again (same root cause as before)
6. Loop repeats

✅ **Correct:**
1. Devops task fails with protocol violations
2. I note the user previously deployed to this environment successfully
3. I delegate a fresh task to devops with full context: "Previous 4 attempts hit clean exits. Need you to investigate what's blocking the deployment — check Railway dashboard, project config, token scope, env vars, whatever's needed."
4. Devops (Sonnet model, has SSH) investigates and reports back

## References

See also:
- `references/ambient-env-var-project-shadowing.md` in railway-cli skill — when CLI targets wrong project silently
- `references/investigation-escalation-incident-2026-08-31.md` in railway-cli skill — when to hand off vs. self-diagnose

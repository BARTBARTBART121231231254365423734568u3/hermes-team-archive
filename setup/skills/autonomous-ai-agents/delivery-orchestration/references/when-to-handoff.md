# When to Hand Off (Delegation Decision Tree)

**Session context:** Thomas corrected the agent for over-engineering a database fix (`"i dont know why you are doing this"`) and then corrected the workflow (`"you should be handing this off"`). These are explicit signals that delegation decisions need sharper criteria.

## The Core Signal

If you are about to spend more than 2-3 minutes on any of these:
- Custom tooling (Rust programs, Python scripts, shell one-liners)
- Workarounds for missing CLI tools
- Trying three different approaches to the same problem
- Building a solution when a specialist tool exists

**STOP and hand off.** Do not keep iterating.

## Decision Tree

### Database Fix / Data Mutation

**You:** Read the actual data, understand the problem, write SQL or a small script to fix it.

**Reality:** You don't have direct interactive CLI access in many runtimes (Railway containers, isolated workers, etc.). Building custom Rust tools to connect to the DB, writing Python workarounds, attempting heredoc SQL over SSH — all of this is friction.

**Signal:** If you find yourself writing a Rust/Python program to query a database, or using `railway run` + shell workarounds to get a CLI tool working, **you have already spent too long**.

**Hand off to:** `devops` with the exact problem, expected state, and verification steps. They have the CLI tools and SSH access already configured.

**Example:** Jar Jar's stale Steam ID.
- ✅ **What to do:** Note the problem, create a kanban card titled "Fix Jar Jar's stale Steam ID," hand to devops.
- ❌ **What not to do:** Spend 10 minutes writing a Rust query tool, debugging `railway run` heredoc syntax, trying to install sqlite3 in the container.

### Infrastructure Debugging (Railway, Git, Deployment)

**You:** Notice something is broken (deployment stalled, env var wrong, credential rejected).

**Temptation:** Try the `railway` CLI differently, check a different endpoint, edit the config manually, re-run with different flags.

**Signal:** If you're about to try the same command a third time with different flags, or you're inventing a workaround (e.g., "let me use the GraphQL API instead of the CLI"), **stop.**

**Hand off to:** `devops` with the exact command, exact error output, and what you already tried.

**Example:** Deployment hung on a credential issue.
- ✅ **What to do:** State the error ("git push: fatal: could not read Username"), create a kanban card, hand to devops.
- ❌ **What not to do:** Try `git push` with `--force`, then `git push` with a different credential, then build a custom curl-based deploy trigger.

### Investigation / Diagnosis

**You:** Suspect the root cause is X (a specific commit, a database state, a config issue).

**Temptation:** Inspect the logs yourself, read through code, narrow it down, present your findings as verified fact.

**Reality:** You run on Haiku. Narrowing down a root cause often requires looking at multiple pieces of evidence and making judgment calls—exactly where a cheaper model is most likely to hallucinate specific details ("the root cause is line 42 of X.rs") that sound plausible but are wrong.

**Signal:** If you are about to tell Thomas "I checked and found that X is the problem," and X is a specific code location, commit hash, or system state you didn't independently verify by re-reading it in this exact turn, **hand off.**

**Hand off to:** `coder` (for code investigation), `devops` (for deployment/runtime state), `security` (for audit findings).

**Example:** Wipe RSVP reason not posting.
- ✅ **What to do:** Create a kanban card, hand to coder with the exact behavior ("when users mark Can't Attend, no reason is logged"), let them investigate and verify.
- ❌ **What not to do:** Spend an hour reading the code, conclude "I think it's the ? operator in handle_wipe_reason_modal," and tell Thomas it's fixed.

### Coding / Implementation

**You:** Task is "implement playtime tracking."

**Temptation:** Read the spec, start writing Rust, commit code locally, declare it done.

**Reality:** You run on Haiku. Implementation work benefits massively from a stronger model (Sonnet) that is less likely to invent plausible-sounding-but-wrong library names, config values, or patterns.

**Signal:** The moment a task needs `write_file` to create/edit actual source code, or a terminal command that builds/compiles/runs the project, **stop.**

**Hand off to:** `coder` via `claude -p "..." --permission-mode acceptEdits --add-dir <repo>`.

**Example:** Building the wipe playtime feature.
- ✅ **What to do:** Give planner the requirements, planner writes a detailed spec, hand the spec to coder to implement.
- ❌ **What not to do:** Write the Rust code yourself, commit it, test it locally, hand it to Thomas.

## Practical Flow

1. **Encounter problem** → Read/understand the issue.
2. **First action:** Could a specialist handle this faster with their tools? (devops has CLI + SSH, coder has compilation + testing, security has audit tools, etc.)
3. **If yes:** Create kanban card immediately. Do NOT spend 2+ minutes on workarounds.
4. **If no (truly one-off, you can do it now):** Proceed.
5. **After 2-3 minutes of trying:** If you're inventing workarounds or trying the same thing differently, **that's the signal to hand off.** Do not finish; create the kanban card and explain what you tried.

## Why This Matters

**Thomas gets angry at waits.** He also gets angry at you trying things for 10 minutes when a specialist could have done it in 2 (because they have the right tools). The pattern is: hand off fast, let specialists work, report results. Don't be the bottleneck building custom tooling.

**Your role:** Route work, verify outcomes, summarize for Thomas. NOT execute every step yourself.

## Reference Links

- `delivery-orchestration` skill contains the full procedure for handing off and tracking outcomes.
- See `references/duplicate-ta<REDACTED_SECRET>.md` for what happens when you don't hand off clearly (work gets blocked in queues, user has to chase you).

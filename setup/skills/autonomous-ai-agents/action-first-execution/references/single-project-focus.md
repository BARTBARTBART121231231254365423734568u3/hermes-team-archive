# Single-Project Focus: Stop Cross-Pollinating Unrelated Work

**Session Context:** Thomas was frustrated when the agent repeatedly mentioned BiteWise, worthy-healing, and other projects during an AuthList debugging session. Explicit correction: "BitWise has nothing to do with this please stop bringing other projects into it."

## When This Happens

You're debugging Project A (authlist-bot on Railway) and you:
1. Search Railway CLI output and see other projects listed
2. Think "Hey, I should check if it's in a different project"
3. Query other projects by name (BiteWise, worthy-healing, wipe-react-bot)
4. Mention or suggest those projects as alternative possibilities
5. User corrects you sharply

## The Pattern

**User says:** "I think its going wrong because it's on the bot project instead of the main one?"

You should interpret this as:
- They suspect the code was deployed to the WRONG PLACE
- The "wrong place" is somewhere within the authlist STRUCTURE (e.g., bot/ subdir instead of root)
- NOT: "Maybe we're working on the wrong entirely-different-product project"

**What you did wrong**:
- Suggested checking BiteWise, worthy-healing
- Said "maybe we should deploy to BiteWise instead"
- Brought external projects into a single-project session

**Why it's wrong**:
- User specified the project upfront: authlist
- Other projects are unrelated noise that distracts
- When user questions scope, they mean SCOPE WITHIN THEIR PROJECT, not "are we in the right product"
- Bringing in external projects wastes time and looks like the agent is confused

## Fix

**When debugging a single project and user questions scope:**
1. Assume they mean scope WITHIN that project (monorepo dirs, subfolders, configuration)
2. Do NOT search for or mention entirely-different projects
3. If unclear, ASK: "Do you mean we should check a different Railway project, or is it a directory/configuration issue within authlist?"
4. ONLY explore other projects if user explicitly says "check the BiteWise project" or "this might be in the wrong product"

**Example Correction**:

❌ **Wrong:**
```
User: "It's on the bot project instead of the main one?"
Agent: "Maybe we should deploy to BiteWise instead..."
Agent: [starts checking worthy-healing]
User: "Please stop, just focus on authlist"
```

✅ **Right:**
```
User: "It's on the bot project instead of the main one?"
Agent: "I think you mean the bot/ subdirectory vs root? Let me check the monorepo structure."
Agent: [explores only authlist-bot project's directories and configuration]
```

## Context Anchoring

When user says the project name or picks it from a list, that is your ANCHOR for the entire session. Every query, every tool call, every diagnostic should stay within that project unless explicitly told otherwise.

**Anchors from this session**:
- User: "I'm working on the authlist project"
- Artifact: Looking at authlist repository
- URL: deployment URL is bot-production-7612.up.railway.app (clearly authlist)
- Directory: /root/AUTH_LIST_RUST

**What should have anchored the agent**: Any one of these. All four of them together is unmistakable.

## Related Pattern: Multi-Project Context Switching

If a user DOES ask you to work on multiple projects in one session:
- Label your work clearly by project name
- When switching projects, state the switch explicitly
- When done with Project A, confirm before moving to Project B
- If confused about which project you're in, ask

Example:
```
User: "Fix the authlist bug, then check the BiteWise dashboard."
Agent: "Starting on authlist... [work] ...done with authlist."
Agent: "Switching to BiteWise now... [different work] ...done."
```

BUT for single-project sessions, **never introduce other projects into the conversation voluntarily**.

## Language Signals

**User rejection signals** that indicate you've over-scoped:
- "just focus on [project name]"
- "[project name] has nothing to do with this"
- "stop bringing other projects into it"
- "this is just about [project]"

When you see these, immediately:
1. Acknowledge the correction
2. Narrow focus to ONLY the stated project
3. Do not mention other projects again unless user brings them up
4. Do not query, list, or suggest other projects

## Monorepo vs. Multi-Project Confusion

**Monorepo**: One repository (e.g., authlist) with multiple services (bot/, dashboard/). Belongs in ONE Railway project.

**Multi-Project**: Entirely different products (authlist vs. BiteWise vs. worthy-healing) often in separate GitHub repos and separate Railway projects.

When user says "it's on the bot project" they likely mean the bot SERVICE within the authlist RAILWAY PROJECT, not a separate product. Stay in authlist-bot project, but check its bot vs. dashboard services.

When user says "we have two separate Railway projects", THEN you look at multiple projects. But in single-project sessions, never volunteer that possibility.

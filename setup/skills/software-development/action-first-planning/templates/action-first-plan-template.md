# [Feature Name] Implementation Plan

> **For Action-First Users:** This plan covers everything needed for autonomous execution + verification. No steps are optional. No manual user testing needed.

**Goal:** [One sentence: what problem this solves and what user gets]

**Current State:** [What's broken or missing right now]

**Architecture:** [2-3 sentences: how this will work, key components]

**Tech Stack:** [Technologies/libraries involved]

---

## Task 1: [Specific Name]

**Objective:** [One sentence: what this accomplishes]

**Files:**
- Create: `path/to/new_file.ext`
- Modify: `path/to/existing.ext` (lines X-Y if known)

**Step 1: [Action]**

[Details and code blocks]

Run: `[exact command]`
Expected: [exact output]

**Step 2: [Verify]**

Run: `[exact verification command]`
Expected: [exact output that proves success]

**Step 3: Commit**

```bash
git add [files]
git commit -m "type: description"
```

---

## Task 2: [Next Task]

[Same structure as Task 1]

---

## Risks & Pitfalls

- **Risk:** [What can go wrong]
  **Detection:** [How to spot it]
  **Fix:** [What to do about it]

---

## Verification Checklist

Agent MUST verify ALL of these before reporting completion:

- [ ] Task 1 completed and tested
- [ ] Task 2 completed and tested
- [ ] Full end-to-end flow works
- [ ] No errors in logs
- [ ] All files modified as planned
- [ ] No manual steps remain

---

## Files Modified Summary

| File | Changes |
|------|----------|
| file1.rs | Added function X, modified function Y |
| file2.svelte | Added component with props, imported in parent |

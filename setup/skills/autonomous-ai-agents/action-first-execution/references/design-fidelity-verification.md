# Design Fidelity Verification Checklist

**When to use**: Before declaring a design task complete, especially previews, prototypes, and UI mockups.

## The Problem

Designer claims: "Created screenshot-faithful BiteWise preview matching all supplied references."

You relay the preview link without checking.

User opens it and says: "It looks like dogshit. The Goals screen has five cards; your reference shows two cards + a banner. The Statistics chart is a bar chart; the reference is a line chart."

Three wrong previews in a row, all rejected, all wasted time.

## The Fix

Visual claims are easy to verify: **just look at both screens side by side.**

### Before Publishing Any Visual Artifact

1. **Get the rendered preview** — agent publishes it
2. **For each screen in the brief**, do:
   - Render the preview at the same viewport dimensions as the reference
   - Take a screenshot (or open live in browser)
   - Load the user's reference image
   - Compare them side by side (even in prose: "Diary left half is reference, right half is preview")
3. **List any visible mismatches** — **specific, not generic**:
   - ❌ "It doesn't look the same"
   - ✅ "Diary shows 4 metric cards across top; reference shows metric cards in a 2×2 grid below header"
   - ✅ "Statistics chart is a bar chart; reference is a line chart with 4 data series"
   - ✅ "Wellness left rail is missing; reference has left sidebar visible"
4. **If mismatches found**: Block the task, list what's wrong, and hand it back
5. **If no significant mismatches**: Accept and publish

### Comparison Evidence

Best case: agent renders screenshot artifact showing reference + preview side-by-side (even a crude split-screen).

Acceptable case: agent lists specific matches ("Card borders match. Type size matches. Spacing between items is 12px in both. Goals ring color is #28D7A1 in both").

Unacceptable: "Matches reference" with no evidence.

### For Multi-Screen Artifacts

Do NOT skip screens. If five screens are claimed, five comparisons must happen.

**Red flag pattern** (from session 2026-09-04):
- Agent creates generic preview without comparing to references
- Agent self-audits and claims "screenshot-faithful"
- Comparison happens only after user rejects it

This pattern **destroys credibility** and wastes cycles. Do the comparison BEFORE publishing.

## Session Context: BiteWise Preview Spiral

**What happened:**
1. Thomas supplied five high-fidelity screenshots (Diary, Foods, Statistics, Wellness, Goals)
2. Designer task: "Build an exact pixel-faithful clickable preview"
3. Designer delivered preview #1; agent skipped comparison, sent link to Thomas
4. Thomas: "It looks disgusting" (correct — layout, hierarchy, charts all wrong)
5. Agent created preview #2 with explicit comparison instructions
6. Designer delivered with attachments showing "comparison screenshots"; agent didn't look at them, forwarded to Thomas
7. Thomas: Same complaint (correct again — still completely wrong hierarchy/layout)
8. Agent created preview #3 on different designer with different requirements
9. Same result — published without comparison, rejected by Thomas
10. **Cost: 3 hours, three rejected artifacts, visible user frustration**

**Root cause**: Agent accepted designer completion claims (`"comparison artifacts attached", "rendered against references"`) without actually looking at the evidence.

## Implementation Pattern

```python
# Pseudo-code for agent flow

if design_task_complete_claim:
    for screen in reference_screens:
        preview_screenshot = render_screen_from_preview(screen)
        reference_image = load_user_reference(screen)
        
        # ACTUALLY LOOK
        comparison = visual_compare(preview_screenshot, reference_image)
        
        if comparison.mismatches:
            return kanban_block(f"Visual mismatch on {screen}: {comparison.list_issues()}")
    
    # Only here: accept and publish
    return accept_and_publish(preview_url)
```

## Key Insight

Visual verification is the EASIEST class of verification to do objectively. You don't need to understand the code, run tests, or trace execution. You just look at both pictures and note what's different.

Yet it was skipped three times because "the agent said it was done."

Never skip the visual check for visual work. It takes 2 minutes per screen and prevents 1–3 hour rejection spirals.

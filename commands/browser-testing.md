---
description: Walk a feature's testing.md QA checklist in a real browser and report what diverged, without fixing anything. Marks the items only a human can judge so you can work those in parallel, walks the rest against a local or explicitly-named QA environment, records one line of evidence per step, and writes a numbered run record to the feature folder. Optional stage that runs after implementation and before /aiforging:review-loop. Never edits source, never opens a work item, never invents a checklist.
user_invocable: true
argument-hint: "[feature-name]"
---

# /aiforging:browser-testing

This command runs the **`browser-testing` skill**.

## What you must do when this command is invoked

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/browser-testing/SKILL.md` with the Read tool.
2. Execute the instructions in that file **exactly**, treating any argument passed here as the feature name the user is proposing (which you must still confirm, per the skill's preconditions).
3. Do not paraphrase, summarize, or "improve" the instructions as you follow them. The SKILL.md is the authoritative version.
4. Do not add rules in this file that are not in the SKILL.md. If you catch yourself wanting to, stop and update the SKILL.md instead. This file must stay a thin pointer.

## Why this is a pointer rather than a copy

AI Forging has a framework-wide rule: **one source of truth per concept.** The skill is the source of truth, because it is also what activates on its own when the model recognizes the situation, and what gets installed into a forge workspace at `.claude/skills/browser-testing/SKILL.md`. This command exists only so the capability has a name you can type.

The cost is one extra Read tool call per invocation. The benefit is that the rules — especially the ones that say what this pass may *never* do — are defined once.

## The one rule worth repeating even in a pointer

**This pass fixes nothing.** A failing checklist step is evidence that the product and the specification disagree; it is not evidence about which of them is wrong. Findings go to a human conversation. If you find yourself about to edit source, open a work item, or retry a step differently until it passes, stop — the SKILL.md explains why at length.

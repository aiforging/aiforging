---
description: Pick up a feature that already exists in this forge workspace — one you paused, or one a teammate started months ago. Reads its spec, plan, notes, QA checklist and review escalations, reports where things actually stand and what is next, then stops and asks. With no argument, presents the workspace's features and asks which. Read-only — changes no code, checks out no branches, dispatches nothing.
user_invocable: true
argument-hint: "[feature-name]"
---

# /aiforging:resume

This command runs the **`resume-feature` skill**.

## What you must do when this command is invoked

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/resume-feature/SKILL.md` with the Read tool.
2. Execute the instructions in that file **exactly**, treating any argument passed here as the feature name to match (matching rules are in the skill; ask rather than guess between two candidates).
3. Do not paraphrase, summarize, or "improve" the instructions as you follow them. The SKILL.md is the authoritative version.
4. Do not add rules in this file that are not in the SKILL.md. If you catch yourself wanting to, stop and update the SKILL.md instead. This file must stay a thin pointer.

## Why this is a pointer rather than a copy

**One source of truth per concept**, the same rule that makes `/aiforging:forge` a pointer at `new-feature.md`. The skill is the source of truth because it also activates on its own — "where did we leave off on the invoicing feature?" should reach it without anyone typing a command — and because it is copied into the forge workspace at `.claude/skills/resume-feature/SKILL.md`, so a teammate who cloned the workspace has it whether or not they installed the plugin.

## The rule worth repeating even in a pointer

**This is read-only.** It orients and then stops. It does not dispatch the next slice, check out a branch, or update the plan — because on a shared workspace the feature in front of you is frequently someone else's, and the decisions in their plan have reasons that may not be written down. Report, then let a human choose.

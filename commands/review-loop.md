---
description: Run multiple rounds of code review and fixes on a feature branch across every implicated target repo. Spawns one review subagent per repo, triages each finding against the source before accepting it, classifies green/amber/red, plans accepted findings into work items, dispatches fixes serialized per repo, and stops on a stated stop condition. Optional stage that runs after /aiforging:browser-testing. Not for a single one-off review.
user_invocable: true
argument-hint: "[feature-name] [effort level]"
---

# /aiforging:review-loop

This command runs the **`review-loop` skill**.

## What you must do when this command is invoked

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/review-loop/SKILL.md` with the Read tool.
2. Execute the instructions in that file **exactly**. Treat any arguments passed here as the feature name and, if the user named one, the review effort level — which the skill requires you to pass through in the form the underlying review capability expects.
3. Do not paraphrase, summarize, or "improve" the instructions as you follow them. The SKILL.md is the authoritative version.
4. Do not add rules in this file that are not in the SKILL.md. If you catch yourself wanting to, stop and update the SKILL.md instead. This file must stay a thin pointer.

## Why this is a pointer rather than a copy

Same framework-wide rule as every other alias here: **one source of truth per concept.** The skill is where the loop is defined, and it is what gets installed into a forge workspace at `.claude/skills/review-loop/SKILL.md`. This command exists so the capability has a name you can type.

## Two rules worth repeating even in a pointer

- **A clean loop is not a merge signal.** It means no more code-visible defects were found. The human's full test suite, their own manual QA, and their own code review all remain required, and none of them are automated here.
- **Verify every finding against the source before acting on it.** Roughly a third of review findings describe deliberate behavior. Skipping triage is how a review loop spends a round fixing things that were already right.

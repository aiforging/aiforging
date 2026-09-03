---
description: Run the Hammer stage against a feature or a specific file. Given a green feature test suite, merges the shared and target-local pattern tiers, scans the changed code for detection signals, and dispatches one fresh-context subagent per approved refactor slice — each committed atomically after the feature's suite stays green. Refuses to run before Fire is green or against untested code. Never runs the full repository suite.
user_invocable: true
argument-hint: "[feature-name | path/to/file]"
---

# /aiforging:hammer-refactor

This command runs the **`hammer-refactor` skill**.

## What you must do when this command is invoked

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/hammer-refactor/SKILL.md` with the Read tool.
2. Execute the instructions in that file **exactly**. Treat any argument passed here as either the feature name (plan-driven mode) or a specific file or directory (targeted mode) — the skill defines both entry points and how to tell them apart.
3. Do not paraphrase, summarize, or "improve" the instructions as you follow them. The SKILL.md is the authoritative version.
4. Do not add rules in this file that are not in the SKILL.md. If you catch yourself wanting to, stop and update the SKILL.md instead. This file must stay a thin pointer.

## Why this is a pointer rather than a copy

**One source of truth per concept**, the same rule that makes `/aiforging:forge` a pointer at `new-feature.md`. The skill is the source of truth for three reasons: it activates on its own when the model recognizes the situation, it is what a Fire subagent dispatches at the close of a sequence, and it is what gets copied into each onboarded target at `<target>/.claude/skills/hammer-refactor/SKILL.md` for teammates who don't have the plugin installed. This command exists only so the capability has a name you can type.

Note that the copy inside a target repo is the same file. If you are working directly inside a target without the plugin, the skill is still there — you just don't have this command.

## Two rules worth repeating even in a pointer

- **No refactor without green tests, and no refactor of untested code.** If the feature's named suite isn't passing, or the target file has no coverage, stop and say so. Fire comes first.
- **Never the full repository suite.** Between slices, run only the feature's named suite — the one `plan.md` names. When every slice is done, hand the full suite to the human in words rather than running it.

---
description: Capture a lesson from a code review into the pattern library as a new file. Use after correcting Claude's work in a way that encodes a reusable structural rule — the skill writes one .md per pattern or anti-pattern, asks whether it belongs to the workspace shared tier or just this target repo, and makes it available to every subsequent Hammer pass. This is the Tempering stage. The skill also offers itself unprompted at genuine corrective moments.
user_invocable: true
argument-hint: "[what to capture]"
---

# /aiforging:capture-pattern

This command runs the **`capture-pattern` skill**.

## What you must do when this command is invoked

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/capture-pattern/SKILL.md` with the Read tool.
2. Execute the instructions in that file **exactly**. Treat any argument passed here as the user's description of the lesson to capture. If no argument was given, the lesson is whatever correction just happened in this conversation — say what you understood it to be and confirm before writing anything.
3. Do not paraphrase, summarize, or "improve" the instructions as you follow them. The SKILL.md is the authoritative version.
4. Do not add rules in this file that are not in the SKILL.md. If you catch yourself wanting to, stop and update the SKILL.md instead. This file must stay a thin pointer.

## Why this is a pointer rather than a copy

**One source of truth per concept.** The skill is the source of truth, and in this case that matters more than usual: `capture-pattern` is primarily **reactive** — its real job is to notice a corrective moment during an ordinary session and offer to persist it, without being asked. It is installed both in the forge workspace and in each onboarded target so it can do that from either place.

This command is the explicit door into the same skill, for when you already know you want to capture something and would rather say so than wait to be offered.

## The rule worth repeating even in a pointer

**One correction, one file.** The library scales precisely because the 50th pattern costs no more than the 5th — each lives in its own file and gets its own fresh-context subagent on every Hammer pass. Do not append to an existing pattern file to avoid creating a new one, and do not batch several lessons into one capture.

And the skill's own bias: **it should decline to prompt more often than it prompts.** An over-eager capture offer trains the human to reflexively say no, which breaks the whole feedback loop. A capture is warranted when the correction encodes a *reusable structural rule*, not when it was a one-off preference.

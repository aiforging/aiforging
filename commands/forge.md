---
description: Alias for /aiforging:new-feature. Start a new feature (or extend an existing one) in the current forge workspace. Creates docs/features/<name>/ with the right shape (flat or nested), seeds spec.md with a Summary section captured from the user's initial prompt, and hands off to superpowers:brainstorming. Runs Planning Workflow Step 1 and stops at the Summary checkpoint. Non-destructive; never executes plans.
user_invocable: true
argument-hint: "[feature-name] [initial prompt...]"
---

# /aiforging:forge

This command is an **alias for `/aiforging:new-feature`**. It exists because "forge" is the natural verb for the action ("forge a new feature") and is faster to type than "new-feature" when you're in the middle of a thought.

## What you must do when this command is invoked

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/new-feature.md` with the Read tool.
2. Execute the instructions in that file **exactly**, treating whatever arguments the user passed to `/aiforging:forge` as if they had been passed to `/aiforging:new-feature`.
3. Do not paraphrase, summarize, or "improve" the instructions as you follow them. `new-feature.md` is the authoritative version.
4. Do not add rules in this file that are not in `new-feature.md`. If you catch yourself wanting to, stop and update `new-feature.md` instead. This file must stay a thin pointer.

## Why this is a pointer rather than a copy

AI Forging has a framework-wide rule: **one source of truth per concept.** If `new-feature.md` and `forge.md` drift, the framework degrades in the place users interact with it most often — and it degrades silently, because users who type one form will never notice the other form is different. The pointer-and-reread approach is the cheapest possible implementation of that rule while still letting the user type `/aiforging:forge` during a fast-moving session.

The cost is one extra Read tool call per invocation, which is negligible. The benefit is that every rule, every hard constraint, every Summary-checkpoint behavior is defined once.

## Namespacing note for the reader

Claude Code plugin commands are namespaced by the owning plugin, so the resolvable form of this alias is `/aiforging:forge` — there is no bare `/forge` command published by this plugin. That's intentional: bare top-level slash commands would collide with other plugins the user has installed. If you want even less typing, set up a shell-level or editor-level snippet on your own machine.

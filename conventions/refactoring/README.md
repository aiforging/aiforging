# Refactoring — Hammer & Tempering Stages

## What this directory is

This directory is the **pattern library** for the Hammer stage of the forge. It contains two subdirectories:

- `patterns/` — one Markdown file per named architectural pattern you want the refactor pass to enforce.
- `anti-patterns/` — one Markdown file per named smell you want the refactor pass to detect and eliminate.

Each file is self-contained and describes exactly one concern. There is no monolithic "refactor rules" document. This is on purpose — see "Why one file per pattern" below.

## The two skills this directory depends on

AI Forging does not implement the refactor pass itself. It delegates to two skills shipped by the `superpowers` plugin:

1. **`superpowers:subagent-driven-development`** — dispatches a fresh-context subagent per task. In our case, one subagent per pattern or anti-pattern file, each iterating that file's rules against the session's changed files independently. This is how the Hammer scales without a context ceiling.
2. **`superpowers:test-driven-development`** — the Fire-stage loop that must precede Hammer. A refactor pass never runs on code that isn't covered by a green test suite.

If either skill is unavailable, the Hammer and Tempering stages degrade. Install the `superpowers` plugin first.

## How a refactor pass runs

Once the Fire stage is green:

1. List the files changed in the current working session (`git diff --name-only` against the session's base, or a tracked set maintained by the loop).
2. List the pattern files under `patterns/` and the anti-pattern files under `anti-patterns/`.
3. For each pattern file, dispatch one fresh subagent via `superpowers:subagent-driven-development`. The subagent's context is exactly:
   - The pattern file.
   - The changed-files list.
   - Read-only access to the rest of the codebase for reference.
   - The instruction: "apply this pattern to these files. Propose edits. Run the relevant tests after each edit. Report."
4. Collect each subagent's results. Present a unified diff to the human for review. No edits ship without human approval — this is one of the four governance gates.
5. Any pattern that produced new observations during the pass may warrant a new pattern file. That's the **Tempering** stage: knowledge gets captured back into the library.

Adding the 50th pattern costs no more than the 5th, because each lives in its own file and gets its own subagent with its own fresh context. There is no accumulating "big refactoring prompt" that hits a ceiling.

## Why one file per pattern

1. **No context ceiling.** Monolithic refactor prompts grow until they exceed the model's context, at which point the last patterns added silently stop being enforced. One-file-one-subagent removes that failure mode entirely.
2. **No cross-pattern interference.** Two patterns that disagree on edge cases (e.g., "extract method aggressively" vs. "keep single-use helpers inlined") don't confuse a single pass; they are enforced by different subagents and reconciled at the human-review gate.
3. **Easy to add, remove, or disable.** A pattern you're experimenting with lives in one file you can delete. A pattern that turned out wrong doesn't need to be surgically removed from a shared document.
4. **Authorship and review are clean.** Each pattern file gets a Git history. Each pattern can be owned, versioned, and reviewed independently.

## File format

Each pattern / anti-pattern file should contain, at minimum:

```markdown
# <Pattern Name>

## Rule

One or two sentences stating the rule as plainly as possible.

## Why

The reasoning. Link to architectural principles in `architecture/` where relevant.

## Detect

How to recognize this pattern / anti-pattern in code. Be specific — describe
file structure, naming, method shape, or mechanical signals the subagent
can check.

## Apply (or Eliminate)

What the fix looks like. Step-by-step if possible. Include a before/after
code sketch.

## Don't apply when

Edge cases or situations where the pattern does not belong. (For
anti-patterns, situations where the smell is actually okay.)

## Related

Links to other pattern files or architecture docs.
```

Keep each file short and concrete. If you can't fit a pattern onto two screens of text, it's probably two patterns.

## Adding a new pattern

When a review or a refactor pass reveals a pattern you want to enforce going forward, use the `capture-pattern` skill (installed at `.claude/skills/capture-pattern/SKILL.md` in this repo) — it handles duplicate detection, the file template, cross-linking, and approval flow automatically. The manual steps it performs are:

1. Write a new file in `.aiforging/patterns/` or `.aiforging/anti-patterns/`, named in kebab-case.
2. Use the file format documented below in "File format".
3. Commit it alone, with a message that says what triggered its creation.
4. Re-run the Hammer pass on the current working session. The new pattern's subagent now participates automatically (no wiring needed — the Hammer pass globs these directories on every run).

Do NOT edit an existing pattern file to "also cover" a new concern. That's how files turn into monoliths. Make a new file.

## Anti-pattern detection tips

For the anti-pattern subagents to be effective, the file should describe mechanical detection signals, not just philosophical ones. "Fat controller" is easier to detect as "more than one public method on a controller class" than as "controller is doing too much." Always include the mechanical version.

## Related

- `tdd/fire-red-green-refactor.md`
- `architecture/domain-driven-hexagonal.md`
- `architecture/single-action-controllers.md`

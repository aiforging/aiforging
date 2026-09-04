# Refactoring — Hammer & Tempering Stages

## What this directory is

This directory is the **pattern library** for the Hammer stage of the forge. It contains two subdirectories:

- `patterns/` — one Markdown file per named architectural pattern you want the refactor pass to enforce.
- `anti-patterns/` — one Markdown file per named smell you want the refactor pass to detect and eliminate.

Each file is self-contained and describes exactly one concern. There is no monolithic "refactor rules" document. This is on purpose — see "Why one file per pattern" below.

## The tier placeholder — `README.md` in a tier directory

Every `patterns/` and `anti-patterns/` directory ships with a `README.md`. It is **not a pattern**, and **every glob over the library excludes it** — `hammer-refactor` when it builds the merged set, `capture-pattern` when it scans for duplicates and cross-links, `review-loop` when it hands the library to a review agent, and `uninstall` when it sorts plugin files from your captures.

That last one matters most and is the easiest to get wrong. The usual test for "is this the plugin's file or the user's?" is the `seeded: true` frontmatter — and the placeholder has no frontmatter, by design, because target-local patterns do not carry any. So it fails the frontmatter test and looks like one of your captures. **Match it by filename instead.** A file named `README.md` inside a tier directory is always the plugin's placeholder.

Why it exists at all: git cannot track an empty directory. A tier created with `mkdir` alone disappears the moment anything touches the working tree, is missing for every teammate who clones, and causes `/aiforging:update-targets` to offer to recreate it on every future run — indefinitely. The placeholder ends that, and gives the two-tier explanation a home in the directory you are about to write a pattern into.

## Two-tier pattern library

Patterns exist at two tiers, and the `hammer-refactor` skill merges both when scanning a target:

**Shared tier** — lives at the workspace level. For separate forge workspaces (multi-repo teams): `<workspace>/.aiforging/patterns/` and `<workspace>/.aiforging/anti-patterns/`. For in-repo workspaces (monorepo/single-repo): `<repo-root>/.aiforging/patterns/` and `<repo-root>/.aiforging/anti-patterns/`. Shared patterns have a YAML frontmatter block with an `applies-to` list of stack identifiers (the same vocabulary `detect-project.py` outputs: `symfony-php`, `laravel-php`, `react`, `next`, `doctrine`, `eloquent`, etc.) or the special value `all` for universal patterns. The `hammer-refactor` skill reads shared patterns and filters by the current target's detected stack before dispatching subagents.

**Target-local tier** — lives in each target's own `.aiforging/patterns/` and `.aiforging/anti-patterns/` (for multi-repo), or each sub-project's `.aiforging/patterns/` (for monorepo). Target-local patterns have no `applies-to` frontmatter — they apply unconditionally to that target. Use this tier for repo-specific patterns that only apply to one target (e.g., "this legacy repo uses X weird pattern because of Y historical debt").

When both tiers contain a pattern file with the same filename, the target-local copy wins. This lets a target override a shared pattern with a repo-specific version.

### Frontmatter format for shared patterns

```yaml
---
applies-to: [symfony-php, doctrine]
captured-from: hub-plus-api
captured-date: 2026-04-13
seeded: true
---
```

- `applies-to` (required for shared tier): list of stack identifiers. Use `[all]` for universal patterns.
- `captured-from` (optional): the target where the pattern was first observed.
- `captured-date` (optional): when the pattern was captured.
- `seeded` (optional): `true` for patterns shipped with the plugin and seeded during setup. Distinguishes plugin-provided patterns from team-captured ones.

Target-local patterns omit the frontmatter entirely (or include only `captured-from` and `captured-date` for provenance). The `## Source` section at the bottom of the file body is preserved for human-readable attribution.

## The two skills this directory depends on

AI Forging does not implement the refactor pass itself. It delegates to two skills shipped by the `superpowers` plugin:

1. **`superpowers:subagent-driven-development`** — dispatches a fresh-context subagent per task. In our case, one subagent per pattern or anti-pattern file, each iterating that file's rules against the session's changed files independently. This is how the Hammer scales without a context ceiling.
2. **`superpowers:test-driven-development`** — the Fire-stage loop that must precede Hammer. A refactor pass never runs on code that isn't covered by a green test suite.

If either skill is unavailable, the Hammer and Tempering stages degrade. Install the `superpowers` plugin first.

## How a refactor pass runs

Once the Fire stage is green:

1. List the files changed in the current working session (`git diff --name-only` against the session's base, or a tracked set maintained by the loop).
2. Build the merged pattern set from both tiers: (a) all target-local patterns from the target's own `.aiforging/patterns/` and `.aiforging/anti-patterns/`, plus (b) all shared patterns from the workspace whose `applies-to` includes at least one of the target's detected stacks (or `all`). If a shared pattern and a target-local pattern share a filename, the target-local copy wins.
3. For each pattern file in the merged set, dispatch one fresh subagent via `superpowers:subagent-driven-development`. The subagent's context is exactly:
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

When a review or a refactor pass reveals a pattern you want to enforce going forward, use the `capture-pattern` skill (installed at `.claude/skills/capture-pattern/SKILL.md` in this repo or in the forge workspace) — it handles duplicate detection, the file template, tier selection, cross-linking, and approval flow automatically.

The skill asks a key question at capture time: **"Does this apply only to `<current-target>`, or to all `<stack-family>` targets?"** If shared, it writes to the workspace-level shared tier with `applies-to` frontmatter. If local, it writes to the target's own `.aiforging/patterns/` or `.aiforging/anti-patterns/`.

The manual equivalent:

1. Decide the tier. If the pattern is generalizable across same-stack targets → shared tier (workspace-level `.aiforging/`). If repo-specific → target-local tier (target's `.aiforging/`).
2. Write a new file named in kebab-case. For shared-tier files, include the `applies-to` frontmatter.
3. Use the file format documented below in "File format".
4. Commit it alone, with a message that says what triggered its creation.
5. Re-run the Hammer pass. The new pattern's subagent participates automatically (no wiring needed — the Hammer pass globs both tiers on every run).

Do NOT edit an existing pattern file to "also cover" a new concern. That's how files turn into monoliths. Make a new file.

## Anti-pattern detection tips

For the anti-pattern subagents to be effective, the file should describe mechanical detection signals, not just philosophical ones. "Fat controller" is easier to detect as "more than one public method on a controller class" than as "controller is doing too much." Always include the mechanical version.

## Related

- `tdd/fire-red-green-refactor.md`
- `architecture/domain-driven-hexagonal.md`
- `architecture/single-action-controllers.md`

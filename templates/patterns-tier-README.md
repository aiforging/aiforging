<!-- AI Forging — pattern tier placeholder. Installed by /aiforging:setup and
     /aiforging:update-targets. Excluded from every pattern-library glob. -->

# Patterns

One `.md` file per pattern. **This file is documentation, not a pattern** — the tooling skips `README.md`.

## What belongs here

A *pattern* is a shape worth reaching for: "Extract Service From Controller," "Scoped Find-Or-Throw Helper." Name them as imperative verb phrases. The counterpart directory, `anti-patterns/`, holds the shapes worth removing.

Each file needs enough that **a fresh-context subagent reading only that one file can find the situation and apply the change correctly** — detection signals concrete enough to grep for, why it helps, a minimal before-and-after, and what to reach for next. If your file needs surrounding context to be actionable, it is not finished.

## Which tier am I in?

Two tiers, merged on every Hammer pass:

- **Shared tier** — at the forge workspace root. Applies to every target whose stack matches, so these files carry `applies-to` YAML frontmatter. Patterns shipped with the plugin live here and are marked `seeded: true`.
- **Target-local tier** — inside a target repo. Applies only to that repo; no frontmatter needed.

If this file sits inside a target repo, you are in the target-local tier. A file here with the same name as a shared one overrides it.

## How files get here

Mostly not by hand. The `capture-pattern` skill offers to write one when you correct Claude during a review in a way that encodes a reusable structural rule — one correction, one file. It asks which tier each capture belongs to.

The library scales because the 50th pattern costs no more than the 5th: every file gets its own fresh-context subagent on every Hammer pass, so nothing competes for room in a single instruction file.

## Why this file exists at all

Git cannot track an empty directory. Without a file in it, this tier disappears on the next clone and the tooling offers to recreate it on every run, forever. That is the whole job of this README — plus giving the explanation above somewhere to live.

Full format: the pattern-library README at the workspace root (`.aiforging/README.md`).

<!-- AI Forging workspace marker — tooling greps this file for "AI Forging workspace" (or the older "AI Forging forge workspace").
     Keep this line, or the phrase below, intact. Losing both makes the directory
     stop being recognized as a workspace. -->
# Forge Workspace — Claude Context

> **You are in an AI Forging workspace.** This is NOT a codebase. It is a shared, committed orchestration directory from which the team drives feature work — its feature folders are the durable record any engineer can pick up from, via `/aiforging:resume`. The actual code lives in the repos registered under `permissions.additionalDirectories` in `.claude/settings.local.json` (the gitignored, per-user settings file — see the "Settings file split" section below).

## First thing to do in any session

1. Read `docs/features/README.md` to refresh the feature-folder convention.
2. Check whether the user named a specific feature. If yes, read that feature's `docs/features/<feature-name>/spec.md` and `plan.md` if they exist.
3. If the user has not named a feature, ask which feature they want to work on (or whether they want to start a new one).

## What this workspace is for

- **Cross-repo feature planning.** Any feature that touches more than one repo has its spec and plan centralized here, not fragmented across the target repos.
- **Spec/plan/execute orchestration.** The `superpowers` plugin's `brainstorming`, `writing-plans`, and `executing-plans` skills are the primary drivers. AI Forging layers feature-folder conventions and the `hammer-refactor` skill on top.
- **Dispatching subagents across repos.** Plans written in `docs/features/<name>/plan.md` are structured so that each slice can be handed to a fresh-context subagent via `superpowers:subagent-driven-development`. Subagents read the slice, reach into the relevant target repo via additionalDirectories, make the change, run tests, and report back.

## What this workspace is NOT for

- **Not a code repo.** Do not write application source code here. Source code belongs in a target repo under `additionalDirectories`.
- **Not a dumping ground.** Only `docs/features/<name>/` directories live here (plus this `CLAUDE.md`, the `README.md`, `.gitignore`, and the `.claude/` settings files). If you're tempted to drop a random `.py` or `.ts` file at the root, stop and ask where it actually belongs.
- **Not a substitute for the target repos' own docs.** Architecture decisions that are specific to one repo belong inside that repo's `.aiforging/` or in an ADR within that repo. The workspace holds cross-cutting work.

## Settings file split

This workspace uses Claude Code's native two-file settings convention. Both files live under `.claude/`:

- **`settings.json`** — COMMITTED to git. Holds only `enabledPlugins`. Shared with teammates; never contains absolute local paths. When a teammate clones the workspace, this file auto-activates `superpowers` and `aiforging` for them.
- **`settings.local.json`** — GITIGNORED (by `.gitignore` at the workspace root). Holds `permissions.additionalDirectories` — the absolute local paths to the target repos on THIS machine. A teammate cloning the workspace gets no `settings.local.json` and must re-run `/aiforging:setup` on their own machine to register their own local copies of the targets.

**When working in this workspace, do NOT edit either settings file by hand.** Use the aiforging helper scripts: `configure-plugins.py` for `settings.json`, `configure-directories.py` for `settings.local.json`. If you find a config inconsistency (e.g., `additionalDirectories` sitting in `settings.json` from an old version), offer to migrate by moving the key to `settings.local.json` — never silently rewrite.

## Two-tier pattern library

The pattern library has two tiers that `hammer-refactor` merges on every run:

**Shared tier** — lives in THIS workspace at `.aiforging/patterns/` and `.aiforging/anti-patterns/`. Shared patterns have YAML frontmatter with an `applies-to` list of stack identifiers (e.g., `symfony-php`, `react`, `doctrine`, or `all`). When `hammer-refactor` runs against a target, it reads the shared tier and includes only patterns whose `applies-to` matches the target's detected stack. Seeded patterns (shipped with the plugin) live here.

**Target-local tier** — lives in each target repo's own `.aiforging/patterns/` and `.aiforging/anti-patterns/`. Target-local patterns have no `applies-to` frontmatter and apply unconditionally to that target. Use this tier for repo-specific rules. Each tier directory ships with a `README.md` explaining which tier you are in and what belongs there — it also keeps the directory alive, since git will not track an empty one. Every pattern-library glob excludes it.

If both tiers contain a file with the same name, the target-local copy wins (allows per-target overrides).

## Target repos

The repos this workspace is onboarded to are listed in `.claude/settings.local.json` under `permissions.additionalDirectories`. Each one has its own `.aiforging/` folder containing:

- `ANALYSIS.md` — snapshot from `architecture-analyzer` (regenerated on rerun).
- `architecture/`, `tdd/`, `subagent-orchestration/` — AI Forging conventions copied in during onboarding.
- `patterns/` and `anti-patterns/` — the target-local tier of the pattern library (holds repo-specific captures; ships with a tier README that every glob excludes).

Additionally, candidate target repos have two AI Forging skills committed at `.claude/skills/` so that anyone cloning the target repo can use them independently of whether the aiforging plugin is installed on their machine:

- **`hammer-refactor/SKILL.md`** — the executable Hammer stage. Reads both tiers when scanning.
- **`capture-pattern/SKILL.md`** — the reactive Tempering feedback loop (see next section).

The two verification skills — `browser-testing` and `review-loop` — are **workspace-level only** and are not copied into targets. Their inputs live here: the feature's `testing.md`, the feature folder, and the list of registered targets. A copy inside a single target repo would be a skill whose primary input isn't in that repo.

Each target repo also has its own `.claude/settings.json` with an `enabledPlugins` block committed to its git history, so teammates who clone the target repo (without cloning this workspace) still get `superpowers` and `aiforging` auto-activated when they run Claude inside the target.

## Tempering feedback loop — capture-pattern

This workspace has `capture-pattern` installed at `.claude/skills/capture-pattern/SKILL.md`, which is the reactive mechanism for the Tempering pillar. When the human corrects your work during an interactive session in a way that encodes a reusable structural rule — "don't do it that way," "always do X," "never do Y," rejecting a diff with a structural reason — detect the corrective moment and follow the `capture-pattern` skill's instructions. The skill handles:

- Classifying the correction as pattern vs anti-pattern (or asking the human if ambiguous).
- Asking the **tier question**: "Does this apply only to `<target>`, or to all same-stack targets?" If shared → writes to the workspace's `.aiforging/` with `applies-to` frontmatter. If target-local → writes to the target's `.aiforging/`.
- Resolving WHICH target the pattern was observed in (when running from the workspace with multiple registered targets).
- Duplicate-checking across BOTH tiers before drafting.
- Drafting the file in the AI Forging pattern format and showing it for approval before writing.
- Cross-linking with any related pattern or anti-pattern already in the library.

The skill biases toward NOT prompting — only offer capture when the correction clearly encodes a reusable, structural rule. An over-eager `capture-pattern` prompt trains the human to reflexively decline, which breaks the whole loop.

Every captured pattern is ONE `.md` file. The next `hammer-refactor` run against any matching target automatically picks it up — shared-tier captures are immediately available to ALL same-stack targets with no propagation step.

## Working flow

For any feature you're asked to work on:

1. **Spec.** If `docs/features/<feature-name>/spec.md` does not exist, use `superpowers:brainstorming` to interview the user and produce it. Do not skip this.
2. **Plan.** Use `superpowers:writing-plans` to produce `plan.md` **in the AI Forging slice format** documented in `docs/features/README.md`. Each slice is tagged `[fire]`, `[hammer]`, or `[tempering]`, names its target repo, includes its test, and has an explicit subagent prompt.
3. **Gates.** Any slice marked `[gate: architecture]`, `[gate: schema]`, or `[gate: contract]` must be explicitly approved by the user before it dispatches.
4. **Register the feature's test suite.** One named suite per feature — not one per work item — registered before the first test is written and augmented by every later work item. Its name and exact run command go in `plan.md`'s `## Test suite` block. See `docs/features/README.md`.
5. **Execute Fire.** Use `superpowers:executing-plans` + `superpowers:test-driven-development` to walk the `[fire]` slices. Fire must produce a green feature suite before any Hammer slice runs.
6. **Execute Hammer.** Invoke `aiforging:hammer-refactor` on the target repo. The skill reads `plan.md`, merges patterns from both the workspace shared tier and the target-local tier (filtered by the target's stack), and dispatches one subagent per approved slice. Human review after each slice.
7. **Temper.** When the feature is done, any newly-discovered patterns or anti-patterns get captured via `capture-pattern`. The skill asks whether each capture should be shared (workspace level) or target-local.
8. **Verify — optional, and worth it whenever there's a UI.** `aiforging:browser-testing` walks the feature's `testing.md` in a real browser while the human works the 👤 items in parallel. It reports what diverged and fixes nothing; every finding is a conversation before it becomes work. Then `aiforging:review-loop` runs rounds of review, triage, and fix across every implicated repo. Browser testing first — reading the diff harder can't find a feature that works exactly as written and is wrong.
9. **Hand the full suite to the human.** Say it in words: every run in this session was scoped to the feature's suite, a cross-feature regression would not have surfaced, here is the command, each refactor is individually revertible. Then their own pass over `testing.md`, their own code review, and a PR.

## Hard rules

- **Never execute Hammer before Fire is green.** The `hammer-refactor` skill enforces this, but you should too.
- **Never run the full repository test suite.** Not during Fire, not during Hammer, not to "make sure nothing broke." Run the feature's named suite. If you believe the full suite must run, stop and ask the user — running it is their job, once, at the end.
- **Never declare implementation complete without handing the full suite to the human, in words.** Even when the feature was small. Especially then.
- **Never weaken or skip tests.** If a test blocks a refactor, the refactor is wrong.
- **Never let `browser-testing` fix what it finds.** A failing checklist step means the product and the spec disagree; which one is wrong is the human's call.
- **Never write source code in this workspace.** Source code belongs in the target repos.
- **Never delete or silently rewrite a feature folder.** History matters. If the spec is wrong, add a new feature folder with a new name.
- **Never dispatch more than one subagent per refactor slice.** One pattern, one slice, one subagent. That's how we keep each refactor's reasoning scoped and reviewable.
- **Never commit `.claude/settings.local.json`.** It contains absolute local paths that are meaningless or harmful on another machine. The `.gitignore` at the workspace root already protects it, but double-check `git status` before committing if you're unsure.
- **Never write absolute local paths into `.claude/settings.json`.** That file is committed and shared. If a path needs to be written, it goes to `settings.local.json`.

## Tool expectations

Phase A of `/aiforging:setup` wrote an `enabledPlugins` block into this workspace's committed `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true,
    "aiforging@aiforging": true
  }
}
```

Claude Code auto-activates both plugins whenever it runs in this directory, as long as they're installed at the machine level:

- **`aiforging`** — provides `/aiforging:setup`, `/aiforging:new-feature` (aliased `/aiforging:forge`), `/aiforging:update-targets`, `/aiforging:uninstall`, and the `architecture-analyzer` skill. Four more skills are each available both automatically and as a command you can type: `/aiforging:hammer-refactor`, `/aiforging:capture-pattern`, and the optional verification pair `/aiforging:browser-testing` and `/aiforging:review-loop`.
- **`superpowers`** — provides `test-driven-development`, `brainstorming`, `writing-plans`, `executing-plans`, and `subagent-driven-development`. AI Forging depends on these directly and does not reinvent them.

If Claude Code warns that either plugin isn't installed, install it once at the machine level with `/plugin install <name>@claude-plugins-official`, then reopen the session. If you installed from a different marketplace (e.g., `superpowers@superpowers-dev`), update the `enabledPlugins` key in `.claude/settings.json` to match, or re-run `/aiforging:setup` and tell it the right source when prompted.

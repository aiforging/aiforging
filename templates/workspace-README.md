# Forge Workspace

This directory is an **AI Forging workspace** — a central orchestration hub for driving feature work across one or more codebases.

> **This is not a project.** No application source code lives here. The actual code being worked on lives in the repos registered under `permissions.additionalDirectories` in `.claude/settings.local.json`.

## What's in here

```
.
├── CLAUDE.md                              # Tells Claude this is a forge workspace and how to work in it
├── README.md                              # This file
├── .gitignore                             # Protects settings.local.json and helper-script backups
├── .claude/
│   ├── settings.json                      # COMMITTED: enabledPlugins (superpowers + aiforging)
│   ├── settings.local.json                # GITIGNORED: absolute paths to your target repos
│   └── skills/
│       ├── capture-pattern/
│       │   └── SKILL.md                   # Tempering feedback loop (see below)
│       ├── browser-testing/               # optional — walk testing.md in a real browser
│       │   └── SKILL.md
│       └── review-loop/                   # optional — rounds of review, triage, fix
│           └── SKILL.md
├── .aiforging/
│   ├── patterns/                          # SHARED TIER — applies-to frontmatter, stack-filtered
│   └── anti-patterns/                     # SHARED TIER — seeded patterns live here
└── docs/
    └── features/
        ├── README.md                      # The feature-folder convention (read first)
        └── <feature-name>/                # One folder per active feature
            ├── spec.md                    # WHAT we're building and WHY
            ├── plan.md                    # HOW, broken into subagent-friendly slices
            └── notes.md                   # Optional scratch notes
```

## The two settings files (important)

Claude Code reads `settings.json` AND `settings.local.json` at session start and merges them. AI Forging splits them by lifecycle:

**`.claude/settings.json`** is the committed, shareable settings file. It contains `enabledPlugins` and nothing else. Every teammate who clones this workspace gets `superpowers` and `aiforging` auto-activated when they run Claude here, without touching their personal config.

**`.claude/settings.local.json`** is the gitignored, per-user file. It contains `permissions.additionalDirectories` — the absolute paths to YOUR target repos on YOUR machine. These paths never belong in the shared repo because every teammate has their code at a different absolute path. When a teammate clones this workspace and runs `/aiforging:setup` to register their own target repos, their paths go into their own `settings.local.json`.

The `.gitignore` at the workspace root protects `settings.local.json` from accidental commits.

## Required plugins

`/aiforging:setup` wrote an `enabledPlugins` block into this workspace's committed `.claude/settings.json` so that Claude Code auto-activates both plugins when it runs here:

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true,
    "aiforging@claude-plugins-official": true
  }
}
```

The plugins themselves are installed once per user at the machine level — Claude Code reads the enable-map at session start and activates the matching installs. If you haven't installed them yet:

- **[aiforging](https://github.com/aiforging/aiforging)** — the framework that defines the slice plan format and ships the `hammer-refactor`, `capture-pattern`, `architecture-analyzer`, `browser-testing`, and `review-loop` skills. Install with `/plugin install aiforging@claude-plugins-official`.
- **[superpowers](https://github.com/obra/superpowers)** — the foundation. Provides `test-driven-development`, `brainstorming`, `writing-plans`, `executing-plans`, and `subagent-driven-development`. AI Forging depends on these. Install with `/plugin install superpowers@claude-plugins-official`.

If you installed either from a different marketplace (for example `superpowers@superpowers-dev` via `/plugin marketplace add obra/superpowers`), update `.claude/settings.json` to match the identifier you actually installed, or re-run `/aiforging:setup` and supply the right marketplace source when prompted.

## The Tempering feedback loop — capture-pattern

`/aiforging:setup` installed a skill called `capture-pattern` at `.claude/skills/capture-pattern/SKILL.md` in this workspace. It is the operational mechanism for the **Tempering** pillar of the forge (the third pillar, after Fire and Hammer): capturing human code-review lessons back into the per-target pattern library so the Hammer pass enforces them on every subsequent feature.

**How it works.** During any interactive session in this workspace (or inside one of your target repos — `/aiforging:setup` also installs a copy there), when you correct the AI's work in a way that encodes a reusable structural rule — "no, don't do it that way, always do X," "that's the wrong layer," "we never mix those concerns" — the skill detects the corrective moment and offers to persist the lesson as a new pattern or anti-pattern file. It asks:

1. Which target the correction was observed in (if running from the workspace with multiple targets).
2. **The tier question**: "Does this apply only to `<target>`, or to all same-stack targets?" If shared → writes to the workspace's `.aiforging/patterns/` or `.aiforging/anti-patterns/` with `applies-to` frontmatter (stack identifiers). If target-local → writes to the target's own `.aiforging/patterns/` or `.aiforging/anti-patterns/`.

The file name is kebab-case and the format is prescriptive — see `conventions/refactoring/README.md` in the plugin source for the full two-tier documentation.

**Why this is the whole framework's point.** Each captured pattern is ONE `.md` file. Shared-tier captures are immediately available to ALL same-stack targets — no manual propagation step needed. Adding the 50th pattern costs the same as the 5th because each pattern gets its own fresh-context subagent during the Hammer pass. Every team member contributes just by doing normal code reviews. Quality compounds.

**The skill is reactive, not proactive** — it only fires when a corrective moment happens, and it biases heavily toward NOT prompting to avoid training you to reflexively decline. If it's firing too often, tell it to back off and give specific guidance on what kinds of corrections should and shouldn't trigger it; update the skill file's "Over-prompting guard" section in both locations.

## Git and the workspace history

This workspace is designed to be a git repo. Specs, plans, and the accumulated feature history are first-class artifacts that compound in value over time — the git log of `docs/features/` is your institutional memory of how cross-repo work got done. `/aiforging:setup` will offer to `git init` the workspace automatically and stage an initial commit; re-runs will offer to commit each onboarding as a follow-up commit.

**What gets committed:**

- `CLAUDE.md`, `README.md`, `.gitignore`
- `docs/features/**` (specs, plans, notes for every feature — this is the valuable part)
- `.aiforging/patterns/**` and `.aiforging/anti-patterns/**` (the shared-tier pattern library — seeded patterns plus team captures)
- `.claude/settings.json` (the `enabledPlugins` block — shared with teammates)
- `.claude/skills/capture-pattern/SKILL.md` (the Tempering feedback-loop skill, shared with teammates so every clone of the workspace behaves the same way when corrective moments occur)

**What does NOT get committed:**

- `.claude/settings.local.json` (absolute paths to YOUR target repos)
- `*.bak-*` files (timestamped backups from the configure-plugins.py / configure-directories.py helpers)

### Cloning this workspace on another machine

When a teammate clones the workspace, they'll see:

- `CLAUDE.md`, `README.md`, `docs/features/**`, and `.gitignore` — immediately useful.
- `.claude/settings.json` with `enabledPlugins` — Claude Code auto-activates superpowers and aiforging for them.
- `.claude/skills/capture-pattern/SKILL.md` — the same Tempering feedback loop you set up, ready to fire the first time they correct the AI.
- NO `.claude/settings.local.json` — because it's gitignored.

The teammate then runs `/aiforging:setup` in the cloned workspace. Phase detection will see an initialized workspace but no `settings.local.json`, recognize this as the "cloned-workspace-needs-local-setup" case, and walk them through onboarding their own local copies of the target repos — writing their paths into their own fresh `settings.local.json`.

## How to use this workspace

1. **Pick or create a feature.** `/aiforging:forge <name> "<what you want>"`, or create `docs/features/<kebab-case-name>/` by hand.
2. **Spec it.** Run `superpowers:brainstorming` then the spec phase of `superpowers:writing-plans` to fill out `spec.md`.
3. **Plan it.** Run the plan phase of `superpowers:writing-plans` to produce `plan.md` in the AI Forging slice format (see `docs/features/README.md`). The plan names **one test suite for the whole feature** and repeats the scoped-run rule in every slice. If the feature has a UI surface, fill in its `testing.md` checklist now, from the spec.
4. **Execute Fire.** Walk the `[fire]` slices with `superpowers:executing-plans` + `test-driven-development`. Every run is scoped to the feature's suite. Result: that suite green.
5. **Execute Hammer.** Invoke `aiforging:hammer-refactor` on the target repo(s). Result: code shaped toward the prescribed architecture, feature suite still green.
6. **Temper.** When you correct the AI during code review and the correction encodes a reusable rule, the `capture-pattern` skill will offer to persist it. It asks whether the pattern should be shared (workspace `.aiforging/`, available to all same-stack targets) or target-local (target's `.aiforging/`, this repo only). See "The Tempering feedback loop" section above.
7. **Verify — optional.** `/aiforging:browser-testing` walks the feature's `testing.md` in a real browser and reports what diverged without fixing anything; work the 👤 items yourself in parallel while it runs. Then `/aiforging:review-loop` for rounds of review, triage, and fix. Browser testing first.
8. **Run your full test suite.** Nothing here does — every automated run was scoped to this feature's suite, so a regression in a different feature wouldn't have surfaced. The skills will remind you; this is the reminder in writing.
9. **Commit the feature history.** When the feature is done, `git add docs/features/<name>/ && git commit` so the spec, plan, checklist, and run records become part of the workspace's permanent record.

## Adding a new target repo

Run `/aiforging:setup` in this directory. It will detect that the workspace is already initialized and walk you through onboarding an additional project (detection, analysis, copying the conventions, optionally installing the `hammer-refactor` + `capture-pattern` bundle, and creating the target-local pattern tier). The new target's path goes into `.claude/settings.local.json`, and `/aiforging:setup` will offer to capture the onboarding as a follow-up git commit if the workspace is a git repo.

## Removing a target repo

Use the helper (pointed at the local settings file). The script is a single-file PEP 723 script with no third-party deps, so either `uv run` or `python3` works — pick whichever you have on PATH:

```bash
# With uv:
uv run scripts/configure-directories.py remove \
  --settings-file ./.claude/settings.local.json \
  --directory /path/to/repo

# Or with plain python3 (identical behavior):
python3 scripts/configure-directories.py remove \
  --settings-file ./.claude/settings.local.json \
  --directory /path/to/repo
```

Or remove it manually from `./.claude/settings.local.json`. The repo's own `.aiforging/` directory stays intact inside the repo — removing it from the workspace just detaches it from this hub.

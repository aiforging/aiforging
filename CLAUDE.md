# AI Forging Plugin — Claude Context

## What this repo is

This is the **AI Forging** Claude Code plugin source repo. It defines prescriptive conventions, a set of slash commands, and five skills (`architecture-analyzer`, `hammer-refactor`, `capture-pattern`, `browser-testing`, `review-loop`) that teams use to practice the AI Forging methodology (Fire → Hammer → Tempering, plus two optional verification stages after it).

**Do not confuse this with a plugin that gets invoked on its own contents.** This repo is where the plugin is *authored*. End users never clone it — they install it via Claude Code's marketplace. When an end user runs `/aiforging:setup`, the command reads from the installed plugin and writes into the user's *forge workspace* and/or *target repos* — it never modifies this source repo.

## The three-layer model (critical — see Decision 13 in PLAN.md)

There are **three distinct locations** with different lifecycles:

1. **Plugin source repo** — this repo, `~/projects/aiforging`. Where the plugin is *authored*. `superpowers` should be installed here so Chris can dogfood spec/plan/execute while developing the plugin itself.
2. **Forge workspace** — a per-user directory the user creates (e.g., `~/forge`), bootstrapped by `/aiforging:setup` phase A. Holds central `docs/features/<name>/spec.md | plan.md`, a workspace-level `CLAUDE.md`, a committed `.claude/settings.json` (with `enabledPlugins` only — shareable), and a gitignored `.claude/settings.local.json` (with `permissions.additionalDirectories` pointing at target repos — per-user). Phase A also creates a `.gitignore` and offers to `git init` the workspace so feature history accumulates as a real git repo. This is where the end user *runs* Claude for cross-repo feature work.
3. **Target repos** — the code being forged. Each is onboarded to a forge workspace via `/aiforging:setup` phase B. Each gets a committed `.aiforging/` (conventions + seeded pattern library + analysis snapshot + per-repo pointer `CLAUDE.md`) and, for backend/fullstack repos, a committed `.claude/skills/hammer-refactor/SKILL.md`.

When you work in *this* repo (plugin source), you are a plugin developer. When you work in a *forge workspace*, you are a framework user driving features. Never conflate the two.

## First thing you should do in any session

Read `PLAN.md`. It is the persistent plan and session log for the framework build. It contains:

- Locked-in decisions (do not relitigate without a strong reason)
- Target plugin layout
- Current build status (built / in progress / not started)
- The target flow of `/aiforging:setup`
- Open questions
- Session log — append a note at the end of every working session

Every new session should start by reading `PLAN.md` and end by updating the session log.

## Key architectural decisions (see PLAN.md for the full list)

1. **Ship narrow, extend deliberately.** v1 is tightly coupled to React + Symfony/PHP/Doctrine. Other stack adapters come later.
2. **Prescriptive, not descriptive, for v1.**
3. **Install + analyze + propose plan.** `/aiforging:setup` never executes refactors.
4. **Lean on `superpowers`.** Core TDD, brainstorming, writing-plans, executing-plans, and subagent-driven-development come from the `superpowers` plugin. AI Forging is a thin architectural/domain layer on top. DO NOT reimplement those skills here.
5. **Governance: AI Forges, humans decide.** Four human gates. No autonomous execution.
6. **Three-layer model: plugin source ≠ forge workspace ≠ target repo.** See above.
7. **`/aiforging:setup` has two phases.** Phase A (init-workspace) bootstraps a forge workspace in an empty directory. Phase B (onboard-project) adds a target repo to an existing workspace. Re-run from the workspace to onboard more targets.
8. **`hammer-refactor` skill is the executable Hammer stage.** It lives in `skills/hammer-refactor/` in this repo and is *copied* into each onboarded target repo at `<target>/.claude/skills/hammer-refactor/SKILL.md`. Teammates who clone the target repo can run it without needing the aiforging plugin installed.
9. **Feature plans live centrally in the forge workspace**, not fragmented across target repos. `<workspace>/docs/features/<feature-name>/spec.md | plan.md`. Plans use the AI Forging *slice format* so each slice can be dispatched to a fresh-context subagent. See `conventions/features/README.md`.

## Directory map

```
.claude-plugin/             Plugin manifest, marketplace definition, and artifacts.json
commands/                   Slash commands. setup, new-feature (+ forge alias), update-targets, uninstall, plus one thin pointer per user-invocable skill: hammer-refactor, capture-pattern, browser-testing, review-loop. A pointer holds NO rules — it Reads the SKILL.md and follows it. If you want to add a rule, add it to the skill
scripts/                    Helper scripts invoked by commands (uv run, or python3 fallback)
  detect-project.py         Read-only stack detection → JSON
  configure-directories.py  Manages permissions.additionalDirectories in settings.local.json
  configure-plugins.py      Manages enabledPlugins in settings.json (committed)
skills/                     Agent skills
  architecture-analyzer/    Non-destructive advisory analysis pass (runs from workspace)
  hammer-refactor/          Executable Hammer stage (copied into each target repo)
  capture-pattern/          Reactive Tempering feedback loop (copied into workspace AND each target repo)
  browser-testing/          Optional post-implementation stage — walks testing.md in a browser (workspace only)
  review-loop/              Optional post-implementation stage — review/triage/fix rounds (workspace only)
templates/                  Bootstrap templates for forge workspace init (phase A)
  workspace-CLAUDE.md       Copied to <workspace>/CLAUDE.md
  workspace-README.md       Copied to <workspace>/README.md
  docs-features-README.md   Copied to <workspace>/docs/features/README.md
  feature-testing.md        Copied per-feature to docs/features/<name>/testing.md by /aiforging:new-feature
  patterns-tier-README.md   Placeholder for .aiforging/patterns/ — git won't track an empty dir
  anti-patterns-tier-README.md  Same, for anti-patterns/. EXCLUDED from every pattern-library glob
conventions/                The library copied into target repos during onboarding
  CLAUDE.md.template        Per-target repo CLAUDE.md pointer
  features/                 Canonical feature-folder convention (also in templates/ for workspace seeding)
  architecture/             Folder layout, controllers, repositories, DTOs, naming
  tdd/                      Fire stage (delegates to superpowers) + harness contract
  refactoring/              Hammer + Tempering: pattern/anti-pattern library
  frontend-testing/         Optional Playwright layer
docs/releases/              Per-release notes, for pasting into GitHub releases
.github/                    Issue templates and PR template
README.md                   Public-facing plugin README
CONTRIBUTING.md             Contribution guide (field reports, patterns, adapters, the manifest rule)
CHANGELOG.md                Keep a Changelog format; every release gets an entry
PLAN.md                     Persistent plan and session log — always read this first
CLAUDE.md                   You are here
```

## Rules for working in this repo

- **Never remove or modify existing conventions without logging why in `PLAN.md`.** The conventions represent agreed architectural decisions; they should evolve deliberately.
- **Never add a generic "refactor rules" monolith.** One pattern, one file, in `conventions/refactoring/patterns/` or `conventions/refactoring/anti-patterns/`.
- **Never re-implement a superpowers skill.** If a capability exists in the superpowers plugin, reference it — don't copy it.
- **Never modify files outside this repo.** The setup command is the only surface that touches user files (forge workspace + target repos), and even it goes through `configure-directories.py` and explicit copy steps.
- **When the canonical feature convention changes in `conventions/features/README.md`, update `templates/docs-features-README.md` too.** The template is copied into new forge workspaces during phase A init; the canonical doc is the source of truth. These two are the most-drifted pair in the repo — check them together on every change to either.
- **If a change adds anything the plugin COPIES out of itself, register it in `.claude-plugin/artifacts.json` first.** Skills, convention directories, templates, seeded patterns. `/aiforging:setup`, `/aiforging:update-targets`, and `/aiforging:uninstall` all read that manifest. An artifact missing from it will install on fresh setups and never reach anyone already using the plugin — silently, with nothing to notice. Decision 27.
- **Never soften a rule into a recommendation.** The full-suite handoff spent a release as an optional "you may want to..." note at the end of Hammer and was, predictably, the thing that got skipped. If a step matters, it is stated unconditionally and it is stated in the completion contract. Decision 24.
- **When the hammer-refactor skill changes in `skills/hammer-refactor/SKILL.md`, remember that existing target repos have a *copy*.** A future `/aiforging:update-targets` command will propagate updates; for now, note the propagation gap in the session log.
- **Always update `PLAN.md`'s session log** at the end of any working session. Future sessions depend on it.
- **Always test scripts against real data** before committing — `uv run scripts/detect-project.py` and `uv run scripts/configure-directories.py check --settings-file <path>` should both work out of the box. (If `uv` isn't on PATH in your shell, `python3 scripts/...` works identically — these are PEP 723 single-file scripts with no third-party deps. `commands/setup.md` probes for `uv` and falls back to `python3` at runtime; your dev tests should be robust to the same fallback.)

## Expected session flow when adding to the framework

1. Read `PLAN.md`.
2. Pick an item from "Not started" or "In progress."
3. If the item touches a new decision point, use `AskUserQuestion` to get the user's call before coding.
4. Do the work.
5. Verify (smoke-test the scripts, confirm the plugin structure is still valid).
6. Update `PLAN.md`'s status table and append a session log entry.

## Dogfooding the plugin locally

During development, test the plugin WITHOUT going through the marketplace install flow by launching Claude Code with `--plugin-dir` pointing at this repo:

```bash
# From any directory you want to test the plugin in (e.g., an empty ~/forge):
claude --plugin-dir ~/projects/aiforging
```

What this does:

- **Additive load.** `--plugin-dir` loads the specified plugin in *addition* to every plugin you already have installed from marketplaces. It doesn't replace them. You can pass the flag multiple times to load multiple local plugins side-by-side (e.g., to test aiforging against a local checkout of superpowers).
- **Same-name precedence.** If you have a marketplace copy of `aiforging` already installed AND you also pass `--plugin-dir` pointing at this repo, the local copy wins for that session. Great for testing changes without uninstalling the released version first.
- **No cache.** `--plugin-dir` reads directly from the directory every time. No stale `.claude/cache` to fight.
- **Hot reload.** While a session is running, after editing a command, skill, or script in this repo, run `/reload-plugins` inside Claude to pick up the changes without restarting the session. This reloads commands, skills, agents, hooks, MCP servers, and LSP servers from the plugin.

**Recommended dogfood flow for session N+1:**

1. `mkdir ~/forge-test && cd ~/forge-test` (fresh empty workspace candidate).
2. `claude --plugin-dir ~/projects/aiforging`.
3. Inside Claude: `/aiforging:setup`. Phase detection should route to Phase A (init-workspace). Walk it end-to-end.
4. When Phase A asks "onboard a target now?", say yes and walk Phase B against a real CertainPath repo path. Watch for any broken step.
5. After each failure, fix in the source repo, run `/reload-plugins`, re-run the failing step.
6. Log findings in `PLAN.md`'s session log and fix in the next session.

## When something is unclear

Ask. This is a framework being built by and for one person initially, and it will be shared widely. Asking clarifying questions is cheaper than writing the wrong thing.

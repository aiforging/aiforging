# AI Forging — Build Plan & Session Log

> **How to resume**: In a new Cowork / Claude Code session, start by reading this file. It captures the current state of the framework build, the decisions we've locked in, what's been built, what's next, and which questions are still open. Update it at the end of every working session.

## North Star

Ship a Claude Code plugin (`aiforging`) that installs prescriptive conventions, slash commands, and skills into established codebases so teams can practice the AI Forging methodology (Fire → Hammer → Tempering: test-first development, pattern-driven refactoring, and compounding pattern capture) without drowning in setup.

**Primary audience for v1**: software crafters with established codebases who already feel the pain of AI-generated sprawl and are ready to adopt an opinionated workflow. **Not** greenfield projects. **Not** developers without strong architectural opinions.

## Locked-in Decisions

These were agreed during the initial design conversation. Don't relitigate without a strong reason; if we change one, log the reason here.

1. **Ship narrow, extend deliberately.** v1 is tightly coupled to Chris's known-good stack (React + Symfony/PHP/Doctrine). Other stacks get adapters later once the extension-point contract has stabilized by being used once.
2. **Two-layer architecture.** The framework splits into (a) a stack-agnostic core of principles, prompts, workflows, slash commands, and refactoring playbooks; and (b) stack-specific adapters that plug into named extension points.
3. **Prescriptive, not descriptive, for v1.** High adoption friction but concrete value. Prescriptive-with-adapters for non-primary stacks later.
4. **Established codebases first.** No `/aiforging:new-project` in v1. That's a separate product.
5. **Three-tier architectural intervention.** Prerequisites doc (passive), analysis pass (advisory, non-destructive), bootstrapping flow (opt-in, gated). Never automatic, never silent.
6. **Setup command prescriptiveness level: install + analyze + propose plan.** Installs conventions, runs analysis, generates a spec/plan — but does **not** execute refactors. Execution requires a separate, explicit command.
7. **Frontend testing is a first-class optional layer.** Ship a Playwright-oriented convention doc and skill hook, but keep it opt-in in the setup flow. Business logic should still not live on the frontend.
8. **TDD foundation requires dynamic schema from an entity graph.** The framework defines this as a capability contract that a stack adapter must satisfy; stacks that can't satisfy it get less value. DataMapper ORMs (Doctrine, Hibernate, EF Core, TypeORM, MikroORM) are the happy path.
9. **Plugin structure follows the official Claude Code plugin layout.** `.claude-plugin/plugin.json` + `marketplace.json` at the root; `commands/`, `skills/`, `scripts/` at the plugin root. Modeled on vranac's `claude-session-export-obsidian` plus the official `plugin-dev` plugin.
10. **Governance: AI Forges, Humans Decide.** Four human gates: test review, code review at PR, architecture decisions, deployment authorization. No autonomous deployment ever.
11. **User-selected project interview is part of setup.** `/aiforging:setup` must interview the user to identify which project directories they want to drive from this plugin root, add them to `permissions.additionalDirectories` in Claude Code settings, and label each as backend vs frontend.
12. **Lean on existing ecosystem plugins, do not reinvent.** The core TDD, brainstorming, writing-plans, executing-plans, and subagent-driven-development skills come from the [`superpowers` plugin by Jesse Vincent](https://github.com/obra/superpowers) (accepted into the official Anthropic marketplace Jan 2026). AI Forging's job is to be a thin **architectural and domain-opinionated layer on top of superpowers** — we add folder layout, controller/repository/DTO conventions, the test-harness capability contract, and a pattern/anti-pattern library. We do NOT redefine TDD or plan-writing skills. `/aiforging:setup` offers to install `superpowers` as a recommended dependency and then assumes it's present.
13. **Three-layer model: plugin source ≠ forge workspace ≠ target repos.** We explicitly separate three locations with different lifecycles and owners:
    - **Plugin source repo** (`~/projects/aiforging`, this repo) — where the plugin is *authored*. End users never clone it; they install via marketplace. Chris works here to develop the framework itself, with `superpowers` installed for dogfood spec/plan/execute.
    - **Forge workspace** (a new concept, e.g., `~/forge` but user-chosen) — a per-user directory created for orchestrating cross-repo forging work. Holds `docs/features/<name>/spec.md | plan.md`, a central `CLAUDE.md`, a committed `.claude/settings.json` (with `enabledPlugins` — shareable), and a gitignored `.claude/settings.local.json` (with `permissions.additionalDirectories` — per-user). This is where the user *runs* Claude for cross-cutting feature work. Bootstrapped by `/aiforging:setup` when run in an empty/uninitialized directory. Designed to become a git repo so the feature history accumulates over time (see Decision 18). (Decision 17 formalized the two-file settings split after this was originally written.)
    - **Target repos** — the code being forged. Each gets a committed `.aiforging/` (analysis snapshot, seeded pattern/anti-pattern library, per-repo `CLAUDE.md` pointer) and optionally a committed `.claude/skills/hammer-refactor/SKILL.md`. Skills inside the repo make hammer-refactor discoverable to any teammate who clones the repo, independent of whether the aiforging plugin is installed on their machine. The aiforging plugin is the *source of truth* for skill and pattern content, but copies are replicated into each target repo on onboard.
14. **`/aiforging:setup` has two phases it detects and runs in sequence.** Phase A (**init-workspace**) when run in an empty/uninitialized directory: seed `CLAUDE.md`, `docs/features/README.md`, `.claude/settings.json`, check for `superpowers`. Phase B (**onboard-project**): interview + detect + add to `additionalDirectories` + copy conventions into `<target>/.aiforging/` + optionally install `hammer-refactor` skill and seed pattern/anti-pattern library. One entry point, two internal modes. The command inside the forge workspace can be re-run to onboard additional projects.
15. **`hammer-refactor` skill: the executable Hammer stage.** `skills/hammer-refactor/SKILL.md` lives in the plugin source and is copied into each onboarded target repo's `.claude/skills/hammer-refactor/` during onboard. The skill reads the current feature's `plan.md` (in the forge workspace) and the target repo's `.aiforging/patterns/` and `.aiforging/anti-patterns/`, then dispatches one fresh-context subagent per applicable pattern via `superpowers:subagent-driven-development`. Each dispatched subagent handles exactly one refactor slice. This is the piece that turns the static pattern library into an executable refactor loop. Onboarding seeds each target repo's `.aiforging/patterns/` and `.aiforging/anti-patterns/` with the current core library so the skill has something to work with on day one.
16. **Per-scope plugin enablement via `.claude/settings.json`.** Claude Code plugins are *installed* once at the machine level (via `/plugin install`), but *enabled* per-scope by an `enabledPlugins` map inside that scope's `.claude/settings.json`. Identifiers use the `<name>@<source>` form, where `<source>` is the marketplace short name (e.g., `superpowers@claude-plugins-official`, `aiforging@claude-plugins-official`). This overturns the Session-2 assumption that plugins were purely user-level. `/aiforging:setup` writes this block into both the forge workspace (Phase A) and every onboarded target repo (Phase B Step B.3.5), so teammates cloning a target repo get `superpowers` and `aiforging` auto-activated without touching their personal config — as long as they've installed the plugins at the machine level once. `scripts/configure-plugins.py` is the idempotent helper that manages this map (check / enable / disable / set subcommands, timestamped backups, atomic writes, regex-validated IDs).
17. **Split workspace settings into committed vs per-user files.** The forge workspace uses Claude Code's native two-file settings convention. `.claude/settings.json` is committed and holds ONLY `enabledPlugins` (shareable across teammates). `.claude/settings.local.json` is gitignored and holds `permissions.additionalDirectories` (absolute local paths are per-user). Claude Code reads both files at session start and merges them. This split makes the workspace cleanly shareable: a teammate cloning the workspace gets `enabledPlugins` (auto-activation works) but must run `/aiforging:setup` on their own machine to register their own target repo paths. `configure-plugins.py` always targets `settings.json`; `configure-directories.py` always targets `settings.local.json`. Crossing the two is a bug. Target repos do NOT need `settings.local.json` — they only get a committed `settings.json` with `enabledPlugins`, because target repos don't manage cross-repo references.
18. **Forge workspace is a git repo; setup offers to `git init` and stage the initial commit.** Specs and plans in `docs/features/` are the workspace's institutional memory and deserve git history. `/aiforging:setup` offers to `git init` the workspace: Phase A Step A.4 runs the git integration subroutine if the user declined onboarding (no target context), Phase B Step B.10 runs it with target context (for remote inference). The subroutine writes `.gitignore` if missing, checks for parent-repo nesting, computes the common ancestor of registered targets for a physical-location advisory (never moves anything), reads each target's `.git/config` `origin` URL to suggest a matching remote destination (never creates it), and stages an initial commit. Subsequent Phase B runs offer a follow-up commit to capture each onboarding. Hard rules: never `git push`, never `git remote add` automatically, never move the workspace directory, never commit `settings.local.json`, never configure `user.email`/`user.name` without consent.
19. **`capture-pattern` skill: the reactive Tempering feedback loop.** Adapted from Chris's hub-plus-api `/capture-pattern` skill into an AI-Forging-flavored version at `skills/capture-pattern/SKILL.md`. Watches for corrective moments during interactive sessions (human rejects a diff, says "that's not how we do it," points out a structural mistake) and offers to persist the lesson as a new `.md` file in the relevant target repo's `.aiforging/patterns/` or `.aiforging/anti-patterns/` library. One captured correction = one new file. The next `hammer-refactor` run automatically picks it up because the Hammer pass globs those directories on every invocation. This is the operational mechanism for the Tempering pillar and the framework's "Scalable Quality" story: quality grows monotonically as every team member contributes lessons from their normal code reviews, one file at a time. **Installed in BOTH the forge workspace `<workspace>/.claude/skills/capture-pattern/` AND each onboarded target repo's `<target>/.claude/skills/capture-pattern/`.** Workspace-copy fires during cross-repo forge sessions and resolves the write target by reading `permissions.additionalDirectories` from `settings.local.json` (asks the user to pick if there are multiple targets). Target-copy fires when the session is running directly inside the target repo (e.g., a teammate who cloned just the target repo, outside any forge workspace). Both copies are identical. Key design points: the skill is REACTIVE (never invoked at session start), it biases HEAVILY toward NOT prompting (over-eager offers train humans to decline reflexively), it writes in the AI Forging pattern format documented in `conventions/refactoring/README.md` (not the richer hub-plus-api format), and it never writes anywhere outside the resolved target's `.aiforging/patterns|anti-patterns/` directory. Attribution is date-only (`Captured during interactive session on YYYY-MM-DD`) — the git commit of the new file is the authoritative record of who captured it.
20. **Plugin command is forbidden from writing to the plugin source.** Discovered during Session 3 dogfood when `/aiforging:setup` Phase B tried to append to `~/projects/aiforging/PLAN.md` from a session running in `~/forge-test`. Root cause: the command's old Hard Rules told Claude to "Always update `${CLAUDE_PLUGIN_ROOT}/PLAN.md`'s Session Log section at the end of the run." That was a three-layer-model violation — `CLAUDE_PLUGIN_ROOT` resolves to the plugin source, which the end-user command must treat as read-only. Fix: removed the old rule, replaced it with an explicit Hard Rule that says "Never write anywhere under `${CLAUDE_PLUGIN_ROOT}`" and explains why. Also updated Step 0 (Orient yourself) to stop telling Claude to `cat ${CLAUDE_PLUGIN_ROOT}/PLAN.md` — that was feeding plugin-authoring context into end-user runs and making the "update PLAN.md" rule feel natural. Also swept `conventions/README.md` and `conventions/refactoring/README.md` (both copied into target repos during Phase B) to remove references to "the plugin's PLAN.md" that would confuse end users. The plugin-developer-context files (`CLAUDE.md`, `README.md`, `PLAN.md` itself) still reference PLAN.md because those files live in the plugin source and are for the plugin author. End-user session history is captured instead by git commits in the forge workspace (via the git integration subroutine) and by the state of the workspace and target repos themselves. There is no plugin-side log of end-user runs — intentionally.

**Decision 20 (candidate) — upstream pattern propagation.** Parked for post-v1. When a pattern captured in one target's `.aiforging/patterns/` turns out to be generalizable across all targets, a future `/aiforging:propose-pattern` command will let teams promote it back up to the plugin's `conventions/refactoring/patterns/` library so all future onboarded targets start with it. For v1, the flow is manual: if a pattern is worth sharing, PR it against the plugin source. This parking note exists so the design space isn't forgotten.

21. **Workspace-as-role: the forge workspace is not always a separate directory.** (Replaces the rigid "always a separate directory" assumption in Decision 13.) The forge workspace is a *role* — "the place where spec/plan files and the shared pattern library live" — that adapts to the user's repo topology:
    - **Scenario A — multi-repo.** Multiple independent repos (backend API + frontend app, etc.). The forge workspace is a **separate directory** (the current model): a dedicated repo that houses `docs/features/`, the shared pattern library, and `.claude/settings.local.json` with `additionalDirectories` pointing at the target repos. Nothing changes from the current flow.
    - **Scenario B — monorepo.** One git repo with distinct sub-projects (`frontend/`, `backend/`, `packages/*`). The forge workspace **is the monorepo root**. `docs/features/` lives at the root. Each sub-project gets its own `.aiforging/` with stack-appropriate conventions. No `additionalDirectories` needed (everything is under one root). No separate git history needed (the monorepo's own history suffices).
    - **Scenario C — single blended repo.** One repo, one stack (or tightly intertwined stacks). The forge workspace **is the repo**. `docs/features/` and `.aiforging/` both live at the root. Simplest case.
    - **Scenario D — single-purpose repo.** Just a backend or just a frontend. Same as Scenario C.
    - **Detection**: `/aiforging:setup` begins with a scenario interview: "How is your codebase organized?" For multi-repo, it asks whether the user already has a repo where centralized planning docs live (use it) or wants to create one (Phase A). For monorepo/single, it operates in-repo. The workspace marker is the presence of `docs/features/README.md` with the AI Forging marker string — no new config file needed (same detection the current Phase A already uses, now applied to repos too).
    - **Three-layer model update**: the three layers are still conceptually distinct (plugin source ≠ workspace ≠ target), but for scenarios B/C/D, the workspace and target layers **collapse into one physical location**. The plugin source is always separate (marketplace install).

22. **Two-tier pattern library with stack-level matching.** Patterns and anti-patterns exist at two tiers:
    - **Shared tier** — lives at the workspace level. For separate workspaces: `<workspace>/.aiforging/patterns/` and `<workspace>/.aiforging/anti-patterns/`. For in-repo workspaces (monorepo/single): `<repo>/.aiforging/patterns/` and `<repo>/.aiforging/anti-patterns/` at the root level. Shared patterns have YAML frontmatter with an `applies-to` list of stack identifiers (using the vocabulary `detect-project.py` already outputs: `symfony-php`, `laravel-php`, `react`, `next`, `angular`, `node-ts`, `doctrine`, `eloquent`, `typeorm`, etc.) plus the special value `all` for universal patterns. `/hammer-refactor` reads the shared tier and filters by the current target's detected stack before dispatching subagents.
    - **Target-local tier** — lives in each target's `.aiforging/patterns/` and `.aiforging/anti-patterns/` (for multi-repo) or each sub-project's `.aiforging/patterns/` (for monorepo). Target-local patterns have NO `applies-to` frontmatter — they apply unconditionally to that target. Use this tier for repo-specific patterns that genuinely only apply to one target (e.g., "this legacy repo uses X weird pattern because of Y historical debt").
    - **`/hammer-refactor` reads both tiers.** For a given target, it merges: (a) all target-local patterns from `<target>/.aiforging/patterns/` + `<target>/.aiforging/anti-patterns/`, and (b) all shared patterns from the workspace whose `applies-to` list includes at least one of the target's detected stacks (or `all`). The merged set is what gets dispatched to subagents. Duplicate detection is by filename — if a shared pattern and a target-local pattern have the same filename, the target-local copy wins (allows per-target overrides).
    - **`/capture-pattern` asks the scope question.** After drafting a pattern, the skill asks: "Does this apply only to `<current-target>`, or to all `<stack-family>` targets?" If shared → writes to the workspace-level shared tier with `applies-to` frontmatter. If local → writes to the target's own `.aiforging/patterns/`. For in-repo workspaces where workspace = target, both tiers are in the same repo but at different directory levels: root `.aiforging/patterns/` (shared) vs sub-project `.aiforging/patterns/` (local).
    - **Seeded patterns move to the shared tier.** The initial seeded patterns (`fat-controller.md`, `primitive-obsession.md`, `extract-service-from-controller.md`) currently get copied into each target's `.aiforging/` during Phase B. Under the two-tier model, these are shared patterns — they apply to all targets of the right stack. They should be seeded at the workspace level (shared tier) with `applies-to` frontmatter, not duplicated into each target. Phase B still creates the target-local `patterns/` and `anti-patterns/` directories (empty, for future captures), but the seeded content goes to the workspace.
    - **Pattern file format change.** Shared-tier patterns gain a YAML frontmatter block:
      ```yaml
      ---
      applies-to: [symfony-php, doctrine]
      captured-from: hub-plus-api
      captured-date: 2026-04-13
      ---
      ```
      Target-local patterns have no frontmatter (or optionally `captured-from` and `captured-date` for provenance). The `## Source` section at the bottom of the file body is preserved for human-readable attribution; the frontmatter is for machine filtering.

23. **Monorepo sub-project detection with user confirmation.** For monorepo scenarios, `/aiforging:setup` runs `detect-project.py` against the root AND against each detected child (it already recurses one level for meta-repos). It presents the results as a confirmation: "I detected the following sub-projects — `frontend/` (react, playwright), `backend/` (symfony-php, doctrine, phpunit). Is this correct?" The user can correct misdetections, add missed sub-projects, or relabel roles. Each confirmed sub-project is treated as a target for convention installation (gets its own `<sub-project>/.aiforging/`) but does NOT get added to `additionalDirectories` (it's already under the same root). This extends the existing `detect-project.py` child-recursion — the script already outputs a `children` array for meta-repos.

## Target Plugin Layout

```
aiforging/                          # plugin source repo (where we are)
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── README.md
├── LICENSE
├── CLAUDE.md                       # Plugin-level context for Claude working on the plugin itself
├── PLAN.md                         # (this file) — session continuity
├── commands/
│   └── setup.md                    # /aiforging:setup (init-workspace + onboard-project)
├── scripts/
│   ├── detect-project.py           # stack detection (read-only)
│   ├── configure-directories.py    # manages permissions.additionalDirectories
│   └── configure-plugins.py        # manages enabledPlugins map
├── skills/
│   ├── architecture-analyzer/      # advisory analysis, runs from the forge workspace
│   │   └── SKILL.md
│   ├── hammer-refactor/            # executable Hammer stage, copied into each target repo
│   │   └── SKILL.md
│   └── capture-pattern/            # reactive Tempering feedback loop, copied into BOTH workspace AND each target repo
│       └── SKILL.md
├── templates/                      # bootstrap templates for forge workspace init
│   ├── workspace-CLAUDE.md
│   ├── workspace-README.md
│   └── docs-features-README.md
└── conventions/                    # installable library copied into target projects
    ├── CLAUDE.md.template          # per-target CLAUDE.md pointer
    ├── features/
    │   └── README.md               # the docs/features/<name>/spec.md|plan.md convention
    ├── architecture/
    │   ├── domain-driven-hexagonal.md
    │   ├── single-action-controllers.md
    │   ├── repositories.md
    │   ├── dtos-and-value-objects.md
    │   └── naming.md
    ├── tdd/
    │   ├── fire-red-green-refactor.md
    │   ├── test-harness-requirements.md
    │   └── repository-testing.md
    ├── refactoring/
    │   ├── README.md
    │   ├── patterns/
    │   │   └── extract-service-from-controller.md
    │   └── anti-patterns/
    │       ├── fat-controller.md
    │       └── primitive-obsession.md
    └── frontend-testing/           # optional layer
        ├── README.md
        └── playwright-conventions.md
```

### Forge workspace layout — Scenario A: separate workspace (multi-repo)

```
<forge-workspace>/                  # e.g., ~/forge — user-chosen location; intended to become a git repo
├── CLAUDE.md                       # "This is a forge workspace — read docs/features/ for plans"
├── README.md                       # "This is a forge workspace, not a project"
├── .gitignore                      # Protects settings.local.json + helper-script backups
├── .claude/
│   ├── settings.json               # COMMITTED: enabledPlugins only (superpowers + aiforging)
│   ├── settings.local.json         # GITIGNORED: permissions.additionalDirectories (per-user)
│   └── skills/
│       └── capture-pattern/
│           └── SKILL.md            # workspace copy — resolves targets from settings.local.json
├── .aiforging/
│   ├── patterns/                   # SHARED TIER — applies-to frontmatter, stack-filtered
│   │   └── extract-service-from-controller.md   # seeded during Phase A
│   └── anti-patterns/              # SHARED TIER
│       ├── fat-controller.md       # seeded during Phase A
│       └── primitive-obsession.md  # seeded during Phase A
└── docs/
    └── features/
        ├── README.md               # explains the feature-folder convention
        └── <feature-name>/         # one directory per active feature (grows over time)
            ├── spec.md
            └── plan.md
```

### Forge workspace layout — Scenario B: in-repo workspace (monorepo)

```
<monorepo>/                         # the repo IS the workspace
├── CLAUDE.md                       # workspace + repo context merged
├── .claude/
│   ├── settings.json               # COMMITTED: enabledPlugins
│   └── skills/
│       └── capture-pattern/
│           └── SKILL.md
├── .aiforging/
│   ├── patterns/                   # SHARED TIER — cross-sub-project patterns
│   └── anti-patterns/              # SHARED TIER
├── docs/
│   └── features/                   # feature specs/plans live at the repo root
│       └── <feature-name>/
│           ├── spec.md
│           └── plan.md
├── backend/                        # detected sub-project
│   ├── .aiforging/
│   │   ├── CLAUDE.md               # sub-project conventions pointer
│   │   ├── architecture/           # stack-specific conventions
│   │   ├── tdd/
│   │   ├── patterns/               # TARGET-LOCAL TIER — backend-specific overrides
│   │   └── anti-patterns/          # TARGET-LOCAL TIER
│   └── (backend source code)
└── frontend/                       # detected sub-project
    ├── .aiforging/
    │   ├── CLAUDE.md
    │   ├── patterns/               # TARGET-LOCAL TIER — frontend-specific overrides
    │   └── anti-patterns/          # TARGET-LOCAL TIER
    └── (frontend source code)
```

### Target repo layout — Scenario A only (after `/aiforging:setup` phase B onboards it)

```
<target-repo>/
├── .claude/
│   └── skills/
│       ├── hammer-refactor/
│       │   └── SKILL.md            # copy of the skill; discoverable by anyone cloning this repo
│       └── capture-pattern/
│           └── SKILL.md            # copy of the skill; fires during direct-in-repo sessions
├── .aiforging/
│   ├── CLAUDE.md                   # "This repo is onboarded to AI Forging; look in .aiforging/"
│   ├── ANALYSIS.md                 # from architecture-analyzer, regenerated on rerun
│   ├── architecture/               # copied from plugin conventions/architecture/
│   ├── tdd/                        # copied from plugin conventions/tdd/
│   ├── subagent-orchestration/     # copied from plugin conventions/subagent-orchestration/
│   ├── patterns/                   # TARGET-LOCAL TIER — repo-specific only; starts empty
│   └── anti-patterns/              # TARGET-LOCAL TIER — repo-specific only; starts empty
└── (existing project code — untouched except for the additions above)
```

**Key difference from pre-Decision-22 layout:** seeded patterns (`fat-controller.md`, etc.) NO LONGER live in each target repo. They live in the shared tier at the workspace level. Target-local `patterns/` and `anti-patterns/` directories start empty and are only for repo-specific captures. `/hammer-refactor` merges both tiers when scanning a target.

## Current Status

Last updated: 2026-04-10 (Session 4 — conventions extension, /aiforging:new-feature command, run-anywhere pointer file)

### Built

- `PLAN.md` — this file.
- `.claude-plugin/plugin.json` — plugin manifest (v0.1.0).
- `.claude-plugin/marketplace.json` — single-plugin marketplace definition so the repo can be added as a source.
- `scripts/detect-project.py` — read-only stack detection. Emits JSON describing backend/frontend stacks, ORMs, test runners, and children of meta-repos. Smoke-tested Session 1. PEP 723 single-file script, runs under either `uv run` or `python3`.
- `scripts/configure-directories.py` — manages `permissions.additionalDirectories` in `.claude/settings.local.json`. Subcommands: `check`, `add`, `remove`. Idempotent, timestamped backups, atomic writes. Smoke-tested Session 1.
- `scripts/configure-plugins.py` — manages the `enabledPlugins` map in `.claude/settings.json`. Subcommands: `check`, `enable`, `disable`, `set`. Validates identifiers with `^[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+$`, idempotent, timestamped backups, atomic writes. Smoke-tested Session 2-continued (all subcommands, bad-id rejection, idempotency, combined round with `configure-directories.py`).
- `scripts/configure-workspace-pointer.py` — manages the per-user run-anywhere pointer file at `~/.claude/aiforging.json`. Subcommands: `check`, `set-active`, `add`, `forget`. Enforces absolute paths, rejects non-existent paths by default (`--force` override for bootstrap scripts), prepends new workspaces to a deduped most-recently-used history, clears `active_workspace` when the active one is forgotten rather than guessing a replacement. Timestamped backups + atomic writes like the other two helpers. Smoke-tested Session 4 (all subcommands in sequence against a scratch pointer file).
- `commands/setup.md` — the `/aiforging:setup` slash command. Two phases (A: init-workspace, B: onboard-project) with explicit phase detection, split settings files, git integration subroutine, uv/python3 runner probe, a Hard Rule forbidding writes under `${CLAUDE_PLUGIN_ROOT}`, and (Session 4) Steps A.2.5 + B.10.5 that register the workspace in `~/.claude/aiforging.json` so daily-driver commands like `/aiforging:new-feature` work from any directory.
- `commands/new-feature.md` — the `/aiforging:new-feature` slash command. The daily-driver entry point for starting a feature in a forge workspace. Parses feature-name + initial-prompt arguments with kebab-case normalization, detects existing features (exact / substring / token-overlap match) with new/extend/abort choice, offers flat-vs-nested shape picker, creates `docs/features/<name>/` with the right structure, seeds `spec.md` with a Step-1 Summary section pre-filled from the user's initial prompt, and hands off to `superpowers:brainstorming` at the Summary checkpoint. Supports run-anywhere mode via `~/.claude/aiforging.json` lookup when cwd is not a workspace. Never writes `plan.md` (that's Step 4 of the planning workflow, not Step 1 of this command). Never touches target repos. Never commits to git.
- `templates/` — bootstrap templates for forge workspace init (Phase A):
  - `templates/workspace-CLAUDE.md` — central `CLAUDE.md` for the forge workspace.
  - `templates/workspace-README.md` — human-facing README.
  - `templates/docs-features-README.md` — feature-folder convention reference copied into the workspace.
- `conventions/` library (copied into each onboarded target as `.aiforging/`):
  - `conventions/README.md`
  - `conventions/CLAUDE.md.template` — per-target `CLAUDE.md` pointer.
  - `conventions/features/README.md` — canonical feature-folder convention. **Extended Session 4** with: (1) Step 0 scope determination (single-target vs multi-target), (2) flat-vs-nested folder layout with `overview.md + NN-<work-item>/` taxonomy ported from the project-hub-plus orchestrator, (3) four-step planning workflow (Summary checkpoint → grouped clarifying questions in themed rounds → architecture review against every affected target's `.aiforging/` → plan.md with closing `[hammer]` slice per Fire sequence), (4) non-negotiable "read affected target CLAUDE.md before writing plan" rule, (5) living-documents rules (route changes to spec/plan/notes, preserve completed checkboxes, proactive spec updates for visible behavior changes). `templates/docs-features-README.md` mirrors the portable pieces.
  - `conventions/subagent-orchestration/README.md` — **new Session 4.** Portable rules for parent-as-conductor dispatch: parent stays lean, plan.md is authoritative (subagent prompts POINT at it rather than embedding slice details), every subagent reads its target's CLAUDE.md before touching code, dispatch ordering vs parallelism, every Fire sequence closes with hammer-refactor fanned out one-subagent-per-pattern, subagents check their own plan.md boxes, parent never fabricates completion. Portable subagent prompt templates (generic / backend / frontend / hammer-refactor). Delegates to `superpowers:subagent-driven-development` for the actual dispatch mechanism — this doc is the policy layer on top. Will be copied into each onboarded target as part of Phase B so teammates driving Claude directly inside a target inherit the same rules.
  - `conventions/architecture/` — `domain-driven-hexagonal.md`, `single-action-controllers.md`, `repositories.md`, `dtos-and-value-objects.md`, `naming.md`.
  - `conventions/tdd/` — `fire-red-green-refactor.md` (delegates to `superpowers:test-driven-development`), `test-harness-requirements.md`, `repository-testing.md`.
  - `conventions/refactoring/` — `README.md` (Hammer + Tempering, delegates to `superpowers:subagent-driven-development`), `anti-patterns/fat-controller.md`, `anti-patterns/primitive-obsession.md`, `patterns/extract-service-from-controller.md`.
  - `conventions/frontend-testing/` — `README.md`, `playwright-conventions.md`.
- `skills/architecture-analyzer/SKILL.md` — read-only advisory analysis skill with six dimensions, scoring rubric, and severity ladder. Runs from the forge workspace against an onboarded target. Dogfooded Session 3 against hub-plus-api (score 6/10).
- `skills/hammer-refactor/SKILL.md` — executable Hammer stage. Copied into each onboarded target repo's `.claude/skills/hammer-refactor/`. Reads the forge workspace's current `plan.md` plus the target's `.aiforging/patterns|anti-patterns/`, then dispatches one fresh-context subagent per applicable pattern via `superpowers:subagent-driven-development`. **Session 4 update:** documented three entry points (plan-driven auto-trigger as the default path, user-invoked against a specific feature, user-invoked targeted mode) and cross-referenced `conventions/subagent-orchestration/README.md` as the policy layer Hammer follows — Hammer is not a special case, it's the canonical example of parent-as-conductor discipline.
- `skills/capture-pattern/SKILL.md` — reactive Tempering feedback loop. Copied into BOTH the forge workspace `.claude/skills/` (Phase A) AND each onboarded target repo's `.claude/skills/` (Phase B). Detects corrective moments during interactive sessions and offers to persist the lesson as a new `.md` file in the resolved target's `.aiforging/patterns/` or `.aiforging/anti-patterns/` directory. Workspace copy resolves the write target by reading `permissions.additionalDirectories` from `settings.local.json`. Decision 19.
- `README.md` — public-facing plugin README with install instructions, Fire/Hammer/Tempering explanation, and `superpowers` relationship section.
- `CLAUDE.md` — plugin-level context for Claude working on the plugin source itself.

### Not started

- `skills/forging-principles/SKILL.md` — summary of the three-stage forge for model invocation. (Optional — the conventions library and `architecture-analyzer` already cover this surface. Defer until v0.2.)
- `scripts/analyze-architecture.py` — dropped from the v0.1.0 plan. The analysis pass is a skill (`architecture-analyzer/SKILL.md`), not a script. The skill uses `Read`/`Glob`/`Grep` directly rather than shelling out.
- `/aiforging:execute-plan` — takes a `PROPOSED_PLAN.md` and drives execution via superpowers' `executing-plans` + `subagent-driven-development`. Out of scope for v0.1.0 ("install + analyze + propose plan" boundary).
- First dedicated stack adapter beyond the happy path (Laravel, Spring, .NET, Node/TS).
- `LICENSE` file — README references MIT; the actual `LICENSE` file still needs to be added to the repo root.

## Setup Command Flow (current)

The `/aiforging:setup` command is the primary onboarding surface. The canonical, up-to-date flow lives in `commands/setup.md` itself — read that file for the authoritative sequence. Summary of the current shape (Session 2, post-settings-split and post-git-integration):

**Phase A — init-workspace** (runs in an empty/uninitialized cwd):

1. Orient + phase detection + refuse-to-run guards (plugin source repo, already-onboarded target repo).
2. A.1: Check for `superpowers` plugin dependency.
3. A.2: Seed workspace files (`CLAUDE.md`, `README.md`, `docs/features/README.md`, `.gitignore`), create split settings files (`.claude/settings.json` with `{}` then populated by `configure-plugins.py`; `.claude/settings.local.json` with empty `additionalDirectories`), and write `enabledPlugins` for `superpowers` + `aiforging` to the committed settings file.
4. A.3: Offer to onboard the first target project. If yes → Phase B. If no → A.4.
5. A.4: Git integration subroutine with no target context (only if onboarding declined). Offers `git init` + initial commit without target-aware remote inference.
6. A.5: Phase A summary showing both settings files, `.gitignore`, and git state.

**Phase B — onboard-project** (runs when cwd is already a workspace):

1. Preamble: 8-item onboarding checklist shown to user.
2. B.1: Detect target via `detect-project.py`.
3. B.2: Confirm role (backend / frontend / fullstack / meta-child).
4. B.3: Register target path in workspace's `.claude/settings.local.json` (per-user). NEVER writes to `settings.json`.
5. B.3.5: Verify superpowers installed at user level; write `enabledPlugins` block to `<target>/.claude/settings.json` so teammates cloning the target get auto-activation.
6. B.4: Copy `conventions/architecture/` and `conventions/tdd/` into `<target>/.aiforging/`; write `<target>/.aiforging/CLAUDE.md` from the template.
7. B.5: Offer to install the AI Forging skills bundle (`hammer-refactor` + `capture-pattern`) into `<target>/.claude/skills/`, with per-skill fallback if the bundle is declined.
8. B.6: Offer to seed `<target>/.aiforging/patterns/` and `anti-patterns/` from the plugin's core library.
9. B.7: Run `architecture-analyzer` on the target; write `<target>/.aiforging/ANALYSIS.md`.
10. B.8: Optional frontend testing layer (Playwright conventions) for frontend/fullstack.
11. B.9: Offer to draft a feature folder in `<workspace>/docs/features/<name>/` with spec.md + plan.md in the AI Forging slice format based on the analyzer's findings.
12. B.10: Git integration subroutine with target context. First-time: git-init + initial commit + remote inference from target's `.git/config`. Subsequent: offer follow-up commit capturing the onboarding.
13. B.11: Phase B summary with 9-item checklist (✓/—/✗ markers), plus git state line, plus push-to-remote hint if applicable.

**Hard rules (both phases):** install + analyze + propose, never execute refactors; never overwrite user files silently; never hand-edit settings files (use the two helpers, each targeting its correct file); never write absolute local paths into the committed `settings.json`; never run from the plugin source repo; never `git push` or `git remote add` automatically; **never write anywhere under `${CLAUDE_PLUGIN_ROOT}`** (Decision 20 — the plugin source is read-only from an end-user run).

See `commands/setup.md` for the full text including the Git integration subroutine at the bottom.

## Extension Points (to be formalized as adapters mature)

The first adapter we'll ship (Symfony/PHP/Doctrine) will implement all of these. When they stabilize, we freeze the contract and document it for other stacks.

- **Stack detector** — given a directory, emits a normalized `ProjectInfo`. (Currently one monolithic script; should become pluggable.)
- **Architecture validator** — given a `ProjectInfo`, emits a list of findings with severities.
- **Test-harness bootstrapper** — given a `ProjectInfo`, knows how to scaffold an isolated test database with real schema from the entity graph.
- **Scaffold generator** — given a feature name, creates a new domain-feature folder following the ideal layout.
- **Refactoring playbook** — stack-specific pattern/anti-pattern files.

## Open Questions

- **How prescriptive should the conventions installer be about the `Domain/Feature/Subfeature` folder layout?** Our CertainPath code uses a deeper `Module/Feature/…` nesting we'd rather not propagate. v1 proposal: ship the two-level `Domain/Feature/Subfeature` layout as the prescribed default, note the deeper variant in the conventions doc as "we use this internally, you probably don't need it."
- **Should the architecture-analyzer skill run as a subagent with fresh context?** Leaning yes — it fits the "dedicated sub-agent per concern" pattern from the framework. But it means the skill invokes a Task tool call, which is a heavier implementation. Defer decision until we've written it once inline.
- **Where does the pattern library actually live per project?** Proposal: `.aiforging/patterns/` and `.aiforging/anti-patterns/`, one `.md` per pattern, mirroring Chris's production setup. Setup command seeds an empty directory with a README explaining how to add the first one.
- **Frontend testing: Playwright-only, or leave room for Cypress?** v1: Playwright-first, but the conventions doc should be written so a Cypress adapter is a drop-in later.
- **Do we need a `/aiforging:analyze` command separate from `/aiforging:setup`?** Leaning yes — re-running the full setup is heavy, and users will want a quick re-analysis after changes. Punt to session 2.
- **Do we need a `/aiforging:execute-plan` command?** Yes, but it's out of scope for the "install + analyze + propose plan" prescriptiveness level we locked in for v1.

## Session Log

### Session 1 — 2026-04-10

- Discussed portability, prescriptiveness, and the pluggable architecture. Locked in decisions 1–10 above.
- User added requirement: setup must interview the user for target project directories and write them to `permissions.additionalDirectories`, labeling each as frontend/backend. Decision 11.
- User added requirement: keep a persistent plan/status file in the repo. This file.
- User added requirement: lean on existing ecosystem plugins — specifically the `superpowers` plugin for TDD, brainstorming, writing-plans, executing-plans, and subagent-driven-development. Decision 12.
- Studied vranac's `claude-session-export-obsidian` plugin structure, the Anthropic `plugin-dev` plugin's `plugin-structure` skill for the canonical layout, and `github.com/obra/superpowers` for the skills AI Forging will depend on.
- Scaffolded: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `scripts/detect-project.py`, `scripts/configure-directories.py`, `commands/setup.md`, and the first pass of `conventions/` (README, architecture/, tdd/).
- Superpowers alignment: rewrote the TDD conventions as **additions to** the superpowers TDD skill, not as a replacement. The test-harness capability contract and Repository testing patterns stay in AI Forging because they're stack-architectural, not generic.
- Added `commands/setup.md` Step 0.5 (superpowers presence check), finished `conventions/frontend-testing/` (README + Playwright conventions), created `skills/architecture-analyzer/SKILL.md`, wrote plugin-level `CLAUDE.md` and public-facing `README.md`, and added `conventions/CLAUDE.md.template` for installation into target projects.
- **End-of-session smoke test (2026-04-10):**
  - `uv run scripts/detect-project.py` on three fake targets (Symfony/Doctrine backend, React/TS/Playwright frontend, meta parent containing both). All three produced correct `ProjectInfo` JSON with proper evidence, stack, orm, test_runner, kind, and children fields. Meta-repo recursion works.
  - `uv run scripts/configure-directories.py check` / `add` / `remove` against a temp settings.json. Verified: idempotent add (no duplicates, no backup when nothing changes), timestamped backups on actual mutations, atomic writes via `.tmp` rename, preservation of unrelated keys (`permissions.allow` stayed intact), clean JSON output on every invocation.
  - Full plugin tree verified against the target layout in this file — 25 files across manifest, command, scripts, skill, and conventions library. No stragglers, no missing files relative to the "Built" list above.
- Session 1 status: v0.1.0 scaffold is **complete**. Plugin can be added to a Claude Code marketplace, `/aiforging:setup` has an interview-driven flow that does not execute refactors, both helper scripts are verified, and the full conventions library is present.
- Next session opening moves: (1) add a `LICENSE` file at the repo root, (2) create an actual git repo if one isn't initialized yet, (3) attempt a dogfood install of `aiforging` into a real side-by-side project to validate the end-to-end `/aiforging:setup` flow inside Claude Code, (4) start designing `/aiforging:execute-plan` on paper (still deferred from v0.1.0 shipping scope).

### Session 2 — 2026-04-10 (continued)

- **Chris surfaced two conceptual gaps from Session 1 that required a significant rework:**
  1. The `post-tdd-refactor` / Hammer skill had not actually been built. Session 1 shipped a *pattern library* (`conventions/refactoring/`) and prose about dispatching subagents, but no `skills/hammer-refactor/SKILL.md` that actually orchestrates the dispatch.
  2. The design was conflating "plugin source repo" with "user's central forge workspace". Session 1's setup command assumed the user would check out the aiforging repo next to their projects and run Claude from there, which is wrong — end users install the plugin via marketplace and should never clone it. Central feature planning needs its own dedicated location.
- **Locked in three new decisions:**
  - **Decision 13** — three-layer model: plugin source (where we are), forge workspace (user's per-user orchestration hub, created by setup phase A), target repos (the code being forged, reached via `additionalDirectories`). Each layer has distinct lifecycle and ownership.
  - **Decision 14** — `/aiforging:setup` has two phases it detects and runs in sequence: init-workspace (Phase A) when the cwd is not yet a workspace, onboard-project (Phase B) when it is. One entry point, two internal modes, re-runnable for onboarding additional targets.
  - **Decision 15** — `hammer-refactor` is the executable Hammer stage. Lives in `skills/hammer-refactor/` and is *copied* into each onboarded target repo at `<target>/.claude/skills/hammer-refactor/SKILL.md` so it's discoverable by anyone cloning the target, independent of whether the aiforging plugin is installed on their machine.
- **Built this session:**
  - `skills/hammer-refactor/SKILL.md` — full skill definition with the six-step flow (read plan → scan anti-patterns → prioritize → dispatch subagents one at a time → verify each slice → Tempering handoff), hard refusal rules, and an example invocation. Frontmatter `description` is specific enough for the skill router to trigger it only when tests are green and a refactor pass is explicitly requested.
  - `conventions/features/README.md` — canonical feature-folder convention for the forge workspace, including the AI Forging slice format for `plan.md` (stage tags `[fire]`/`[hammer]`/`[tempering]`, target repo naming, test references, gate markers, explicit subagent prompts per slice).
  - `templates/workspace-CLAUDE.md` — central `CLAUDE.md` copied into a new forge workspace during Phase A. Tells Claude the workspace is NOT a codebase, points at `docs/features/`, describes the forge working flow, lists hard rules (no source code in workspace, Fire before Hammer, etc.).
  - `templates/workspace-README.md` — human-facing README copied to the workspace. Explains required plugins, directory layout, how to use the workspace.
  - `templates/docs-features-README.md` — a concise mirror of `conventions/features/README.md` that gets copied into `<workspace>/docs/features/README.md` during Phase A. Canonical version stays in `conventions/`; template is maintained in parallel.
  - **Full rewrite of `commands/setup.md`** — now structured as Phase A (init-workspace) + Phase B (onboard-project) with explicit phase detection at Step 1, workspace-marker checks, refusals when run in the plugin source repo or a target repo by mistake, and a Phase B flow that covers: detect → confirm role → register under additionalDirectories → copy conventions into target's `.aiforging/` → offer to install `hammer-refactor` into target's `.claude/skills/` → offer to seed pattern/anti-pattern library → run architecture-analyzer → offer to draft a feature folder in the workspace with a sliced plan. Still never executes refactors.
  - **Plugin-level `CLAUDE.md`** updated to reflect the three-layer model, the two-phase setup, and the hammer-refactor copy-into-target strategy. Directory map now shows `skills/hammer-refactor/`, `templates/`, and `conventions/features/` alongside the existing entries.
- **File count:** 30 source files (up from 25 at end of Session 1). New directories: `skills/hammer-refactor/`, `templates/`, `conventions/features/`.
- **Known propagation gap (to address in a future session):** hammer-refactor and the pattern library are *copied* into target repos at onboard time. When the plugin updates those sources, existing target repos' copies drift. A future `/aiforging:update-targets` command will sweep the workspace's additionalDirectories and refresh each target's copies (with diff-and-ask semantics). Logged here so we don't forget.
- **Session 2 status:** the three-layer model is fully reflected in the plugin. Setup command is coherent end-to-end but has not yet been dry-run against a real forge workspace in a live Claude Code session — that's the dogfood task for Session 3.
- **Next session opening moves (revised):**
  1. Add `LICENSE` file (still pending).
  2. Run `/aiforging:setup` in Claude Code from an empty `~/forge` directory, dogfood Phase A end-to-end, fix whatever breaks.
  3. Then onboard one real CertainPath target repo via Phase B, fix whatever breaks.
  4. Start designing `/aiforging:update-targets` on paper (mentioned above as a propagation-gap fix).
  5. Design `/aiforging:new-feature <name>` as a thin wrapper that creates `docs/features/<name>/` and hands off to `superpowers:brainstorming`.

### Session 2 — 2026-04-10 (continued further)

- **Chris surfaced the onboarding checklist gap.** Phase B existed but didn't present itself AS a checklist to the user, and the superpowers prerequisite was only checked in Phase A — a user invoking Phase B directly in a pre-existing workspace wouldn't be reminded. Also, the Phase B summary didn't clearly show which of the onboarding items were done, skipped, or declined.
- **Clarified the superpowers-in-target-repo nuance.** Claude Code plugins are user-level, not per-repo. We cannot "install superpowers inside a target repo" — only skills can be installed per-repo (via `.claude/skills/<name>/SKILL.md`), and superpowers' skills belong to Jesse, so we don't redistribute them. The correct pattern is: verify superpowers is present at the user level, record the prerequisite in the target repo's `.aiforging/CLAUDE.md` (like npm peerDependencies), and let the user install once machine-wide.
- **Updated `commands/setup.md` Phase B:**
  - Added an explicit 8-item onboarding checklist at the top of Phase B, presented as a preamble so the user knows what's coming.
  - Added Step B.3.5 "Verify superpowers prerequisite" that re-runs the check if Phase A was not part of the same session, and records the status for the summary.
  - Rewrote Step B.11 (summary) to emit a checklist block with `✓`, `—`, `✗` markers per item, plus a trailing warning if superpowers was missing.
- **Updated `conventions/CLAUDE.md.template`** (the per-target-repo pointer): added a "Prerequisites" section as the second section (right after the intro), documenting superpowers as a peer dependency with install instructions. Also corrected the pattern library references from `.aiforging/refactoring/patterns/` to `.aiforging/patterns/` (the shorter path we seed on onboard), updated the Hammer description to call the `hammer-refactor` skill by name, and updated the "where the plan lives" section to point at the forge workspace's `docs/features/` rather than a per-repo `PROPOSED_PLAN.md`.
- **Documented local dogfood command in plugin `CLAUDE.md`.** Confirmed via web search that `claude --plugin-dir <path>` is the correct flag: it's additive (loads alongside installed plugins), a local copy takes precedence if the same-named plugin is also installed, no caching, and `/reload-plugins` inside a running session picks up edits without restart. Added a "Dogfooding the plugin locally" section to `CLAUDE.md` with the recommended dogfood flow for Session 3.
- **Srdjan's tip** was correct — the flag name is exactly `--plugin-dir`, and it's documented in the official Anthropic Claude Code docs.
- **Known remaining gaps after this round:** we still have not run the setup command end-to-end in a live Claude Code session. That's Session 3's primary job. The `/aiforging:update-targets` propagation-gap command, the `/aiforging:new-feature <name>` feature-folder creator, and the LICENSE file are all still deferred to Session 3 or later.

### Session 2 — 2026-04-10 (continued even further — plugin enablement mechanism)

- **Chris corrected a wrong call from earlier this session.** I had claimed Claude Code plugins were "user-level only" and couldn't be enabled per-repo. Chris showed a working `~/projects/hub-plus-api/.claude/settings.json` with `{ "enabledPlugins": { "superpowers@claude-plugins-official": true } }`, proving that per-project enablement IS a real mechanism. Acknowledged the mistake, updated the mental model: plugins are *installed* once at the machine level via `/plugin install`, but *enabled* per-scope via `enabledPlugins` in each scope's `.claude/settings.json`. Identifiers use the `<name>@<source>` convention.
- **Locked in Decision 16** — per-scope plugin enablement via `.claude/settings.json`. The Session 2 claim "we can only record superpowers as a peer dep in CLAUDE.md" was wrong; we can and should actively write the `enabledPlugins` block into every workspace and every onboarded target repo so teammates who clone get auto-activation for free.
- **Built this round:**
  - `scripts/configure-plugins.py` — PEP 723 uv script, mirror of `configure-directories.py` in shape but for the `enabledPlugins` map. Subcommands: `check`, `enable`, `disable`, `set`. Validates identifiers against `^[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+$`. Creates the settings file if missing, takes timestamped `.bak-<ts>` backups on any change, writes atomically via `.tmp` rename, emits JSON status on every invocation. Idempotent `enable` tracks `already_on`; `disable` removes keys rather than setting them to false (matching how real settings files look).
  - **Smoke-tested end-to-end**: 8 test cases against a temp settings file — check on a non-existent file, enable from nothing, idempotent re-enable, disable, bad-id rejection, set-replacement, and a combined round with `configure-directories.py` to confirm that adding plugins doesn't clobber `additionalDirectories` and vice versa. All passed.
- **Updated `commands/setup.md`:**
  - Phase A Step A.2 now calls `configure-plugins.py enable --plugin superpowers@claude-plugins-official --plugin aiforging@claude-plugins-official` against the workspace's `.claude/settings.json` right after the workspace files are seeded, with a user prompt confirming the marketplace source (in case the user installed from `obra/superpowers` as `superpowers@superpowers-dev`).
  - Phase B Step B.3.5 was rewritten from "verify the prerequisite and document it" to "actively write the `enabledPlugins` block into the target repo's `.claude/settings.json`." Uses the same `configure-plugins.py enable` call, same marketplace-source prompt, and records the result for the B.11 summary checklist. The prerequisite verification (that superpowers is actually installed at the machine level) stays — we just add active enablement on top.
- **Updated `conventions/CLAUDE.md.template`:** the Prerequisites section now leads with the `enabledPlugins` block that `/aiforging:setup` wrote into the repo's own `.claude/settings.json`, explains that anyone cloning the repo gets auto-activation as long as they've installed the plugins at the machine level, and adds an alternate-marketplace note for users who installed `superpowers@superpowers-dev`. The footer "Updating this file" section now lists `.claude/settings.json`, `.claude/skills/hammer-refactor/SKILL.md`, and `.aiforging/` as the three things `setup` wrote, and notes that re-running setup is idempotent and won't clobber other plugin entries the user added themselves.
- **Updated `templates/workspace-CLAUDE.md` and `templates/workspace-README.md`:** both now show the `enabledPlugins` block that Phase A writes into the workspace's `.claude/settings.json`, explain the machine-level-install + per-scope-enable split, and include alternate-marketplace guidance.
- **Updated this PLAN.md:** added `configure-plugins.py` to the target plugin layout's `scripts/` section, added Decision 16, added the script to the Built list with smoke-test details, and wrote this log entry.
- **Session 2-continued status:** the enablement mechanism is now end-to-end correct across setup command, helper script, templates, target-repo pointer, plugin CLAUDE.md, and this plan. The plugin is still un-dogfooded — Session 3's primary job is still to run `claude --plugin-dir ~/projects/aiforging` from an empty `~/forge-test` and walk Phase A + Phase B end-to-end against a real CertainPath target repo.
- **Next session opening moves (still):**
  1. Add `LICENSE` file.
  2. Dogfood Phase A end-to-end from empty `~/forge-test` using `claude --plugin-dir ~/projects/aiforging`. Fix whatever breaks.
  3. Dogfood Phase B against a real CertainPath target. Fix whatever breaks.
  4. Design `/aiforging:update-targets` on paper.
  5. Design `/aiforging:new-feature <name>` on paper.

### Session 2 — 2026-04-10 (continued even further — settings split + git integration)

- **Chris surfaced a real issue while thinking about the upcoming dogfood.** Specs and plans accumulate in the forge workspace over time, and they're the whole institutional memory of cross-repo work — but the current design left the workspace as a loose directory with no git history. One `rm -rf` on a test workspace would wipe everything. He asked whether setup should git-init the workspace at the end of Phase A, and whether it could infer a logical remote destination from the registered target repos.
- **Uncovered a deeper conflation this forced us to fix first.** We had been cramming both `enabledPlugins` AND `permissions.additionalDirectories` into the workspace's single `.claude/settings.json`. Those two keys have opposite share profiles: `enabledPlugins` is identifier-based and shareable across teammates, `additionalDirectories` is a list of absolute local paths that are useless or harmful on any other machine. The moment we git-init'd the workspace, committing `settings.json` would leak Chris's personal paths to anyone who cloned it.
- **Locked in two new decisions:**
  - **Decision 17** — Split workspace settings into `.claude/settings.json` (committed, `enabledPlugins` only) and `.claude/settings.local.json` (gitignored, `additionalDirectories` only), matching Claude Code's native two-file convention. `configure-plugins.py` always targets the committed file; `configure-directories.py` always targets the local file. Target repos still only get one file (`settings.json`) because they don't manage cross-repo references.
  - **Decision 18** — Forge workspace is a git repo; `/aiforging:setup` offers `git init` + initial commit, never pushes, never creates remotes, never moves the workspace. Remote destination is *suggested* based on inference from `<target>/.git/config` origin URLs when targets share a host+org. Physical-location sanity check is advisory only.
- **Rewrote `commands/setup.md` extensively:**
  - New top-of-doc section "Settings file split" explaining the two-file model before any phase runs.
  - Step 1 phase-detection now checks for BOTH settings files; handles a migration case for workspaces created by the old single-file version (moves `additionalDirectories` from `settings.json` to `settings.local.json` before proceeding).
  - Step A.2 now creates `settings.json` (empty `{}`), `settings.local.json` (empty `additionalDirectories` list), and `.gitignore` (protecting the local file and helper-script backups). Then calls `configure-plugins.py enable` against the committed file.
  - New Step A.4 "Git integration (onboard-declined path)" calls the shared subroutine with `target_context=[]`. Runs only when the user declines to onboard a first target in A.3.
  - Step A.5 Phase A summary now shows both settings files, `.gitignore`, and git state.
  - Step B.3 now writes `additionalDirectories` to the workspace's `settings.local.json` instead of `settings.json`. Explicit warning in the step body: writing to `settings.json` is a bug.
  - New Step B.10 "Git integration" with two branches: first-time (init + initial commit with target-aware remote inference) and subsequent-run (offer follow-up commit to capture the onboarding). Called after all Phase B work is done so `docs/features/<feature>/` drafts are included in the commit.
  - Step B.11 Phase B summary updated: checklist item 1 now references `settings.local.json`, new checklist items 2a (enabledPlugins in target) and 9 (git state), trailing "Next" step 5 for the `git remote add` + `git push` hint.
  - Entirely new "Git integration subroutine" section at the bottom of the doc, ~150 lines. Five steps: (1) detect repo state + handle parent-repo nesting, (2) physical-location sanity check against common ancestor, (3) remote inference from target `.git/config` parsing, (4) git init + staged initial commit with confirmation, (5) print remote-add hint. Subroutine hard rules: never push, never auto-`git remote add`, never move, never commit `settings.local.json`, never touch `user.email`/`user.name` without consent.
  - Updated top-level "Hard rules" to reflect the split and the git integration hard rules.
- **Updated templates:**
  - `templates/workspace-README.md` — new "The two settings files (important)" section explaining the split; new "Git and the workspace history" section explaining what gets committed, what doesn't, and the clone-onto-another-machine flow (teammate clones → Claude Code auto-activates plugins from committed `settings.json` → teammate re-runs `/aiforging:setup` to register their own local target paths into their own `settings.local.json`); working-flow step 7 added for committing feature history.
  - `templates/workspace-CLAUDE.md` — opening line now points at `settings.local.json` for target paths; new "Settings file split" section; hard rules extended with "never commit settings.local.json" and "never write absolute paths into settings.json".
- **Updated `conventions/CLAUDE.md.template`** (per-target-repo pointer) — the "first session in this repo" guidance now correctly describes finding the forge workspace via its `CLAUDE.md` marker and `docs/features/` tree, and notes that the target repo's path lives in the workspace's `settings.local.json`. Target repos themselves still only have a committed `.claude/settings.json` with `enabledPlugins` — no `settings.local.json` needed.
- **Updated `PLAN.md`** — added Decision 17 (settings split), Decision 18 (git integration), updated the forge workspace layout diagram to show both settings files and `.gitignore`, and wrote this session log entry.
- **Session 2-settings-and-git status:** the workspace is now cleanly shareable. A clean flow now looks like: `/aiforging:setup` in an empty dir → split settings + .gitignore seeded → onboarding target → `additionalDirectories` in local file, `enabledPlugins` in committed file → git init + initial commit with inferred remote suggestion → later re-runs onboard more targets with follow-up commits. Still un-dogfooded — Session 3 is the first live Claude Code run.
- **Known issues carried forward to Session 3:**
  - The "cloned-workspace-needs-local-setup" case (a teammate clones an existing workspace onto their machine and needs to populate their own `settings.local.json`) is mentioned in `templates/workspace-README.md` as a design intent, but `/aiforging:setup` doesn't yet detect it explicitly. Phase A routes when markers are missing and Phase B routes when markers are present — but the "markers present BUT settings.local.json empty, AND this machine has no local targets yet" hybrid case needs its own subtle route. TBD in Session 3.
  - We haven't actually tested that Claude Code merges `settings.json` + `settings.local.json` the way we expect. Should confirm in Session 3 by launching `claude` inside a workspace and asking Claude to read both, then reporting what merged state it sees.
  - `configure-plugins.py` and `configure-directories.py` never needed to know about the other file; that's still true, but we should update both scripts' help text to recommend the correct file for each key type.
  - The git integration subroutine is long and has many branches. First dogfood run will probably surface at least one logic hole.
- **Next session opening moves (updated):**
  1. Add `LICENSE` file.
  2. Dogfood Phase A end-to-end from empty `~/forge-test`. Verify the split settings files land correctly and Claude Code merges them.
  3. Dogfood Phase B against a throwaway clone of a CertainPath target (`git clone --depth 1` into `/tmp`). Verify `additionalDirectories` lands in `settings.local.json`, `enabledPlugins` lands in the target's `settings.json`, and the `.gitignore` actually prevents `settings.local.json` from being committed.
  4. Verify git-init remote inference by inspecting the target's `.git/config` and checking the suggested URL matches expectations.
  5. Handle the cloned-workspace-needs-local-setup case explicitly in Phase detection.
  6. Design `/aiforging:update-targets` on paper.
  7. Design `/aiforging:new-feature <name>` on paper.

### Session 3 — 2026-04-10 (Phase A dogfood)

- Ran `/aiforging:setup` from empty `/Users/chrisholland/forge-test`. Phase detection correctly routed to Phase A. Workspace seeded: `CLAUDE.md`, `README.md`, `docs/features/README.md`, `.claude/settings.json`. Plugins enabled in workspace settings: `superpowers@claude-plugins-official`, `aiforging@claude-plugins-official` (superpowers v5.0.1 confirmed installed at user level via `~/.claude/plugins/installed_plugins.json`).
- **First dogfood breakage:** the setup command's instructions invoke helper scripts via `uv run …`, but `uv` is not on the interactive shell PATH in this environment. Worked around by invoking with `python3` directly — the scripts have no third-party deps so this is safe, but `commands/setup.md` should be updated to either probe for `uv` and fall back to `python3`, or document the requirement up front. Logged as a Session 3 fix.

### Session 3 fix — 2026-04-10 (uv/python3 runner probe)

- Resolved the dogfood breakage above. `commands/setup.md` now has a dedicated "Helper script runner (uv vs python3)" section right after the "Settings file split" section that explains the motivation and establishes the probe pattern. Every helper-script bash block in the command (4 call sites: Step A.2 `configure-plugins enable` for workspace, Step B.1 `detect-project`, Step B.3 `configure-directories add`, Step B.3.5 `configure-plugins enable` for target repo) now inlines the probe:

  ```bash
  if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi
  $FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-plugins.py enable …
  ```

  The probe is inlined per call site rather than set once globally because bash invocations from Claude Code are independent and don't carry env vars across calls.

- Ran the same fix across the other stragglers the initial edit missed: `skills/architecture-analyzer/SKILL.md` (step 1 of "How to run" now uses the probe before invoking `detect-project.py`), `templates/workspace-README.md` (the "Removing a target repo" example now shows both `uv run` and `python3` variants), and `CLAUDE.md` developer-facing "test scripts against real data" rule now mentions the fallback.

- The `scripts/*.py` files themselves need no changes — they're already PEP 723 single-file scripts with `dependencies = []`, so invoking them via `python3` behaves identically to `uv run` (the `# /// script` header is inert when `python3` sees it).

- Resolves the "First dogfood breakage" item above. Next dogfood run from `/Users/chrisholland/forge-test` (or a fresh empty workspace) should complete Phase A without any manual workaround. Phase B against a throwaway target clone is still untested — that's the next dogfood target.

### Session 3 — 2026-04-10 (Phase B dogfood against hub-plus-api)

- **Phase B dogfooded against `/Users/chrisholland/projects/hub-plus-api`** (Symfony 6.4 + Doctrine + PHPUnit, detected as `kind: backend`, no ambiguity). All install steps succeeded. Note: this run preceded the Session 3 `uv/python3` probe fix above, so all helper scripts were invoked via `python3` directly as a manual workaround. The workaround is no longer needed.
- **Install checklist results:**
  - Registered in workspace `additionalDirectories` ✓
  - Merged `aiforging@claude-plugins-official` into the target's existing `.claude/settings.json` alongside the pre-existing `superpowers@claude-plugins-official` entry ✓
  - Copied `conventions/architecture/` and `conventions/tdd/` into `<target>/.aiforging/`, wrote `<target>/.aiforging/CLAUDE.md` from the template ✓
  - Appended a 14-line `## AI Forging conventions` pointer section to the target's root `CLAUDE.md` (was 178 lines, now 192) ✓
  - Installed `hammer-refactor` SKILL.md into `<target>/.claude/skills/hammer-refactor/` ✓
  - Seeded the pattern library with the 1 pattern + 2 anti-patterns currently in `conventions/refactoring/` ✓
- **architecture-analyzer skill ran end-to-end against hub-plus-api** and produced `<target>/.aiforging/ANALYSIS.md`. Score: 6/10. Two High-severity findings: (1) persistence boundary leakage — 66 non-repository files in `src/Module/` inject `EntityManagerInterface` directly, and no repository interfaces exist anywhere in the codebase; (2) no factory-based test fixtures — inline `initializeXxx()` helpers on a monolithic `AbstractKernelTestCase` plus raw SQL files instead of Foundry/Alice. One Medium folder-layout finding: ~34% of controllers (129/379) and parallel legacy `src/Service/` and `src/Repository/` trees still live in the old layer-first layout. Notable positives: every Module-tree controller is single-action `VerbNoun` style, 313 DTO classes at the HTTP boundary, and the test harness has the right bones (DAMA bundle + `SchemaTool::createSchema()` bootstrap).
- **Step B.9 (draft feature folder) was declined by Chris.** The analyzer's findings are known and acceptable to live with for hub-plus-api right now. No `docs/features/hub-plus-api-architecture-alignment/` was created. `ANALYSIS.md` remains in the target as the record of findings, but no remediation plan was drafted in the workspace and no refactor execution will follow from this onboarding.
- **Skill invocation worked.** `aiforging:architecture-analyzer` was reachable via the `Skill` tool and dispatched correctly. The skill's "How to run" step 1 invokes `uv run scripts/detect-project.py` if no ProjectInfo was passed in — that path was not exercised in this run because Phase B had already detected the project earlier, but it's now covered by the Session 3 probe fix above.
- **Session 3 status:** Phase A and Phase B have both been dogfooded end-to-end against a real CertainPath repo, plus the `uv/python3` probe fix is in. The setup command works as designed. Outstanding items: (1) the propagation gap noted in Session 2 (a future `/aiforging:update-targets` command), (2) LICENSE file still pending, (3) `/aiforging:new-feature <name>` still in design.

### Session 3 continued — 2026-04-10 (PLAN.md writing bug + capture-pattern skill)

**Two threads this segment.** First a bug fix discovered during dogfood, then a feature addition prompted by seeing the hub-plus-api `capture-pattern` skill.

**Thread 1 — PLAN.md writing bug (Decision 20 reference).** Chris ran `/aiforging:setup` from empty `~/forge-test` launched via `claude --plugin-dir ~/projects/aiforging`, reached the end of Phase B, and Claude tried to append to `~/projects/aiforging/PLAN.md` — i.e., mutate the plugin source from an end-user run. Root cause was two lines in `commands/setup.md`:

- **Line 70 (Step 0)** told Claude to `cat ${CLAUDE_PLUGIN_ROOT}/PLAN.md` to orient. That was plugin-authoring context leaking into end-user runs.
- **Line 765 (Hard Rules)** said "Always update `${CLAUDE_PLUGIN_ROOT}/PLAN.md`'s Session Log section at the end of the run." That was the actual write instruction.

Both have been removed. Step 0 is now a self-sufficient three-bullet orientation (three-layer model, slice plan format reference, explicit "do not read or reference `${CLAUDE_PLUGIN_ROOT}/PLAN.md`"). Hard Rules now has a replacement that says "Never write anywhere under `${CLAUDE_PLUGIN_ROOT}`" with an explanation of why, a note that the old rule was a three-layer-model violation, and a directive to treat similar rules in other files as bugs.

I also swept `conventions/README.md` and `conventions/refactoring/README.md` (both of which are copied into target repos during Phase B) and removed references to "the plugin's PLAN.md" that would have confused end users or perpetuated the same misconception inside target-repo sessions. The plugin-developer-context files (`CLAUDE.md`, `README.md`, `PLAN.md` itself) still reference PLAN.md because those live in the plugin source and are for the plugin author. Logged the whole thing as **Decision 20** (numbered in the Locked-in Decisions list above — though only if you count "never write to plugin source" as its own decision; otherwise it's a clarification of Decision 13). Kept **Decision 20 (candidate)** as a separate parked note for the upstream pattern propagation mechanism.

**Thread 2 — capture-pattern skill (Decision 19).** Chris pointed at `~/projects/hub-plus-api/.claude/skills/capture-pattern/SKILL.md` as a candidate to adapt into AI Forging — the reactive skill that detects when the human corrects the AI's work and offers to persist the lesson as a new pattern/anti-pattern file. We discussed where it should live in the three-layer model and Chris chose:

- **Install in BOTH the forge workspace AND each onboarded target repo** (not one or the other).
- **Date-only attribution** — match the existing skill's `Captured during interactive session on YYYY-MM-DD` format. No prompt for author name.
- **Upstream propagation parked** as Decision 20 candidate.

Implementation:

- Created `skills/capture-pattern/SKILL.md` in the plugin source. Adapted from the hub-plus-api version with four substantive changes: (1) path changed from `project_docs/code-analysis/` to `.aiforging/patterns|anti-patterns/`, (2) downstream consumer reference changed from `post-tdd-refactoring` to `hammer-refactor`, (3) file format changed from the hub-plus-api-specific rich template to the simpler AI Forging plugin format documented in `conventions/refactoring/README.md` (sections are `## Rule`, `## Why`, `## Detect`, `## Apply` or `## Eliminate`, `### Before`, `### After`, `## Don't apply when`, `## Related`, `## Source`), (4) new "Step 2 — Resolve the target library" section that handles the workspace-vs-target distinction: detect cwd as target repo (look for `.aiforging/patterns/` directory) vs forge workspace (look for `CLAUDE.md` marker + `settings.local.json`); for workspace case, read `permissions.additionalDirectories` from `settings.local.json` and ask the user which target the pattern applies to if there are multiple.
- Updated `commands/setup.md` Phase A Step A.2 to copy `skills/capture-pattern/SKILL.md` into `<workspace>/.claude/skills/capture-pattern/SKILL.md` during workspace seeding. Updated the Phase A summary (Step A.5) file tree to show the new skill.
- Renamed Phase B Step B.5 from "Install hammer-refactor skill" to "Install AI Forging skills into the target repo" and rewrote it to offer BOTH `hammer-refactor` AND `capture-pattern` as a bundle (default Y for backend/fullstack). If the user declines the bundle, the step falls back to offering each skill separately. Added an "Overwrite safety" paragraph (diff-and-confirm, never silent) and a "Why capture-pattern lives in both the workspace and each target repo" paragraph explaining the dual-install rationale.
- Updated the Phase B checklist preamble item 4 to describe the skills bundle. Updated Step B.6 preamble ("For any target that received the conventions copy (Step B.4) OR the Hammer/Tempering skills bundle"). Updated Step B.11 summary checklist to have separate lines 4a (hammer-refactor) and 4b (capture-pattern).
- Updated `templates/workspace-README.md` with a new "The Tempering feedback loop — capture-pattern" section after the "Required plugins" section, updated the directory tree to show `.claude/skills/capture-pattern/`, updated "What gets committed" and the cloned-workspace teammate walkthrough, and rewrote "How to use this workspace" step 6 (Temper) to reference the skill.
- Updated `templates/workspace-CLAUDE.md` with a new "Tempering feedback loop — capture-pattern" section after the "Target repos" section, and listed `capture-pattern` alongside `hammer-refactor` when describing skills committed to target repos.
- Updated `conventions/CLAUDE.md.template` (copied into every onboarded target as its `.aiforging/CLAUDE.md`): extended the "Tempering" bullet in "The framework in one minute" to reference the skill, updated "What Claude should do in this repo" step 4 to reference `capture-pattern` by name, and added `capture-pattern/SKILL.md` to the installation manifest at the bottom.
- Updated plugin source `CLAUDE.md` directory map to list `skills/capture-pattern/` and also to list `configure-plugins.py` under `scripts/` (which was missing).

**Dogfood implications.** The next Phase A dogfood run should show `.claude/skills/capture-pattern/SKILL.md` in the workspace seed and the Phase A summary should list it in the file tree. The next Phase B dogfood run should offer the skills bundle, install both skills into the target, and the Step B.11 summary should show ✓ for both 4a and 4b. The capture-pattern skill itself cannot be fully tested in dogfood until an actual corrective moment occurs during an interactive session in a workspace or target repo — that will happen naturally as Chris uses the framework.

**Three-layer model self-reminder (after this thread).** I caught myself wanting to store some of the capture-pattern documentation inside the skill file by referencing pattern file models from `conventions/refactoring/patterns/` (e.g., "follow extract-service-from-controller.md"). That would have created exactly the wrong kind of coupling — the skill would break if Chris renamed or removed those files. Resolved by having the skill document the format inline instead and reference `conventions/refactoring/README.md` (seeded into every target) as the canonical format source. The skill is self-contained: reading the skill file is sufficient to know exactly what format to write.

**Next dogfood targets still standing:** (1) Phase A dogfood with the capture-pattern install, (2) Phase B dogfood against a throwaway target clone to verify both skills land and the bundle-decline fallback path works, (3) trigger a real `capture-pattern` fire by correcting Claude during a workspace session and verifying the target resolution logic picks the right repo, (4) LICENSE file, (5) `/aiforging:update-targets` design, (6) `/aiforging:new-feature <name>` design.

### Session 4 — 2026-04-10 (conventions extension + daily-driver command + run-anywhere pointer)

**Framing: a design audit against Chris's project-hub-plus orchestrator.** Chris wanted to compare his existing CertainPath orchestrator CLAUDE.md (`~/projects/project-hub-plus/CLAUDE.md`, ~465 lines, meta-project that orchestrates 4 sub-projects via symlinks) against what AI Forging had built and identify gaps plus portable patterns. I read the full orchestrator file, scored each section as gold/skip/needs-adaptation, and proposed a 6-item ordered build list. Chris approved: "ok yes please go ahead. please be sure to commit along the way." Session 4 is the execution of that list.

**What's gold and got ported:**

1. **Work item taxonomy.** The orchestrator uses `docs/features/<name>/overview.md + 01-<work>/spec.md + plan.md + 02-<work>/…` for features that decompose into multiple work items, plus the flat shape for single-work-item features. This was the clearest gap in the AI Forging feature convention. I ported both shapes explicitly with directory-tree examples, added the naming rule (numbered prefix `01-`, `02-`, … reflecting dispatch dependency order, then kebab-case), and added an explicit Step-0 scope determination (single-target vs multi-target) that drives the shape choice.
2. **Four-step planning workflow with Summary checkpoint.** Ported from the orchestrator: Step 1 creates spec.md with a Summary section capturing the user's initial prompt and stops for confirmation BEFORE filling the rest; Step 2 runs a grouped-clarifying-questions interview (themed rounds of 3–5 questions, not twenty-at-once or open-ended interrogation); Step 3 is an architecture review — the plan generator **must** read every affected target's `.aiforging/architecture/` and root CLAUDE.md before writing plan.md; Step 4 writes plan.md in the slice format with a closing `[hammer]` slice at the end of every Fire sequence.
3. **Read affected target CLAUDE.md before writing plan — non-negotiable rule.** Direct port from the orchestrator's rationale: "plans with incorrect paths produce incorrectly-placed code across every subagent that dispatches against them." A subagent has fresh context and trusts the plan; if the plan puts the controller in `src/Http/` when the target uses `src/Controller/`, every dispatched slice lands in the wrong place. Hardcoded into the feature convention as an explicit hard rule.
4. **Living-documents rules.** I initially misread Chris's "living documents is brittle" concern in the audit discussion; after reading the actual orchestrator rules I corrected myself — the rules are actually clean (route changes to spec vs plan vs notes, preserve completed checkboxes, proactive spec updates for visible behavior changes, subagents check their own boxes, parent never fabricates completion). Ported all of them verbatim-in-spirit.
5. **Parent-as-conductor subagent discipline.** The orchestrator treats the parent conversation as a conductor that dispatches slices to fresh-context subagents and never touches code itself. Ported as a new convention doc `conventions/subagent-orchestration/README.md` with: parent stays lean, plan.md is authoritative (subagent prompts POINT at it rather than embedding details so plan updates during execution don't desync), every subagent reads its target's CLAUDE.md, dispatch ordering vs parallelism, always close with hammer-refactor, subagents check their own boxes, parent never fabricates completion. Portable subagent prompt templates (generic / backend / frontend / hammer-refactor). This doc gets copied into every onboarded target repo as part of Phase B so teammates driving Claude directly inside a target inherit the same rules.

**What was deliberately skipped:** the orchestrator has a mandatory feature-permissions workflow (BusinessRole / Voter system), a mandatory branch check against qa/main, a Cross-Project Conventions section with API contract and shared domain module specifics, and a Commands section with composer/yarn/phpunit commands. All four are CertainPath-specific and do not belong in a portable framework. Skipped without regret.

**Commits this session (in order):**

1. `213296f` — `conventions/features: port planning workflow, work-item taxonomy, and living-docs rules from project-hub-plus orchestrator`. Touches `conventions/features/README.md` (canonical) and `templates/docs-features-README.md` (workspace template, mirrored).
2. `7efcea0` — `conventions/subagent-orchestration: add portable rules for parent-as-conductor dispatch model`. New directory `conventions/subagent-orchestration/` with one `README.md`.
3. `3a3b9aa` — `skills/hammer-refactor: document plan-driven auto-trigger and reference subagent-orchestration conventions`. Added a "How this skill gets triggered" subsection naming three legitimate entry points (plan-driven auto-trigger as the default path, user-invoked against a specific feature, user-invoked targeted mode), cross-referenced `conventions/subagent-orchestration/README.md` as the policy layer Hammer follows, and extended the "Subagent dispatch" bullet in "Relationship to other skills" to name the new conventions doc.
4. `57bd5c6` — `commands: add /aiforging:new-feature as the daily-driver entry point; align setup Phase B.9 to the same convention`. Created `commands/new-feature.md` from scratch (Step 0 orient, Step 1 locate workspace with cwd-first + run-anywhere pointer fallback, Step 2 parse args with kebab-case normalization, Step 3 feature detection with new/extend/abort choice, Step 4 flat-vs-nested shape picker, Step 5 extension flow that upgrades flat to nested or appends a new numbered work item, Step 6 Summary checkpoint handoff to superpowers:brainstorming, Step 7 hard rules). Reworked `commands/setup.md` Phase B Step B.9 to explicitly frame itself as an auto-invoked specialization of `/aiforging:new-feature` with the feature convention as the single source of truth both commands must agree on. Documented the intentional differences: B.9's initial prompt is pre-supplied from the analyzer, B.9 DOES write a plan.md draft (analyzer output is structured enough), B.9 is auto-invoked vs user-invoked.
5. `54ffc41` — `scripts + setup: add run-anywhere pointer file (~/.claude/aiforging.json) and wire into setup Phase A + Phase B`. New helper script `scripts/configure-workspace-pointer.py` matching the existing helper-script style (PEP 723, zero deps, atomic writes, timestamped backups, JSON status output). Subcommands: `check`, `set-active`, `add`, `forget`. `set-active` validates the path is absolute and exists (rejects typos; `--force` for bootstrap); `forget` clears `active_workspace` when the active one is forgotten rather than guessing a replacement; `workspaces` list is prepended MRU and deduped, never auto-pruned. Smoke-tested all four subcommands against a scratch pointer file in `/tmp` before committing. Wired into `commands/setup.md`: new Step A.2.5 (write the freshly-bootstrapped workspace to the pointer file as active, with explicit user confirmation, mentioning previous active if one existed), new Step B.10.5 (refresh the pointer at end of onboarding; idempotent with A.2.5 if Phase A routed directly into Phase B; silent no-op if the pointer already points at the current workspace), updated Phase A.5 and Phase B.11 summaries to report pointer state, and updated the settings-file-split section to document pointer config as a THIRD kind of config separate from `settings.json` and `settings.local.json`.

**The new `/aiforging:new-feature` + run-anywhere pointer together give users the daily-driver experience Chris asked for:** type `/aiforging:new-feature <name> <prompt>` from any directory on the machine, the command reads `~/.claude/aiforging.json` to find the active workspace, drops into `docs/features/<name>/`, creates the spec.md skeleton with the Summary section captured from the prompt, stops at the Step-1 checkpoint, and hands off to `superpowers:brainstorming` for the rest of the interview. No manual `cd` into the workspace, no manual file creation, no fragmented-per-repo state.

**Three-layer model observed.** Every write this session went to the forge-workspace layer (docs/features/, .claude/skills/, .claude/settings.json), the target-repo layer (subagent-orchestration conventions get copied into each target during Phase B), or the per-user per-machine layer (`~/.claude/aiforging.json` via the new helper script). Zero writes to the plugin source from end-user runs — the only writes to the plugin source this session were the plugin-author ones I'm making in Chris's dev session against `~/projects/aiforging/`.

**Dogfood gap still pending.** None of the Session 4 work has been exercised in a fresh `claude --plugin-dir` dogfood run yet. The items that need dogfood verification:

- Phase A Step A.2.5 — confirm the pointer file write prompts the user correctly and writes `~/.claude/aiforging.json` with the right content.
- Phase B Step B.10.5 — confirm the pointer refresh is silent when unchanged and prompts when switching.
- `/aiforging:new-feature` end-to-end — (a) from inside a forge workspace with no existing features, (b) from inside a workspace with a matching existing feature (to exercise the detection + extend flow), (c) from outside any workspace with the pointer populated (to exercise run-anywhere), (d) from outside any workspace with the pointer missing (to exercise the graceful stop message).
- `/aiforging:setup` Phase B Step B.9 — confirm the reworked Step B.9 still produces a sensible architecture-alignment feature folder from analyzer output, following the new convention.

**Propagation gap reminder.** The new `conventions/subagent-orchestration/README.md` needs to be copied into target repos as part of Phase B Step B.4 (the conventions copy step). I did NOT update Step B.4 this session to include the new directory — Step B.4 currently copies only `conventions/architecture/` and `conventions/tdd/`. This is a quick next-session fix: extend Step B.4 to also copy `conventions/subagent-orchestration/` into `<target>/.aiforging/subagent-orchestration/`. Logged here so it doesn't get forgotten.

**Similarly**, the target-repo `CLAUDE.md.template` (copied as `<target>/.aiforging/CLAUDE.md`) should reference the new subagent-orchestration conventions so teammates driving Claude directly inside the target discover them. Not updated this session.

**Next session opening moves:**

1. Fix the two propagation gaps above: Phase B Step B.4 copies `conventions/subagent-orchestration/` and the target-repo CLAUDE.md template references it.
2. Fresh `claude --plugin-dir` dogfood of the run-anywhere flow: bootstrap a new `~/forge-test` via Phase A, verify the pointer file gets written, `cd` out, run `/aiforging:new-feature` from somewhere else, verify the detection and creation flow works, verify the Summary checkpoint hand-off to superpowers:brainstorming fires.
3. Still standing: LICENSE file, `/aiforging:update-targets` design, hammer-refactor propagation when patterns change upstream.
4. Consider a `/forge` alias for `/aiforging:new-feature` if Chris confirms he'd use it — either as a second thin command file or via Claude Code's alias mechanism if one exists.

### Session 5 — 2026-04-13

**Picking up from Session 4 wrap-up.** Two items carried over from where Session 4 cut out mid-reply:

1. **`commands/forge.md` committed** (`51a260c`). Chris requested a `/forge` alias for `/aiforging:new-feature`. Implemented as a thin pointer file: when invoked, Claude reads `${CLAUDE_PLUGIN_ROOT}/commands/new-feature.md` and executes it exactly, treating arguments as if passed to `/aiforging:new-feature`. One source of truth — no duplicated logic. Plugin namespacing means the alias resolves as `/aiforging:forge`, not bare `/forge`.

2. **Layer-split anti-pattern callout added to the feature convention** (this commit). During a day-to-day walkthrough in Session 4, I incorrectly used nested shape to split a cohesive backend+frontend feature (`tax-inclusive-pricing`) into repo-boundary work items (`01-backend-tax-model/` and `02-frontend-tax-display/`). Chris caught it: separate specs per repo let the API contract drift. The correct shape is FLAT — one spec, one plan, per-slice target-repo tags, `[gate: contract]` on the API-shape slice. Nested is only for sequential phases (e.g., dual-write migration → cutover). Added an explicit "When NOT to use nested — the layer-split anti-pattern" subsection to both `conventions/features/README.md` (canonical) and `templates/docs-features-README.md` (workspace template mirror).

**Then, continuing in the same session after resuming from context loss:**

3. **Closed both propagation gaps from Session 4** (`ae52eab`). Phase B Step B.4 now copies `conventions/subagent-orchestration/` into `<target>/.aiforging/subagent-orchestration/` alongside `architecture/` and `tdd/`. The target-repo `CLAUDE.md.template` now includes a "Subagent orchestration, in short" section referencing `.aiforging/subagent-orchestration/README.md`, and the "Updating this file" footer lists `subagent-orchestration` as part of the conventions library.

4. **MIT LICENSE added** (`1778745`). Standard MIT license, copyright 2026 Chris Holland. Matches `license: "MIT"` in `plugin.json`.

5. **Dogfood verification (script-level).** Can't run `claude --plugin-dir` from inside Cowork, but smoke-tested all four helper scripts end-to-end against scratch files:
   - `configure-plugins.py enable` → creates `enabledPlugins` in settings.json, no cross-contamination with local file.
   - `configure-directories.py add` → creates `additionalDirectories` in settings.local.json, no cross-contamination with committed file.
   - `configure-workspace-pointer.py set-active` → writes pointer file independently of both settings files.
   - Simulated Phase B Step B.4 copy: `architecture/` (5 files), `tdd/` (3 files), `subagent-orchestration/` (1 file) all land correctly in `<target>/.aiforging/`. The installed `CLAUDE.md` references `subagent-orchestration` in 2 places.
   - **Still needed:** a real `claude --plugin-dir ~/projects/aiforging` dogfood run from a fresh empty directory to exercise the full Phase A → Phase B → `/aiforging:new-feature` flow interactively. This is the one verification that requires a Claude Code terminal session, not Cowork.

**Commits this session (in order):**

1. `51a260c` — `commands: add /aiforging:forge as thin pointer alias for /aiforging:new-feature`
2. `0d4be5c` — `conventions/features: add layer-split anti-pattern callout for nested shape`
3. `ae52eab` — `setup + template: close two propagation gaps from Session 4`
4. `1778745` — `Add MIT license`
5. This commit — `PLAN.md: Session 5 log`

**Two-tier pattern library + workspace-as-role rework (continued in same session after context loss):**

Chris raised concerns about the `~/forge` working directory model not fitting all scenarios (monorepo, single repo, blended repo). After discussion, three new decisions were locked in:

- **Decision 21 (workspace-as-role):** Four scenarios — multi-repo (separate workspace), monorepo (workspace IS repo root), single blended repo, single-purpose repo. The workspace is a role, not always a separate directory.
- **Decision 22 (two-tier pattern library):** Shared tier at workspace level with `applies-to` YAML frontmatter (stack identifiers). Target-local tier per-target with no frontmatter. `hammer-refactor` merges both tiers filtered by detected stack. `capture-pattern` asks shared-vs-local at capture time. Default recommendation: shared.
- **Decision 23 (monorepo sub-project detection):** `detect-project.py` already recurses children for meta-repos. Setup presents detected sub-projects for user confirmation, each gets its own `.aiforging/`.

Chris explicitly said: "I would be in favor of going all-in on Approach 2 right now, even if it means a lot of reworking of the framework. I would rather do this now, while nobody is using this."

The rework touched every framework file that references the pattern library or workspace model:

6. `162cb57` — `PLAN.md: Decisions 21-23 — workspace-as-role, two-tier pattern library, monorepo detection`
7. `91c5293` — `conventions/refactoring: two-tier pattern library + applies-to frontmatter` — added frontmatter to all three seeded patterns (`extract-service-from-controller`: all backend stacks, `fat-controller`: all backend stacks, `primitive-obsession`: `all`). Updated README with two-tier docs.
8. `5aa0572` — `skills/hammer-refactor: workspace awareness + two-tier pattern merging` — Step 0 resolves workspace (Cases A/B/C). Step 2 merges shared + local tiers with stack filtering. Filename-based dedup (local wins).
9. `9743b09` — `skills/capture-pattern: two-tier support — shared vs target-local with stack frontmatter` — Step 2 four-case workspace resolution. Step 4.5 tier selection with `applies-to` frontmatter for shared captures. Duplicate check across both tiers.
10. `c02d3d9` — `conventions/CLAUDE.md.template: update for two-tier pattern model` — Hammer, Tempering, and "What Claude should do" sections updated for both tiers.
11. `9019689` — `templates: update workspace-CLAUDE.md and workspace-README.md for two-tier patterns` — New two-tier section in CLAUDE.md. Directory tree, Tempering section, commit list updated in README.md.
12. `36dcda6` — `setup.md: two-tier pattern library + workspace-as-role (Decisions 21-23)` — Step 0.5 scenario interview. Phase A seeds shared tier, conditional `settings.local.json`. Step A.2.7 monorepo sub-project detection. Phase B scenario-dependent entry points. Step B.3 skip for Scenario B/C. Step B.6 empty target-local dirs.

**Commits this session (full list, in order):**

1. `51a260c` — `commands: add /aiforging:forge as thin pointer alias for /aiforging:new-feature`
2. `0d4be5c` — `conventions/features: add layer-split anti-pattern callout for nested shape`
3. `ae52eab` — `setup + template: close two propagation gaps from Session 4`
4. `1778745` — `Add MIT license`
5. `063ade1` — `PLAN.md: Session 5 log` (first half)
6. `162cb57` — `PLAN.md: Decisions 21-23`
7. `91c5293` — `conventions/refactoring: two-tier + frontmatter`
8. `5aa0572` — `skills/hammer-refactor: two-tier merging`
9. `9743b09` — `skills/capture-pattern: two-tier support`
10. `c02d3d9` — `conventions/CLAUDE.md.template: two-tier`
11. `9019689` — `templates: two-tier`
12. `36dcda6` — `setup.md: two-tier + workspace-as-role`
13. This commit — `PLAN.md: Session 5 log (continued)`

**Next session opening moves:**

1. **Interactive dogfood** — `mkdir ~/forge-test && cd ~/forge-test && claude --plugin-dir ~/projects/aiforging`, run Phase A end-to-end with each scenario (multi-repo, monorepo, single-repo). Test Phase B against a real CertainPath target. Test `/aiforging:new-feature` or `/aiforging:forge` from outside the workspace.
2. **Re-validate project README.md** — Chris explicitly flagged this for later. Make sure it's still accurate after the two-tier rework.
3. `/aiforging:update-targets` design — the propagation-gap command that sweeps `additionalDirectories` and refreshes each target's `.aiforging/` copies + skills with diff-and-ask semantics.
4. Clean up stale `.git/*.lock.bak.*` and `.git/objects/*/tmp_obj_*` files from the host shell (FUSE mount artifacts from Cowork commits).

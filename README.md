# AI Forging

> A structured framework for **agentic software development** — test-first, pattern-driven refactoring, domain-driven architecture. Shipped as a Claude Code plugin. The counterpoint to vibe coding.

AI Forging is a counterpoint to "vibe coding." The thesis: AI is incredibly powerful at generating code, but without structure, every feature shipped makes the codebase worse. AI Forging provides that structure as three stages of a metallurgical forge: **Fire → Hammer → Tempering.**

**Going agentic is easy. Going agentic without wrecking quality is the hard part.** Autonomy (how big a unit of work you hand the AI) and discipline (how much spec, testing, and review wrap it) are two different axes. Cross them and you get four very different places to build — and AI Forging is the top-right: whole units of work, forged.

<p align="center">
  <img src="docs/quadrant.png" alt="A map for agentic software development — autonomy versus discipline. Vibe Coding (low/low), Disciplined AI-Assist (high discipline, low autonomy), Agentic Vibe Coding (low discipline, high autonomy), and AI Forging (high discipline, high autonomy — the goal)." width="720"/>
</p>

- **Fire** — AI-powered TDD. Tests are written first and capture intent before a single line of implementation exists. Red, Green, Refactor. *Uses the [`superpowers` plugin](https://github.com/obra/superpowers)'s `test-driven-development` skill.*
- **Hammer** — Automated pattern-driven refactoring. The `hammer-refactor` skill dispatches one fresh-context subagent per pattern or anti-pattern file against the session's changed files, in parallel. *Built on top of `superpowers:subagent-driven-development`.*
- **Tempering** — Scalable knowledge capture. The `capture-pattern` skill watches for corrective moments during interactive code review and offers to persist the lesson as a new `.md` file in the pattern library. One correction, one file. Adding the 50th pattern costs no more than the 5th, because every pattern lives in its own file and gets its own subagent on every Hammer pass.

Each iteration through the cycle leaves the codebase stronger than it started.

Two **optional** stages run after the forge, once a feature is built to presumed-working. Neither generates code:

- **`browser-testing`** — walks the feature's `testing.md` QA checklist in a real browser. It marks the items only a human can judge so you can work those in parallel, walks the rest, records one line of evidence per step, and reports what diverged. **It fixes nothing, deliberately.** A failing step is evidence that the product and the spec disagree; it is not evidence about which one is wrong, and deciding that needs a person.
- **`review-loop`** — rounds of code review across every repo the feature touched, with each finding triaged against the source before it is accepted (in practice about a third of review findings describe deliberate behavior), classified, and fixed by serialized agents. It stops on a real stop condition rather than on a finding count.

Run `browser-testing` first. Six rounds of review cannot find a feature that works exactly as written and is wrong.

<p align="center">
  <img src="docs/feature-workflow.svg" alt="Building a Feature with AI Forging — workflow diagram showing Fire, Hammer, and Tempering stages with human gates" width="680"/>
</p>

## Day-to-day usage

Once your workspace and targets are set up, these are the commands you'll reach for:

**Building a new feature.** From any directory: `/aiforging:forge my-feature-name "brief description of what you want to build"`. It scaffolds a feature folder, pre-fills the spec, and walks you through refining scope and planning before any code is written. (Full form: `/aiforging:new-feature`.)

**Reviewing code and catching a lesson.** You're pair-programming with Claude, spot something less than ideal, and explain the fix. Claude's `capture-pattern` skill activates and offers to persist the lesson as a new pattern or anti-pattern file — one correction, one file, immediately available on every future Hammer pass. It'll ask whether the pattern applies to just this repo or all same-stack targets.

**Hammer passes run automatically.** At the end of each TDD cycle, `hammer-refactor` auto-triggers against the changed files — one fresh-context subagent per applicable pattern, parallel, isolated, no drift. You review each proposal and accept or reject. (You can also invoke it manually against any set of files if you want a targeted pass outside the normal flow.)

**Verifying a feature you just built.** Two optional stages, in this order. `/aiforging:browser-testing` walks the feature's `testing.md` in a real browser against your local environment while you work the 👤 items — the ones judged by eye — in parallel; it reports what diverged and changes nothing. Then `/aiforging:review-loop` runs rounds of review, triage, and fix across every repo the feature touched. Neither replaces your own pass, and neither runs your full test suite.

**Running your full test suite.** No AI Forging stage ever does. Every Fire, Hammer, and fix agent runs one named suite scoped to the feature in scope, because a fast loop is the whole point — and the skills will tell you, in words, when implementation is done and it is your turn to run everything.

**Auditing a codebase you just inherited.** Onboard it with `/aiforging:setup`, and the architecture analyzer produces a scored assessment with prioritized findings. A structured starting point instead of grepping around.

**Planning work that spans repos.** From your forge workspace, `/aiforging:forge tax-inclusive-pricing` creates a single feature folder with one spec covering both backend and frontend targets — slices tagged per-repo, `[gate: contract]` on the API boundary. One plan, no drift between repos.

## Who this is for

Software crafters with **established codebases** who already feel the pain of AI-generated sprawl and are ready to adopt an opinionated workflow. Teams whose backends are built around a Data Mapper ORM (Doctrine, Hibernate, Entity Framework Core, TypeORM, MikroORM) will get the most value out of the box. Teams on Active Record stacks (Eloquent, Rails) can still adopt the framework with caveats documented in the conventions.

AI Forging is **not descriptive** — it is prescriptive, and it will tell you to refactor things. That's the point.

## The three-layer model

AI Forging deliberately separates three locations with different lifecycles:

1. **The plugin itself** — installed once per machine from a marketplace. Holds the conventions library, skills, helper scripts, and the `/aiforging:setup` command. You never clone or edit this.
2. **Your forge workspace** — the directory from which you orchestrate feature work. Bootstrapped by `/aiforging:setup` Phase A. Holds your central `docs/features/<name>/spec.md` + `plan.md` files, a committed `.claude/settings.json` with `enabledPlugins`, and the **shared-tier pattern library** (`.aiforging/patterns/` and `.aiforging/anti-patterns/` with `applies-to` frontmatter for stack filtering). Also installs the workspace-level `capture-pattern` skill for feedback loops that span repos. Designed to accumulate feature history as a git repository over time.
3. **Your target repos** — the codebases being forged. Each is onboarded to a forge workspace via `/aiforging:setup` Phase B. Gets a committed `.aiforging/` (conventions library + **target-local pattern directories** + `ANALYSIS.md` snapshot + per-repo `CLAUDE.md` pointer) and, for backend/fullstack repos, committed `.claude/skills/hammer-refactor/` and `.claude/skills/capture-pattern/` so any teammate who clones the repo gets the full toolkit without having to install the aiforging plugin on their machine.

**Workspace as a role, not always a separate directory.** `/aiforging:setup` opens with a scenario interview that adapts to how your codebase is organized:

- **Multiple repos** — the workspace is a separate directory (e.g., `~/forge`) that points at your target repos via `additionalDirectories` in a gitignored `settings.local.json`.
- **Monorepo** — the workspace IS your repo root. Sub-projects (e.g., `frontend/`, `backend/`) are detected and each gets its own `.aiforging/` conventions.
- **Single repo** — the workspace IS the repo. Conventions install at the root.

The split keeps the plugin shareable, each workspace personal, and each target repo self-contained.

**Two-tier pattern library.** Patterns live in two places: a **shared tier** at the workspace level (applies to all targets with matching stacks, has `applies-to` YAML frontmatter) and a **target-local tier** per target repo (applies only to that repo, no frontmatter needed). The `hammer-refactor` skill merges both tiers on every run, filtering by the target's detected stack. The `capture-pattern` skill asks whether each new capture should be shared or target-local. Seeded patterns from the plugin ship in the shared tier. A target-local directory starts with only its tier README — the placeholder that keeps it alive, since git will not track an empty directory.

## Installation

### 1. Install the plugins at the machine level

AI Forging depends on the `superpowers` plugin for TDD and plan-writing skills. You install both plugins once per machine via Claude Code's `/plugin` command:

```
# In your Claude Code CLI:
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-dev

/plugin marketplace add aiforging/aiforging
/plugin install aiforging@aiforging
```

If you've added Anthropic's official plugin marketplace, you can also install these as `superpowers@claude-plugins-official` and `aiforging@claude-plugins-official` respectively — `/aiforging:setup` will ask you which marketplace source to reference when it writes the `enabledPlugins` block.

Installing a plugin at the machine level makes it *available*. Activating it in a specific project is a separate step, handled automatically by `/aiforging:setup` — see the "install vs enable" note at the end of this section.

### 2. Bootstrap a forge workspace

Run `/aiforging:setup` from the directory that will become your workspace. For multiple repos, create a new directory; for monorepos or single repos, `cd` into the repo root:

```
# Multiple repos — create a new workspace directory:
mkdir ~/forge && cd ~/forge && claude
# then: /aiforging:setup

# Monorepo — cd into the repo root:
cd ~/my-monorepo && claude
# then: /aiforging:setup

# Single repo — same as monorepo:
cd ~/my-project && claude
# then: /aiforging:setup
```

This runs **Phase A — init-workspace**. It:

1. Asks how your codebase is organized (multiple repos / monorepo / single repo) and adapts accordingly.
2. Verifies `superpowers` is installed at the machine level.
3. Seeds `CLAUDE.md`, `README.md`, `docs/features/README.md`, and a `.gitignore` into the workspace.
4. Creates a committed `.claude/settings.json` with `enabledPlugins` for `superpowers` and `aiforging`.
5. For multi-repo workspaces only: creates a gitignored `.claude/settings.local.json` for per-user `permissions.additionalDirectories`.
6. Copies the `capture-pattern` skill into the workspace's own `.claude/skills/`.
7. Seeds the **shared-tier pattern library** (`.aiforging/patterns/` and `.aiforging/anti-patterns/`) with the framework's starting patterns.
8. Registers the workspace in `~/.claude/aiforging.json` so commands like `/aiforging:new-feature` work from any directory.
9. For monorepo/single-repo: detects sub-projects and onboards them inline.
10. For multi-repo: offers to onboard the first target project (Phase B).
11. Offers to `git init` (if not already a repo) and stage an initial commit.

### 3. Onboard a target repo

For multi-repo workspaces, either continue into Phase B at the end of Phase A or re-run `/aiforging:setup` at any later time to onboard another target. For monorepo/single-repo workspaces, sub-project onboarding happens inline during Phase A. Either way, **Phase B — onboard-project** performs:

1. Detects the target's stack (Symfony/Doctrine, React/TS/Playwright, etc.) and confirms whether it's backend, frontend, fullstack, or a meta-repo.
2. For multi-repo only: registers the target's absolute path in the workspace's `settings.local.json`.
3. Writes `enabledPlugins` into the *target repo's* own `.claude/settings.json` so teammates who clone the target get `superpowers` + `aiforging` auto-activated without touching their personal config.
4. Copies the conventions library into `<target>/.aiforging/` (architecture, tdd, subagent-orchestration) plus a per-repo `CLAUDE.md` pointer.
5. For backend / fullstack targets, offers to install the `hammer-refactor` + `capture-pattern` skills as a bundle into `<target>/.claude/skills/` so anyone cloning the target repo can run them directly.
6. Creates `<target>/.aiforging/patterns/` and `<target>/.aiforging/anti-patterns/` for the **target-local tier**, each with a short README explaining the tier (and keeping the directory alive — git will not track an empty one). Writes `<target>/.aiforging/VERSION` so future updates can tell plugin changes from your changes. Seeded patterns live in the workspace's shared tier — `hammer-refactor` merges both tiers on every run.
7. Runs the `architecture-analyzer` skill against the target and writes a structured `.aiforging/ANALYSIS.md` report with a score and prioritized findings.
8. Optionally installs the Playwright-oriented frontend testing convention for frontend / fullstack targets.
9. Optionally drafts a feature folder at `<workspace>/docs/features/<feature-name>/` with a `spec.md` and a `plan.md` (in the AI Forging slice format) based on the analyzer's findings.
10. Stages a follow-up git commit in the workspace capturing the onboarding.

Phase B is re-runnable. Each re-run adds another target to the same workspace.

**`/aiforging:setup` will never execute any refactors.** The boundary is explicit and has held since v0.1.0: install + analyze + propose plan. Running the actual Hammer pass is a separate, explicit step via the `hammer-refactor` skill once a plan has been approved. A future `/aiforging:execute-plan` command will orchestrate plan execution with per-step approval gates.

### A note on "install vs enable"

Claude Code keeps these two operations separate, and the distinction matters when teammates clone your workspace or a target repo:

- **Installing** a plugin (`/plugin install …`) downloads its code to `~/.claude/plugins/` on that machine. This is one-time per machine.
- **Enabling** a plugin in a scope writes `{ "enabledPlugins": { "pluginname@source": true } }` into that scope's `.claude/settings.json`. This is what `/aiforging:setup` does automatically for your workspace and for each onboarded target repo.

The enablement block is identifier-based — it *points at* a plugin but doesn't contain the plugin's code. A teammate who clones a target repo inherits its `enabledPlugins` block for free, but they still need to run the machine-level `/plugin install` steps once before Claude Code can actually activate those plugins. Give teammates the same install block from the top of this section and everything else is automatic.

## What's in the plugin

```
aiforging/
├── .claude-plugin/
│   ├── plugin.json                 # plugin manifest
│   ├── marketplace.json            # marketplace definition
│   └── artifacts.json              # what gets copied where, and how it updates
├── commands/
│   ├── setup.md                    # /aiforging:setup (Phase A + Phase B)
│   ├── new-feature.md              # /aiforging:new-feature — daily-driver feature scaffolding
│   ├── forge.md                    # /aiforging:forge — thin alias for new-feature
│   ├── hammer-refactor.md          # /aiforging:hammer-refactor — pointer to the skill
│   ├── capture-pattern.md          # /aiforging:capture-pattern — pointer to the skill
│   ├── browser-testing.md          # /aiforging:browser-testing — pointer to the skill
│   ├── review-loop.md              # /aiforging:review-loop — pointer to the skill
│   ├── update-targets.md           # /aiforging:update-targets — manifest-driven propagation
│   └── uninstall.md                # /aiforging:uninstall — clean removal, preserves your work
├── scripts/                        # PEP 723 single-file Python scripts (run under uv or python3)
│   ├── detect-project.py           #   read-only stack detection (recurses for monorepos)
│   ├── configure-directories.py    #   manages permissions.additionalDirectories
│   ├── configure-plugins.py        #   manages enabledPlugins
│   └── configure-workspace-pointer.py  #   manages ~/.claude/aiforging.json (run-anywhere pointer)
├── skills/
│   ├── architecture-analyzer/      # non-destructive advisory analysis, runs from workspace
│   │   └── SKILL.md
│   ├── hammer-refactor/            # executable Hammer stage, copied into each target repo
│   │   └── SKILL.md
│   ├── capture-pattern/            # reactive Tempering feedback loop
│   │   └── SKILL.md                #   installed in both workspace and each target repo
│   ├── browser-testing/            # optional — walks testing.md in a real browser, fixes nothing
│   │   └── SKILL.md                #   workspace-level
│   └── review-loop/                # optional — rounds of review, triage, and fix
│       └── SKILL.md                #   workspace-level
├── templates/                      # bootstrap templates for forge workspace init (Phase A)
│   ├── workspace-CLAUDE.md
│   ├── workspace-README.md
│   ├── docs-features-README.md
│   ├── feature-testing.md          # testing.md skeleton, copied per feature
│   ├── patterns-tier-README.md     # tier placeholder — keeps the directory alive in git
│   └── anti-patterns-tier-README.md
└── conventions/                    # library copied into each target repo as .aiforging/
    ├── CLAUDE.md.template          #   per-target CLAUDE.md pointer
    ├── features/                   #   feature-folder + slice-plan convention
    ├── architecture/               #   Domain-Driven Hexagonal, Single-Action Controllers, Repositories, DTOs, Naming
    ├── tdd/                        #   Fire loop (delegates to superpowers), the feature-test-suite rule, harness capability contract, repository testing
    ├── subagent-orchestration/     #   subagent dispatch conventions (one shot per pattern)
    ├── refactoring/                #   two-tier pattern library + Tempering feedback format
    │   ├── patterns/               #     one file per pattern (applies-to frontmatter for shared tier)
    │   └── anti-patterns/          #     one file per anti-pattern
    └── frontend-testing/           #   optional Playwright layer
```

## Relationship to the `superpowers` plugin

AI Forging deliberately delegates core skills to `superpowers`:

- `superpowers:test-driven-development` — the Red/Green/Refactor loop.
- `superpowers:brainstorming` — spec-before-code dialogue.
- `superpowers:writing-plans` — plan generation.
- `superpowers:executing-plans` — plan execution with checkpoints.
- `superpowers:subagent-driven-development` — fresh-context subagent dispatch, which `hammer-refactor` is built on top of.

AI Forging adds what superpowers intentionally leaves to each team's architecture:

- A prescriptive, domain-centric folder layout.
- Single-action controllers, data-mapper Repositories, Value Objects / DTOs, naming rules.
- The **test-harness capability contract** that makes the Fire stage trustworthy for data-driven code.
- A pattern / anti-pattern library structured for fresh-context subagent refactor passes.
- The `architecture-analyzer` skill for advisory audits.
- The `hammer-refactor` skill as the executable Hammer stage.
- The `capture-pattern` skill as the reactive Tempering feedback loop that grows the library one code review at a time — with a two-tier model (shared across all same-stack targets, or target-local) so cross-pollination is built in.
- The **feature test suite** rule: one named suite per feature, registered before the first test, augmented by every subsequent work item — and nothing else ever runs during the loop. The full suite is handed back to the human, in words, when implementation ends.
- The `browser-testing` skill: an optional pass that walks the feature's human QA checklist in a real browser and reports divergence without fixing anything.
- The `review-loop` skill: an optional multi-round review / triage / fix cycle across every repo a feature touched, with a triage step because roughly a third of review findings describe deliberate behavior.
- An optional Playwright convention layer for frontend integration tests.
- A forge workspace model (separate directory, monorepo root, or single-repo root) with a central `docs/features/<name>/spec.md + plan.md` convention, so features that touch multiple repos (or sub-projects) have one place to plan and track them.

Think of it as a domain-and-architecture opinion layer on top of superpowers. If superpowers is "how", AI Forging is "what you're building and how it should be shaped."

## Upgrading

The plugin code itself updates when you pull a new version from the marketplace. But the artifacts that `/aiforging:setup` *copied* into your workspace and target repos — conventions, skills, seeded patterns — are frozen at the version they were installed at. Two paths to get them current:

### Light upgrade (recommended)

Update the plugin at the machine level, then propagate the changes.

**Step 1 — find out what you actually have.** Updating an installed plugin is a *shell* command, not a slash command — there is no `/plugin update` — and it needs two details that vary per user. Run this in your terminal:

```bash
claude plugin list
```

```
Installed plugins:
  ❯ aiforging@aiforging          ← the marketplace you installed from
    Version: 0.2.0
    Scope: project               ← the scope you installed at
    Status: ✔ enabled
```

Note the **marketplace** (after the `@`) and the **scope**. You need both in step 2.

> **Expect `Scope: project`.** `/aiforging:setup` writes plugin enablement into your *project's* `.claude/settings.json` — that's how teammates who clone the repo get the plugin activated without touching their personal config. The side effect is that `aiforging` (and `superpowers`) usually end up installed at **project** scope, not user scope. Since `claude plugin update` defaults to `--scope user`, omitting the scope gives you:
>
> ```
> ✘ Failed to update plugin "aiforging@aiforging": Plugin "aiforging" is not installed at scope user
> ```
>
> That message means "wrong scope," not "not installed." Pass the scope `claude plugin list` reported.

**Step 2 — update the marketplace, then the plugin.** Substitute the marketplace and scope from step 1:

```bash
# Typical case — installed from this repo's marketplace, at project scope.
# Run from inside the repo/workspace where it's installed:
claude plugin marketplace update aiforging
claude plugin update aiforging@aiforging --scope project

# If you installed from Anthropic's official marketplace instead:
claude plugin marketplace update claude-plugins-official
claude plugin update aiforging@claude-plugins-official --scope project

# If plugin list said "Scope: user", drop the flag (user is the default).
```

The marketplace refresh comes first because it updates the *catalog*; the second command updates the *plugin*.

You may be able to skip both: marketplaces can auto-update installed plugins in the background at startup. That is **on by default for `claude-plugins-official`** and **off by default for third-party marketplaces** like this one — so if you installed from `aiforging/aiforging`, you almost certainly need to run the commands above. You can toggle it per marketplace under `/plugin` → Marketplaces.

Re-run `claude plugin list` afterwards and confirm the version actually moved. An update that silently no-ops is the failure mode that wastes the most time next.

> **Nothing in your repo will have changed yet, and that is correct.** Plugin code lives in Claude Code's own cache (`~/.claude/plugins/cache/...`) no matter which scope you installed at — project scope controls registration, not file location. The `.aiforging/` directories in your workspace and targets are *copies* made at onboarding time, and nothing but step 3 ever touches them. If `git status` is empty after step 2, the update worked.

You can see the resulting drift directly. After updating to a version that added a convention, the plugin has it and your repo does not:

```bash
ls .aiforging/tdd/          # 0.2.0 install: no feature-test-suite.md
```

Closing that gap is step 3's entire job.

**Step 3 — propagate to your workspace and targets.** Start Claude from your forge workspace and run:

```
/aiforging:update-targets
```

If the install summary asked you to run `/reload-plugins`, do that first (and re-run it as `/reload-plugins --force` if it warns about re-reading the conversation).

> **Upgrading from v0.2.0, or from an older workspace?** This path is newly manifest-driven and has had limited real-world mileage. If you run it, `CONTRIBUTING.md` has a short [checklist of what to verify afterwards](CONTRIBUTING.md#testing-the-upgrade-path) — seven checks, three of them about what must *not* have changed — and a field-report template. A clean run is as useful to hear about as a broken one.

`/aiforging:update-targets` diffs every copied artifact (conventions, skills, seeded patterns) against the new plugin version and asks before overwriting. Your user-captured patterns and everything under `docs/features/` — specs, plans, `testing.md` checklists, and the `ai-testing/` and `ai-reviews/` run records — are never touched. This is the right choice for minor version bumps and incremental improvements, and it is the intended path for every upgrade — including v0.2.0 → v0.3.1.

Since v0.3.0 the command is **manifest-driven**: it reads `.claude-plugin/artifacts.json` rather than a list baked into the command file. New artifacts therefore propagate to existing workspaces automatically, including into targets onboarded several versions ago — an artifact whose `since` is newer than what you have installed is presented as an *offer* with an explanation, not a silent install. Optional artifacts you previously declined stay declined unless you opt in.

Since v0.3.1 it also reads `.aiforging/VERSION` — a stamp recording which release your copies came from — so it can tell *the plugin changed this file* from *you changed this file*, rather than inferring it. Workspaces onboarded before 0.3.1 have no stamp; the command falls back to inference, says so, and defaults anything that looks customized to skip rather than overwrite.

### Clean reinstall (for major upgrades or a fresh start)

If you're jumping across major versions, or if your setup feels tangled from experimental changes, a clean reinstall is the safest path:

```
# 1. In Claude, from your forge workspace — remove all plugin artifacts
#    (preserves your feature specs and user-captured patterns):
/aiforging:uninstall
```

```bash
# 2. In your terminal — update the plugin. Substitute the marketplace and
#    scope that `claude plugin list` reports (see Steps 1-2 above; project
#    scope is the common case for AI Forging users):
claude plugin marketplace update aiforging
claude plugin update aiforging@aiforging --scope project
```

```
# 3. Back in Claude — re-bootstrap from scratch:
/aiforging:setup
```

The uninstall is designed to preserve your work: `docs/features/` (all your specs and plans), user-captured patterns (anything without `seeded: true` in frontmatter), and customized template files (it asks before removing those). After the reinstall, your workspace will have the latest conventions and skills, and your existing feature history is still there.

**What you'll need to redo after a clean reinstall:** the scenario interview (multi-repo / monorepo / single-repo), target onboarding for each repo or sub-project, and the architecture analyzer run. The setup command walks you through all of this interactively — it's the same flow as the first time, just faster because your repos haven't changed.

## Governance

**AI Forges. Humans decide.** Four human gates, always — checkpoints on completed work, not per-step sign-offs:

1. Review the tests — do they capture your intent? (At feature completion, not one test at a time.)
2. Code review at the PR level.
3. Architecture decisions (which refactors to run, which patterns to add).
4. Deployment authorization.

No autonomous deployment. No silent refactoring. Every proposal goes to a human before a merge happens.

Two of the framework's rules exist specifically to keep those gates real rather than ceremonial:

- **`browser-testing` never fixes what it finds.** A step that fails in the browser means the product and the specification disagree — it says nothing about which one is wrong, and an auto-fixer would cement the wrong assumption *and* produce a green checklist attesting to it. Every finding goes to a conversation first.
- **Nothing here runs your full test suite.** Every agent's test run is scoped to the feature's own suite, which is what keeps the loop fast. That trades a real risk — a cross-feature regression a scoped run cannot see — so the skills stop at the end of implementation and hand the full suite back to you explicitly, every time.

## Status

**v0.3.1 — open source, MIT licensed.** The plugin structure, conventions library, two-phase `/aiforging:setup`, and five skills (`architecture-analyzer`, `hammer-refactor`, `capture-pattern`, `browser-testing`, `review-loop`) are in place and have been dogfooded against real production codebases by the author and by external testers. Symfony / PHP / Doctrine is the happy path; other stacks work to the extent that the conventions apply — which is substantial, but mileage will vary until dedicated adapters ship.

### What's new

**v0.3.1** — six fixes from the first real-world run of `/aiforging:update-targets` against a production monorepo. The upgrade path passed every correctness check and surfaced six defects the pre-release audit could not have found, because each was a claim about the outside world rather than about the repo itself. Highlights: the workspace marker check no longer fails on a customized `CLAUDE.md`; `/aiforging:setup` can no longer clobber an existing `.gitignore`; pattern tiers survive git; and `.aiforging/VERSION` now records which release your copies came from. See `CHANGELOG.md`.

### What was new in v0.3.0

See `CHANGELOG.md` for the full entry.

- **Two optional post-implementation skills.** `browser-testing` walks a feature's `testing.md` in a real browser, marks the items only a human can judge, records one line of evidence per step, and reports what diverged **without fixing anything**. `review-loop` runs rounds of review → triage → fix across every repo a feature touched, with a triage step, a real stop condition, and convergence rules so the loop terminates. Both are workspace-level and both are optional.
- **The feature test suite rule.** One named test suite per feature, registered before the first test and augmented by every later work item. No agent — Fire, Hammer, or fix — ever runs the full repository suite. The convention names the regression risk that trades against, and makes the full-suite handoff to the human a mandatory, spoken step rather than a footnote.
- **`testing.md`, `overview.md`, and `summary.md`.** The feature-folder convention now specifies all three: a UI-driven QA checklist required for any feature with a UI surface (and the required input to `browser-testing`), the work-item umbrella for nested features, and an optional post-implementation snapshot for features with three or more work items. `/aiforging:new-feature` scaffolds `testing.md` from a template, or records why the feature does not need one.
- **An artifact manifest.** `.claude-plugin/artifacts.json` describes every artifact the plugin copies out of itself — destination, scope, applicable target roles, and update policy. `/aiforging:setup`, `/aiforging:update-targets`, and `/aiforging:uninstall` all read it instead of carrying their own hardcoded lists, which is what previously let a new artifact install on fresh setups and never reach existing users.
- **The workflow diagram** now shows the optional verification stages, the concurrency between machine and human browser testing, and the final full-suite gate.

Existing workspaces pick all of this up through `/aiforging:update-targets` — see [Upgrading](#upgrading). Nothing in `docs/features/` is touched.

### Shipped earlier

- `/aiforging:new-feature <name> <prompt>` (aliased `/aiforging:forge`) — scaffolds `docs/features/<name>/` and hands off to `superpowers:brainstorming`. Works from any directory via the run-anywhere pointer file (`~/.claude/aiforging.json`).
- `/aiforging:update-targets` — propagates plugin updates into previously onboarded targets with diff-and-ask semantics.
- `/aiforging:uninstall` — clean removal of plugin artifacts while preserving your feature folders and captured patterns.
- **Two-tier pattern library** — a shared tier at workspace level with `applies-to` frontmatter, plus a target-local tier per repo. `hammer-refactor` merges both; `capture-pattern` asks which tier at capture time.
- **Workspace-as-role** — setup adapts to multi-repo, monorepo, and single-repo layouts via a scenario interview.
- **Monorepo and service-wrapper detection** — `detect-project.py` recurses into child directories and recognizes Dockerized layouts where framework code sits in a subdirectory, so `.aiforging/` lands at the service boundary.

### Not yet shipped

- `/aiforging:execute-plan` — walks a workspace feature plan with per-step approval gates via `superpowers:executing-plans` and `superpowers:subagent-driven-development`.
- Dedicated stack adapters for Laravel, Spring/Java, .NET/C#, Node/TS.
- A community marketplace of user-contributed patterns.

The most useful contribution right now is still the same: run it on a real codebase and open an issue about what broke. See `CONTRIBUTING.md`.

## Author

[Chris Holland](https://linkedin.com/in/chrisholland) — the guy who [coined](https://www.linkedin.com/feed/update/urn:li:activity:7445936135371083776/?originTrackingId=j81PqnmwyBMk4rNkIUCzbQ%3D%3D) "AI Forging" as a counterpoint to vibe coding.

- Website: [aiforging.dev](https://aiforging.dev)

## License

MIT. See `LICENSE`.

## Acknowledgments

- [Jesse Vincent](https://github.com/obra) and the contributors to [`superpowers`](https://github.com/obra/superpowers) for the TDD, plan-writing, plan-execution, and subagent-dispatch skills that AI Forging builds on.
- [Srdjan Vranac](https://github.com/vranac) for [`claude-session-export-obsidian`](https://github.com/vranac/claude-session-export-obsidian), which served as the structural reference for this plugin.

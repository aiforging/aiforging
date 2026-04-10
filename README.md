# AI Forging

> A structured AI-assisted development framework for producing robust, maintainable codebases. Test-first, pattern-driven refactoring, domain-driven architecture — shipped as a Claude Code plugin.

AI Forging is a counterpoint to "vibe coding." The thesis: AI is incredibly powerful at generating code, but without structure, every feature shipped makes the codebase worse. AI Forging provides that structure as three stages of a metallurgical forge: **Fire → Hammer → Tempering.**

- **Fire** — AI-powered TDD. Tests are written first and capture intent before a single line of implementation exists. Red, Green, Refactor. *Uses the [`superpowers` plugin](https://github.com/obra/superpowers)'s `test-driven-development` skill.*
- **Hammer** — Automated pattern-driven refactoring. The `hammer-refactor` skill dispatches one fresh-context subagent per pattern or anti-pattern file against the session's changed files, in parallel. *Built on top of `superpowers:subagent-driven-development`.*
- **Tempering** — Scalable knowledge capture. The `capture-pattern` skill watches for corrective moments during interactive code review and offers to persist the lesson as a new `.md` file in the pattern library. One correction, one file. Adding the 50th pattern costs no more than the 5th, because every pattern lives in its own file and gets its own subagent on every Hammer pass.

Each iteration through the cycle leaves the codebase stronger than it started.

## Who this is for

Software crafters with **established codebases** who already feel the pain of AI-generated sprawl and are ready to adopt an opinionated workflow. Teams whose backends are built around a Data Mapper ORM (Doctrine, Hibernate, Entity Framework Core, TypeORM, MikroORM) will get the most value out of the box. Teams on Active Record stacks (Eloquent, Rails) can still adopt the framework with caveats documented in the conventions.

AI Forging is **not for greenfield projects** in v0.1.0. A separate `/aiforging:new-project` command may come later. It is also **not descriptive** — it is prescriptive, and it will tell you to refactor things. That's the point.

## The three-layer model

AI Forging deliberately separates three locations with different lifecycles:

1. **The plugin itself** — installed once per machine from a marketplace. Holds the conventions library, skills, helper scripts, and the `/aiforging:setup` command. You never clone or edit this.
2. **Your forge workspace** — a directory you create (e.g., `~/forge`) that orchestrates cross-repo feature work. Bootstrapped by `/aiforging:setup` Phase A. Holds your central `docs/features/<name>/spec.md` + `plan.md` files, a committed `.claude/settings.json` with `enabledPlugins`, a gitignored `.claude/settings.local.json` with per-user `permissions.additionalDirectories`, and the workspace-level `capture-pattern` skill for feedback loops that span repos. Designed to become its own git repository so feature history accumulates over time.
3. **Your target repos** — the codebases being forged. Each is onboarded to a forge workspace via `/aiforging:setup` Phase B. Gets a committed `.aiforging/` (conventions library + pattern/anti-pattern seed + `ANALYSIS.md` snapshot + per-repo `CLAUDE.md` pointer) and, for backend/fullstack repos, committed `.claude/skills/hammer-refactor/` and `.claude/skills/capture-pattern/` so any teammate who clones the repo gets the full toolkit without having to install the aiforging plugin on their machine.

The split keeps the plugin shareable, each workspace personal, and each target repo self-contained.

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

Create an empty directory anywhere you'd like your forge workspace to live, and run `/aiforging:setup` from inside it:

```
mkdir ~/forge
cd ~/forge
claude
# then, inside Claude Code:
/aiforging:setup
```

This runs **Phase A — init-workspace**. It:

1. Verifies `superpowers` is installed at the machine level.
2. Seeds `CLAUDE.md`, `README.md`, `docs/features/README.md`, and a `.gitignore` into the workspace.
3. Creates a committed `.claude/settings.json` with `enabledPlugins` for `superpowers` and `aiforging` — so anyone (including you) who runs Claude Code in this directory gets both plugins auto-activated.
4. Creates a gitignored `.claude/settings.local.json` for your per-user `permissions.additionalDirectories`.
5. Copies the `capture-pattern` skill into the workspace's own `.claude/skills/` so cross-repo Tempering works during workspace sessions.
6. Offers to `git init` the workspace and stage an initial commit.
7. Offers to immediately onboard your first target project (which runs Phase B — see next section).

### 3. Onboard a target repo

From the same workspace, either continue into Phase B at the end of the Phase A run or re-run `/aiforging:setup` at any later time to onboard another target. This runs **Phase B — onboard-project**. It:

1. Detects the target's stack (Symfony/Doctrine, React/TS/Playwright, etc.) and confirms whether it's backend, frontend, fullstack, or a meta-repo.
2. Registers the target's absolute path in the workspace's `settings.local.json`.
3. Writes `enabledPlugins` into the *target repo's* own `.claude/settings.json` so teammates who clone the target get `superpowers` + `aiforging` auto-activated without touching their personal config.
4. Copies the conventions library into `<target>/.aiforging/` (architecture, tdd) plus a per-repo `CLAUDE.md` pointer.
5. For backend / fullstack targets, offers to install the `hammer-refactor` + `capture-pattern` skills as a bundle into `<target>/.claude/skills/` so anyone cloning the target repo can run them directly.
6. Seeds `<target>/.aiforging/patterns/` and `<target>/.aiforging/anti-patterns/` with the core AI Forging library as a starting point.
7. Runs the `architecture-analyzer` skill against the target and writes a structured `.aiforging/ANALYSIS.md` report with a score and prioritized findings.
8. Optionally installs the Playwright-oriented frontend testing convention for frontend / fullstack targets.
9. Optionally drafts a feature folder at `<workspace>/docs/features/<feature-name>/` with a `spec.md` and a `plan.md` (in the AI Forging slice format) based on the analyzer's findings.
10. Stages a follow-up git commit in the workspace capturing the onboarding.

Phase B is re-runnable. Each re-run adds another target to the same workspace.

**`/aiforging:setup` will never execute any refactors.** The v0.1.0 boundary is explicit: install + analyze + propose plan. Running the actual Hammer pass is a separate, explicit step via the `hammer-refactor` skill once a plan has been approved. A future `/aiforging:execute-plan` command will orchestrate plan execution with per-step approval gates.

### A note on "install vs enable"

Claude Code keeps these two operations separate, and the distinction matters when teammates clone your workspace or a target repo:

- **Installing** a plugin (`/plugin install …`) downloads its code to `~/.claude/plugins/` on that machine. This is one-time per machine.
- **Enabling** a plugin in a scope writes `{ "enabledPlugins": { "pluginname@source": true } }` into that scope's `.claude/settings.json`. This is what `/aiforging:setup` does automatically for your workspace and for each onboarded target repo.

The enablement block is identifier-based — it *points at* a plugin but doesn't contain the plugin's code. A teammate who clones a target repo inherits its `enabledPlugins` block for free, but they still need to run the machine-level `/plugin install` steps once before Claude Code can actually activate those plugins. Give teammates the same install block from the top of this section and everything else is automatic.

## What's in the plugin

```
aiforging/
├── .claude-plugin/                 # plugin manifest + marketplace definition
├── commands/
│   └── setup.md                    # /aiforging:setup (Phase A + Phase B)
├── scripts/                        # PEP 723 single-file Python scripts (run under uv or python3)
│   ├── detect-project.py           #   read-only stack detection
│   ├── configure-directories.py    #   manages permissions.additionalDirectories
│   └── configure-plugins.py        #   manages enabledPlugins
├── skills/
│   ├── architecture-analyzer/      # non-destructive advisory analysis, runs from workspace
│   │   └── SKILL.md
│   ├── hammer-refactor/            # executable Hammer stage, copied into each target repo
│   │   └── SKILL.md
│   └── capture-pattern/            # reactive Tempering feedback loop
│       └── SKILL.md                #   installed in both workspace and each target repo
├── templates/                      # bootstrap templates for forge workspace init (Phase A)
│   ├── workspace-CLAUDE.md
│   ├── workspace-README.md
│   └── docs-features-README.md
└── conventions/                    # library copied into each target repo as .aiforging/
    ├── CLAUDE.md.template          #   per-target CLAUDE.md pointer
    ├── features/                   #   feature-folder + slice-plan convention
    ├── architecture/               #   Domain-Driven Hexagonal, Single-Action Controllers, Repositories, DTOs, Naming
    ├── tdd/                        #   Fire loop (delegates to superpowers), harness capability contract, repository testing
    ├── refactoring/                #   Hammer pattern library + Tempering feedback format
    │   ├── patterns/               #     one file per pattern
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
- The `capture-pattern` skill as the reactive Tempering feedback loop that grows the library one code review at a time.
- An optional Playwright convention layer for frontend integration tests.
- A cross-repo forge workspace model with a central `docs/features/<name>/spec.md + plan.md` convention, so features that touch multiple repos have one place to plan and track them.

Think of it as a domain-and-architecture opinion layer on top of superpowers. If superpowers is "how", AI Forging is "what you're building and how it should be shaped."

## Governance

**AI Forges. Humans decide.** Four human gates, always:

1. Test review and approval.
2. Code review at the PR level.
3. Architecture decisions (which refactors to run, which patterns to add).
4. Deployment authorization.

No autonomous deployment. No silent refactoring. Every proposal goes to a human before a merge happens.

## Status

v0.1.0 — **research preview.** The plugin structure, conventions library, two-phase `/aiforging:setup` command, and the three skills (`architecture-analyzer`, `hammer-refactor`, `capture-pattern`) are all in place and have been dogfooded against a real backend target. The Symfony/PHP/Doctrine stack is the happy path; other stacks work to the extent that the conventions apply (which is substantial, but mileage will vary until we ship dedicated adapters).

**Not yet shipped:**

- `/aiforging:execute-plan` — walks through a workspace feature plan with per-step approval gates via `superpowers:executing-plans` and `superpowers:subagent-driven-development`.
- `/aiforging:update-targets` — propagates plugin-level updates (new skills, new patterns) into previously onboarded target repos.
- `/aiforging:new-feature <name>` — scaffolds `docs/features/<name>/` and hands off to `superpowers:brainstorming`.
- `/aiforging:propose-pattern` — promotes a pattern captured in one target's `.aiforging/` back into the plugin's core library so future onboards start with it.
- Dedicated stack adapters for Laravel, Spring/Java, .NET/C#, Node/TS.
- `/aiforging:new-project` — greenfield scaffolding with stack templates.
- A community marketplace of patterns contributed by users.

Contributions welcome once the extension-point contracts stabilize — for now, the best way to contribute is to try it on a real codebase and open issues about what broke.

## Author

Chris Holland — VP of Software Development at CertainPath, the guy who coined the term as a counterpoint to vibe coding.

- Website: [aiforging.dev](https://aiforging.dev)
- LinkedIn: [linkedin.com/in/chrisholland](https://linkedin.com/in/chrisholland)

## License

MIT. See `LICENSE`.

## Acknowledgments

- [Jesse Vincent](https://github.com/obra) and the contributors to [`superpowers`](https://github.com/obra/superpowers) for the TDD, plan-writing, plan-execution, and subagent-dispatch skills that AI Forging builds on.
- [Srdjan Vranac](https://github.com/vranac) for [`claude-session-export-obsidian`](https://github.com/vranac/claude-session-export-obsidian), which served as the structural reference for this plugin.

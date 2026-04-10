# AI Forging

> A structured AI-assisted development framework for producing robust, maintainable codebases. Test-first, pattern-driven refactoring, domain-driven architecture — shipped as a Claude Code plugin.

AI Forging is a counterpoint to "vibe coding." The thesis: AI is incredibly powerful at generating code, but without structure, every feature shipped makes the codebase worse. AI Forging provides that structure as three stages of a metallurgical forge: **Fire → Hammer → Tempering.**

- **Fire** — AI-powered TDD. Tests are written first and capture intent before a single line of implementation exists. Red, Green, Refactor. *Uses the [`superpowers` plugin](https://github.com/obra/superpowers)'s `test-driven-development` skill.*
- **Hammer** — Automated pattern-driven refactoring. One fresh-context subagent per pattern or anti-pattern file, dispatched in parallel against the session's changed files. *Uses `superpowers:subagent-driven-development`.*
- **Tempering** — Knowledge capture. New patterns and anti-patterns observed during work get captured into the pattern library, one `.md` file per pattern, reviewed independently. Adding the 50th pattern costs no more than the 5th.

Each iteration through the cycle leaves the codebase stronger than it started.

## Who this is for

Software crafters with **established codebases** who already feel the pain of AI-generated sprawl and are ready to adopt an opinionated workflow. Teams whose backends are built around a Data Mapper ORM (Doctrine, Hibernate, Entity Framework Core, TypeORM, MikroORM) will get the most value out of the box. Teams on Active Record stacks (Eloquent, Rails) can still adopt the framework with caveats documented in the conventions.

AI Forging is **not for greenfield projects** in v0.1.0. A separate `/aiforging:new-project` command may come later. It is also **not descriptive** — it is prescriptive, and it will tell you to refactor things. That's the point.

## Installation

AI Forging is a Claude Code plugin. It depends on the `superpowers` plugin for TDD and plan-writing skills, so install that first.

```
# In your Claude Code CLI:
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-dev

/plugin marketplace add aiforging/aiforging
/plugin install aiforging@aiforging
```

Then, from a directory that contains (or is adjacent to) the projects you want to drive with the framework:

```
/aiforging:setup
```

The setup command is interactive. It will:

1. Check that `superpowers` is installed. If it isn't, walk you through installing it.
2. Detect every project directory nearby and identify each as backend / frontend / fullstack / meta.
3. Interview you to confirm which projects you actually want to drive with AI Forging, with room to add directories the detector missed.
4. Add those directories to `permissions.additionalDirectories` in your chosen Claude Code settings file (user, project, or local).
5. Install the conventions library into each confirmed backend project as `.aiforging/`.
6. Run the `architecture-analyzer` skill against each project, producing a non-destructive `.aiforging/ANALYSIS.md` report with a score and prioritized findings.
7. Generate a `.aiforging/PROPOSED_PLAN.md` describing a refactor path broken into small reviewable steps.
8. (Optional) Install the Playwright-oriented frontend testing layer if you have frontend projects.
9. Summarize what was installed and what to do next.

**Setup will not execute any refactors.** The v0.1.0 boundary is explicit: install + analyze + propose plan. A future `/aiforging:execute-plan` command will drive the spec/plan/execute workflow with per-step approval gates.

## What's in the plugin

```
aiforging/
├── .claude-plugin/          # plugin manifest + marketplace
├── PLAN.md                  # persistent plan & session log (read this first if resuming)
├── commands/
│   └── setup.md             # /aiforging:setup
├── scripts/
│   ├── detect-project.py    # read-only stack detection
│   └── configure-directories.py  # manages permissions.additionalDirectories
├── skills/
│   └── architecture-analyzer/
│       └── SKILL.md         # the advisory analysis pass
└── conventions/             # the library copied into each target project as .aiforging/
    ├── architecture/        # Domain-Driven Hexagonal, Single-Action Controllers, Repositories, DTOs, Naming
    ├── tdd/                 # Fire loop (delegates to superpowers), harness capability contract, repository testing
    ├── refactoring/         # Hammer + Tempering stages, starter patterns and anti-patterns
    └── frontend-testing/    # Optional Playwright layer
```

## Relationship to the `superpowers` plugin

AI Forging deliberately delegates core skills to `superpowers`:

- `superpowers:test-driven-development` — the Red/Green/Refactor loop.
- `superpowers:brainstorming` — spec-before-code dialogue.
- `superpowers:writing-plans` — plan generation.
- `superpowers:executing-plans` — plan execution with checkpoints.
- `superpowers:subagent-driven-development` — fresh-context subagent dispatch.

AI Forging adds what superpowers intentionally leaves to each team's architecture:

- A prescriptive, domain-centric folder layout.
- Single-action controllers, data-mapper Repositories, Value Objects / DTOs, naming rules.
- The **test-harness capability contract** that makes the Fire stage trustworthy for data-driven code.
- A pattern / anti-pattern library structured for fresh-context subagent refactor passes.
- The `architecture-analyzer` skill for advisory audits.
- An optional Playwright convention layer for frontend integration tests.

Think of it as a domain-and-architecture opinion layer on top of superpowers. If superpowers is "how", AI Forging is "what you're building and how it should be shaped."

## Governance

**AI Forges. Humans decide.** Four human gates, always:

1. Test review and approval.
2. Code review at the PR level.
3. Architecture decisions (which refactors to run, which patterns to add).
4. Deployment authorization.

No autonomous deployment. No silent refactoring. Every proposal goes to a human before a merge happens.

## Status

v0.1.0 — **research preview.** The plugin structure and core conventions are in place. The architecture-analyzer skill is written as an instruction set but has not been exercised against a large variety of real codebases. The Symfony/PHP/Doctrine stack is the happy path; other stacks work to the extent that the conventions apply (which is substantial, but mileage will vary until we ship dedicated adapters).

**Not yet shipped:**

- `/aiforging:execute-plan` — takes a `PROPOSED_PLAN.md` and walks the user through execution with superpowers' `executing-plans` and `subagent-driven-development` skills.
- Dedicated stack adapters for Laravel, Spring/Java, .NET/C#, Node/TS.
- `/aiforging:new-project` — greenfield scaffolding with stack templates.
- A community marketplace of patterns contributed by users.

See `PLAN.md` for the current state of the build and the session log. Contributions welcome once the extension-point contracts stabilize — for now, the best way to contribute is to try it on a real codebase and open issues about what broke.

## Author

Chris Holland — VP of Software Development at CertainPath, the guy who coined the term as a counterpoint to vibe coding.

- Website: [aiforging.dev](https://aiforging.dev)
- LinkedIn: [linkedin.com/in/chrisholland](https://linkedin.com/in/chrisholland)

## License

MIT. See `LICENSE`.

## Acknowledgments

- Jesse Vincent and the contributors to [`superpowers`](https://github.com/obra/superpowers) for the TDD and subagent-dispatch skills that AI Forging builds on.
- Srdjan Vranac for [`claude-session-export-obsidian`](https://github.com/vranac/claude-session-export-obsidian), which served as the structural reference for this plugin.

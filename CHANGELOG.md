# Changelog

All notable changes to the AI Forging plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-09-03

Verification stages, scoped test suites, and a manifest so future additions actually reach existing users.

This release adds the two stages that come *after* the forge — checking the running product, and reviewing the diff — and formalizes a test-scoping discipline that had been carried informally in project instructions. It also fixes the structural reason earlier improvements could strand existing users.

### Added

- **`browser-testing` skill** (`/aiforging:browser-testing`). Walks a feature's `testing.md` in a real browser against a local or explicitly-named QA environment. Marks the checklist items only a human can produce a *believable* verdict on (👤) inline so the human can work those in parallel, walks the rest, records one line of plain-text evidence per step, and writes a numbered run record to `docs/features/<feature>/ai-testing/NN/`.

  **It fixes nothing, and that is the point.** A step that fails in the browser is evidence that the product and the specification disagree; it is not evidence about which of them is wrong. An auto-fixer would cement the wrong assumption *and* produce a green checklist attesting to it. Every finding goes to `escalations.md` and to a human conversation. The skill also refuses to run without a `testing.md` rather than inventing one — a run against a guessed checklist tests whatever the machine imagined.

  Workspace-scoped: its required input and its output both live in the feature folder, and it orchestrates across every implicated target.

- **`review-loop` skill** (`/aiforging:review-loop`). Rounds of review → triage → fix across every repo a feature touched, replacing the manual cycle of running reviews in separate terminals and pasting output back. One read-only review subagent per repo in parallel; fixes serialized per repo; findings triaged against the source *before* acceptance; classification by change class (green / amber / red) rather than by felt confidence, because a confident agent is exactly the one that does not ask.

  Includes convergence rules — prior triage verdicts are a required input to every review agent — so the loop terminates instead of re-litigating settled decisions. Stops on a real stop condition rather than a finding count or a severity trend; both were tried and both misled. Writes `docs/features/<feature>/ai-reviews/NN/`.

  Runs **after** `browser-testing`, deliberately: review rounds can run to exhaustion on a diff while a behavioral defect sits untouched in the most-used screen, and the cheapest moment to reverse a wrong decision is before more work is built on it.

- **`conventions/tdd/feature-test-suite.md`** — the scoped-test-suite convention. One named test suite per **feature**, registered before the first test is written and augmented by every later work item; that suite, and only that suite, runs during Fire, Hammer, and any fix agent. Includes per-stack registration syntax, the four places the rule has to be repeated to reach a fresh-context subagent, and an explicit statement of the regression risk the framework accepts in exchange for a fast loop.

- **`testing.md` in the feature-folder convention** — a UI-driven QA checklist required for every feature with a UI surface, covering access and gating, the happy path, and key edge cases, in that order. One per feature (never one per work item), ordered by work item in the nested shape, written *before* implementation ends so it describes what was supposed to be built rather than what was. Research-only work and purely internal changes may skip it, but the decision is recorded in the spec rather than silently omitted.

- **`summary.md` in the feature-folder convention** — an optional post-implementation snapshot for features with three or more work items: work-item table, what was built, what was deferred and why, architecture highlights. Written after implementation, never before.

- **`templates/feature-testing.md`** — the `testing.md` skeleton, copied per-feature by `/aiforging:new-feature`.

- **A typeable command for every user-invocable skill.** `/aiforging:browser-testing`, `/aiforging:review-loop`, `/aiforging:hammer-refactor`, and `/aiforging:capture-pattern` are now thin command pointers at their skills, following the same one-source-of-truth pattern as `/aiforging:forge`. The last two closed a documentation bug rather than adding a capability: `/aiforging:setup` had been telling users for two releases that they could invoke `hammer-refactor` and `capture-pattern` as commands, and they could not. Each pointer holds no rules of its own — it reads the SKILL.md and follows it, so the skill and the command can never drift.

- **Frontmatter on `/aiforging:update-targets` and `/aiforging:uninstall`**, which previously had none and so appeared in the command list without a description.

- **`.claude-plugin/artifacts.json`** — a manifest of every artifact the plugin copies out of itself: source path, destination per scope, applicable target roles, whether it is optional, and its update policy (`diff-and-ask`, `offer-default-no`, `seeded-only`, `create-if-missing`, `never`), plus a `user_owned` list nothing may touch.

- **`CONTRIBUTING.md`** — how to propose a pattern, a convention, or a stack adapter, and the dogfooding loop for plugin development.

### Changed

- **Nothing runs the full test suite any more — and the handoff to the human is now a spoken step.** The Fire convention, the subagent-orchestration prompt templates (all four), and the `hammer-refactor` skill all now scope every run to the feature's named suite and refuse to widen it without asking. In exchange, `hammer-refactor`, `browser-testing`, and `review-loop` each end by telling the user, in words, that every run was scoped, what that means for cross-feature regressions, and which command to run themselves before opening a PR. Previously the full-suite run was described as an optional final "recommendation," which is exactly the kind of note that gets skipped when a pass went well.

- **`plan.md` now carries the test-scoping rule.** Every plan opens with a `## Test suite` block naming the suite and its exact run command, and every slice's subagent prompt repeats the scoped-run instruction verbatim. The repetition is deliberate: a fresh-context subagent reads the slice it was handed, and "run everything to prove I'm done" is the strongest default an agent has.

- **`/aiforging:update-targets` is manifest-driven.** It previously carried a hardcoded list of skills and convention directories, which meant every new artifact required editing the command — and forgetting to meant the artifact installed on fresh setups but never propagated to existing users, silently. It now reads `artifacts.json`, treats anything whose `since` is newer than the installed version as an *offer* with an explanation rather than a silent install, and reports what changed in **behavior**, not just which files changed. `/aiforging:setup` and `/aiforging:uninstall` read the same manifest.

- **`/aiforging:new-feature` asks whether the feature has a UI surface** and scaffolds `testing.md` from the template if so — leaving the checklist items as placeholders, because the spec that produces them does not exist yet. If not, it records the reason in the spec. Its extension flow now keeps `testing.md` at the feature level when converting a flat feature to the nested shape, rather than moving it into a work item.

- **`/aiforging:setup` Phase A offers the two verification skills** (default Y) with an explanation of what each does. Declining is remembered for the run, and `/aiforging:update-targets` will offer them again later.

- **The feature-folder convention documents all six document roles** — spec, plan, overview, testing, summary, notes — plus the two machine-written run-record directories, with a table saying which are required, when each is written, and what job each has. The lifecycle now runs to eleven steps, including the two optional verification stages and the full-suite handoff.

- **`docs/feature-workflow.svg`** gained a VERIFY band showing `browser-testing` and the human's own browser pass running *concurrently*, `review-loop` after them, and a final human gate for the full test suite.

- **The Upgrading instructions actually work now.** The README told users to run `/plugin update aiforging@aiforging`, which is not a command — updating an installed plugin is a shell command (`claude plugin update`), and there is no slash form. It also omitted the marketplace refresh, assumed one of the two possible marketplace sources, and defaulted to user scope. That last one broke for essentially every AI Forging user: because `/aiforging:setup` writes plugin enablement into the *project's* settings, `aiforging` typically installs at **project** scope, and `claude plugin update` without `--scope project` fails with `Plugin "aiforging" is not installed at scope user` — a message that reads like "not installed" when it means "wrong scope." The section now starts by having you run `claude plugin list` to read off your own marketplace and scope, and explains that error explicitly.

- **The "research preview" label is retired.** The plugin is v0.3.0, open source, MIT licensed, and running against real production codebases. The README and the website say that instead.

### Notes for existing users

Run `/aiforging:update-targets` from your forge workspace. Everything in this release is additive:

- Nothing under `docs/features/` is read, moved, or modified — including existing specs, plans, and any `testing.md` you already wrote by hand.
- User-captured patterns (anything without `seeded: true` frontmatter) are untouched, in both tiers.
- The two new skills are **offered**, not installed. Declining is fine and the framework works without them.
- Features already in flight keep working. The scoped-suite rule and `testing.md` apply to features you plan from here on; retrofitting an in-flight feature is optional, and registering a suite for it is a two-minute change if you want the benefit early.

## [0.2.0] — 2026-04-23

First external feedback round — incorporating field testing from [Srdjan Vranac](https://github.com/vranac) who ran `/aiforging:setup` against a real Dockerized Symfony monorepo.

### Changed

- **Service wrapper detection in `detect-project.py`.** The detector now recognizes "service wrapper" directories — a common pattern in Dockerized projects where a service directory (e.g., `webapp/`) contains an `application/` subdirectory with the actual framework code, plus infrastructure directories like `docker/` and `bin/`. Previously, the detector would report `webapp/application/` as the project root, placing `.aiforging/` inside the app subdirectory instead of at the service boundary. Now, the detector reports the wrapper directory as the service root and records the app subdirectory in a new `app_subdir` field. Convention installation respects this boundary — `.aiforging/` lands at `webapp/.aiforging/`, not `webapp/application/.aiforging/`. ([Feedback #3])

- **Playwright convention onboarding no longer skipped when Playwright is already configured.** Previously, Step B.8 would silently skip the Playwright testing conventions if it detected an existing `playwright.config.ts`. This was backwards — an existing Playwright setup is evidence that the team uses Playwright, which makes the conventions *more* relevant, not less. Now, if Playwright is detected, the default flips to Y and the prompt explains that the conventions complement the existing setup. If Playwright is not detected, the default remains N. ([Feedback #4])

- **Global config consent (`~/.claude/aiforging.json`) is now opt-in with front-loaded explanation.** Step A.2.5 previously defaulted to Y for writing the run-anywhere pointer file to `~/.claude/aiforging.json`. Since this is the only step that writes outside the current working directory, the consent flow now leads with an explicit explanation of what will be written, where, and why — and defaults to N. Users who want run-anywhere support opt in deliberately; users who prefer cwd-only operation are not surprised by writes to global config space. ([Feedback #2])

- **Skill copy messaging in Step B.5 now explains the plugin-vs-repo distinction.** Users with the `aiforging` plugin installed already have `hammer-refactor` and `capture-pattern` available as plugin skills. The setup prompt now explicitly acknowledges this and explains that copying skills into the target repo is for teammate discoverability — ensuring anyone who clones the repo gets the skills automatically, even without the plugin installed. ([Feedback #1])

- **`hammer-refactor` now makes atomic git commits per refactor slice.** After each subagent completes a slice and tests pass, the skill commits the change with a descriptive message naming the pattern and target file. This gives a clean, individually-revertible history instead of one large uncommitted diff at the end.

- **Scoped test runs throughout the forge cycle.** Both Fire (TDD) and Hammer now prescribe running only the feature's test class or directory during the iterative loop — not the full repository suite. The full suite is recommended once at the end of Fire (before Hammer) and optionally after all Hammer slices complete, as a non-blocking final check. This keeps feedback loops fast on large codebases.

### Added

- `CHANGELOG.md` — this file.
- `app_subdir` field in `detect-project.py` output for service wrapper detection.

## [0.1.0] — 2026-04-13

Initial release. Built over five development sessions.

### Added

- Two-phase `/aiforging:setup` command (Phase A: init-workspace, Phase B: onboard-project).
- Three skills: `architecture-analyzer` (advisory analysis), `hammer-refactor` (executable Hammer stage), `capture-pattern` (reactive Tempering feedback loop).
- Conventions library: `architecture/`, `tdd/`, `subagent-orchestration/`, `refactoring/` (with seeded patterns), `frontend-testing/`.
- Four helper scripts: `detect-project.py`, `configure-directories.py`, `configure-plugins.py`, `configure-workspace-pointer.py`.
- `/aiforging:new-feature` and `/aiforging:forge` commands for daily-driver feature scaffolding.
- `/aiforging:update-targets` for propagating plugin updates to onboarded targets.
- `/aiforging:uninstall` for clean removal preserving user content.
- Two-tier pattern library (shared + target-local) with `applies-to` YAML frontmatter.
- Workspace-as-role model supporting multi-repo, monorepo, and single-repo scenarios.
- Monorepo sub-project detection via `detect-project.py` child recursion.
- Run-anywhere pointer file (`~/.claude/aiforging.json`) for commands that work from any directory.
- Templates for workspace bootstrapping (`workspace-CLAUDE.md`, `workspace-README.md`, `docs-features-README.md`).
- MIT license.

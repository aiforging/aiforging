# Changelog

All notable changes to the AI Forging plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-04-23

First external feedback round — incorporating field testing from [Srdjan Vranac](https://github.com/vranac) who ran `/aiforging:setup` against a real Dockerized Symfony monorepo.

### Changed

- **Service wrapper detection in `detect-project.py`.** The detector now recognizes "service wrapper" directories — a common pattern in Dockerized projects where a service directory (e.g., `webapp/`) contains an `application/` subdirectory with the actual framework code, plus infrastructure directories like `docker/` and `bin/`. Previously, the detector would report `webapp/application/` as the project root, placing `.aiforging/` inside the app subdirectory instead of at the service boundary. Now, the detector reports the wrapper directory as the service root and records the app subdirectory in a new `app_subdir` field. Convention installation respects this boundary — `.aiforging/` lands at `webapp/.aiforging/`, not `webapp/application/.aiforging/`. ([Feedback #3])

- **Playwright convention onboarding no longer skipped when Playwright is already configured.** Previously, Step B.8 would silently skip the Playwright testing conventions if it detected an existing `playwright.config.ts`. This was backwards — an existing Playwright setup is evidence that the team uses Playwright, which makes the conventions *more* relevant, not less. Now, if Playwright is detected, the default flips to Y and the prompt explains that the conventions complement the existing setup. If Playwright is not detected, the default remains N. ([Feedback #4])

- **Global config consent (`~/.claude/aiforging.json`) is now opt-in with front-loaded explanation.** Step A.2.5 previously defaulted to Y for writing the run-anywhere pointer file to `~/.claude/aiforging.json`. Since this is the only step that writes outside the current working directory, the consent flow now leads with an explicit explanation of what will be written, where, and why — and defaults to N. Users who want run-anywhere support opt in deliberately; users who prefer cwd-only operation are not surprised by writes to global config space. ([Feedback #2])

- **Skill copy messaging in Step B.5 now explains the plugin-vs-repo distinction.** Users with the `aiforging` plugin installed already have `hammer-refactor` and `capture-pattern` available as plugin skills. The setup prompt now explicitly acknowledges this and explains that copying skills into the target repo is for teammate discoverability — ensuring anyone who clones the repo gets the skills automatically, even without the plugin installed. ([Feedback #1])

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

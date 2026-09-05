# Changelog

All notable changes to the AI Forging plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] — 2026-09-04

**Teams.** The forge workspace was always meant to be a shared git repository the whole team clones — that is why feature specs, plans and review records live in files rather than in a chat transcript. The plugin never quite said so, and in one important respect never quite supported it.

### Added

- **`/aiforging:join`** — the flow for the second engineer onward. Clone a workspace a teammate created, run this, and it locates each target repo on your machine (offering to clone what you don't have), writes your own gitignored `settings.local.json`, verifies your plugin prerequisites, and shows you what the team is working on. It re-onboards nothing: the conventions and skills came with the clone.

- **`.aiforging/targets.json`** — a committed registry of which repos a workspace forges: name, git remote, role, stack. **This closes a real hole.** The target list previously existed *only* in `settings.local.json`, which is gitignored — correctly, since it holds absolute paths. So a workspace could be committed, pushed and cloned, and the person who cloned it had no way to discover what it forged. The workspace was shareable in principle and not in practice.

- **`/aiforging:resume` and the `resume-feature` skill** — pick up a feature you did not start. Reads the spec, plan, notes, QA checklist and any open review escalations, then reports what's done, what's next, what was deliberately deferred, and who last touched it. Read-only: it orients and stops, because on a shared workspace the plan in front of you is often someone else's and its decisions have reasons that may not be written down.

  Status comes from counting the plan's own checkboxes rather than from a status field. Nothing to remember to update, and it cannot disagree with the plan — because it *is* the plan.

- **`docs/features/INDEX.md`** — a generated table of every feature with status, last activity and a one-line summary, so a teammate can see what exists without opening nine spec files. Every column is derived from the feature folders and git; `resume-feature` rebuilds it on each run and self-heals folders that were created by hand.

### Changed

- **`/aiforging:setup` treats a workspace as shared by default.** git-init and an initial commit are the expected path rather than an offer to be talked into, and setup asks about a remote and explains what pushing buys. Solo use still works identically and is mentioned as a variation.

- **Setup routes a joiner away from Phase B.** If the workspace has a target registry but no `settings.local.json`, the user has cloned someone else's workspace — setup now says so and points at `/aiforging:join` instead of re-onboarding targets that already have their conventions, which would have produced an unwanted diff on shared files.

- **The README is 40% shorter and reorganized** around install → day-to-day → upgrade → remove, with the team model near the top. Removed: the "who this is for" section, the full plugin file tree, and most of the internal mechanics. The upgrade section went from a hundred lines to thirty, with starting-over folded into a collapsed block.

### Fixed

- **`aiforging@claude-plugins-official` does not exist**, and `/aiforging:setup` was writing it into `enabledPlugins` in three places — producing a block that looks correct and silently matches nothing. The correct identifier is `aiforging@aiforging`, from the plugin's own marketplace. (`superpowers@claude-plugins-official` is real and unchanged.) Setup now opens with a note on why the two plugins use different marketplace identifiers, and tells the reader to check `claude plugin list` rather than assume.

### Notes for existing users

`/aiforging:update-targets` as usual. New this version and offered, not installed silently: the `resume-feature` skill and the feature index.

**`.aiforging/targets.json` is not created retroactively.** A workspace onboarded before 0.4.0 has no registry, so `/aiforging:join` falls back to inferring targets from committed plans and `.aiforging/` directories, asks you to confirm, and offers to write the registry — after which the next person to join doesn't have to guess. Onboarding a new target with `/aiforging:setup` also creates it.

If you enabled the plugin before this release, check your workspace and target `.claude/settings.json` for `aiforging@claude-plugins-official` and change it to `aiforging@aiforging`.

## [0.3.2] — 2026-09-04

One regression fix. **If you are on 0.3.1, take this before running `/aiforging:update-targets`.**

### Fixed

- **Workspace detection now accepts both marker phrasings, and 0.3.1 broke one of them.** Two markers exist in the wild: `AI Forging workspace` (written by the current workspace template) and `AI Forging forge workspace` (written by earlier onboardings — some of those `CLAUDE.md` files explicitly instruct the reader to keep that exact phrase intact). **The short string is not a substring of the long one**, so `grep -q "AI Forging workspace"` silently misses every workspace carrying the older marker.

  0.3.1 narrowed `/aiforging:new-feature` to the short phrase only. That command had previously matched the long one and worked; after 0.3.1 it would report a genuine, long-running workspace as not-a-workspace and refuse to run. Every detection site now matches `grep -qE "AI Forging( forge)? workspace"`.

  This also corrects the diagnosis behind one of the 0.3.1 fixes. The first `/aiforging:update-targets` run reported `NO_CLAUDE_MD` and attributed it to the 500-byte `head -c` window; the real cause was the marker mismatch. Removing the byte window was still right — a customized `CLAUDE.md` can push any marker out of a fixed window — but it was not what had failed. **A plausible explanation for a real symptom is not the same as the cause**, and building a fix on an unverified diagnosis left the actual bug in place through a release.

- **Detection has a second signal now.** `docs/features/README.md` carries its own marker comment. If `CLAUDE.md`'s marker is absent but that file's is present and `.claude/settings.json` exists, the commands treat the directory as a workspace, offer to add the missing marker line, and continue instead of aborting. A workspace that has been working for months should not stop being one because of a phrasing change.

- **`templates/workspace-CLAUDE.md` now opens with a durable marker comment** naming both accepted phrasings and warning against removing them, so customizing the file cannot silently strip the thing that makes it recognizable.

## [0.3.1] — 2026-09-04

Six fixes from the first real-world run of `/aiforging:update-targets`.

v0.3.0 shipped with a manifest-driven upgrade path that had never been executed end to end. It was run the next day against a real monorepo (Symfony backend + React frontend, onboarded at v0.1.0, ten user-captured patterns, seven locally-customized convention files). **It passed every correctness check** — no user-owned file was modified, no file went missing, and a three-way merge preserved a hand-added cross-reference while taking the plugin's change to the same file.

It also surfaced six defects, none of which the pre-release audit could have found. Every finding that audit produced was a claim the repo made *about itself*. Every one of these is a claim about the outside world: what a customized `CLAUDE.md` looks like, what git does with empty directories, what an existing repo's `.gitignore` already contains, what a person reads when they are interrupted.

### Fixed

- **The workspace marker check had a false negative.** `head -c 500 ./CLAUDE.md | grep -q "AI Forging workspace"` reported a genuine workspace as not-a-workspace, because the user had customized the top of the file and pushed the marker past the window. The run reasoned around it; a more literal execution would have aborted with "run `/aiforging:setup` first." Workspace `CLAUDE.md` files are *meant* to be customized — `/aiforging:update-targets` itself treats them as "commonly customized" — so any fixed byte window is a bug waiting on a paragraph. Now greps the whole file, in `setup.md`, `update-targets.md`, `new-feature.md`, and `capture-pattern`.

- **`/aiforging:setup` could clobber an existing `.gitignore`.** It used `cat > ./.gitignore`, which is safe in Scenario A (new empty workspace) and destructive in Scenarios B and C, where the workspace *is* an existing repo that already has one. Now appends only the rules that are genuinely absent, matched whole-line and fixed-string, and never rewrites the file.

- **The `.gitignore` rules never reached existing users.** Seven `.bak-*` backups landed tracked-eligible because the workspace had `.claude/*.bak-*`, which matches neither nested paths nor the backups written into `.aiforging/` and `docs/`. The plugin had carried the correct `*.bak-*` rule for releases — but `.gitignore` was not in `artifacts.json`, so nothing propagated it. **That is precisely the failure mode the manifest was built to eliminate, reproduced by the manifest.** `.gitignore` is now a manifest entry with a new `append-missing-lines` policy; `update-targets` checks each required rule and offers to add what is missing. It also now offers to delete the backups once you have reviewed the diff.

- **Empty tier directories cannot survive git.** `update-targets` offered to create `fe/.aiforging/patterns/`, absent because it had never held a tracked file in the repository's entire history — `mkdir` alone produces a directory git will not store, so it vanishes on the next checkout and the offer recurs forever, for every teammate, on every run. Both tier directories are now seeded with a `README.md` explaining the two-tier model: git tracks it, the loop ends, and the explanation lands in the directory someone is about to write a pattern into. **Every pattern-library glob now excludes `README.md`** — in `hammer-refactor`, `capture-pattern` (both its duplicate scan and its cross-link step), `review-loop` (which must also put the exclusion in the prompt of every review agent it dispatches), `update-targets`, and `uninstall`, where a placeholder with no `seeded: true` frontmatter would otherwise be misclassified as the user's own capture and kept. The manifest gained a `$precedence` rule for the same reason: three of the plugin's own files matched a `user_owned` pattern literally, which a strict reading would have made permanently uncorrectable.

- **The upgrade-time offer for new artifacts read like a changelog entry.** It described what `browser-testing` and `review-loop` *do* and never said why anyone would want them, while `/aiforging:setup` carried the actual reason ("a failing step means the product and the spec disagree, and deciding which one is wrong needs a person"). The asymmetry was backwards: at install time the user is already bought in, at upgrade time they are being interrupted about something they have never heard of. The spec was the weak link, not the execution — `update-targets` had only been told to give "an offer with an explanation." It now carries the same reason the install-time offer does.

- **Interim counts were off by one.** The pre-apply summary said "10 features" and "11 user-captured patterns" where the truth was 9 and 10, then self-corrected in the final summary. Cosmetic in effect, but both numbers appeared in the sentence describing *what is protected from modification* — the worst available place to be approximately right, since it is the figure a user checks before granting permission. Counts must now be derived from the same enumeration used to classify, and sets small enough to name are listed rather than counted.

### Added

- **`.aiforging/VERSION`** — a one-line stamp recording which plugin release a scope's copied artifacts correspond to, written by `setup` at onboarding and by `update-targets` after a successful run. Reversing a call made during v0.3.0 design, where it was deferred as unnecessary.

  The first real run had to *reconstruct* provenance: thirteen files showed as modified, most of them user customizations of files the release never touched, and separating those took several extra passes. It worked because the run was careful. A less careful one presents all thirteen as needing update, the user accepts, and their customizations are replaced — with backups, but backups nobody reads. With a stamp, `update-targets` can diff on-disk against the plugin *at the version the user installed* and know the difference. Absent (any workspace onboarded before 0.3.1), it falls back to inference, says so out loud, and defaults customized-looking files to skip rather than overwrite.

- **`templates/patterns-tier-README.md`** and **`templates/anti-patterns-tier-README.md`** — the tier placeholders.

### Notes for existing users

`/aiforging:update-targets` again. Everything here is additive and nothing under `docs/features/` is touched. This run will also write your first `.aiforging/VERSION`, offer any missing `.gitignore` rules, and install the tier placeholders — after which the "create the empty patterns directory?" prompt stops recurring.

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

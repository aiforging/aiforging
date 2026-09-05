# AI Forging

> A structured framework for **agentic software development** — test-first, pattern-driven refactoring, domain-driven architecture. **Built for teams.** Shipped as a Claude Code plugin. The counterpoint to vibe coding.

AI is extraordinary at generating code. Without structure, every feature it ships makes the codebase a little worse. AI Forging is that structure, as three stages of a metallurgical forge: **Fire → Hammer → Tempering.**

**Going agentic is easy. Going agentic without wrecking quality is the hard part.** Autonomy — how big a unit of work you hand the AI — and discipline — how much spec, testing and review wrap it — are different axes. Cross them and you get four very different places to build. AI Forging is the top-right.

<p align="center">
  <img src="docs/quadrant.png" alt="A map for agentic software development — autonomy versus discipline. Vibe Coding (low/low), Disciplined AI-Assist (high discipline, low autonomy), Agentic Vibe Coding (low discipline, high autonomy), and AI Forging (high discipline, high autonomy — the goal)." width="720"/>
</p>

- **Fire** — AI-powered TDD. The test is written first and captures intent before a line of implementation exists.
- **Hammer** — pattern-driven refactoring. One fresh-context subagent per pattern, in parallel, against just the changed files.
- **Tempering** — knowledge capture that scales. One correction, one pattern file. The 50th costs no more than the 5th.

Then two **optional** stages, after the feature is built. Neither writes a feature:

- **`browser-testing`** walks the feature's QA checklist in a real browser and reports what diverged. **It fixes nothing, deliberately** — a failing step means the product and the spec disagree, and deciding which is wrong needs a person.
- **`review-loop`** runs rounds of review, triage and fix across every repo the feature touched. The triage step is the point: roughly a third of review findings describe deliberate behavior.

<p align="center">
  <img src="docs/feature-workflow.svg" alt="Building a Feature with AI Forging — two entry points (forge and resume), then Fire, Hammer, Tempering, optional verification, and a final human gate for the full test suite" width="680"/>
</p>

## Built for teams

**The forge workspace is a git repository you share with your team.** One engineer creates it and pushes it; everyone else clones it and runs `/aiforging:join`.

That workspace holds every feature's spec, plan, QA checklist and review record. Kept on one laptop, all of it disappears the week that person is on vacation — and the framework's central claim, that knowledge lives in durable files instead of a chat transcript, quietly stops being true.

Shared, it means:

- **An engineer goes on holiday mid-feature.** Someone else runs `/aiforging:resume <feature>` and gets what's done, what's next, what was deliberately deferred, and any open findings. No handover meeting.

- **A feature from three months ago needs one more work item.** Point the AI at the feature folder and it re-reads the specs — the business intent *and* the engineering intent, as written at the time.

  This is the difference that compounds. The alternative is telling an AI "the code for this lives roughly in these folders, it currently does A, B and C, now I want X" — asking it to reconstruct the original *intent* from the *implementation*. That's tedious, error-prone, and the blind spots are large and quiet. A feature folder skips the reconstruction entirely.

- **Several people forge different features concurrently** against the same target repos, with one plan format and one shared pattern library.

- **One person's review catches something, and everyone's next feature benefits.** When an engineer spots the AI doing something less than ideal and runs `capture-pattern`, the lesson becomes a file every future Hammer pass checks — for every engineer, in every feature. Expertise that would otherwise have stayed in one pull request.

Two practices worth stealing: **one workspace per project**, committed as its own repo, and **one engineer owning a feature end to end** rather than splitting it between a backend and a frontend specialist. The AI writes the code; the guardrails are what make it reasonable for one person to review across the whole stack.

You can absolutely run a workspace solo — it works the same way. It just works for one person.

Three locations, three lifecycles, and it's worth knowing which is which:

| | What it is | Shared how |
|---|---|---|
| **The plugin** | Conventions, skills, commands | Installed per machine from a marketplace |
| **The forge workspace** | Feature specs, plans, pattern library | **A git repo your team clones** |
| **Your target repos** | The code being forged | Already yours; gains a committed `.aiforging/` |

## Installation

### 1. Install both plugins, once per machine

AI Forging depends on [`superpowers`](https://github.com/obra/superpowers) for the TDD loop, brainstorming, plan writing and subagent dispatch. **They come from different marketplaces:**

```
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-dev

/plugin marketplace add aiforging/aiforging
/plugin install aiforging@aiforging
```

`superpowers` is also on Anthropic's official marketplace as `superpowers@claude-plugins-official`. **AI Forging is not** — install it from `aiforging/aiforging`. `claude plugin list` shows the real identifier of anything you've installed.

> **Installing ≠ enabling.** Installing downloads the plugin to your machine. *Enabling* writes `{"enabledPlugins": {...}}` into a scope's `.claude/settings.json` — `/aiforging:setup` does that for you, and it's why teammates who clone a repo don't have to configure anything. But an `enabledPlugins` entry only points at a plugin; it doesn't contain one. Everyone still runs the install above once.

### 2a. Creating a workspace (first person on the team)

```
mkdir ~/forge && cd ~/forge && claude     # multiple repos
cd ~/my-monorepo && claude                # monorepo or single repo — the repo IS the workspace
```

Then `/aiforging:setup`. It asks how your codebase is organized, seeds the workspace, onboards your first target repo (detecting its stack, installing conventions, running an architecture audit), and commits the result as a git repo.

**Push it.** That's what makes the next section possible.

### 2b. Joining a workspace (everyone else)

```
git clone <your-team's-forge-workspace>
cd forge && claude
```

Then `/aiforging:join`. It reads the committed target registry, finds each target repo on your machine — offering to clone the ones you don't have — writes your own gitignored `settings.local.json`, and checks your plugin prerequisites. It does **not** re-onboard anything; the conventions and skills came with your clone.

You'll finish with a list of what the team is working on.

## Day-to-day usage

**Start a feature.** `/aiforging:forge my-feature "brief description"` — from any directory. Scaffolds the feature folder, captures your prompt into a spec, and walks you through scope and planning before any code is written. For work spanning repos, one spec covers all of them, with slices tagged per repo and a `[gate: contract]` on the API boundary.

**Pick up existing work.** `/aiforging:resume <feature>` — or with no argument, to choose from the list. Reads the spec, plan, notes, QA checklist and any open review escalations, then reports what's done, what's next, what was deliberately deferred, and who last touched it. Works the same whether you paused it on Friday or a teammate started it in March. It's read-only: it orients you and stops.

**Build.** Fire runs the TDD loop; `hammer-refactor` fires automatically at the end of each cycle, one subagent per applicable pattern, and you accept or reject each proposal.

**Capture a lesson.** When you correct Claude during review in a way that encodes a reusable rule, `capture-pattern` offers to persist it as one file. It's then checked on every future Hammer pass — by every engineer on the workspace, not just you. Your choice whether it applies to this repo or to every same-stack target.

**Verify.** `/aiforging:browser-testing` first, then `/aiforging:review-loop`. Both optional. Six rounds of review can't find a feature that works exactly as written and is wrong.

**Run your full test suite.** No AI Forging stage ever does. Every agent runs one named suite scoped to the feature at hand, because a fast loop is the whole point — and the skills tell you, in words, when it's your turn to run everything.

**Audit a codebase you inherited.** Onboard it with `/aiforging:setup` and the architecture analyzer produces a scored assessment with prioritized findings.

## Relationship to the `superpowers` plugin

AI Forging deliberately delegates its core loops to [`superpowers`](https://github.com/obra/superpowers) rather than reimplementing them: `test-driven-development` (Red/Green/Refactor), `brainstorming` (spec-before-code), `writing-plans`, `executing-plans`, and `subagent-driven-development` — the fresh-context dispatch that `hammer-refactor` is built on.

AI Forging adds what superpowers intentionally leaves to each team's architecture:

- **A prescriptive domain-centric layout** — single-action controllers, data-mapper repositories, value objects and DTOs, naming rules.
- **A test-harness capability contract** that makes the Fire stage trustworthy for data-driven code, plus the one-suite-per-feature rule that keeps the loop fast.
- **A pattern library** structured for one-subagent-per-pattern refactor passes, in two tiers, that grows one code review at a time.
- **A shared forge workspace** where features spanning several repos get one spec, one plan, and a history any teammate can resume from.
- **The skills** — `architecture-analyzer`, `hammer-refactor`, `capture-pattern`, `resume-feature`, and the optional `browser-testing` and `review-loop`.

If superpowers is *how*, AI Forging is *what you're building and how it should be shaped*.

## Upgrading

Two halves have to move, and git only carries one of them.

**The repo half** — the conventions, skills and pattern library copied into your workspace and targets. These are committed files. `git pull` gets them, and one person propagates them for everybody (below).

**The plugin half** — lives on your machine, not in git. Pulling never touches it.

```bash
claude plugin list                                         # note the marketplace and Scope
claude plugin marketplace update aiforging
claude plugin update aiforging@aiforging --scope project    # use YOUR scope
```

> **Use the scope `plugin list` reports.** Because `/aiforging:setup` writes plugin enablement into a project's settings, `aiforging` usually installs at **project** scope — while `claude plugin update` defaults to `user`. Omitting the flag gives you `Plugin "aiforging" is not installed at scope user`, which reads like "not installed" and means "wrong scope."

Then, from your workspace:

```
/aiforging:update-targets
```

It diffs every copied artifact against the new plugin version and asks before overwriting, backing up whatever it replaces. **Your feature folders and captured patterns are never touched.** Artifacts added since your version are presented as offers with an explanation, not installed silently.

Restart any running Claude session afterwards — an open one is still holding the old code.

**On a shared workspace, one person does this and commits the result.** Everyone else gets it with `git pull` — plus the `claude plugin update` line above, since that half is per-machine.

<details>
<summary>Starting over from scratch</summary>

Across major versions, or if a workspace feels tangled from experiments:

```
/aiforging:uninstall                                       # in Claude, from the workspace
claude plugin update aiforging@aiforging --scope <scope>    # in your terminal
/aiforging:setup                                           # back in Claude
```

`/aiforging:uninstall` preserves everything you made: all of `docs/features/`, your captured patterns, and any convention file you customized (it asks about those). You'll redo the scenario interview, target onboarding, and the analyzer run — the same flow as the first time, faster because your repos haven't changed.

</details>

## Removing it

```
/aiforging:uninstall
```

Removes every plugin-sourced artifact from the workspace and its targets — conventions, skills, seeded patterns, settings entries — and leaves your work alone: feature folders, captured patterns, and customized files (it asks before touching those). Idempotent, and it commits nothing.

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

**v0.4.0 — open source, MIT licensed.** The conventions library, `/aiforging:setup`, the shared-workspace flow, and six skills (`architecture-analyzer`, `hammer-refactor`, `capture-pattern`, `resume-feature`, `browser-testing`, `review-loop`) are in place and dogfooded against real production codebases by the author, a small team, and external testers. Symfony / PHP / Doctrine is the happy path; other stacks work to the extent that the conventions apply — which is substantial, but mileage will vary until dedicated adapters ship.

### What's new

**v0.4.0 — teams.** The forge workspace is now positioned and built as a **shared git repository** rather than a personal directory, which is what it was always meant to be. `/aiforging:join` wires a cloned workspace to a new engineer's machine; `/aiforging:resume` picks up a feature you didn't start and reports where it stands; `.aiforging/targets.json` is a committed registry of which repos a workspace forges — before this, that list existed only in a gitignored file, so a teammate who cloned a workspace could not discover its targets at all. Also: a generated feature index for discovery, and a corrected marketplace identifier (`aiforging@aiforging`; there is no `aiforging@claude-plugins-official`).

**v0.3.2** — fixes a workspace-detection regression introduced in 0.3.1: two marker phrasings exist in the wild and 0.3.1 matched only the newer one, so `/aiforging:new-feature` would refuse to run in workspaces onboarded earlier. Take this before upgrading targets.

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

The most useful contribution is still the same: run it on a real codebase and open an issue about what broke. See `CONTRIBUTING.md`.

## Author

[Chris Holland](https://linkedin.com/in/chrisholland) — the guy who [coined](https://www.linkedin.com/feed/update/urn:li:activity:7445936135371083776/?originTrackingId=j81PqnmwyBMk4rNkIUCzbQ%3D%3D) "AI Forging" as a counterpoint to vibe coding.

- Website: [aiforging.dev](https://aiforging.dev)

## License

MIT. See `LICENSE`.

## Acknowledgments

- [Jesse Vincent](https://github.com/obra) and the contributors to [`superpowers`](https://github.com/obra/superpowers) for the TDD, plan-writing, plan-execution, and subagent-dispatch skills that AI Forging builds on.
- [Srdjan Vranac](https://github.com/vranac) for [`claude-session-export-obsidian`](https://github.com/vranac/claude-session-export-obsidian), which served as the structural reference for this plugin.

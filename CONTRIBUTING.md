# Contributing to AI Forging

Thanks for being here. AI Forging is a young, opinionated framework, and the most valuable thing anyone can do for it right now is **run it against a real codebase and report what broke.**

## The most useful contribution

Open an issue. Really.

The plugin has been dogfooded against Symfony/PHP/Doctrine backends and React/TypeScript frontends by the author and a handful of external testers. Every one of those runs surfaced something — a detector that misread a Dockerized layout, a prompt that defaulted the wrong way, a convention that assumed a directory structure that isn't universal. Those reports are what v0.2.0 and v0.3.0 were built from.

A good issue tells us:

- **What you ran** — the command, and which phase or step it was in.
- **What your codebase looks like** — stack, framework, whether it's a monorepo, and anything unusual about the layout (a service wrapper, a non-standard test directory, a workspace tool).
- **What you expected, and what happened.**
- **Whether you could work around it**, and how.

You do not need to propose a fix. A precise description of a wrong assumption is worth more than a patch that papers over it.

## What the project is opinionated about

Some things are deliberate and will not change without a strong argument. Knowing them up front saves everyone a round trip:

- **Prescriptive, not descriptive.** The conventions tell you to restructure things. That's the point. "This doesn't match how my team already works" is not, by itself, a bug — though "this is impossible on my stack" absolutely is.
- **Test-first, never test-after.** Order changes what a test measures. A test written first asks *does this match the intended outcome*; a test written after quietly shrinks to *does this match the code I already wrote*.
- **One pattern, one file.** No monolithic rules document. The pattern library scales precisely because the 50th pattern costs the same as the 5th — each gets its own file and its own fresh-context subagent.
- **Nothing runs your full test suite.** Every agent run is scoped to one named suite per feature. See `conventions/tdd/feature-test-suite.md` for why, including the regression risk that trades against and the handoff that covers it.
- **`browser-testing` never fixes what it finds.** A failing checklist step means the product and the spec disagree. Which one is wrong is a human decision.
- **Delegate to `superpowers`, don't reimplement it.** The TDD loop, brainstorming, plan writing, plan execution, and subagent dispatch all come from [`superpowers`](https://github.com/obra/superpowers). AI Forging is the architecture-and-domain layer on top. A PR that reimplements one of those will be declined.

## Testing the upgrade path

`/aiforging:update-targets` is the command the whole framework leans on and the one least exercised. If you have a workspace that predates the current release, running this and reporting what happened is worth more than most code contributions.

**Set up an honest "before".** The interesting case is a workspace that was genuinely onboarded at an older version, with at least two targets and, ideally, one onboarded before the two-tier pattern model. A fresh workspace created five minutes ago tests nothing, because there is no drift to reconcile.

Make the result measurable before you start. In the workspace and in each target repo:

```bash
git status --short && git rev-parse --short HEAD
```

Commit or stash anything outstanding. A dirty tree makes it impossible to tell afterwards what the command did and what you did.

**Then upgrade** — the plugin, then the propagation — following [Light upgrade](#light-upgrade-recommended) in the README.

**Then check these, in this order.** The first three are correctness; the rest are whether it is pleasant to use.

1. **Nothing under `docs/features/` changed.** Not a spec, not a plan, not a `testing.md`, not an `ai-testing/` or `ai-reviews/` record. The one permitted exception is `docs/features/README.md`, which is the installed convention. `git status` in the workspace is the check, and any other change here is a serious bug — report it immediately.
2. **User-captured patterns survived.** Every `.md` in a `patterns/` or `anti-patterns/` directory *without* `seeded: true` frontmatter must be byte-identical afterwards, in both tiers.
3. **`.aiforging/ANALYSIS.md` was not touched** in any target. It describes your codebase, not the plugin.
4. **New artifacts arrived as offers, not surprises.** Anything added since your installed version should have been presented with a line saying what it does, and you should have been able to decline it. If something appeared without being offered, say so.
5. **Previously-declined optional artifacts stayed declined.** If you said no to the Playwright conventions at onboarding, they should not have reappeared.
6. **Backups exist for anything overwritten** — `*.bak-*` next to the original. Note that target repos are separate git repos whose `.gitignore` may not cover that pattern.
7. **The summary told you what changed in *behavior*,** not just which files moved. If you finished the run unsure what is now different about how the framework works, that is a real finding even though nothing crashed.

**Report it either way.** A run that went cleanly is as useful to know about as one that broke — open a [field report](https://github.com/aiforging/aiforging/issues/new?template=field-report.yml) with your stack, how old the workspace was, how many targets, and which of the seven checks you actually verified. Please say which ones you *didn't* check rather than leaving them ambiguous; "I verified 1-3 and didn't look at the rest" is a useful report, and "seemed fine" is not.

## Contributing a pattern or anti-pattern

The pattern library is where contributions compound fastest, and it's the easiest place to start.

One file per pattern, in `conventions/refactoring/patterns/` or `conventions/refactoring/anti-patterns/`. Follow the format documented in `conventions/refactoring/README.md`. Every file needs:

- A **name** — an imperative verb phrase for a pattern ("Extract Service From Controller"), a noun phrase for an anti-pattern ("Fat Controller").
- **Detection signals** — how to spot it in code, concretely. A subagent greps against these. "The class feels too big" is not a signal; "a controller method longer than N lines that constructs more than one collaborator" is.
- **Severity** — Critical / High / Medium / Low / Info.
- **Why it matters** — the failure it causes, not the aesthetic it violates.
- **A before and after** — minimal code, illustrating the actual refactor.
- **Related patterns** — what to reach for next.
- **`applies-to` frontmatter**, listing the stack identifiers it applies to, or `all`.

The bar: **a fresh-context subagent that reads only your file, with no other knowledge of the codebase, must be able to find the problem and fix it correctly.** If your file needs a paragraph of surrounding context to be actionable, it is not done yet.

## Contributing a convention

Conventions live in `conventions/` and are copied into every onboarded target repo. They are load-bearing — a convention that's wrong for a stack produces misplaced code across every subagent that trusts it.

Before opening a PR:

1. **Say what problem it solves and what it costs.** Every convention constrains something. If you can't name the cost, the convention isn't understood well enough yet.
2. **Say which stacks it applies to**, and what teams on other stacks should do instead.
3. **Check it against `conventions/README.md`'s five principles.** A convention that contradicts one of them needs to argue with the principle, not sidestep it.

## Contributing a stack adapter

The biggest open gap. Laravel, Spring/Java, .NET/C#, and Node/TS all deserve first-class support and don't have it yet.

An adapter is not a rewrite of the conventions — it is the mapping from this framework's requirements onto that stack's idioms. Start with `conventions/tdd/test-harness-requirements.md`, which already lists what a conforming harness must do and names the standard approach for several ORMs. An adapter needs:

1. A documented test-harness setup for the stack — one page, copy-pasteable config.
2. A smoke-test command confirming each of the harness capabilities.
3. A sample factory for one entity, in that stack's idiom.
4. A sample repository test showing transaction-based isolation and schema-from-metadata.
5. Detection signals for `scripts/detect-project.py`.

Where the stack genuinely cannot satisfy a requirement cleanly, **document the closest workaround and name its trade-offs** rather than pretending the gap isn't there.

Open an issue before starting one of these. They're large, and it's worth agreeing on the shape first.

## Adding an artifact to the plugin

If your change adds anything the plugin *copies* into a workspace or a target repo — a skill, a convention directory, a template, a seeded pattern — **it must be registered in `.claude-plugin/artifacts.json`.**

This is not bookkeeping. `/aiforging:setup`, `/aiforging:update-targets`, and `/aiforging:uninstall` all read that manifest. An artifact missing from it will install on fresh setups and never reach anyone who is already using the plugin — silently, with nothing to notice. That exact failure is why the manifest exists.

## Developing the plugin locally

Test without going through the marketplace install flow:

```bash
# From a directory you want to test the plugin in — e.g. an empty ~/forge-test:
claude --plugin-dir /path/to/your/aiforging/checkout
```

`--plugin-dir` loads your local copy *in addition* to everything installed from marketplaces, and a local copy wins over an installed one of the same name. It reads from disk every time — no cache to fight. After editing a command, skill, or script, run `/reload-plugins` inside the session to pick up the change without restarting.

The full dogfood loop is in `CLAUDE.md`, along with the three-layer model (plugin source ≠ forge workspace ≠ target repo) that every change has to respect. **Read `CLAUDE.md` and `PLAN.md` before your first PR** — `PLAN.md` holds the locked-in decisions and the session log, and a PR that relitigates a locked decision without engaging with why it was locked will get a link rather than a review.

## Pull requests

- **One concern per PR.** A pattern, a convention, a bug fix, an adapter — not several at once.
- **Update `CHANGELOG.md`** under an `## [Unreleased]` heading, in the Keep a Changelog format already in use. Say what changed *in behavior*, not just which files moved.
- **Update both copies when a convention is mirrored.** `conventions/features/README.md` and `templates/docs-features-README.md` say the same things to different audiences and must not drift. `CLAUDE.md` lists the other mirrored pairs.
- **Smoke-test the scripts** if you touched them: `uv run scripts/detect-project.py` and `uv run scripts/configure-directories.py check --settings-file <path>` must both work, and so must the `python3` fallback — they're PEP 723 single-file scripts with no third-party dependencies, and `commands/setup.md` probes for `uv` and falls back at runtime.

## Code of conduct

Be decent. Assume the person on the other side is trying to build something good. Disagree with the argument, not the person making it.

## License

By contributing, you agree that your contributions are licensed under the MIT License, the same as the rest of the project.

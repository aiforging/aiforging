# AI Forging — Conventions Library

This directory is the portable, prescriptive layer of the AI Forging framework. When you run `/aiforging:setup`, the contents of this folder are copied into each backend project you confirm as `<project>/.aiforging/`.

The conventions are organized into four groups:

- **architecture/** — how we structure code: Domain-Driven Hexagonal layout, Single-Action Controllers, Repositories, DTOs / Value Objects, naming.
- **tdd/** — how we test-drive: the Fire (Red-Green-Refactor) loop, the test-harness capability contract, how we test Repositories against a real isolated schema.
- **refactoring/** — the pattern and anti-pattern library. One `.md` per pattern. New patterns can be added at any time; the framework's post-TDD refactor pass iterates each one independently via a fresh-context sub-agent, so adding the 50th pattern costs no more than the 5th.
- **frontend-testing/** — optional. Playwright-oriented guidance for integration tests between frontend and backend. Not required by the core framework.

## How Claude should use these files

When you open this project with Claude, it should treat the files under `.aiforging/architecture/` and `.aiforging/tdd/` as prescriptive — the shape of new code must match them. The files under `.aiforging/refactoring/` are a library of named patterns to apply during the post-TDD refactor pass. New patterns belong in the library as soon as they're observed; don't inline them in `CLAUDE.md`.

## Principles (the very short version)

1. **Write the test before the code.** Every feature begins with a failing test.
2. **Refactor with a pattern library, not a prayer.** Post-TDD refactor iterates each pattern file against changed files.
3. **Capture knowledge that scales without ceilings.** One pattern, one file. No monolithic CLAUDE.md.
4. **Let AI generate. Let humans govern.** AI proposes. Humans review and merge.
5. **Compound quality, not just features.** Each cycle leaves the codebase stronger.

For the full framework context, see the AI Forging plugin's public `README.md` on GitHub. Do NOT attempt to read files inside the plugin source repo from this target repo — the plugin is installed user-globally (via Claude Code's plugin system) and its source is not intended to be browsed or modified from end-user target repos.
